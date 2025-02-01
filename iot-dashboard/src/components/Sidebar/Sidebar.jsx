import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Typography,
  Divider,
} from '@mui/material';
import DashboardIcon from '@mui/icons-material/Dashboard';
import DevicesIcon from '@mui/icons-material/Devices';

const drawerWidth = 240;

function Sidebar() {
  const location = useLocation();

  const menuItems = [
    {
      text: 'IOT Dashboard',
      icon: <DashboardIcon />,
      path: '/dashboard'
    },
    {
      text: 'Device Monitor',
      icon: <DevicesIcon />,
      path: '/device-monitor'
    }
  ];

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: drawerWidth,
        fontFamily: 'Poppins',
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: drawerWidth,
          boxSizing: 'border-box',
        },
      }}
    >
      <div>
        <Typography variant="h6" sx={{ p: 2, fontFamily: 'Poppins' }} >
          IoT Dashboard
        </Typography>
        <Divider />
        <List>
          {menuItems.map((item) => (
            <ListItem
              button
              key={item.text}
              component={Link}
              to={item.path}
              selected={location.pathname === item.path}
              sx={{
                '&.Mui-selected': {
                  backgroundColor: 'rgba(25, 118, 210, 0.12)',
                },
                '&.Mui-selected:hover': {
                  backgroundColor: 'rgba(25, 118, 210, 0.2)',
                },
              }}
            >
              <ListItemIcon>{item.icon}</ListItemIcon>
              <ListItemText primary={item.text} sx={{ fontFamily: 'Poppins' }} />
            </ListItem>
          ))}
        </List>
      </div>
    </Drawer>
  );
}

export default Sidebar; 