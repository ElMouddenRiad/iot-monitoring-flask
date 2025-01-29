import React, { useState, useEffect, useCallback } from 'react';
import { Grid, Paper, Typography } from '@mui/material';
import DeviceList from '../DeviceList/DeviceList';
import TemperatureChart from '../TemperatureChart/TemperatureChart';
import DeviceMap from '../DeviceMap/DeviceMap';
import Statistics from '../Statistics/Statistics';
import DeviceModal from '../DeviceModal/DeviceModal';
import { deviceService } from '../../services/api';
import { io } from 'socket.io-client';
import './Dashboard.css';

const socket = io('http://localhost:5000', {
    transports: ['websocket', 'polling'],
    reconnection: true,
    reconnectionAttempts: 10,
    reconnectionDelay: 1000,
    reconnectionDelayMax: 5000,
    timeout: 20000,
    autoConnect: true,
    forceNew: true,
    withCredentials: false
});

const API_BASE_URL = 'http://localhost:5000';

function Dashboard() {
    const [devices, setDevices] = useState({});
    const [selectedDevice, setSelectedDevice] = useState(null);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingDevice, setEditingDevice] = useState(null);
    const [temperatureData, setTemperatureData] = useState([]);
    const [stats, setStats] = useState(null);

    const fetchStats = async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/api/stats`);
            if (!response.ok) {
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

    const updateData = useCallback(async (data) => {
        console.log('Received new data:', data);
        try {
            if (!selectedDevice || selectedDevice === data.device_id) {
                setTemperatureData(prev => {
                    const newData = [...prev, {
                        timestamp: new Date(data.timestamp),
                        temperature: parseFloat(data.temperature),
                        device_id: data.device_id
                    }];
                    console.log('Updated temperature data:', newData);
                    return newData.slice(-50);
                });
                
                await fetchStats();  // Update stats after new data
            }
        } catch (error) {
            console.error('Error in updateData:', error);
        }
    }, [selectedDevice]);

    useEffect(() => {
        const initializeSocketConnection = () => {
            console.log('Initializing socket connection...');
            
            socket.on('connect', () => {
                console.log('Connected to WebSocket');
            });

            socket.on('connect_error', (error) => {
                console.error('Socket connection error:', error);
            });

            socket.on('new_reading', (data) => {
                console.log('New reading received from socket:', data);
                updateData(data);
            });

            socket.on('connection_response', (data) => {
                console.log('Socket connection response:', data);
            });

            socket.on('disconnect', () => {
                console.log('Disconnected from WebSocket');
            });
        };

        initializeSocketConnection();
        
        // Initial stats load
        fetchStats();

        return () => {
            socket.off('connect');
            socket.off('connect_error');
            socket.off('new_reading');
            socket.off('connection_response');
            socket.off('disconnect');
            socket.disconnect();
        };
    }, [updateData]);

    const loadDevices = async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/api/devices`);
            if (!response.ok) {
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
        const loadInitialData = async () => {
            try {
                // Load initial temperature readings
                const response = await fetch(`${API_BASE_URL}/api/readings/recent`);
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                const readings = await response.json();
                console.log('Initial readings:', readings);
                setTemperatureData(readings.map(reading => ({
                    timestamp: new Date(reading.timestamp),
                    temperature: parseFloat(reading.temperature),
                    device_id: reading.device_id
                })));
            } catch (error) {
                console.error('Error loading initial data:', error);
            }
        };

        loadInitialData();
        loadDevices();
    }, []);

    const handleDeviceSelect = (deviceId) => {
        setSelectedDevice(deviceId);
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

    return (
        <div className="dashboard">
            <Typography variant="h4" gutterBottom className="dashboard-title">
                IoT Temperature Dashboard
            </Typography>
            
            <Grid container spacing={3}>
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
                
                <Grid item xs={12} md={4}>
                    <Paper className="paper">
                        <Statistics stats={stats} />
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
                                        location
                                    });
                                }
                            }}
                        />
                    </Paper>
                </Grid>
            </Grid>

            <DeviceModal 
                open={isModalOpen}
                device={editingDevice}
                onClose={() => setIsModalOpen(false)}
                onSave={handleSaveDevice}
            />
        </div>
    );
}

export default Dashboard; 