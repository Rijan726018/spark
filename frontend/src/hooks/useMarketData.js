/**
 * useMarketData — WebSocket hook for live market data
 *
 * Connects to ws://localhost:8000/ws/market and maintains:
 *   bars[symbol]   → array of {time, open, high, low, close, volume}  (newest last)
 *   trades[algoId] → array of {time, side, price, qty, symbol, algo_id}
 *   connected      → WebSocket state
 *   ntConnected    → NinjaTrader bridge status
 *   brokerConnected→ IB broker status
 *   activeAlgos    → number of live algos
 */

import { useEffect, useRef, useState, useCallback } from 'react';

const WS_URL = `${import.meta.env.VITE_WS_URL || 'ws://localhost:8000'}/ws/market`;
const MAX_BARS_PER_SYMBOL = 2000;
const MAX_TRADES_PER_ALGO = 500;
const INITIAL_BACKOFF_MS  = 1_000;
const MAX_BACKOFF_MS       = 30_000;

export default function useMarketData() {
  const wsRef            = useRef(null);
  const backoffRef       = useRef(INITIAL_BACKOFF_MS);
  const reconnectTimer   = useRef(null);
  const mountedRef       = useRef(true);
  const pingTimer        = useRef(null);

  const [connected,       setConnected]       = useState(false);
  const [ntConnected,     setNtConnected]     = useState(false);
  const [brokerConnected, setBrokerConnected] = useState(false);
  const [activeAlgos,     setActiveAlgos]     = useState(0);

  // Bars per symbol: { ES: [{time,open,high,low,close,volume}, ...] }
  const [bars,   setBars]   = useState({});
  // Trades per algo: { "001": [{type,algo_id,symbol,side,price,qty,time}, ...] }
  const [trades, setTrades] = useState({});
  // All trades flat list (for trade log table)
  const [allTrades, setAllTrades] = useState([]);
  // Last bar per symbol (for quick price display)
  const [lastBar, setLastBar] = useState({});

  // ── Message handlers ────────────────────────────────────────────────────────

  const handleBar = useCallback((msg) => {
    const { symbol, bar } = msg;
    if (!symbol || !bar) return;

    setBars(prev => {
      const existing = prev[symbol] || [];
      // Update-or-append: if last bar has same timestamp, update it; else append
      let updated;
      if (existing.length > 0 && existing[existing.length - 1].time === bar.time) {
        updated = [...existing.slice(0, -1), bar];
      } else {
        updated = [...existing, bar];
        if (updated.length > MAX_BARS_PER_SYMBOL) {
          updated = updated.slice(updated.length - MAX_BARS_PER_SYMBOL);
        }
      }
      return { ...prev, [symbol]: updated };
    });

    setLastBar(prev => ({ ...prev, [symbol]: bar }));
  }, []);

  const handleExecution = useCallback((msg) => {
    const algoId = String(msg.algo_id || 'unknown');
    const trade  = { ...msg, algo_id: algoId };

    setTrades(prev => {
      const existing = prev[algoId] || [];
      const updated  = [...existing, trade];
      if (updated.length > MAX_TRADES_PER_ALGO) {
        updated.splice(0, updated.length - MAX_TRADES_PER_ALGO);
      }
      return { ...prev, [algoId]: updated };
    });

    setAllTrades(prev => {
      const updated = [trade, ...prev];  // newest first
      return updated.slice(0, 1000);
    });
  }, []);

  const handleStatus = useCallback((msg) => {
    setNtConnected(!!msg.nt_connected);
    setBrokerConnected(!!msg.broker_connected);
    if (typeof msg.active_algos === 'number') setActiveAlgos(msg.active_algos);
  }, []);

  // ── WebSocket lifecycle ─────────────────────────────────────────────────────

  const connect = useCallback(() => {
    if (!mountedRef.current) return;

    try {
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        if (!mountedRef.current) { ws.close(); return; }
        backoffRef.current = INITIAL_BACKOFF_MS;
        setConnected(true);

        // Send ping every 25s to keep connection alive
        if (pingTimer.current) clearInterval(pingTimer.current);
        pingTimer.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'ping' }));
          }
        }, 25_000);
      };

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          switch (msg.type) {
            case 'bar':       handleBar(msg);       break;
            case 'tick':      /* ignore ticks for chart, bars only */ break;
            case 'execution': handleExecution(msg); break;
            case 'status':    handleStatus(msg);    break;
            case 'pong':      /* keepalive ack */   break;
            default:          break;
          }
        } catch (e) {
          // Ignore malformed messages
        }
      };

      ws.onerror = () => {
        // Errors are followed by onclose, handle reconnection there
      };

      ws.onclose = () => {
        if (pingTimer.current) clearInterval(pingTimer.current);
        if (!mountedRef.current) return;
        setConnected(false);
        setNtConnected(false);

        // Exponential backoff reconnect
        const delay = backoffRef.current;
        backoffRef.current = Math.min(delay * 2, MAX_BACKOFF_MS);
        reconnectTimer.current = setTimeout(connect, delay);
      };

    } catch (e) {
      // WebSocket constructor threw — retry
      reconnectTimer.current = setTimeout(connect, backoffRef.current);
      backoffRef.current = Math.min(backoffRef.current * 2, MAX_BACKOFF_MS);
    }
  }, [handleBar, handleExecution, handleStatus]);

  useEffect(() => {
    mountedRef.current = true;
    connect();

    return () => {
      mountedRef.current = false;
      if (pingTimer.current)    clearInterval(pingTimer.current);
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      if (wsRef.current) {
        wsRef.current.onclose = null; // prevent reconnect on intentional close
        wsRef.current.close();
      }
    };
  }, [connect]);

  // ── Expose seedBars for initial REST data load ──────────────────────────────

  const seedBars = useCallback((symbol, barsArray) => {
    setBars(prev => {
      const existing = prev[symbol] || [];
      if (existing.length >= barsArray.length) return prev;  // already have more
      return { ...prev, [symbol]: barsArray };
    });
    if (barsArray.length > 0) {
      setLastBar(prev => ({ ...prev, [symbol]: barsArray[barsArray.length - 1] }));
    }
  }, []);

  const seedTrades = useCallback((algoId, tradesArray) => {
    setTrades(prev => {
      if ((prev[algoId] || []).length >= tradesArray.length) return prev;
      return { ...prev, [algoId]: tradesArray };
    });
    // Also merge into allTrades (sorted newest first)
    setAllTrades(prev => {
      const existing = new Set(prev.map(t => `${t.algo_id}-${t.time}-${t.price}`));
      const newTrades = tradesArray.filter(
        t => !existing.has(`${t.algo_id}-${t.time}-${t.price}`)
      );
      return [...newTrades, ...prev].slice(0, 1000);
    });
  }, []);

  return {
    // Connection state
    connected,
    ntConnected,
    brokerConnected,
    activeAlgos,

    // Data
    bars,       // { [symbol]: Bar[] }
    trades,     // { [algoId]: Trade[] }
    allTrades,  // Trade[] newest first
    lastBar,    // { [symbol]: Bar }

    // Seeding from REST
    seedBars,
    seedTrades,
  };
}
