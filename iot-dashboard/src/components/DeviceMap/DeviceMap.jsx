import React, { useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import './DeviceMap.css';

// Fix for default marker icon
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
    iconUrl: require('leaflet/dist/images/marker-icon.png'),
    shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});

// Component to update map bounds
function MapBounds({ devices }) {
    const map = useMap();
    
    useEffect(() => {
        if (Object.keys(devices).length > 0) {
            const devicesWithLocation = Object.values(devices).filter(
                device => device.latitude && device.longitude
            );
            
            if (devicesWithLocation.length > 0) {
                const bounds = L.latLngBounds(
                    devicesWithLocation.map(device => [
                        device.latitude,
                        device.longitude
                    ])
                );
                map.fitBounds(bounds, { padding: [50, 50] });
            }
        }
    }, [devices, map]);

    return null;
}

function DeviceMap({ devices, selectedDevice, onLocationSelect }) {
    const mapRef = useRef(null);
    const defaultCenter = [0, 0];
    const defaultZoom = 2;

    // Handle map click for adding new device location
    const handleMapClick = (e) => {
        if (onLocationSelect) {
            onLocationSelect({
                latitude: e.latlng.lat,
                longitude: e.latlng.lng
            });
        }
    };

    return (
        <MapContainer 
            center={defaultCenter} 
            zoom={defaultZoom} 
            style={{ height: '400px', width: '100%' }}
            ref={mapRef}
            onClick={handleMapClick}
        >
            <TileLayer
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            />
            
            {Object.entries(devices).map(([mac, device]) => (
                device.latitude && device.longitude ? (
                    <Marker
                        key={mac}
                        position={[device.latitude, device.longitude]}
                        eventHandlers={{
                            click: () => {
                                if (mapRef.current) {
                                    mapRef.current.setView(
                                        [device.latitude, device.longitude],
                                        13
                                    );
                                }
                            }
                        }}
                    >
                        <Popup>
                            <div className="device-popup">
                                <h3>{device.name}</h3>
                                <p>MAC: {mac}</p>
                                <p>Status: {device.status}</p>
                                {device.temperature && (
                                    <p>Temperature: {device.temperature}°C</p>
                                )}
                                <p>Location: {device.latitude.toFixed(6)}, {device.longitude.toFixed(6)}</p>
                                {device.location && <p>Address: {device.location}</p>}
                            </div>
                        </Popup>
                    </Marker>
                ) : null
            ))}
            
            <MapBounds devices={devices} />
        </MapContainer>
    );
}

export default DeviceMap; 