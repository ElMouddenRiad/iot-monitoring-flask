import axios from 'axios';
// import { Navigate } from 'react-router-dom';


const API_BASE_URL = 'http://localhost:5000';
// const token = localStorage.getItem('token');

export const deviceService = {
    getDevices: async () => {
        try {
            const response = await axios.get(`${API_BASE_URL}/api/devices`);
            return response.data;

        } catch (error) {
            console.error('Error fetching devices:', error);
            return {};
        }
    },

    addDevice: async (deviceData) => {
        const response = await axios.post(`${API_BASE_URL}/api/devices`, deviceData);


        return response.data;
    },


    updateDevice: async (mac, deviceData) => {
        const response = await axios.put(`${API_BASE_URL}/api/devices/${mac}`, deviceData);
        return response.data;
    },




    deleteDevice: async (mac) => {
        const response = await axios.delete(`${API_BASE_URL}/api/devices/${mac}`);
        return response.data;
    },



    getStats: async () => {
        try {
            const response = await axios.get(`${API_BASE_URL}/api/stats`);
            return response.data;

        } catch (error) {
            console.error('Error fetching stats:', error);
            return null;
        }
    },

    getRecentReadings: async () => {
        try {
            const response = await axios.get(`${API_BASE_URL}/api/readings/recent`);
            return response.data;

        } catch (error) {

            console.error('Error fetching recent readings:', error);
            return [];
        }
    }
}; 