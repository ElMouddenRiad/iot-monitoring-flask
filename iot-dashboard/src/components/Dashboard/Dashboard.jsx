import React, { useState, useEffect, useCallback } from 'react';
import './Dashboard.css';
import { Grid, Paper, Typography } from '@mui/material';
import DeviceList from '../DeviceList/DeviceList';
import TemperatureChart from '../TemperatureChart/TemperatureChart';
import DeviceMap from '../DeviceMap/DeviceMap';
import Statistics from '../Statistics/Statistics';
import DeviceModal from '../DeviceModal/DeviceModal';
import { deviceService } from '../../services/api';
import { io } from 'socket.io-client';
import useAuth from '../../hooks/useAuth';
import { Navigate } from 'react-router-dom';
const socket = io('http://localhost:5000', {
    transports: ['websocket', 'polling'],
    reconnection: true,
    cors: {
        origin: "http://localhost:3000"
    },    
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
    
    useAuth(); // Ensure user is authenticated

    const fetchStats = async () => {
        try {
            const token = localStorage.getItem('token');    
            if (!token) {
                Navigate('/login');
                return;
            }
            const response = await fetch(`${API_BASE_URL}/api/stats`, {
                headers: {
                    Authorization: `Bearer ${token}`,
                },
            });
            if (!response.ok) {
                if (response.status === 401) {
                    localStorage.removeItem('token');
                    Navigate('/login');
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
        // Load initial data
        loadInitialData();

        // Set up Socket.IO listeners
        socket.on('connect', () => {
            console.log('Connected to WebSocket server');
        });

        socket.on('new_reading', (reading) => {
            console.log('New temperature reading received:', reading);
            setTemperatureData(prevData => {
                const newData = [...prevData, reading];
                // Keep only last 50 readings
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
    }, [updateData]); // Add updateData to dependency array

    const loadInitialData = async () => {
        try {
            // Load recent temperature readings
            const readings = await deviceService.getRecentReadings();
            console.log('Initial readings:', readings);
            setTemperatureData(readings);

            // Load initial statistics
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
                Navigate('/login');
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
                    Navigate('/login');
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