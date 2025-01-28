import React, { useState, useEffect } from 'react';
import { Grid, Paper, Typography } from '@material-ui/core';
import DeviceList from '../DeviceList/DeviceList';
import TemperatureChart from '../TemperatureChart/TemperatureChart';
import DeviceMap from '../DeviceMap/DeviceMap';
import Statistics from '../Statistics/Statistics';
import DeviceModal from '../DeviceModal/DeviceModal';
import { io } from 'socket.io-client';
import './Dashboard.css';

const socket = io('http://localhost:5000');

function Dashboard() {
    const [devices, setDevices] = useState({});
    const [selectedDevice, setSelectedDevice] = useState(null);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingDevice, setEditingDevice] = useState(null);
    const [temperatureData, setTemperatureData] = useState([]);
    const [stats, setStats] = useState(null);

    useEffect(() => {
        loadDevices();
        
        socket.on('connect', () => {
            console.log('Connected to WebSocket');
        });

        socket.on('new_reading', (data) => {
            updateData(data);
        });

        return () => {
            socket.disconnect();
        };
    }, []);

    const loadDevices = async () => {
        try {
            const response = await fetch('http://localhost:5000/api/devices');
            const data = await response.json();
            setDevices(data);
        } catch (error) {
            console.error('Error loading devices:', error);
        }
    };

    const updateData = (data) => {
        if (!selectedDevice || selectedDevice === data.device_id) {
            setTemperatureData(prev => [...prev, data].slice(-50));
            updateStats();
        }
    };

    const updateStats = async () => {
        try {
            const response = await fetch('http://localhost:5000/api/stats');
            const data = await response.json();
            setStats(data);
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
                        <DeviceMap devices={devices} />
                    </Paper>
                </Grid>
            </Grid>

            <DeviceModal 
                open={isModalOpen}
                device={editingDevice}
                onClose={() => setIsModalOpen(false)}
                onSave={loadDevices}
            />
        </div>
    );
}

export default Dashboard; 