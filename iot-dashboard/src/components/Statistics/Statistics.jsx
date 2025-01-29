import React from 'react';
import { Paper, Grid2, Typography } from '@mui/material';

const Statistics = ({ stats }) => {
  if (!stats) {
    return (
      <Paper elevation={3} style={{ padding: 20 }}>
        <Typography>Loading statistics...</Typography>
      </Paper>
    );
  }

  return (
    <Paper elevation={3} style={{ padding: 20 }}>
      <Grid2 container spacing={2}>
        <Grid2 item xs={12}>
          <Typography variant="h6">Latest Statistics</Typography>
        </Grid2>
        <Grid2 item xs={6}>
          <Typography>
            Average Temperature: {stats.average_temp ? `${stats.average_temp.toFixed(2)}°C` : 'N/A'}
          </Typography>
          <Typography>
            Maximum Temperature: {stats.max_temp ? `${stats.max_temp.toFixed(2)}°C` : 'N/A'}
          </Typography>
          <Typography>
            Minimum Temperature: {stats.min_temp ? `${stats.min_temp.toFixed(2)}°C` : 'N/A'}
          </Typography>
        </Grid2>
        <Grid2 item xs={6}>
          <Typography>
            Total Readings: {stats.num_readings || 0}
          </Typography>
          <Typography>
            Active Devices: {stats.active_devices || 0}
          </Typography>
          <Typography>
            Last Updated: {stats.last_updated ? new Date(stats.last_updated).toLocaleString() : 'N/A'}
          </Typography>
        </Grid2>
      </Grid2>
    </Paper>
  );
};

export default Statistics; 