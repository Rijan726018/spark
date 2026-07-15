/**
 * AlgoSidebar — Scrollable list of all algos with status and quick stats.
 *
 * Props:
 *   algos[]    - algo config objects
 *   selected   - selected algo id string
 *   onSelect   - callback(algo)
 *   trades     - { [algoId]: Trade[] }  — for P&L calculation
 */

import React, { useMemo } from 'react';

const STATUS_COLORS = {
  LIVE:    '#00ff88',
  IDLE:    '#ffa500',
  STOPPED: '#ff4444',
  PAUSED:  '#aaaaaa',
};

const CATEGORY_COLORS = {
  'Mean Reversion':  '#00d4aa',
  'Breakout':        '#ffa500',
  'Trend Following': '#7b68ee',
  'Momentum':        '#ff6b9d',
  'Orderflow':       '#00bfff',
  'Scalping':        '#ffdd57',
  'General':         '#888888',
};

function computeDailyPnl(trades) {
  if (!trades || !trades.length) return 0;
  const todayStart = new Date();
  todayStart.setHours(0, 0, 0, 0);
  const ts = todayStart.getTime() / 1000;

  let pnl = 0;
  let lastBuy = null;
  const todayTrades = trades.filter(t => t.time >= ts).sort((a, b) => a.time - b.time);

  for (const t of todayTrades) {
    if (t.side === 'BUY') {
      lastBuy = t.price;
    } else if (t.side === 'SELL' && lastBuy !== null) {
      pnl += (t.price - lastBuy) * (t.qty || 1) * 50; // ES tick value ~$50
      lastBuy = null;
    }
  }
  return pnl;
}

function AlgoRow({ algo, isSelected, onSelect, algoTrades }) {
  const dailyPnl = useMemo(() => computeDailyPnl(algoTrades), [algoTrades]);
  const statusColor = STATUS_COLORS[algo.status] || '#888';
  const catColor    = CATEGORY_COLORS[algo.category] || '#888';
  const pnlColor    = dailyPnl > 0 ? '#00d4aa' : dailyPnl < 0 ? '#ff3366' : '#888';
  const tradeCount  = (algoTrades || []).length;

  return (
    <div
      onClick={() => onSelect(algo)}
      style={{
        padding:       '8px 10px',
        borderBottom:  '1px solid rgba(255,255,255,0.04)',
        cursor:        'pointer',
        background:    isSelected ? 'rgba(0,212,170,0.07)' : 'transparent',
        borderLeft:    isSelected ? '2px solid #00d4aa' : '2px solid transparent',
        transition:    'background 0.1s',
      }}
      onMouseEnter={e => { if (!isSelected) e.currentTarget.style.background = 'rgba(255,255,255,0.03)'; }}
      onMouseLeave={e => { if (!isSelected) e.currentTarget.style.background = 'transparent'; }}
    >
      {/* Row 1: ID + name */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
        <span style={{
          fontFamily:   'monospace',
          fontSize:     '9px',
          color:        '#555',
          minWidth:     '24px',
        }}>{algo.id}</span>

        <span style={{
          fontSize:    '11px',
          fontWeight:  isSelected ? '600' : '400',
          color:       isSelected ? '#fff' : '#ccc',
          flex:        1,
          overflow:    'hidden',
          textOverflow:'ellipsis',
          whiteSpace:  'nowrap',
        }}>{algo.name}</span>

        {/* Status dot */}
        <span style={{
          width:        '6px',
          height:       '6px',
          borderRadius: '50%',
          background:   statusColor,
          flexShrink:   0,
          boxShadow:    algo.status === 'LIVE' ? `0 0 4px ${statusColor}` : 'none',
        }} />
      </div>

      {/* Row 2: category tag, tf, win rate */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
        <span style={{
          fontSize:     '9px',
          color:        catColor,
          background:   `${catColor}15`,
          padding:      '1px 5px',
          borderRadius: '3px',
          whiteSpace:   'nowrap',
        }}>{algo.category || 'General'}</span>

        <span style={{ fontSize: '9px', color: '#666' }}>{algo.tf}</span>
        <span style={{ fontSize: '9px', color: '#666' }}>{algo.symbol}</span>

        <span style={{
          fontSize:  '9px',
          color:     algo.win_rate >= 55 ? '#00d4aa' : algo.win_rate >= 50 ? '#ffa500' : '#ff4444',
          marginLeft: 'auto',
        }}>{algo.win_rate?.toFixed(1)}%</span>
      </div>

      {/* Row 3: daily P&L and trade count */}
      {(dailyPnl !== 0 || tradeCount > 0) && (
        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '3px' }}>
          <span style={{ fontSize: '9px', color: pnlColor }}>
            {dailyPnl >= 0 ? '+' : ''}{dailyPnl.toFixed(0)} today
          </span>
          <span style={{ fontSize: '9px', color: '#555' }}>
            {tradeCount} fills
          </span>
        </div>
      )}
    </div>
  );
}

const AlgoSidebar = ({ algos = [], selected, onSelect, trades = {} }) => {
  // Group by category for section headers
  const categories = useMemo(() => {
    const map = {};
    for (const a of algos) {
      const cat = a.category || 'General';
      if (!map[cat]) map[cat] = [];
      map[cat].push(a);
    }
    return map;
  }, [algos]);

  const liveCount = algos.filter(a => a.status === 'LIVE').length;

  return (
    <div style={{
      width:        '220px',
      minWidth:     '220px',
      background:   '#050505',
      borderRight:  '1px solid rgba(255,255,255,0.06)',
      display:      'flex',
      flexDirection:'column',
      overflow:     'hidden',
    }}>
      {/* Header */}
      <div style={{
        padding:       '8px 10px',
        borderBottom:  '1px solid rgba(255,255,255,0.06)',
        display:       'flex',
        alignItems:    'center',
        justifyContent:'space-between',
        flexShrink:    0,
      }}>
        <span style={{ fontSize: '10px', color: '#888', letterSpacing: '0.05em', fontWeight: '600' }}>
          ALGO ROSTER
        </span>
        <span style={{
          fontSize:     '9px',
          color:        '#00ff88',
          background:   'rgba(0,255,136,0.1)',
          padding:      '1px 6px',
          borderRadius: '10px',
        }}>
          {liveCount} LIVE
        </span>
      </div>

      {/* Scrollable list */}
      <div style={{
        flex:       1,
        overflowY:  'auto',
        overflowX:  'hidden',
        scrollbarWidth: 'thin',
        scrollbarColor: '#222 #000',
      }}>
        {Object.entries(categories).map(([cat, catAlgos]) => (
          <React.Fragment key={cat}>
            {/* Category separator */}
            <div style={{
              padding:     '5px 10px 3px',
              fontSize:    '9px',
              color:       CATEGORY_COLORS[cat] || '#555',
              letterSpacing: '0.08em',
              fontWeight:  '600',
              background:  'rgba(255,255,255,0.01)',
              borderBottom:'1px solid rgba(255,255,255,0.03)',
              marginTop:   '2px',
            }}>
              {cat.toUpperCase()} ({catAlgos.length})
            </div>

            {catAlgos.map(algo => (
              <AlgoRow
                key={algo.id}
                algo={algo}
                isSelected={selected?.id === algo.id}
                onSelect={onSelect}
                algoTrades={trades[algo.id] || []}
              />
            ))}
          </React.Fragment>
        ))}

        {algos.length === 0 && (
          <div style={{ padding: '20px 10px', textAlign: 'center', color: '#444', fontSize: '11px' }}>
            Loading algos...
          </div>
        )}
      </div>

      {/* Footer: total count */}
      <div style={{
        padding:    '6px 10px',
        borderTop:  '1px solid rgba(255,255,255,0.05)',
        fontSize:   '9px',
        color:      '#444',
        flexShrink: 0,
      }}>
        {algos.length} total strategies
      </div>
    </div>
  );
};

export default AlgoSidebar;
