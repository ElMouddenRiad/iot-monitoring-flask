import React, { useState, useEffect } from 'react';
import { 
    List, 
    ListItem, 
    ListItemText, 
    ListItemSecondaryAction,
    IconButton,
    TextField,
    Button,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    FormControl,
    InputLabel,
    Select,
    MenuItem,
    Box,
    Typography
} from '@mui/material';
import { Edit, Delete, Visibility } from '@mui/icons-material';
import { MapContainer, TileLayer, Marker, useMapEvents } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import './DeviceList.css';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:5000';

// Fix for default marker icon
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
    iconUrl: require('leaflet/dist/images/marker-icon.png'),
    shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});

function LocationSelector({ onSelect, initialPosition }) {
    const [position, setPosition] = useState(initialPosition || null);

    useMapEvents({
        click(e) {
            setPosition(e.latlng);
            onSelect(e.latlng);
        },
    });

    return position === null ? null : (
        <Marker position={position}></Marker>
    );
}

function DeviceList({ onDeviceSelect }) {
    const [devices, setDevices] = useState([]);
    const [searchTerm, setSearchTerm] = useState('');
    const [openDialog, setOpenDialog] = useState(false);
    const [selectedDevice, setSelectedDevice] = useState(null);
    const [formData, setFormData] = useState({
        name: '',
        mac: '',
        status: 'inactive',
        latitude: null,
        longitude: null
    });

    useEffect(() => {
        fetchDevices();
    }, []);

    const fetchDevices = async () => {
        try {
            const token = localStorage.getItem('token');  // Retrieve the token from localStorage
            const response = await fetch(`${API_BASE_URL}/api/devices`, {
                headers: {
                    Authorization: `Bearer ${token}`,  // Add the token to the headers
                },
            });
            if (!response.ok) {
                throw new Error('Failed to fetch devices');
            }
            const data = await response.json();
            setDevices(Array.isArray(data) ? data : []);
        } catch (error) {
            console.error('Error fetching devices:', error);
            setDevices([]);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        // Ensure latitude and longitude are selected
        if (formData.latitude === null || formData.longitude === null) {
            alert('Please select a location on the map.');
            return;
        }

        try {
            const url = selectedDevice 
                ? `${API_BASE_URL}/api/devices/${selectedDevice.mac}`
                : `${API_BASE_URL}/api/devices`;
            
            const method = selectedDevice ? 'PUT' : 'POST';
            
            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData),
            });

            if (response.ok) {
                setOpenDialog(false);
                fetchDevices();
                resetForm();
            } else {
                const error = await response.json();
                alert(error.message || 'Error saving device');
            }
        } catch (error) {
            console.error('Error saving device:', error);
            alert('Error saving device');
        }
    };

    const handleDelete = async (mac) => {
        if (window.confirm('Are you sure you want to delete this device?')) {
            try {
                const token = localStorage.getItem('token');  // Retrieve the token from localStorage
                const response = await fetch(`${API_BASE_URL}/api/devices/${mac}`, {
                    method: 'DELETE',
                    headers: {
                        Authorization: `Bearer ${token}`,  // Add the token to the headers
                    },
                });
                if (response.ok) {

                    fetchDevices();
                } else {
                    alert('Error deleting device');
                }
            } catch (error) {
                console.error('Error deleting device:', error);
                alert('Error deleting device');
            }
        }
    };

    const handleEdit = (device) => {
        setSelectedDevice(device);
        setFormData({
            name: device.name,
            mac: device.mac,
            status: device.status,
            latitude: device.latitude || null,
            longitude: device.longitude || null
        });
        setOpenDialog(true);
    };

    const resetForm = () => {
        setSelectedDevice(null);
        setFormData({
            name: '',
            mac: '',
            status: 'inactive',
            latitude: null,
            longitude: null
        });
    };

    const handleLocationSelect = (latlng) => {
        setFormData({
            ...formData,
            latitude: latlng.lat,
            longitude: latlng.lng
        });
    };

    const filteredDevices = devices.filter(device =>
        device.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        device.mac.toLowerCase().includes(searchTerm.toLowerCase())
    );

    return (
        <Box className="device-list">
            <Box className="device-list-header" sx={{ mb: 2, display: 'flex', gap: 2 }}>
                <TextField
                    placeholder="Search devices..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    variant="outlined"
                    size="medium"
                    fullWidth
                />
                <Button
                    variant="contained"
                    color="primary"
                    onClick={() => {
                        resetForm();
                        setOpenDialog(true);
                    }}
                    sx={{ fontFamily: 'Poppins' }}
                >
                    NEW
                </Button>
            </Box>

            <List>
                {filteredDevices.map((device) => (
                    <ListItem 
                        key={device.mac}
                        sx={{
                            mb: 1,
                            bgcolor: 'background.paper',
                            borderRadius: 1,
                            '&:hover': {
                                bgcolor: 'action.hover',
                            }
                        }}
                    >
                        <ListItemText
                            primary={device.name}
                            secondary={`MAC: ${device.mac} | Status: ${device.status}`}
                        />
                        <ListItemSecondaryAction>
                            <IconButton onClick={() => onDeviceSelect(device)}>
                                <Visibility />
                            </IconButton>
                            <IconButton onClick={() => handleEdit(device)}>
                                <Edit />
                            </IconButton>
                            <IconButton onClick={() => handleDelete(device.mac)}>
                                <Delete />
                            </IconButton>
                        </ListItemSecondaryAction>
                    </ListItem>
                ))}
            </List>

            <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="md" fullWidth>
                <DialogTitle>
                    {selectedDevice ? 'Edit Device' : 'Add New Device'}
                </DialogTitle>
                <DialogContent>
                    <Box component="form" onSubmit={handleSubmit} sx={{ mt: 2 }}>
                        <TextField
                            fullWidth
                            label="Device Name"
                            value={formData.name}
                            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                            margin="normal"
                            required
                        />
                        <TextField
                            fullWidth
                            label="MAC Address"
                            value={formData.mac}
                            onChange={(e) => setFormData({ ...formData, mac: e.target.value })}
                            margin="normal"
                            required
                            disabled={!!selectedDevice}
                        />
                        <FormControl fullWidth margin="normal">
                            <InputLabel>Status</InputLabel>
                            <Select
                                value={formData.status}
                                onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                                label="Status"
                            >
                                <MenuItem value="active">Active</MenuItem>
                                <MenuItem value="inactive">Inactive</MenuItem>
                            </Select>
                        </FormControl>

                        <Typography variant="subtitle1" sx={{ mt: 2, mb: 1 }}>
                            Select Location
                        </Typography>
                        <Box sx={{ height: 300 }}>
                            <MapContainer 
                                center={formData.latitude && formData.longitude ? [formData.latitude, formData.longitude] : [0, 0]} 
                                zoom={formData.latitude && formData.longitude ? 13 : 2} 
                                style={{ height: '100%', width: '100%' }}
                            >
                                <TileLayer
                                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                                />
                                <LocationSelector 
                                    onSelect={handleLocationSelect} 
                                    initialPosition={formData.latitude && formData.longitude ? { lat: formData.latitude, lng: formData.longitude } : null}
                                />
                            </MapContainer>
                        </Box>
                        {formData.latitude && formData.longitude && (
                            <Box sx={{ mt: 2 }}>
                                <Typography variant="body2">
                                    Selected Location: Latitude {formData.latitude.toFixed(6)}, Longitude {formData.longitude.toFixed(6)}
                                </Typography>
                            </Box>
                        )}
                    </Box>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setOpenDialog(false)}>Cancel</Button>
                    <Button onClick={handleSubmit} variant="contained" color="primary">
                        {selectedDevice ? 'Update' : 'Add'}
                    </Button>
                </DialogActions>
            </Dialog>
        </Box>
    );
}

export default DeviceList;