import React, { useState, useEffect } from 'react';
import { Grid, Paper, Typography } from '@mui/material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';
import './EndDeviceMonitor.css';

function EndDeviceMonitor() {
    const [endDevices, setEndDevices] = useState([]);
    const [selectedDevice, setSelectedDevice] = useState(null);
    const [metrics, setMetrics] = useState([]);
    const [loading, setLoading] = useState(true);

    // Fetch end devices
    useEffect(() => {
        const fetchEndDevices = async () => {
            setLoading(true);
            try {
                const token = localStorage.getItem('token');
                const response = await fetch('http://localhost:5000/api/end-devices', {
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                });
                if (response.ok) {
                    const data = await response.json();
                    setEndDevices(data);

                }
            } catch (error) {
                console.error('Error fetching end devices:', error);
            } finally {
                setLoading(false);
            }
        };

        fetchEndDevices();
        const interval = setInterval(fetchEndDevices, 60000); // Refresh every 60 seconds

        return () => clearInterval(interval);
    }, []);

    // Fetch metrics for selected device
    useEffect(() => {
        const fetchMetrics = async () => {
            if (!selectedDevice) return;
            setLoading(true);
            try {
                const token = localStorage.getItem('token');
                const response = await fetch(`http://localhost:5000/api/end-devices/metrics/${selectedDevice.mac}`, {
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                });
                if (response.ok) {
                    const data = await response.json();

                    setMetrics(data);
                }
            } catch (error) {
                console.error('Error fetching metrics:', error);
            } finally {
                setLoading(false);
            }
        };

        fetchMetrics();
        const interval = setInterval(fetchMetrics, 60000); // Refresh every 60 seconds

        return () => clearInterval(interval);
    }, [selectedDevice]);

    const formatBytes = (bytes) => {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    };

    return (
        <div className="end-device-monitor">
            <Typography variant="h4" gutterBottom>
                End Device Monitor
            </Typography>

            <Grid container spacing={3}>
                {/* Device List */}
                <Grid item xs={12} md={3}>
                    <Paper className="paper">
                        <Typography variant="h6" gutterBottom>
                            Connected Devices
                        </Typography>
                        <div className="device-list">
                            {loading && <Typography>Loading devices...</Typography>}
                            {!loading && endDevices.map((device) => (
                                <div
                                    key={device.mac}
                                    className={`device-item ${selectedDevice?.mac === device.mac ? 'selected' : ''}`}
                                    onClick={() => setSelectedDevice(device)}
                                >
                                    <Typography variant="subtitle1">{device.name}</Typography>
                                    <Typography variant="body2" color="textSecondary">
                                        {device.ip_address}
                                    </Typography>
                                    <div className={`status-indicator ${device.status}`} />
                                </div>
                            ))}
                        </div>
                    </Paper>
                </Grid>

                {/* Metrics Display */}
                <Grid item xs={12} md={9}>
                    {selectedDevice ? (
                        <Grid container spacing={2}>
                            {/* CPU Usage Chart */}
                            <Grid item xs={12} md={6}>
                                <Paper className="paper">
                                    <Typography variant="h6" gutterBottom>
                                        CPU Usage
                                    </Typography>
                                    {loading ? (
                                        <Typography>Loading metrics...</Typography>
                                    ) : (
                                        <LineChart width={440} height={300} data={metrics}>
                                            <CartesianGrid strokeDasharray="3 3" />
                                            <XAxis dataKey="timestamp" />
                                            <YAxis />
                                            <Tooltip />
                                            <Legend />
                                            <Line 
                                                type="monotone" 
                                                dataKey="system_metrics.cpu.percent" 
                                                stroke="#8884d8" 
                                                name="CPU %" 
                                            />
                                        </LineChart>
                                    )}
                                </Paper>
                            </Grid>

                            {/* Memory Usage Chart */}
                            <Grid item xs={'auto'} md={6}>
                                <Paper className="paper">
                                    <Typography variant="h6" gutterBottom>
                                        Memory Usage
                                    </Typography>
                                    {loading ? (
                                        <Typography>Loading metrics...</Typography>
                                    ) : (
                                        <LineChart width={440} height={300} data={metrics}>
                                            <CartesianGrid strokeDasharray="3 3" />
                                            <XAxis dataKey="timestamp" />
                                            <YAxis />
                                            <Tooltip />
                                            <Legend />
                                            <Line 
                                                type="monotone" 
                                                dataKey="system_metrics.memory.percent" 
                                                stroke="#82ca9d" 
                                                name="Memory %" 
                                            />
                                        </LineChart>
                                    )}
                                </Paper>
                            </Grid>

                            {/* System Info */}
                            <Grid item xs={12}>
                                <Paper className="paper">
                                    <Typography variant="h6" gutterBottom>
                                        System Information
                                    </Typography>
                                    <Grid container spacing={2}>
                                        <Grid item xs={6} md={3}>
                                            <Typography variant="subtitle2">Operating System</Typography>
                                            <Typography>{selectedDevice.os} {selectedDevice.os_version}</Typography>
                                        </Grid>
                                        <Grid item xs={6} md={3}>
                                            <Typography variant="subtitle2">Processor</Typography>
                                            <Typography>{selectedDevice.processor}</Typography>
                                        </Grid>
                                        <Grid item xs={6} md={3}>
                                            <Typography variant="subtitle2">MAC Address</Typography>
                                            <Typography>{selectedDevice.mac}</Typography>
                                        </Grid>
                                        <Grid item xs={6} md={3}>
                                            <Typography variant="subtitle2">Last Seen</Typography>
                                            <Typography>{new Date(selectedDevice.last_seen).toLocaleString()}</Typography>
                                        </Grid>
                                        <Grid item xs={6} md={3}>
                                            <Typography variant="subtitle2">Total Memory</Typography>
                                            <Typography>
                                                {metrics.length > 0 && formatBytes(metrics[metrics.length - 1].system_metrics.memory.total)}
                                            </Typography>
                                        </Grid>
                                    </Grid>
                                </Paper>
                            </Grid>
                        </Grid>
                    ) : (
                        <Paper className="paper">
                            <Typography variant="h6" align="center">
                                Select a device to view metrics
                            </Typography>
                        </Paper>
                    )}
                </Grid>
            </Grid>
        </div>
    );
}

export default EndDeviceMonitor; 