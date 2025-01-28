import React, { useState, useEffect } from 'react';
import { MapPin, Plus, X, Thermometer } from 'lucide-react';
import { io } from 'socket.io-client';

const Dashboard = () => {
    const [devices, setDevices] = useState([]);
    const [readings, setReadings] = useState({});
    const [showAddDevice, setShowAddDevice] = useState(false);
    const [newDevice, setNewDevice] = useState({
        mac: '',
        name: '',
        location: {
            latitude: '',
            longitude: ''
        },
        frequency: 15
    });

    // Initialize Socket.IO connection
    useEffect(() => {
        const socket = io('http://localhost:5000');
        
        socket.on('new_data', (data) => {
            setReadings(prev => ({
                ...prev,
                [data.device_id]: {
                    temperature: data.temperature,
                    timestamp: data.timestamp
                }
            }));
        });

        return () => socket.disconnect();
    }, []);

    // Fetch devices on component mount
    useEffect(() => {
        fetchDevices();
    }, []);

    const fetchDevices = async () => {
        try {
            const response = await fetch('http://localhost:5001/devices');
            const data = await response.json();
            setDevices(data);
        } catch (error) {
            console.error('Error fetching devices:', error);
        }
    };

    const handleAddDevice = async (e) => {
        e.preventDefault();
        try {
            const response = await fetch('http://localhost:5001/devices', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(newDevice),
            });

            if (response.ok) {
                setShowAddDevice(false);
                setNewDevice({
                    mac: '',
                    name: '',
                    location: {
                        latitude: '',
                        longitude: ''
                    },
                    frequency: 15
                });
                fetchDevices();
            }
        } catch (error) {
            console.error('Error adding device:', error);
        }
    };

    return (
        <div className="min-h-screen bg-gray-100 p-8">
            <div className="max-w-7xl mx-auto">
                <header className="mb-8">
                    <h1 className="text-3xl font-bold text-gray-900">IoT Temperature Dashboard</h1>
                </header>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {/* Device Management Section */}
                    <div className="bg-white rounded-lg shadow p-6">
                        <div className="flex justify-between items-center mb-4">
                            <h2 className="text-xl font-semibold">Device Management</h2>
                            <button
                                onClick={() => setShowAddDevice(true)}
                                className="bg-blue-500 text-white p-2 rounded-full hover:bg-blue-600"
                            >
                                <Plus size={20} />
                            </button>
                        </div>
                        <div className="space-y-4">
                            {devices.map(device => (
                                <div key={device.mac} className="border rounded-lg p-4">
                                    <h3 className="font-medium">{device.name || device.mac}</h3>
                                    <div className="text-sm text-gray-500">
                                        <p>MAC: {device.mac}</p>
                                        <p>Location: {device.location.latitude}, {device.location.longitude}</p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Latest Readings Section */}
                    <div className="bg-white rounded-lg shadow p-6">
                        <h2 className="text-xl font-semibold mb-4">Latest Temperature Readings</h2>
                        <div className="space-y-4">
                            {Object.entries(readings).map(([deviceId, data]) => (
                                <div key={deviceId} className="border rounded-lg p-4">
                                    <div className="flex items-center">
                                        <Thermometer className="text-red-500 mr-2" />
                                        <div>
                                            <p className="font-medium">{deviceId}</p>
                                            <p className="text-2xl font-bold">{data.temperature}°C</p>
                                            <p className="text-sm text-gray-500">
                                                Last updated: {new Date(data.timestamp).toLocaleString()}
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Device Locations Section */}
                    <div className="bg-white rounded-lg shadow p-6">
                        <h2 className="text-xl font-semibold mb-4">Device Locations</h2>
                        <div className="space-y-4">
                            {devices.map(device => (
                                <div key={device.mac} className="border rounded-lg p-4">
                                    <div className="flex items-center">
                                        <MapPin className="text-blue-500 mr-2" />
                                        <div>
                                            <p className="font-medium">{device.name || device.mac}</p>
                                            <p className="text-sm text-gray-500">
                                                Lat: {device.location.latitude}
                                                <br />
                                                Long: {device.location.longitude}
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Add Device Modal */}
                {showAddDevice && (
                    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
                        <div className="bg-white rounded-lg p-6 w-full max-w-md">
                            <div className="flex justify-between items-center mb-4">
                                <h2 className="text-xl font-semibold">Add New Device</h2>
                                <button
                                    onClick={() => setShowAddDevice(false)}
                                    className="text-gray-500 hover:text-gray-700"
                                >
                                    <X size={20} />
                                </button>
                            </div>
                            <form onSubmit={handleAddDevice} className="space-y-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700">MAC Address</label>
                                    <input
                                        type="text"
                                        value={newDevice.mac}
                                        onChange={(e) => setNewDevice({...newDevice, mac: e.target.value})}
                                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                                        required
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700">Name</label>
                                    <input
                                        type="text"
                                        value={newDevice.name}
                                        onChange={(e) => setNewDevice({...newDevice, name: e.target.value})}
                                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700">Latitude</label>
                                    <input
                                        type="number"
                                        step="any"
                                        value={newDevice.location.latitude}
                                        onChange={(e) => setNewDevice({
                                            ...newDevice,
                                            location: {...newDevice.location, latitude: e.target.value}
                                        })}
                                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                                        required
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700">Longitude</label>
                                    <input
                                        type="number"
                                        step="any"
                                        value={newDevice.location.longitude}
                                        onChange={(e) => setNewDevice({
                                            ...newDevice,
                                            location: {...newDevice.location, longitude: e.target.value}
                                        })}
                                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                                        required
                                    />
                                </div>
                                <div className="flex justify-end space-x-4">
                                    <button
                                        type="button"
                                        onClick={() => setShowAddDevice(false)}
                                        className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
                                    >
                                        Cancel
                                    </button>
                                    <button
                                        type="submit"
                                        className="px-4 py-2 text-sm font-medium text-white bg-blue-500 rounded-md hover:bg-blue-600"
                                    >
                                        Save
                                    </button>
                                </div>
                            </form>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default Dashboard;