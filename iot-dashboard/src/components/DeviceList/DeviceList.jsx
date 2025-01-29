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
    Box
} from '@mui/material';
import { Edit, Delete, Visibility } from '@mui/icons-material';
import './DeviceList.css';

function DeviceList({ onDeviceSelect }) {
    const [devices, setDevices] = useState([]);
    const [searchTerm, setSearchTerm] = useState('');
    const [openDialog, setOpenDialog] = useState(false);
    const [selectedDevice, setSelectedDevice] = useState(null);
    const [formData, setFormData] = useState({
        name: '',
        mac: '',
        location: '',
        status: 'inactive'
    });

    useEffect(() => {
        fetchDevices();
    }, []);

    const fetchDevices = async () => {
        try {
            const response = await fetch('http://localhost:5000/api/devices');
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
        try {
            const url = selectedDevice 
                ? `http://localhost:5000/api/devices/${selectedDevice.mac}`
                : 'http://localhost:5000/api/devices';
            
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
                const response = await fetch(`http://localhost:5000/api/devices/${mac}`, {
                    method: 'DELETE'
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
            location: device.location || '',
            status: device.status
        });
        setOpenDialog(true);
    };

    const resetForm = () => {
        setSelectedDevice(null);
        setFormData({
            name: '',
            mac: '',
            location: '',
            status: 'inactive'
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

            <Dialog open={openDialog} onClose={() => setOpenDialog(false)}>
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
                        <TextField
                            fullWidth
                            label="Location"
                            value={formData.location}
                            onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                            margin="normal"
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