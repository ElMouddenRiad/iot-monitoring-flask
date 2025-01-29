import React from 'react';
import { Dialog, DialogTitle, DialogContent, DialogActions, Button, TextField } from '@mui/material';

const DeviceModal = ({ open, handleClose, handleSubmit, device = {}, setDevice }) => {
  return (
    <Dialog open={open} onClose={handleClose}>
      <DialogTitle>{device?.id ? 'Edit Device' : 'Add Device'}</DialogTitle>
      <DialogContent>
        <TextField
          margin="dense"
          label="Name"
          fullWidth
          value={device?.name || ''}
          onChange={(e) => setDevice({...device, name: e.target.value})}
        />
        <TextField
          margin="dense"
          label="Location"
          fullWidth
          value={device?.location || ''}
          onChange={(e) => setDevice({...device, location: e.target.value})}
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose}>Cancel</Button>
        <Button onClick={handleSubmit} color="primary">Save</Button>
      </DialogActions>
    </Dialog>
  );
};

export default DeviceModal; 