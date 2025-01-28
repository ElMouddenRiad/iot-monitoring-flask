import React from 'react';
import Plot from 'react-plotly.js';

function TemperatureChart({ data }) {
    const traces = {
        x: data.map(reading => new Date(reading.timestamp)),
        y: data.map(reading => reading.temperature),
        type: 'scatter',
        mode: 'lines+markers',
        name: 'Temperature'
    };

    const layout = {
        title: 'Temperature Readings',
        xaxis: { title: 'Time' },
        yaxis: { title: 'Temperature (°C)' },
        autosize: true
    };

    return (
        <Plot
            data={[traces]}
            layout={layout}
            style={{ width: '100%', height: '400px' }}
        />
    );
}

export default TemperatureChart;