import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';

const TemperatureChart = ({ data }) => {
    const handleDeviceSelect = (deviceId) => {
        setSelectedDevice(deviceId);
        setTemperatureData([]); // Reset temperature data when a new device is selected
    };
    return (
        <LineChart width={600} height={300} data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="timestamp" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="temperature" stroke="#8884d8" />
        </LineChart>
    );
};

export default TemperatureChart;