import React, { useState, useEffect, useCallback } from 'react';
import { Grid, Paper, Typography, Button } from '@mui/material';
import DeviceList from '../DeviceList/DeviceList';
import TemperatureChart from '../TemperatureChart/TemperatureChart';
import DeviceMap from '../DeviceMap/DeviceMap';
import Statistics from '../Statistics/Statistics';
import DeviceModal from '../DeviceModal/DeviceModal';
import { deviceService } from '../../services/api';
import { predictionService } from '../../services/predictionService';
import { io } from 'socket.io-client';
import useAuth from '../../hooks/useAuth';
import { useNavigate } from 'react-router-dom';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:5000';

const socket = io(process.env.REACT_APP_SOCKET_URL || API_BASE_URL, {
  transports: ['websocket', 'polling'],
  reconnection: true,
  cors: {
    origin: 'http://localhost:3000',
  },
  reconnectionAttempts: 10,
  reconnectionDelay: 1000,
  reconnectionDelayMax: 5000,
  timeout: 20000,
  autoConnect: true,
  forceNew: true,
  withCredentials: false,
});

function Dashboard() {
  const navigate = useNavigate();
  const [devices, setDevices] = useState({});
  const [selectedDevice, setSelectedDevice] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingDevice, setEditingDevice] = useState(null);
  const [temperatureData, setTemperatureData] = useState([]);
  const [stats, setStats] = useState(null);
  const [prediction, setPrediction] = useState(null);

  useAuth(); // Vérifier l'authentification

  // Récupérer les statistiques (votre fonction existante)
  const fetchStats = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        navigate('/login');
        return;
      }
      if (!selectedDevice) {
        console.warn('Aucun appareil sélectionné');
        return;
      }

      const response = await fetch(`${API_BASE_URL}/api/stats`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ device_id: selectedDevice }),
      });

      if (!response.ok) {
        if (response.status === 401) {
          localStorage.removeItem('token');
          navigate('/login');
          return;
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const statsData = await response.json();
      console.log('Fetched stats:', statsData);
      setStats(statsData);
    } catch (error) {
      console.error('Error fetching stats:', error);
      setStats(null);
    }
  };

  // Mettre à jour les données à la réception de nouvelles mesures via Socket.IO
  const updateData = useCallback(
    async (data) => {
      console.log('Received new data:', data);
      try {
        if (!selectedDevice || selectedDevice === data.device_id) {
          setTemperatureData((prev) => {
            const newData = [
              ...prev,
              {
                timestamp: new Date(data.timestamp),
                temperature: parseFloat(data.temperature),
                device_id: data.device_id,
              },
            ];
            return newData.slice(-50);
          });
          await fetchStats();
        }
      } catch (error) {
        console.error('Error in updateData:', error);
      }
    },
    [selectedDevice]
  );

  useEffect(() => {
    loadInitialData();

    // Configuration des listeners Socket.IO
    socket.on('connect', () => {
      console.log('Connected to WebSocket server');
    });
    socket.on('new_reading', (reading) => {
      console.log('New temperature reading received:', reading);
      if (!reading || !reading.device_id || !reading.temperature || !reading.timestamp) {
        console.error('Invalid reading data:', reading);
        return;
      }
      setTemperatureData((prevData) => {
        const newData = [
          ...prevData,
          {
            ...reading,
            timestamp: new Date(reading.timestamp),
            temperature: parseFloat(reading.temperature),
          },
        ];
        return newData.slice(-50);
      });
      updateData(reading);
    });
    socket.on('stats_updated', (newStats) => {
      console.log('Stats updated:', newStats);
      setStats(newStats);
    });
    socket.on('connect_error', (error) => {
      console.error('Socket connection error:', error);
    });

    return () => {
      socket.off('new_reading');
      socket.off('stats_updated');
      socket.off('connect_error');
      socket.disconnect();
    };
  }, [updateData]);

  const loadInitialData = async () => {
    try {
      const readings = await deviceService.getRecentReadings();
      console.log('Initial readings:', readings);
      setTemperatureData(readings);

      const statsData = await deviceService.getStats();
      console.log('Initial stats:', statsData);
      setStats(statsData);
    } catch (error) {
      console.error('Error loading initial data:', error);
    }
  };

  const loadDevices = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        navigate('/login');
        return;
      }
      const response = await fetch(`${API_BASE_URL}/api/devices`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      if (!response.ok) {
        if (response.status === 401) {
          localStorage.removeItem('token');
          navigate('/login');
          return;
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const devicesData = await response.json();
      console.log('Loaded devices:', devicesData);
      setDevices(devicesData);
    } catch (error) {
      console.error('Error loading devices:', error);
      setDevices({});
    }
  };

  useEffect(() => {
    loadDevices();
  }, []);

  const handleDeviceSelect = (deviceId) => {
    setSelectedDevice(deviceId);
    setPrediction(null); // réinitialiser la prédiction lors du changement d'appareil
  };

  const handleAddDevice = () => {
    setEditingDevice(null);
    setIsModalOpen(true);
  };

  const handleEditDevice = (device) => {
    setEditingDevice(device);
    setIsModalOpen(true);
  };

  const handleSaveDevice = async (deviceData) => {
    try {
      if (editingDevice) {
        await deviceService.updateDevice(deviceData.mac, deviceData);
      } else {
        await deviceService.addDevice(deviceData);
      }
      setIsModalOpen(false);
      loadDevices();
    } catch (error) {
      console.error('Error saving device:', error);
    }
  };

  // Fonction pour déclencher la récupération de la prédiction
  const handleRunPrediction = async () => {
    if (!selectedDevice) {
      console.warn('Aucun appareil sélectionné pour la prédiction');
      return;
    }
    try {
      // On suppose ici que selectedDevice correspond à la mac de l'appareil.
      const predictionData = await predictionService.getDevicePrediction(selectedDevice);
      console.log('Prediction received:', predictionData);
      setPrediction(predictionData);
    } catch (error) {
      console.error('Error fetching prediction:', error);
    }
  };

  return (
    <div className="dashboard">
      <Typography variant="h3" gutterBottom className="dashboard-title" fontFamily="Poppins" fontWeight={700}>
        IoT Dashboard
      </Typography>
      <Grid container spacing={3}>
        <Grid item xs={12} md={12}>
          <Paper className="paper">
            <Statistics stats={stats} />
          </Paper>
        </Grid>
        <Grid item xs={12} md={4}>
          <Paper className="paper">
            <DeviceList
              devices={devices}
              selectedDevice={selectedDevice}
              onDeviceSelect={handleDeviceSelect}
              onAddDevice={handleAddDevice}
              onEditDevice={handleEditDevice}
            />
          </Paper>
        </Grid>
        <Grid item xs={12} md={8}>
          <Paper className="paper">
            <TemperatureChart data={temperatureData} />
          </Paper>
        </Grid>
        <Grid item xs={12} md={8}>
          <Paper className="paper">
            <DeviceMap
              devices={devices}
              selectedDevice={selectedDevice}
              onLocationSelect={(location) => {
                if (editingDevice) {
                  setEditingDevice({
                    ...editingDevice,
                    location,
                  });
                }
              }}
            />
          </Paper>
        </Grid>
        {/* Bouton pour déclencher la prédiction */}
        <Grid item xs={12}>
          <Paper className="paper" style={{ padding: '16px', textAlign: 'center' }}>
            <Button variant="contained" color="primary" onClick={handleRunPrediction}>
              Lancer la Prédiction
            </Button>
          </Paper>
        </Grid>
        {/* Affichage graphique des résultats de la prédiction */}
        {prediction && (
          <Grid item xs={12}>
            <Paper className="paper" style={{ padding: '16px' }}>
              <Typography variant="h6">Prédiction pour l'appareil {selectedDevice}</Typography>
              <Typography variant="body1">
                Température prédite : {prediction.prediction_temperature.toFixed(2)} °C
              </Typography>
              <Typography variant="body1">
                Humidité prédite : {prediction.prediction_humidity.toFixed(2)} %
              </Typography>
            </Paper>
          </Grid>
        )}
      </Grid>
      <DeviceModal open={isModalOpen} device={editingDevice} onClose={() => setIsModalOpen(false)} onSave={handleSaveDevice} />
    </div>
  );
}

export default Dashboard;
