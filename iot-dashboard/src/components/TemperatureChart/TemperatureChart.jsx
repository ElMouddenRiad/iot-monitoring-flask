import React, { useMemo } from 'react';
import Plot from 'react-plotly.js';

const TemperatureChart = ({ data }) => {
  const chartData = useMemo(() => {
    if (!data || data.length === 0) {
      return [];
    }

    const traces = {};
    
    // Group data by device
    data.forEach(reading => {
      const deviceId = reading.device_id || 'unknown';
      if (!traces[deviceId]) {
        traces[deviceId] = {
          x: [],
          y: [],
          type: 'scatter',
          mode: 'lines+markers',
          name: deviceId,
          marker: { size: 6 }
        };
      }
      traces[deviceId].x.push(new Date(reading.timestamp));
      traces[deviceId].y.push(reading.temperature);
    });

    return Object.values(traces);
  }, [data]);

  if (chartData.length === 0) {
    return <div>No temperature data available</div>;
  }

  return (
    <div className="temperature-chart">
      <h3>Temperature Readings</h3>
      <Plot
        data={chartData}
        layout={{
          autosize: true,
          margin: { l: 50, r: 20, t: 20, b: 50 },
          showlegend: true,
          xaxis: {
            title: 'Time',
            type: 'date',
            tickformat: '%I:%M:%S %p',
            showgrid: true
          },
          yaxis: {
            title: 'Temperature (°C)',
            showgrid: true
          },
          paper_bgcolor: 'rgba(255, 255, 255, 0.84)',
          plot_bgcolor: 'rgba(221, 208, 208, 0)',
        }}
        config={{
          responsive: true,
          displayModeBar: false
        }}
        style={{ width: '100%', height: '400px' }}
      />
    </div>
  );
};

export default TemperatureChart; 