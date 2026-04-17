import React from 'react';
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

const PredictionChart = ({ data, prediction, title = "Évolution de la Température" }) => {
  // Préparation des données pour le graphique
  // On suppose que 'data' est un tableau d'objets avec { timestamp, temperature }
  // et que 'prediction' est un objet contenant { prediction_temperature }
  const chartData = data.map((item) => ({
    // On formate l'heure à partir du timestamp
    time: new Date(item.timestamp).toLocaleTimeString(),
    temperature: item.temperature,
  }));

  // Valeur prédite (si disponible)
  const predictedTemp = prediction?.prediction_temperature;

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
