import React, { useState, useEffect, useCallback } from 'react';
import { Grid, Paper, Typography } from '@mui/material';
import DeviceList from '../DeviceList/DeviceList';
import TemperatureChart from '../TemperatureChart/TemperatureChart';
import DeviceMap from '../DeviceMap/DeviceMap';
import Statistics from '../Statistics/Statistics';
import DeviceModal from '../DeviceModal/DeviceModal';
import { deviceService, statsService } from '../../services/api';
import { io } from 'socket.io-client';
import './Dashboard.css';

const socket = io('http://localhost:5000', {
    transports: ['websocket', 'polling'],
    reconnection: true,
    reconnectionAttempts: 5,
    reconnectionDelay: 1000,
    timeout: 10000
});

function Dashboard() {
    const [devices, setDevices] = useState({});
    const [selectedDevice, setSelectedDevice] = useState(null);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingDevice, setEditingDevice] = useState(null);
    const [temperatureData, setTemperatureData] = useState([]);
    const [stats, setStats] = useState(null);

    const updateData = useCallback(async (data) => {
        if (!selectedDevice || selectedDevice === data.device_id) {
            setTemperatureData(prev => [...prev, data].slice(-50));
            await updateStats();
        }
    }, [selectedDevice]);

    useEffect(() => {
        const initializeSocketConnection = () => {
            socket.on('connect', () => {
                console.log('Connected to WebSocket');
            });
    
            socket.on('new_reading', (data) => {
                console.log('New reading received:', data);
                updateData(data);
            });
    
            socket.on('connect_error', (error) => {
                console.error('Socket connection error:', error);
            });
        };
    
        initializeSocketConnection();
    
        return () => {
            socket.disconnect();
        };
    }, [updateData]);

    // useEffect(() => {
    //     loadDevices();
    //     initializeSocketConnection();
        
    //     return () => {
    //         socket.disconnect();
    //     };
    // }, [initializeSocketConnection]);

    

    const loadDevices = async () => {
        try {
            const response = await fetch('http://localhost:5000/api/devices');
            const devicesData = await response.json();
            setDevices(devicesData);
        } catch (error) {
            console.error('Error loading devices:', error);
        }
    };
    
    useEffect(() => {
        loadDevices();
    }, []);

    const updateStats = async () => {
        try {
            const statsData = await statsService.getStats();
            setStats(statsData);
        } catch (error) {
            console.error('Error updating stats:', error);
        }
    };

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
            <Typography variant="h4" gutterBottom>
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