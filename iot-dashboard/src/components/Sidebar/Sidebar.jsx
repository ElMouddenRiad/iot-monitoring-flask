import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Typography,
  Divider,
  Button,
} from '@mui/material';
import DashboardIcon from '@mui/icons-material/Dashboard';
import DevicesIcon from '@mui/icons-material/Devices';
import ExitToAppIcon from '@mui/icons-material/ExitToApp';


const drawerWidth = 240;

function Sidebar() {
  const location = useLocation();
  const navigate = useNavigate();

  const menuItems = [
    {
      text: 'Dashboard',
      icon: <DashboardIcon />,
      path: '/dashboard'
    },
    {
      text: 'Device Monitor',
      icon: <DevicesIcon />,
      path: '/device-monitor'
    },
    {
      text: 'Prediction',
      icon: <DashboardIcon />,
      path: '/prediction'
    }
  ];


  const handleLogout = async () => {
    const token = localStorage.getItem('token');
    if (token) {
      try {
        
        const response = await fetch('http://localhost:5000/auth/logout', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          }
        });

        if (response.ok) {
          localStorage.removeItem('token');
          navigate('/login');
        } else {
          console.error('Logout failed.');
        }
      } catch (error) {
        console.error('Logout error:', error);
      }
    }
  };

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
        <Divider />
        <List>
          <ListItem>
            <Button
              variant="outlined"
              color="secondary"
              startIcon={<ExitToAppIcon />}
              onClick={handleLogout}
              fullWidth
            >
              Logout
            </Button>
          </ListItem>
        </List>
      </div>
    </Drawer>
  );
}

export default Sidebar; 