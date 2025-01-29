import React from 'react';
import Plot from 'react-plotly.js';

const TemperatureChart = ({ data }) => {
  if (!data || data.length === 0) {
    return <div>No temperature data available</div>;
  }

  const traces = {};
  
  // Group data by device
  const colors = [
    'rgb(192, 108, 75)',  // Orange/brown
    'rgb(75, 192, 192)',  // Teal
    'rgb(153, 102, 255)', // Purple
    'rgb(255, 159, 64)',  // Orange
    'rgb(75, 192, 75)',   // Green
  ];
  let colorIndex = 0;

  data.forEach(reading => {
    if (!traces[reading.device_id]) {
      traces[reading.device_id] = {
        x: [],
        y: [],
        type: 'scatter',
        mode: 'lines+markers',
        name: reading.device_id,
        marker: { color: colors[colorIndex % colors.length] }
      };
      colorIndex++;
    }
    traces[reading.device_id].x.push(new Date(reading.timestamp));
    traces[reading.device_id].y.push(reading.temperature);
  });

  return (
    <div className="temperature-chart">
      <h3>Temperature Readings</h3>
      <Plot
        data={Object.values(traces)}
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