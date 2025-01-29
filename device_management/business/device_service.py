from datetime import datetime
import pika
import json
import logging
import random
import time
from threading import Thread
from concurrent.futures import ThreadPoolExecutor

class DeviceEventPublisher:
    def __init__(self):
        try:
            # Try to connect to RabbitMQ with retries
            max_retries = 3
            for i in range(max_retries):
                try:
                    self.credentials = pika.PlainCredentials('guest', 'guest')  # Default credentials
                    self.parameters = pika.ConnectionParameters(
                        host='localhost',
                        port=5672,
                        virtual_host='/',
                        credentials=self.credentials,
                        connection_attempts=3,
                        retry_delay=2
                    )
                    # Test connection
                    test_conn = pika.BlockingConnection(self.parameters)
                    test_conn.close()
                    break
                except Exception as e:
                    if i == max_retries - 1:
                        logging.error(f"Failed to initialize RabbitMQ connection after {max_retries} attempts: {e}")
                    time.sleep(2)
        except Exception as e:
            logging.error(f"Error initializing DeviceEventPublisher: {e}")

    def connect(self):
        try:
            connection = pika.BlockingConnection(self.parameters)
            channel = connection.channel()
            channel.exchange_declare(
                exchange='device_events',
                exchange_type='topic',
                durable=True
            )
            return connection, channel
        except Exception as e:
            logging.error(f"Failed to connect to RabbitMQ: {e}")
            return None, None

    def publish_temperature(self, device, temperature):
        try:
            connection, channel = self.connect()
            if not channel:
                return

            payload = {
                'device_id': device['mac'],
                'temperature': temperature,
                'location': {
                    'latitude': device.get('latitude'),
                    'longitude': device.get('longitude')
                },
                'timestamp': datetime.now().isoformat()
            }

            channel.basic_publish(
                exchange='device_events',
                routing_key=f"device.{device['mac']}.temperature",
                body=json.dumps(payload),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # make message persistent
                    content_type='application/json'
                )
            )
            
            logging.info(f"Published temperature {temperature} for device {device['mac']}")
            connection.close()
            
        except Exception as e:
            logging.error(f"Error publishing temperature: {e}")

    def simulate_device_readings(self, device_data):
        try:
            base_temp = 20.0  # Base temperature
            while True:
                try:
                    # Generate random fluctuation between -2 and +2 degrees
                    fluctuation = random.uniform(-2, 2)
                    temperature = base_temp + float(fluctuation)
                    
                    # Create reading payload
                    reading = {
                        'device_id': device_data['mac'],
                        'temperature': round(temperature, 2),
                        'timestamp': datetime.now().isoformat()
                    }

                    # Add location if available
                    if device_data.get('latitude') is not None and device_data.get('longitude') is not None:
                        reading['location'] = {
                            'latitude': float(device_data['latitude']),
                            'longitude': float(device_data['longitude'])
                        }
                    
                    # Publish reading
                    self.publish_temperature(device_data, reading['temperature'])
                    
                except Exception as e:
                    logging.error(f"Error in reading simulation: {e}")
                    
                # Sleep for the device's frequency or default to 30 seconds
                time.sleep(float(device_data.get('frequency', 30)))
                
        except Exception as e:
            logging.error(f"Error in device simulation loop: {e}")

    def start_device_simulation(self, devices):
        """Start simulating multiple devices"""
        with ThreadPoolExecutor(max_workers=len(devices)) as executor:
            for device in devices:
                if device['status'] == 'active':
                    executor.submit(self.simulate_device_readings, device)
                    logging.info(f"Started simulation for device {device['mac']}")

# Update device_manage.py to use this service
def start_device_simulations(devices):
    publisher = DeviceEventPublisher()
    simulation_thread = Thread(
        target=publisher.start_device_simulation,
        args=(devices,),
        daemon=True
    )
    simulation_thread.start()