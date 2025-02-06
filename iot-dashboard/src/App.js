import React from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import CssBaseline from '@mui/material/CssBaseline';
import Box from '@mui/material/Box';
import Dashboard from './components/Dashboard/Dashboard';
import './App.css';
import EndDeviceMonitor from './components/EndDeviceMonitor/EndDeviceMonitor';
import Sidebar from './components/Sidebar/Sidebar';
import PredictionChart from './components/Prediction/PredictionChart';
  // import SignIn from './components/SignIn/SignIn';
  // import SignUp from './components/SignUp/SignUp';

const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

// PrivateRoute component to protect routes
// const PrivateRoute = ({ children }) => {
//     const token = localStorage.getItem('token');
//     return token ? children : <Navigate to="/login" />;
// };

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <BrowserRouter>
        <Box sx={{ display: 'flex' }}>
          <Sidebar />
          <Box component="main" sx={{ flexGrow: 1, p: 3 }}>
            <Routes>
              {/* <Route path="/login" element={<SignIn />} />
              <Route path="/signup" element={<SignUp />} /> */}
              <Route path="/" element={<Dashboard />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/device-monitor" element={<EndDeviceMonitor />} />
              <Route path='/prediction' element={<PredictionChart />} />
            </Routes>
          </Box>
        </Box>
      </BrowserRouter>
    </ThemeProvider>
  );
}

export default App;