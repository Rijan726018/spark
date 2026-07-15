/**
 * TradingViewChart — Full-featured LightweightCharts v5 component
 *
 * Single chart instance: candlestick series + volume histogram overlay.
 * Volume occupies the bottom 20% of the pane via priceScaleId="" and
 * scaleMargins { top: 0.8, bottom: 0 } — no separate DOM container needed.
 *
 * Props:
 *   bars[]     - {time, open, high, low, close, volume}
 *   trades[]   - {time, side, price, qty, algo_id, symbol}
 *   height     - number (default 440)
 *   symbol     - string
 *   tf         - string
 *   autoScroll - boolean (default true)
 */

import { useEffect, useRef } from 'react';
import {
  createChart,
  CrosshairMode,
  LineStyle,
  createSeriesMarkers,
  CandlestickSeries,
  HistogramSeries,
} from 'lightweight-charts';

// ── Colour palette ────────────────────────────────────────────────────────────
const C = {
  bg: '#000000',
  grid: 'rgba(255,255,255,0.03)',
  text: '#b0b0b0',
  border: 'rgba(255,255,255,0.08)',
  upCandle: '#00d4aa',
  downCandle: '#ff3366',
  upWick: '#00d4aa',
  downWick: '#ff3366',
  volUp: 'rgba(0,212,170,0.3)',
  volDown: 'rgba(255,51,102,0.3)',
  buyMarker: '#00ff88',
  sellMarker: '#ff4444',
  crosshair: 'rgba(255,255,255,0.2)',
};

// ── Chart options ─────────────────────────────────────────────────────────────
function buildChartOptions(width, height) {
  return {
    width,
    height,
    layout: {
      background: { color: C.bg },
      textColor: C.text,
      fontFamily: "'JetBrains Mono', 'Courier New', monospace",
      fontSize: 11,
    },
    grid: {
      vertLines: { color: C.grid, style: LineStyle.Solid },
      horzLines: { color: C.grid, style: LineStyle.Solid },
    },
    crosshair: {
      mode: CrosshairMode.Normal,
      vertLine: { color: C.crosshair, width: 1, style: LineStyle.Dashed, labelBackgroundColor: '#111' },
      horzLine: { color: C.crosshair, width: 1, style: LineStyle.Dashed, labelBackgroundColor: '#111' },
    },
    rightPriceScale: {
      borderColor: C.border,
      textColor: C.text,
      // Give the candlestick series comfortable breathing room above the
      // volume bars (which occupy the bottom 20 %).
      scaleMarginTop: 0.1,
      scaleMarginBottom: 0.2,
    },
    timeScale: {
      borderColor: C.border,
      timeVisible: true,
      secondsVisible: false,
      fixLeftEdge: false,
      lockVisibleTimeRangeOnResize: true,
    },
    handleScroll: { mouseWheel: true, pressedMouseMove: true, horzTouchDrag: true, vertTouchDrag: false },
    handleScale: { mouseWheel: true, pinch: true, axisPressedMouseMove: true, axisDoubleClickReset: true },
  };
}

// ── Marker builder ─────────────────────────────────────────────────────────────
function buildMarkers(trades) {
  if (!trades || !trades.length) return [];
  return trades
    .map(t => ({
      time: t.time,
      position: t.side === 'BUY' ? 'belowBar' : 'aboveBar',
      color: t.side === 'BUY' ? C.buyMarker : C.sellMarker,
      shape: t.side === 'BUY' ? 'arrowUp' : 'arrowDown',
      size: 1,
      text: `${t.side} ${t.qty || 1}`,
    }))
    .sort((a, b) => a.time - b.time);
}

// ── Component ─────────────────────────────────────────────────────────────────
const TradingViewChart = ({
  bars = [],
  trades = [],
  height = 440,
  symbol = 'ES',
  tf = '5m',
  autoScroll = true,
}) => {
  const containerRef = useRef(null);   // single DOM mount point
  const chartRef = useRef(null);   // single createChart instance
  const candleRef = useRef(null);   // CandlestickSeries
  const volSeriesRef = useRef(null);   // HistogramSeries (volume overlay)
  const markersApiRef = useRef(null);   // createSeriesMarkers handle (LWC v5)
  const resizeObRef = useRef(null);

  // ── Chart init (runs once) ──────────────────────────────────────────────────
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    // Tear down any previous instance (e.g. HMR)
    if (chartRef.current) {
      chartRef.current.remove();
      chartRef.current = null;
    }

    const w = container.clientWidth || 800;

    // ── ONE chart instance ────────────────────────────────────────────────────
    const chart = createChart(container, buildChartOptions(w, height));
    chartRef.current = chart;

    // ── Candlestick series ────────────────────────────────────────────────────
    const candle = chart.addSeries(CandlestickSeries, {
      upColor: C.upCandle,
      downColor: C.downCandle,
      borderUpColor: C.upCandle,
      borderDownColor: C.downCandle,
      wickUpColor: C.upWick,
      wickDownColor: C.downWick,
    });
    candleRef.current = candle;

    // LWC v5: attach the markers plugin to the candlestick series
    markersApiRef.current = createSeriesMarkers(candle, []);

    // ── Volume histogram — SAME chart instance ────────────────────────────────
    // priceScaleId: ""  → overlay scale (not the right-hand price axis)
    // scaleMargins      → bottom 20 % of the pane; candles get the top 80 %
    const volSeries = chart.addSeries(HistogramSeries, {
      priceFormat: { type: 'volume' },
      priceScaleId: '',               // overlay / independent scale
    });
    volSeries.priceScale().applyOptions({
      scaleMargins: { top: 0.8, bottom: 0 },
    });
    volSeriesRef.current = volSeries;

    // ── Resize observer ───────────────────────────────────────────────────────
    const ro = new ResizeObserver(entries => {
      if (!entries.length) return;
      const { width } = entries[0].contentRect;
      if (chartRef.current) chartRef.current.applyOptions({ width });
    });
    ro.observe(container);
    resizeObRef.current = ro;

    // ── Cleanup ───────────────────────────────────────────────────────────────
    return () => {
      ro.disconnect();
      markersApiRef.current = null;
      if (chartRef.current) {
        chartRef.current.remove();
        chartRef.current = null;
      }
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps — intentionally once

  // ── Data updates ─────────────────────────────────────────────────────────────
  useEffect(() => {
    if (!candleRef.current || !volSeriesRef.current || !bars.length) return;

    // Deduplicate and sort by time (required by lightweight-charts)
    const sorted = [...bars]
      .sort((a, b) => a.time - b.time)
      .filter((b, i, arr) => i === 0 || b.time !== arr[i - 1].time);

    try {
      candleRef.current.setData(sorted);

      const volData = sorted.map(b => ({
        time: b.time,
        value: b.volume || 0,
        color: b.close >= b.open ? C.volUp : C.volDown,
      }));
      volSeriesRef.current.setData(volData);

      if (autoScroll && chartRef.current) {
        chartRef.current.timeScale().scrollToRealTime();
      }
    } catch (_) {
      // Swallow chart-level errors from data gaps / out-of-order frames
    }
  }, [bars, autoScroll]);

  // ── Trade markers (LWC v5 createSeriesMarkers API) ───────────────────────────
  useEffect(() => {
    if (!markersApiRef.current) return;
    try {
      markersApiRef.current.setMarkers(buildMarkers(trades));
    } catch (_) {
      // Ignore if series data not yet loaded
    }
  }, [trades]);

  // ── Render — single container div ────────────────────────────────────────────
  return (
    <div
      ref={containerRef}
      style={{
        width: '100%',
        height: `${height}px`,
        minHeight: `${height}px`,
        position: 'relative',
        background: C.bg,
      }}
    />
  );
};

export default TradingViewChart;
