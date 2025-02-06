import React, { useMemo } from 'react';
import { Paper, Typography } from '@mui/material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ReferenceLine,
} from 'recharts';

const PredictionChart = ({ data = [], prediction, title = "Évolution de la Température" }) => {
  // Ensure data is an array and has valid items
  const chartData = useMemo(() => {
    if (!Array.isArray(data)) {
      console.warn('Invalid data format. Expected array, got:', typeof data);
      return [];
    }

    return data
      .filter(item => item && item.timestamp && item.temperature)
      .map((item) => ({
        time: new Date(item.timestamp).toLocaleTimeString(),
        temperature: parseFloat(item.temperature),
      }));
  }, [data]);

  // Value prédite (si disponible)
  const predictedTemp = prediction?.prediction_temperature;

  if (chartData.length === 0) {
    return (
      <Paper style={{ padding: '16px', marginTop: '16px' }}>
        <Typography variant="h6" gutterBottom>
          {title}
        </Typography>
        <Typography variant="body1" color="textSecondary">
          No data available
        </Typography>
      </Paper>
    );
  }

  return (
    <Paper style={{ padding: '16px', marginTop: '16px' }}>
      <Typography variant="h6" gutterBottom>
        {title}
      </Typography>
      <LineChart
        width={600}
        height={300}
        data={chartData}
        margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
      >
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="time" />
        <YAxis />
        <Tooltip />
        <Legend />
        <Line
          type="monotone"
          dataKey="temperature"
          stroke="#8884d8"
          activeDot={{ r: 8 }}
        />
        {predictedTemp !== undefined && (
          <ReferenceLine
            y={predictedTemp}
            label={`Prédiction: ${predictedTemp.toFixed(2)}°C`}
            stroke="red"
            strokeDasharray="3 3"
          />
        )}
      </LineChart>
    </Paper>
  );
};

export default PredictionChart;
