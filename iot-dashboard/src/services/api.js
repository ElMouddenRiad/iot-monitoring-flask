import axios from 'axios';
import { Navigate } from 'react-router-dom';

const API_BASE_URL = 'http://localhost:5000';
const token = localStorage.getItem('token');

export const deviceService = {
    getDevices: async () => {
        try {
            const response = await axios.get(`${API_BASE_URL}/api/devices`, {
                headers: {
                    Authorization: `Bearer ${token}`,
                },
            });
            return response.data;
        } catch (error) {
            console.error('Error fetching devices:', error);
            return {};
        }
    },

    addDevice: async (deviceData) => {
        const token = localStorage.getItem('token');  // Retrieve the token from localStorage
        const response = await axios.post(`${API_BASE_URL}/api/devices`, deviceData, {
            headers: {
                Authorization: `Bearer ${token}`,
            },
        });
        return response.data;
    },


    updateDevice: async (mac, deviceData) => {
        const token = localStorage.getItem('token');  // Retrieve the token from localStorage
        const response = await axios.put(`${API_BASE_URL}/api/devices/${mac}`, deviceData, {
            headers: {
                Authorization: `Bearer ${token}`,
            },
        });
        return response.data;
    },


    deleteDevice: async (mac) => {
        const token = localStorage.getItem('token');  // Retrieve the token from localStorage
        const response = await axios.delete(`${API_BASE_URL}/api/devices/${mac}`, {
            headers: {
                Authorization: `Bearer ${token}`,
            },
        });
        return response.data;
    },


    getStats: async () => {
        try {
            const response = await axios.get(`${API_BASE_URL}/api/stats`, {
                headers: {
                    Authorization: `Bearer ${token}`,
                },
            });
            return response.data;
        } catch (error) {
            console.error('Error fetching stats:', error);
            return null;
        }
    },

    getRecentReadings: async () => {
        try {
            const token = localStorage.getItem('token');
            if (!token) {
                Navigate('/login');
                return;
            }
            const response = await axios.get(`${API_BASE_URL}/api/readings/recent`, {
                headers: {
                    Authorization: `Bearer ${token}`,

                },
            });
            return response.data;
        } catch (error) {
            console.error('Error fetching recent readings:', error);
            return [];
        }
    }
}; 