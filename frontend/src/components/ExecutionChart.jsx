import { useEffect, useRef } from 'react';
import { createChart } from 'lightweight-charts';

const ExecutionChart = ({ data, markers }) => {
  const chartContainerRef = useRef(null);
  const chart = useRef(null);
  const series = useRef(null);

  // Chart initialization with proper null checks
  useEffect(() => {
    const container = chartContainerRef.current;
    if (!container) return;

    // Clean up any existing chart
    if (chart.current) {
      chart.current.remove();
      chart.current = null;
    }

    const width = container.clientWidth || container.offsetWidth || 800;
    const height = container.clientHeight || container.offsetHeight || 400;

    chart.current = createChart(container, {
      layout: {
        background: { color: '#000000' },
        textColor: '#D9D9D9'
      },
      grid: {
        vertLines: { color: '#2B2B43', visible: false },
        horzLines: { color: '#2B2B43' }
      },
      width,
      height
    });

    series.current = chart.current.addCandlestickSeries();
    
    return () => {
      if (chart.current) {
        chart.current.remove();
        chart.current = null;
      }
    };
  }, []);

  // Update chart data
  useEffect(() => {
    if (series.current && data?.length) {
      series.current.setData(data);
    }
  }, [data]);

  // Update execution markers
  useEffect(() => {
    if (series.current && markers?.length) {
      series.current.setMarkers(markers.map(marker => ({
        ...marker,
        position: marker.side === 'BUY' ? 'belowBar' : 'aboveBar',
        color: marker.side === 'BUY' ? 'rgba(0, 255, 0, 0.7)' : 'rgba(255, 0, 0, 0.7)',
        shape: marker.side === 'BUY' ? 'arrowUp' : 'arrowDown'
      })));
    }
  }, [markers]);

  // Handle resizing
  useEffect(() => {
    const resizeObserver = new ResizeObserver(entries => {
      if (entries.length === 0 || !chart.current) return;
      const { width, height } = entries[0].contentRect;
      chart.current.applyOptions({ width, height });
    });

    if (chartContainerRef.current) {
      resizeObserver.observe(chartContainerRef.current);
    }

    return () => resizeObserver.disconnect();
  }, []);

  return (
    <div 
      ref={chartContainerRef}
      className="execution-chart"
      style={{ 
        width: '100%',
        height: '400px',
        marginBottom: '1rem',
        minHeight: '400px' // Ensure minimum height for chart visibility
      }}
    />
  );
};

export default ExecutionChart;
