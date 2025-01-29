import React from 'react';
import { Paper, Grid, Typography, Box } from '@mui/material';
import { styled } from '@mui/material/styles';
import ThermostatIcon from '@mui/icons-material/Thermostat';
import DevicesIcon from '@mui/icons-material/Devices';
import TimelineIcon from '@mui/icons-material/Timeline';
import UpdateIcon from '@mui/icons-material/Update';

const StyledPaper = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(3), 
  borderRadius: theme.spacing(2),
}));

const StatCard = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(2),
  height: '100%',
  backgroundColor: '#2d2d2d',
  borderRadius: theme.spacing(2),
  transition: 'transform 0.3s ease-in-out, box-shadow 0.3s ease-in-out',
  '&:hover': {
    transform: 'translateY(-5px)',
    boxShadow: '0 8px 16px rgba(0,0,0,0.2)',
  },
}));

const IconBox = styled(Box)({
  display: 'flex',
  alignItems: 'center',
  marginBottom: '16px',
});

const StyledIcon = styled(Box)(({ color }) => ({
  fontSize: 40,
  marginRight: '16px',
  color: color,
}));

const StatValue = styled(Typography)(({ color }) => ({
  fontSize: '1.5rem',
  fontWeight: 'bold',
  color: color || '#fff',
}));

const StatLabel = styled(Typography)({
  color: '#9e9e9e',
  fontSize: '0.875rem',
});

const StatCardComponent = ({ icon, value, label, color }) => (
  <StatCard elevation={3}>
    <IconBox>
      <StyledIcon color={color}>{icon}</StyledIcon>
      <Box>
        <StatValue color={color}>{value}</StatValue>
        <StatLabel>{label}</StatLabel>
      </Box>
    </IconBox>
  </StatCard>
);

const Statistics = ({ stats }) => {
  if (!stats) {
    return (
      <StyledPaper elevation={3}>
        <Typography color="white" fontFamily="Poppins">Loading statistics...</Typography>
      </StyledPaper>
    );
  }

  const formatTemp = (temp) => {
    return typeof temp === 'number' ? temp.toFixed(1) : 'N/A';
  };

  return (
    <StyledPaper elevation={3}>
      {/* <Typography variant="h5" sx={{ color: '#fff', fontWeight: 700, mb: 3, fontFamily: 'Poppins' , textAlign: 'center'}}>
        System Statistics
      </Typography> */}
      <Grid container spacing={3} justifyContent="center" alignItems="center">
        <Grid item xs={12} sm={6} md={'auto'}>
          <StatCardComponent
            icon={<ThermostatIcon />}
            value={`${formatTemp(stats.average_temp)}°C`}
            label="Average Temperature"
            color="#ff9800"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={'auto'}>
          <StatCardComponent
            icon={<ThermostatIcon />}
            value={`${formatTemp(stats.max_temp)}°C`}
            label="Max Temperature"
            color="#f44336"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={'auto'}>
          <StatCardComponent
            icon={<ThermostatIcon />}
            value={`${formatTemp(stats.min_temp)}°C`}
            label="Min Temperature"
            color="#2196f3"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={'auto'}>
          <StatCardComponent
            icon={<DevicesIcon />}
            value={stats.active_devices || 0}
            label="Active Devices"
            color="#4caf50"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={'auto'}>
          <StatCardComponent
            icon={<TimelineIcon />}
            value={stats.num_readings || 0}
            label="Total Readings"
            color="#9c27b0"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={'auto'}>
          <StatCardComponent
            icon={<UpdateIcon />}
            value={stats.last_updated ? new Date(stats.last_updated).toLocaleTimeString() : 'N/A'}
            label="Last Updated"
            color="#607d8b"
          />
        </Grid>
      </Grid>
    </StyledPaper>
  );
};

export default Statistics; 