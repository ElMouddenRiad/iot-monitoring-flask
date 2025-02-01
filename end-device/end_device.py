import psutil
import requests
import socket
import platform
import uuid
import logging
from datetime import datetime
import time
import json

# Configuration
CONFIG = {
    'API_URL': 'http://localhost:5000/api',
    'COLLECTION_INTERVAL': 30,  # seconds
    'MAX_RETRIES': 3,
    'RETRY_DELAY': 5
}

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class EndDeviceMonitor:
    def __init__(self):
        self.device_info = self._get_device_info()
        self.registered = False

    def _get_device_info(self):
        """Collect system information for device registration"""
        try:
            hostname = socket.gethostname()
            ip_address = socket.gethostbyname(hostname)
            mac_address = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff)
                                  for elements in range(0,8*6,8)][::-1])
            
            return {
                'mac': mac_address,
                'name': hostname,
                'ip_address': ip_address,
                'os': platform.system(),
                'os_version': platform.version(),
                'processor': platform.processor(),
                'machine': platform.machine(),
                'status': 'active',
                'device_type': 'computer'  # To distinguish from IoT devices
            }
        except Exception as e:
            logging.error(f"Error collecting device info: {e}")
            return None

    def register_device(self):
        """Register end device with the server"""
        if not self.device_info:
            logging.error("No device info available for registration")
            return False

        for attempt in range(CONFIG['MAX_RETRIES']):
            try:
                response = requests.post(
                    f"{CONFIG['API_URL']}/end-devices/register",
                    json=self.device_info,
                    headers={'Content-Type': 'application/json'}
                )
                
                if response.status_code in [200, 201]:
                    logging.info("End device registered successfully")
                    self.registered = True
                    return True
                elif response.status_code == 409:
                    logging.info("End device already registered")
                    self.registered = True
                    return True
                else:
                    logging.error(f"Registration failed with status {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                logging.error(f"Registration attempt {attempt + 1} failed: {e}")
                
            time.sleep(CONFIG['RETRY_DELAY'])
            
        return False

    def collect_system_metrics(self):
        """Collect system metrics using psutil"""
        try:
            # CPU Information
            cpu_freq = psutil.cpu_freq()
            if cpu_freq:
                cpu_freq_dict = {
                    'current': cpu_freq.current,
                    'min': cpu_freq.min,
                    'max': cpu_freq.max
                }
            else:
                cpu_freq_dict = None

            # Memory Information
            memory = psutil.virtual_memory()
            
            # Disk Information
            disk = psutil.disk_usage('/')
            
            # Network Information
            network_interfaces = {}
            for interface, addresses in psutil.net_if_addrs().items():
                network_interfaces[interface] = [addr.address for addr in addresses]

            metrics = {
                'timestamp': datetime.now().isoformat(),
                'device_id': self.device_info['mac'],
                'system_metrics': {
                    'cpu': {
                        'percent': psutil.cpu_percent(interval=1),
                        'cores': psutil.cpu_count(),
                        'frequency': cpu_freq_dict,
                        'load_avg': psutil.getloadavg()
                    },
                    'memory': {
                        'total': memory.total,
                        'available': memory.available,
                        'percent': memory.percent,
                        'used': memory.used
                    },
                    'disk': {
                        'total': disk.total,
                        'used': disk.used,
                        'free': disk.free,
                        'percent': disk.percent
                    },
                    'network': {
                        'interfaces': network_interfaces,
                        'connections': len(psutil.net_connections())
                    }
                }
            }

            # Add battery information if available
            battery = psutil.sensors_battery()
            if battery:
                metrics['system_metrics']['battery'] = {
                    'percent': battery.percent,
                    'power_plugged': battery.power_plugged,
                    'time_left': battery.secsleft if battery.secsleft != -1 else None
                }

            # Add temperature information if available
            if hasattr(psutil, 'sensors_temperatures'):
                temps = psutil.sensors_temperatures()
                if temps:
                    metrics['system_metrics']['temperature'] = {
                        sensor: [
                            {
                                'label': t.label,
                                'current': t.current,
                                'high': t.high,
                                'critical': t.critical
                            } for t in temps[sensor]
                        ] for sensor in temps
                    }

            return metrics
            
        except Exception as e:
            logging.error(f"Error collecting system metrics: {e}")
            return None

    def send_metrics(self, metrics):
        """Send collected metrics to the server"""
        try:
            response = requests.post(
                f"{CONFIG['API_URL']}/end-devices/metrics",
                json=metrics,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                logging.debug("Metrics sent successfully")
                return True
            else:
                logging.error(f"Failed to send metrics. Status: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            logging.error(f"Error sending metrics: {e}")
            return False

    def run(self):
        """Main loop for monitoring and sending metrics"""
        if not self.register_device():
            logging.error("Failed to register end device. Exiting.")
            return

        logging.info("Starting system monitoring...")
        
        while True:
            try:
                metrics = self.collect_system_metrics()
                if metrics:
                    self.send_metrics(metrics)
                time.sleep(CONFIG['COLLECTION_INTERVAL'])
                
            except KeyboardInterrupt:
                logging.info("Monitoring stopped by user")
                break
            except Exception as e:
                logging.error(f"Error in monitoring loop: {e}")
                time.sleep(CONFIG['RETRY_DELAY'])

if __name__ == "__main__":
    monitor = EndDeviceMonitor()
    monitor.run()