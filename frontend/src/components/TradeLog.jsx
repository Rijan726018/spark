/**
 * TradeLog — Bottom panel showing recent executions across all algos.
 *
 * Props:
 *   trades[]   - flat trade list (newest first)
 *   algos[]    - for resolving algo names
 *   maxRows    - how many rows to show (default 50)
 */

import React, { useMemo } from 'react';

function formatTime(unixTs) {
  if (!unixTs) return '--';
  const d = new Date(unixTs * 1000);
  const hh = String(d.getHours()).padStart(2, '0');
  const mm = String(d.getMinutes()).padStart(2, '0');
  const ss = String(d.getSeconds()).padStart(2, '0');
  return `${hh}:${mm}:${ss}`;
}

function formatDate(unixTs) {
  if (!unixTs) return '--';
  const d = new Date(unixTs * 1000);
  return `${d.getMonth() + 1}/${d.getDate()}`;
}

const COL = {
  header: {
    fontSize:       '9px',
    color:          '#555',
    fontWeight:     '600',
    letterSpacing:  '0.06em',
    padding:        '4px 8px',
    whiteSpace:     'nowrap',
  },
  cell: {
    fontSize:   '10px',
    padding:    '3px 8px',
    whiteSpace: 'nowrap',
    fontFamily: 'monospace',
  },
};

const TradeLog = ({ trades = [], algos = [], maxRows = 60 }) => {
  const algoMap = useMemo(() => {
    const m = {};
    for (const a of algos) m[a.id] = a.name;
    return m;
  }, [algos]);

  const rows = useMemo(() => trades.slice(0, maxRows), [trades, maxRows]);

  return (
    <div style={{
      height:     '160px',
      minHeight:  '160px',
      background: '#030303',
      borderTop:  '1px solid rgba(255,255,255,0.06)',
      display:    'flex',
      flexDirection: 'column',
      overflow:   'hidden',
    }}>
      {/* Header bar */}
      <div style={{
        display:        'flex',
        alignItems:     'center',
        justifyContent: 'space-between',
        padding:        '4px 12px',
        borderBottom:   '1px solid rgba(255,255,255,0.05)',
        flexShrink:     0,
      }}>
        <span style={{ fontSize: '10px', color: '#888', letterSpacing: '0.05em', fontWeight: '600' }}>
          EXECUTION LOG
        </span>
        <span style={{ fontSize: '9px', color: '#555' }}>
          {trades.length} fills
        </span>
      </div>

      {/* Table */}
      <div style={{ flex: 1, overflowY: 'auto', overflowX: 'auto', scrollbarWidth: 'thin', scrollbarColor: '#222 #000' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', tableLayout: 'fixed' }}>
          <colgroup>
            <col style={{ width: '60px' }} />
            <col style={{ width: '55px' }} />
            <col style={{ width: '55px' }} />
            <col style={{ width: '160px' }} />
            <col style={{ width: '55px' }} />
            <col style={{ width: '80px' }} />
            <col style={{ width: '40px' }} />
            <col style={{ width: '80px' }} />
            <col style={{ width: '80px' }} />
          </colgroup>
          <thead>
            <tr style={{ background: '#070707', position: 'sticky', top: 0, zIndex: 1 }}>
              <th style={{ ...COL.header, textAlign: 'left' }}>DATE</th>
              <th style={{ ...COL.header, textAlign: 'left' }}>TIME</th>
              <th style={{ ...COL.header, textAlign: 'left' }}>SYMBOL</th>
              <th style={{ ...COL.header, textAlign: 'left' }}>ALGO</th>
              <th style={{ ...COL.header, textAlign: 'left' }}>SIDE</th>
              <th style={{ ...COL.header, textAlign: 'right' }}>PRICE</th>
              <th style={{ ...COL.header, textAlign: 'right' }}>QTY</th>
              <th style={{ ...COL.header, textAlign: 'right' }}>STOP</th>
              <th style={{ ...COL.header, textAlign: 'right' }}>TARGET</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((t, i) => {
              const isBuy  = t.side === 'BUY';
              const sideColor = isBuy ? '#00d4aa' : '#ff3366';
              const algoName  = algoMap[t.algo_id] || algoMap[String(t.algo_id).padStart(3,'0')] || `Algo ${t.algo_id}`;
              const rowBg     = i % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.01)';

              return (
                <tr
                  key={`${t.time}-${t.algo_id}-${i}`}
                  style={{ background: rowBg }}
                >
                  <td style={{ ...COL.cell, color: '#555' }}>{formatDate(t.time)}</td>
                  <td style={{ ...COL.cell, color: '#777' }}>{formatTime(t.time)}</td>
                  <td style={{ ...COL.cell, color: '#aaa' }}>{t.symbol || 'ES'}</td>
                  <td style={{
                    ...COL.cell,
                    color:       '#999',
                    overflow:    'hidden',
                    textOverflow:'ellipsis',
                    maxWidth:    '160px',
                  }} title={algoName}>{algoName}</td>
                  <td style={{ ...COL.cell, color: sideColor, fontWeight: '600' }}>
                    {isBuy ? '▲ BUY' : '▼ SELL'}
                  </td>
                  <td style={{ ...COL.cell, color: '#e0e0e0', textAlign: 'right' }}>
                    {t.price?.toFixed(2) ?? '--'}
                  </td>
                  <td style={{ ...COL.cell, color: '#aaa', textAlign: 'right' }}>
                    {t.qty || 1}
                  </td>
                  <td style={{ ...COL.cell, color: '#ff4444', textAlign: 'right' }}>
                    {t.stop ? t.stop.toFixed(2) : '--'}
                  </td>
                  <td style={{ ...COL.cell, color: '#00ff88', textAlign: 'right' }}>
                    {t.target ? t.target.toFixed(2) : '--'}
                  </td>
                </tr>
              );
            })}
            {rows.length === 0 && (
              <tr>
                <td colSpan={9} style={{ ...COL.cell, textAlign: 'center', color: '#333', padding: '20px' }}>
                  No executions yet. Waiting for signals...
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default TradeLog;
