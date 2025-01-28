import React, { useState } from 'react';
import { 
    List, 
    ListItem, 
    ListItemText, 
    ListItemSecondaryAction,
    IconButton,
    TextField,
    Button
} from '@material-ui/core';
import { Edit, Delete, Visibility } from '@material-ui/icons';
import './DeviceList.css';

function DeviceList({ devices, selectedDevice, onDeviceSelect, onAddDevice, onEditDevice }) {
    const [searchTerm, setSearchTerm] = useState('');

    const handleDelete = async (mac) => {
        if (window.confirm('Are you sure you want to delete this device?')) {
            try {
                await fetch(`http://localhost:5000/api/devices/${mac}`, {
                    method: 'DELETE'
                });
                window.location.reload();
            } catch (error) {
                console.error('Error deleting device:', error);
            }
        }
    };

    const filteredDevices = Object.entries(devices).filter(([mac, device]) =>
        device.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        mac.toLowerCase().includes(searchTerm.toLowerCase())
    );

    return (
        <div className="device-list">
            <div className="device-list-header">
                <TextField
                    placeholder="Search devices..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    variant="outlined"
                    size="small"
                    fullWidth
                />
                <Button
                    variant="contained"
                    color="primary"
                    onClick={onAddDevice}
                    className="add-button"
                >
                    Add Device
                </Button>
            </div>

            <List>
                {filteredDevices.map(([mac, device]) => (
                    <ListItem 
                        key={mac}
                        selected={selectedDevice === mac}
                        button
                    >
                        <ListItemText
                            primary={device.name}
                            secondary={`MAC: ${mac} | Status: ${device.status}`}
                        />
                        <ListItemSecondaryAction>
                            <IconButton onClick={() => onDeviceSelect(mac)}>
                                <Visibility />
                            </IconButton>
                            <IconButton onClick={() => onEditDevice(device)}>
                                <Edit />
                            </IconButton>
                            <IconButton onClick={() => handleDelete(mac)}>
                                <Delete />
                            </IconButton>
                        </ListItemSecondaryAction>
                    </ListItem>
                ))}
            </List>
        </div>
    );
}

export default DeviceList;