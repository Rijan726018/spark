/**
 * Dashboard — Full trading terminal layout
 *
 * Layout:
 *   ┌─────────────────────────────────────────────────────┐
 *   │  TOP BAR (logo | status | clock | account P&L)       │
 *   ├─────────┬───────────────────────────┬───────────────┤
 *   │ SIDEBAR │ CHART AREA                │ DETAILS PANEL │
 *   │ Algos   │ ChartHeader               │ Win Rate      │
 *   │         │ TradingViewChart          │ Stats         │
 *   │         │ VolumePane                │ Today Trades  │
 *   ├─────────┴───────────────────────────┴───────────────┤
 *   │  TRADE LOG (execution table)                         │
 *   └─────────────────────────────────────────────────────┘
 */

import React, { useState, useEffect, useRef } from 'react';
import AlgoSidebar     from '../components/AlgoSidebar';
import TradingViewChart from '../components/TradingViewChart';
import TradeLog        from '../components/TradeLog';
import useMarketData   from '../hooks/useMarketData';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// ── Helpers ───────────────────────────────────────────────────────────────────

function useNow() {
  const [now, setNow] = useState(new Date());
  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(id);
  }, []);
  return now;
}

function fmtTime(d) {
  return d.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

function fmtPnl(v) {
  if (v == null) return '--';
  const s = v >= 0 ? '+' : '';
  return `${s}$${Math.abs(v).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

// ── Status dot ────────────────────────────────────────────────────────────────
function StatusDot({ label, active, color = '#00ff88' }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
      <div style={{
        width:        '7px',
        height:       '7px',
        borderRadius: '50%',
        background:   active ? color : '#333',
        boxShadow:    active ? `0 0 5px ${color}` : 'none',
        transition:   'all 0.3s',
      }} />
      <span style={{ fontSize: '10px', color: active ? '#aaa' : '#444', fontFamily: 'monospace' }}>
        {label}
      </span>
    </div>
  );
}

// ── Top Bar ───────────────────────────────────────────────────────────────────
function TopBar({ connected, ntConnected, brokerConnected, activeAlgos, account, onRefresh }) {
  const now = useNow();
  const pnlColor = account.daily_pnl >= 0 ? '#00d4aa' : '#ff3366';

  return (
    <div style={{
      height:         '44px',
      minHeight:      '44px',
      background:     '#040404',
      borderBottom:   '1px solid rgba(255,255,255,0.07)',
      display:        'flex',
      alignItems:     'center',
      padding:        '0 16px',
      gap:            '20px',
      flexShrink:     0,
      WebkitAppRegion:'drag',  // Electron drag region
      userSelect:     'none',
    }}>
      {/* Logo */}
      <div style={{
        fontFamily:  "'JetBrains Mono', monospace",
        fontSize:    '13px',
        fontWeight:  '700',
        color:       '#00d4aa',
        letterSpacing:'0.12em',
        flexShrink:  0,
        WebkitAppRegion:'no-drag',
      }}>
        NEXUS
      </div>
      <div style={{ fontSize: '9px', color: '#333', letterSpacing: '0.1em', flexShrink: 0 }}>
        ALGO TERMINAL v3.0
      </div>

      <div style={{ width: '1px', height: '20px', background: 'rgba(255,255,255,0.08)' }} />

      {/* Status indicators */}
      <div style={{ display: 'flex', gap: '14px', WebkitAppRegion:'no-drag' }}>
        <StatusDot label="WS"     active={connected}       color="#00ff88" />
        <StatusDot label="NT"     active={ntConnected}     color="#00d4aa" />
        <StatusDot label="BROKER" active={brokerConnected} color="#ffa500" />
      </div>

      <div style={{ flex: 1 }} />

      {/* Active algos */}
      <div style={{ fontSize: '10px', color: '#666', fontFamily: 'monospace' }}>
        <span style={{ color: '#00ff88' }}>{activeAlgos}</span> LIVE
      </div>

      <div style={{ width: '1px', height: '20px', background: 'rgba(255,255,255,0.08)' }} />

      {/* Account P&L */}
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '1px', WebkitAppRegion:'no-drag' }}>
        <span style={{ fontSize: '9px', color: '#555' }}>DAY P&L</span>
        <span style={{ fontSize: '13px', color: pnlColor, fontFamily: 'monospace', fontWeight: '600' }}>
          {fmtPnl(account.daily_pnl)}
        </span>
      </div>

      <div style={{ width: '1px', height: '20px', background: 'rgba(255,255,255,0.08)' }} />

      {/* Balance */}
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '1px' }}>
        <span style={{ fontSize: '9px', color: '#555' }}>BALANCE</span>
        <span style={{ fontSize: '11px', color: '#ccc', fontFamily: 'monospace' }}>
          ${account.balance?.toLocaleString('en-US', { minimumFractionDigits: 0 }) ?? '--'}
        </span>
      </div>

      <div style={{ width: '1px', height: '20px', background: 'rgba(255,255,255,0.08)' }} />

      {/* Clock */}
      <div style={{
        fontFamily:  'monospace',
        fontSize:    '12px',
        color:       '#888',
        letterSpacing:'0.05em',
        WebkitAppRegion:'no-drag',
        minWidth:    '75px',
      }}>
        {fmtTime(now)}
      </div>
    </div>
  );
}

// ── Chart header ──────────────────────────────────────────────────────────────
function ChartHeader({ algo, lastBar }) {
  if (!algo) return null;
  const bar = lastBar;
  const chg    = bar ? bar.close - bar.open : 0;
  const chgPct = bar && bar.open ? (chg / bar.open) * 100 : 0;
  const chgColor = chg >= 0 ? '#00d4aa' : '#ff3366';

  return (
    <div style={{
      display:      'flex',
      alignItems:   'center',
      gap:          '16px',
      padding:      '6px 14px',
      background:   '#040404',
      borderBottom: '1px solid rgba(255,255,255,0.05)',
      flexShrink:   0,
    }}>
      {/* Algo identifier */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1px' }}>
        <span style={{ fontSize: '11px', color: '#fff', fontWeight: '600', letterSpacing: '0.03em' }}>
          {algo.symbol} <span style={{ color: '#555' }}>·</span> {algo.tf}
        </span>
        <span style={{ fontSize: '9px', color: '#555' }}>#{algo.id} {algo.name}</span>
      </div>

      {/* OHLC readout */}
      {bar && (
        <>
          <div style={{ width: '1px', height: '28px', background: 'rgba(255,255,255,0.06)' }} />
          {[
            ['O', bar.open],
            ['H', bar.high],
            ['L', bar.low],
            ['C', bar.close],
          ].map(([label, val]) => (
            <div key={label} style={{ display: 'flex', flexDirection: 'column', gap: '0px' }}>
              <span style={{ fontSize: '8px', color: '#444' }}>{label}</span>
              <span style={{ fontSize: '11px', color: '#ccc', fontFamily: 'monospace' }}>
                {val?.toFixed(2)}
              </span>
            </div>
          ))}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0px' }}>
            <span style={{ fontSize: '8px', color: '#444' }}>CHG</span>
            <span style={{ fontSize: '11px', color: chgColor, fontFamily: 'monospace', fontWeight: '600' }}>
              {chg >= 0 ? '+' : ''}{chg.toFixed(2)} ({chgPct >= 0 ? '+' : ''}{chgPct.toFixed(2)}%)
            </span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0px' }}>
            <span style={{ fontSize: '8px', color: '#444' }}>VOL</span>
            <span style={{ fontSize: '11px', color: '#888', fontFamily: 'monospace' }}>
              {bar.volume?.toLocaleString()}
            </span>
          </div>
        </>
      )}

      <div style={{ flex: 1 }} />

      {/* Status badge */}
      <span style={{
        fontSize:     '9px',
        color:        algo.status === 'LIVE' ? '#00ff88' : '#888',
        background:   algo.status === 'LIVE' ? 'rgba(0,255,136,0.1)' : 'rgba(136,136,136,0.1)',
        padding:      '2px 8px',
        borderRadius: '4px',
        fontWeight:   '600',
        letterSpacing:'0.05em',
      }}>
        {algo.status}
      </span>
    </div>
  );
}

// ── Algo details panel ────────────────────────────────────────────────────────
function AlgoDetails({ algo, trades = [] }) {
  if (!algo) {
    return (
      <div style={{
        width: '200px', minWidth: '200px',
        background: '#040404',
        borderLeft: '1px solid rgba(255,255,255,0.06)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        color: '#333', fontSize: '11px',
      }}>
        Select an algo
      </div>
    );
  }

  const recentTrades = trades.slice(-10).reverse();
  const wins  = recentTrades.filter((_, i, arr) => {
    // Simplified: alternate BUY/SELL pairs
    return arr[i]?.side === 'SELL';
  }).length;

  const statRows = [
    ['WIN RATE',       `${algo.win_rate?.toFixed(1) ?? '--'}%`,      algo.win_rate >= 55 ? '#00d4aa' : '#ffa500'],
    ['PROFIT FACTOR',  algo.profit_factor?.toFixed(2) ?? '--',        '#aaa'],
    ['MAX DD',         algo.max_dd ? `-${(algo.max_dd * 100).toFixed(1)}%` : '--', '#ff4444'],
    ['TIMEFRAME',      algo.tf,                                        '#888'],
    ['MARKET',         algo.symbol,                                    '#888'],
    ['ENGINE',         algo.engine || '--',                             '#555'],
    ['CATEGORY',       algo.category || '--',                           '#7b68ee'],
  ];

  return (
    <div style={{
      width:        '200px',
      minWidth:     '200px',
      background:   '#040404',
      borderLeft:   '1px solid rgba(255,255,255,0.06)',
      display:      'flex',
      flexDirection:'column',
      overflow:     'hidden',
    }}>
      {/* Header */}
      <div style={{
        padding:     '7px 10px',
        borderBottom:'1px solid rgba(255,255,255,0.05)',
        fontSize:    '9px',
        color:       '#555',
        letterSpacing:'0.06em',
        fontWeight:  '600',
        flexShrink:  0,
      }}>
        ALGO DETAILS
      </div>

      {/* Description */}
      <div style={{ padding: '8px 10px', borderBottom: '1px solid rgba(255,255,255,0.04)', flexShrink: 0 }}>
        <div style={{ fontSize: '11px', color: '#ccc', fontWeight: '600', marginBottom: '4px' }}>
          {algo.name}
        </div>
        <div style={{
          fontSize:   '9px',
          color:      '#555',
          lineHeight: '1.5',
          maxHeight:  '60px',
          overflow:   'hidden',
          display:    '-webkit-box',
          WebkitLineClamp: 4,
          WebkitBoxOrient: 'vertical',
        }}>
          {algo.desc || algo.description || 'No description available.'}
        </div>
      </div>

      {/* Stats grid */}
      <div style={{ padding: '6px 0', borderBottom: '1px solid rgba(255,255,255,0.04)', flexShrink: 0 }}>
        {statRows.map(([label, value, color]) => (
          <div key={label} style={{
            display:        'flex',
            justifyContent: 'space-between',
            padding:        '3px 10px',
          }}>
            <span style={{ fontSize: '9px', color: '#444' }}>{label}</span>
            <span style={{ fontSize: '10px', color: color, fontFamily: 'monospace', fontWeight: '600' }}>
              {value}
            </span>
          </div>
        ))}
      </div>

      {/* Recent trades */}
      <div style={{ padding: '6px 10px 4px', flexShrink: 0 }}>
        <div style={{ fontSize: '9px', color: '#555', marginBottom: '5px', letterSpacing: '0.06em' }}>
          RECENT FILLS
        </div>
        {recentTrades.length === 0 && (
          <div style={{ fontSize: '9px', color: '#333' }}>No fills yet</div>
        )}
        {recentTrades.slice(0, 8).map((t, i) => {
          const d = new Date(t.time * 1000);
          const ts = `${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`;
          const isBuy = t.side === 'BUY';
          return (
            <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '2px 0' }}>
              <span style={{ fontSize: '9px', color: isBuy ? '#00d4aa' : '#ff3366', fontWeight: '600' }}>
                {isBuy ? '▲' : '▼'} {t.side}
              </span>
              <span style={{ fontSize: '9px', color: '#888', fontFamily: 'monospace' }}>
                {t.price?.toFixed(2)}
              </span>
              <span style={{ fontSize: '9px', color: '#444' }}>{ts}</span>
            </div>
          );
        })}
      </div>

      <div style={{ flex: 1 }} />

      {/* Params */}
      {algo.params && Object.keys(algo.params).length > 0 && (
        <div style={{ padding: '6px 10px', borderTop: '1px solid rgba(255,255,255,0.04)' }}>
          <div style={{ fontSize: '9px', color: '#333', marginBottom: '4px', letterSpacing: '0.05em' }}>
            PARAMETERS
          </div>
          {Object.entries(algo.params).slice(0, 6).map(([k, v]) => (
            <div key={k} style={{ display: 'flex', justifyContent: 'space-between', padding: '1px 0' }}>
              <span style={{ fontSize: '8px', color: '#333' }}>{k}</span>
              <span style={{ fontSize: '8px', color: '#555', fontFamily: 'monospace' }}>{String(v)}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Synthetic placeholder bars (shown until live data arrives) ────────────────
function makePlaceholderBars(symbol = 'ES', count = 200) {
  const seedMap = { ES: 5200, NQ: 21000, MNQ: 21000, MES: 5200, GC: 2300, CL: 80, YM: 42000 };
  const basePrice = seedMap[symbol.replace('=F','').toUpperCase()] || 1000;
  const now    = Math.floor(Date.now() / 1000);
  const tf5m   = 5 * 60;
  const bars   = [];
  let price    = basePrice;
  for (let i = count - 1; i >= 0; i--) {
    const chg   = (Math.random() - 0.49) * basePrice * 0.001;
    const open  = price;
    price       = Math.max(price + chg, basePrice * 0.8);
    const close = price;
    const hi    = Math.max(open, close) + Math.random() * basePrice * 0.0005;
    const lo    = Math.min(open, close) - Math.random() * basePrice * 0.0005;
    bars.push({
      time:   now - i * tf5m,
      open:   parseFloat(open.toFixed(2)),
      high:   parseFloat(hi.toFixed(2)),
      low:    parseFloat(lo.toFixed(2)),
      close:  parseFloat(close.toFixed(2)),
      volume: Math.floor(500 + Math.random() * 2000),
    });
  }
  return bars;
}

// ── PAMM Master Trade Panel ──────────────────────────────────────────────────

const STATUS_COLOR = { idle: '#444', sending: '#ffa500', queued: '#00d4aa', error: '#ff3366' };
const STATUS_LABEL = { idle: 'READY', sending: 'SENDING…', queued: 'QUEUED ✓', error: 'ERROR' };

function PammPanel({ onTrade }) {
  const [symbol,   setSymbol]   = useState('ES');
  const [action,   setAction]   = useState('Buy');
  const [quantity, setQuantity] = useState('1');
  const [status,   setStatus]   = useState('idle');   // idle | sending | queued | error
  const [log,      setLog]      = useState([]);

  const addLog = (msg, color = '#aaa') =>
    setLog(prev => [{ msg, color, ts: new Date().toLocaleTimeString('en-US', { hour12: false }) }, ...prev].slice(0, 40));

  const handleFire = async () => {
    const qty = parseFloat(quantity);
    if (!qty || qty <= 0) { addLog('⚠ Invalid quantity', '#ffa500'); return; }
    setStatus('sending');
    addLog(`► Firing ${action.toUpperCase()} ${qty} ${symbol} to PAMM router…`, '#ffa500');
    try {
      const res = await fetch(`${API}/api/trade`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ symbol, action, quantity: qty }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }
      const data = await res.json();
      setStatus('queued');
      addLog(`✅ Queued: ${data.signal}`, '#00d4aa');
      addLog(`   ↳ ${data.message}`, '#555');
      if (onTrade) onTrade(data);
      setTimeout(() => setStatus('idle'), 3000);
    } catch (err) {
      setStatus('error');
      addLog(`❌ Failed: ${err.message}`, '#ff3366');
      setTimeout(() => setStatus('idle'), 4000);
    }
  };

  const col  = STATUS_COLOR[status];
  const isBusy = status === 'sending';

  return (
    <div id="pamm-panel" style={{
      borderTop:      '1px solid rgba(255,255,255,0.07)',
      background:     '#040404',
      display:        'flex',
      alignItems:     'stretch',
      gap:            0,
      flexShrink:     0,
      height:         '62px',
      overflow:       'hidden',
    }}>

      {/* Left label */}
      <div style={{
        display:        'flex',
        flexDirection:  'column',
        justifyContent: 'center',
        padding:        '0 14px',
        borderRight:    '1px solid rgba(255,255,255,0.06)',
        minWidth:       '90px',
      }}>
        <span style={{ fontSize: '7.5px', color: '#333', letterSpacing: '0.1em', fontWeight: '700' }}>PAMM ROUTER</span>
        <span style={{ fontSize: '9px',   color: '#555', marginTop: '2px', fontFamily: 'monospace' }}>Master Signal</span>
      </div>

      {/* Inputs */}
      {[{
        id: 'pamm-symbol', label: 'SYMBOL', value: symbol, onChange: e => setSymbol(e.target.value.toUpperCase()),
        width: '70px', mono: true,
      },{
        id: 'pamm-action', label: 'ACTION', value: action, isSelect: true,
        options: ['Buy','Sell'], onChange: e => setAction(e.target.value),
        width: '72px',
      },{
        id: 'pamm-qty', label: 'QTY (ES)', value: quantity, onChange: e => setQuantity(e.target.value),
        width: '65px', mono: true, type: 'number',
      }].map(({ id, label, value, onChange, width, mono, isSelect, options, type }) => (
        <div key={id} style={{
          display:        'flex',
          flexDirection:  'column',
          justifyContent: 'center',
          padding:        '0 12px',
          borderRight:    '1px solid rgba(255,255,255,0.05)',
          gap:            '3px',
        }}>
          <span style={{ fontSize: '7px', color: '#444', letterSpacing: '0.08em', fontWeight: '600' }}>{label}</span>
          {isSelect ? (
            <select
              id={id}
              value={value}
              onChange={onChange}
              disabled={isBusy}
              style={{
                background:   'transparent',
                border:       '1px solid rgba(255,255,255,0.1)',
                borderRadius: '3px',
                color:        action === 'Buy' ? '#00d4aa' : '#ff3366',
                fontSize:     '11px',
                fontFamily:   'monospace',
                padding:      '2px 4px',
                width,
                cursor:       'pointer',
                outline:      'none',
              }}
            >
              {options.map(o => <option key={o} value={o} style={{ background: '#111' }}>{o.toUpperCase()}</option>)}
            </select>
          ) : (
            <input
              id={id}
              type={type || 'text'}
              value={value}
              onChange={onChange}
              disabled={isBusy}
              style={{
                background:   'rgba(255,255,255,0.04)',
                border:       '1px solid rgba(255,255,255,0.1)',
                borderRadius: '3px',
                color:        '#fff',
                fontSize:     '11px',
                fontFamily:   mono ? 'monospace' : 'inherit',
                padding:      '2px 6px',
                width,
                outline:      'none',
              }}
            />
          )}
        </div>
      ))}

      {/* Fire button */}
      <div style={{ display: 'flex', alignItems: 'center', padding: '0 14px', borderRight: '1px solid rgba(255,255,255,0.05)' }}>
        <button
          id="pamm-execute-btn"
          onClick={handleFire}
          disabled={isBusy}
          style={{
            background:     isBusy
              ? 'rgba(255,165,0,0.15)'
              : action === 'Buy'
                ? 'rgba(0,212,170,0.15)'
                : 'rgba(255,51,102,0.15)',
            border:         `1px solid ${action === 'Buy' ? '#00d4aa' : '#ff3366'}`,
            borderRadius:   '4px',
            color:          action === 'Buy' ? '#00d4aa' : '#ff3366',
            fontSize:       '10px',
            fontWeight:     '700',
            letterSpacing:  '0.08em',
            padding:        '6px 16px',
            cursor:         isBusy ? 'not-allowed' : 'pointer',
            transition:     'all 0.2s',
            whiteSpace:     'nowrap',
            opacity:        isBusy ? 0.6 : 1,
          }}
        >
          {isBusy ? '■ SENDING' : `▶ EXECUTE ${action.toUpperCase()}`}
        </button>
      </div>

      {/* Status badge */}
      <div style={{
        display:        'flex',
        flexDirection:  'column',
        justifyContent: 'center',
        padding:        '0 12px',
        borderRight:    '1px solid rgba(255,255,255,0.05)',
        minWidth:       '72px',
      }}>
        <span style={{ fontSize: '7px', color: '#333', letterSpacing: '0.08em' }}>STATUS</span>
        <span style={{
          fontSize:       '10px',
          color:          col,
          fontFamily:     'monospace',
          fontWeight:     '700',
          marginTop:      '2px',
          letterSpacing:  '0.04em',
          transition:     'color 0.3s',
        }}>
          <span style={{
            display:    'inline-block',
            width:      '6px', height: '6px',
            borderRadius: '50%',
            background: col,
            marginRight:'5px',
            verticalAlign:'middle',
            boxShadow:  status !== 'idle' ? `0 0 6px ${col}` : 'none',
          }} />
          {STATUS_LABEL[status]}
        </span>
      </div>

      {/* Dispatch log */}
      <div style={{
        flex:       1,
        display:    'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        padding:    '4px 12px',
        overflow:   'hidden',
        minWidth:   0,
      }}>
        <span style={{ fontSize: '7px', color: '#333', letterSpacing: '0.08em', marginBottom: '2px' }}>DISPATCH LOG</span>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1px', overflow: 'hidden' }}>
          {log.slice(0, 2).map((entry, i) => (
            <div key={i} style={{ display: 'flex', gap: '6px', alignItems: 'baseline' }}>
              <span style={{ fontSize: '8px', color: '#333', fontFamily: 'monospace', flexShrink: 0 }}>{entry.ts}</span>
              <span style={{ fontSize: '9px', color: entry.color, fontFamily: 'monospace', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{entry.msg}</span>
            </div>
          ))}
          {log.length === 0 && (
            <span style={{ fontSize: '9px', color: '#2a2a2a', fontFamily: 'monospace' }}>Awaiting master signal…</span>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Main Dashboard ───────────────────────────────────────────────────────────

const Dashboard = () => {
  const {
    connected, ntConnected, brokerConnected, activeAlgos,
    bars, trades, allTrades, lastBar,
    seedBars, seedTrades,
  } = useMarketData();

  const [algos,        setAlgos]        = useState([]);
  const [selectedAlgo, setSelectedAlgo] = useState(null);
  const [account,      setAccount]      = useState({ balance: 0, daily_pnl: 0 });
  const [loadingAlgos, setLoadingAlgos] = useState(true);
  const chartWrapperRef = useRef(null);
  const [chartHeight,   setChartHeight] = useState(440);

  const [liveFills, setLiveFills] = useState([]);

  useEffect(() => {
      // Open the tunnel to FastAPI
      const wsBase = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';
      const ws = new WebSocket(`${wsBase}/ws/trades`);
  
      ws.onmessage = (event) => {
          const fillData = JSON.parse(event.data);
          console.log("🔥 Live Fill Received:", fillData);
          
          // Push the new fill to the top of your UI state
          setLiveFills(prev => [fillData, ...prev]);
      };
  
      return () => ws.close(); // Cleanup if the user closes the dashboard
  }, []);
  // ── Measure available chart height ─────────────────────────────────────────
  useEffect(() => {
    if (!chartWrapperRef.current) return;
    const ro = new ResizeObserver(entries => {
      const h = entries[0]?.contentRect.height;
      if (h > 60) setChartHeight(Math.max(h - 90, 200)); // reserve 90px for volume pane label gap
    });
    ro.observe(chartWrapperRef.current);
    return () => ro.disconnect();
  }, []);

  // ── Fetch algo list — retry until backend is ready ─────────────────────────
  useEffect(() => {
    let cancelled = false;
    let retryMs   = 1000;

    const attempt = async () => {
      try {
        const res  = await fetch(`${API}/api/algos`);
        const data = await res.json();
        if (!cancelled && Array.isArray(data) && data.length > 0) {
          setAlgos(data);
          setSelectedAlgo(prev => prev ?? data[0]); // auto-select first only if none chosen
          setLoadingAlgos(false);
          return; // success — stop retrying
        }
      } catch (_) {}
      if (!cancelled) {
        retryMs = Math.min(retryMs * 1.5, 8000);
        setTimeout(attempt, retryMs);
      }
    };

    attempt();
    return () => { cancelled = true; };
  }, []);

  // ── Fetch account ───────────────────────────────────────────────────────────
  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const res  = await fetch(`${API}/api/account`);
        const data = await res.json();
        if (!cancelled) setAccount(data);
      } catch (e) {}
    };
    load();
    const id = setInterval(load, 30_000);
    return () => { cancelled = true; clearInterval(id); };
  }, []);

  // ── Seed bars for selected algo ─────────────────────────────────────────────
  useEffect(() => {
    if (!selectedAlgo) return;
    const sym = selectedAlgo.symbol?.replace('=F', '') || 'ES';
    const tf  = selectedAlgo.tf || '5m';

    // Only fetch if we don't have enough bars yet
    if ((bars[sym] || []).length >= 100) return;

    (async () => {
      try {
        const res  = await fetch(`${API}/api/bars/${sym}?limit=500&tf=${tf}`);
        const data = await res.json();
        if (data.bars?.length) seedBars(sym, data.bars);
      } catch (e) {}
    })();
  }, [selectedAlgo, bars, seedBars]);

  // ── Seed trades for selected algo ───────────────────────────────────────────
  useEffect(() => {
    if (!selectedAlgo) return;
    const id = selectedAlgo.id;
    if ((trades[id] || []).length >= 10) return;

    (async () => {
      try {
        const res  = await fetch(`${API}/api/trades/${id}?limit=100`);
        const data = await res.json();
        if (data.trades?.length) seedTrades(id, data.trades);
      } catch (e) {}
    })();
  }, [selectedAlgo, trades, seedTrades]);

  // ── Derive chart data (fall back to synthetic bars if no live data) ─────────
  const sym         = selectedAlgo?.symbol?.replace('=F', '') || 'ES';
  const liveBars    = bars[sym] || [];
  const chartBars   = liveBars.length >= 5 ? liveBars : makePlaceholderBars(sym, 200);
  const chartTrades = selectedAlgo ? (trades[selectedAlgo.id] || []) : [];
  const lb          = lastBar[sym] || (liveBars.length > 0 ? liveBars[liveBars.length - 1] : null);

  return (
    <div style={{
      display:        'flex',
      flexDirection:  'column',
      height:         '100vh',
      width:          '100vw',
      background:     '#000',
      color:          '#ccc',
      fontFamily:     "'Inter', system-ui, sans-serif",
      overflow:       'hidden',
    }}>
      {/* ── TOP BAR ── */}
      <TopBar
        connected={connected}
        ntConnected={ntConnected}
        brokerConnected={brokerConnected}
        activeAlgos={activeAlgos}
        account={account}
      />

      {/* ── MAIN ROW ── */}
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden', minHeight: 0 }}>

        {/* Algo sidebar */}
        <AlgoSidebar
          algos={algos}
          selected={selectedAlgo}
          onSelect={setSelectedAlgo}
          trades={trades}
        />

        {/* Chart area */}
        <div style={{
          flex:        1,
          display:     'flex',
          flexDirection:'column',
          overflow:    'hidden',
          minWidth:    0,
        }}>
          <ChartHeader algo={selectedAlgo} lastBar={lb} />

          <div
            ref={chartWrapperRef}
            id="chart-wrapper"
            style={{ flex: 1, overflow: 'hidden', minHeight: 0, position: 'relative', display: 'flex', flexDirection: 'column' }}
          >
            <TradingViewChart
              bars={chartBars}
              trades={chartTrades}
              symbol={sym}
              tf={selectedAlgo?.tf || '5m'}
              height={chartHeight}
              autoScroll={true}
            />
            {!selectedAlgo && loadingAlgos && (
              <div style={{
                position:       'absolute', inset: 0,
                display:        'flex', alignItems: 'center', justifyContent: 'center',
                background:     'rgba(0,0,0,0.6)',
                color:          '#444', fontSize: '12px', letterSpacing: '0.1em',
                pointerEvents:  'none',
              }}>
                CONNECTING TO BACKEND...
              </div>
            )}
          </div>
        </div>

        {/* Details panel */}
        <AlgoDetails
          algo={selectedAlgo}
          trades={chartTrades}
        />
      </div>

      {/* ── PAMM MASTER TRADE PANEL ── */}
      <PammPanel />

      {/* ── TRADE LOG ── */}
      <TradeLog trades={allTrades} algos={algos} />
    </div>
  );
};

export default Dashboard;
