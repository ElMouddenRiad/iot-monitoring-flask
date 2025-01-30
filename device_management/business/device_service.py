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
            # Use 127.0.0.1 since it works
            self.parameters = pika.URLParameters('amqp://guest:guest@127.0.0.1:5672/%2F')
            
            print("Attempting to connect to RabbitMQ...")
            self.connection = pika.BlockingConnection(self.parameters)
            self.channel = self.connection.channel()
            
            # Declare exchange
            self.channel.exchange_declare(
                exchange='device_events',
                exchange_type='topic',
                durable=True
            )
            print("Successfully connected to RabbitMQ")
            
        except Exception as e:
            print(f"Error initializing RabbitMQ connection: {type(e).__name__} - {e}")

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
            # Create new connection for each publish
            connection = pika.BlockingConnection(self.parameters)
            channel = connection.channel()
            
            # Ensure exchange exists
            channel.exchange_declare(
                exchange='device_events',
                exchange_type='topic',
                durable=True
            )

            # Create queue and bind it
            queue_name = f"device.{device['mac']}.temperature"
            channel.queue_declare(queue=queue_name, durable=True)
            channel.queue_bind(
                exchange='device_events',
                queue=queue_name,
                routing_key=queue_name
            )

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
                routing_key=queue_name,
                body=json.dumps(payload),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # make message persistent
                    content_type='application/json'
                )
            )
            
            print(f"Published temperature {temperature} for device {device['mac']}")
            connection.close()
            
        except Exception as e:
            print(f"Error publishing temperature: {e}")

    def simulate_device_readings(self, device_data):
        try:
            # Set default values and validate data
            base_temp = 20.0
            
            # Get frequency from device data
            try:
                frequency = int(device_data.get('frequency', 30))
            except (TypeError, ValueError):
                frequency = 30
                print(f"Invalid frequency for device {device_data.get('mac')}, using default {frequency}")

            device_id = device_data.get('mac', 'unknown')
            print(f"Starting simulation for device {device_id} with frequency {frequency}s")

            # Create a dedicated connection for this device
            device_connection = pika.BlockingConnection(self.parameters)
            device_channel = device_connection.channel()
            device_channel.exchange_declare(
                exchange='device_events',
                exchange_type='topic',
                durable=True
            )

            while True:
                try:
                    # Generate reading
                    temperature = round(base_temp + random.uniform(-2, 2), 2)
                    reading = {
                        'device_id': device_id,
                        'temperature': temperature,
                        'timestamp': datetime.now().isoformat()
                    }

                    # Add location if available
                    if device_data.get('location'):
                        try:
                            if isinstance(device_data['location'], str):
                                location = json.loads(device_data['location'])
                            else:
                                location = device_data['location']
                            reading['location'] = {
                                'latitude': float(location['latitude']),
                                'longitude': float(location['longitude'])
                            }
                        except Exception as e:
                            print(f"Error parsing location for device {device_id}: {e}")
                            # Use latitude/longitude directly if available
                            if device_data.get('latitude') and device_data.get('longitude'):
                                reading['location'] = {
                                    'latitude': float(device_data['latitude']),
                                    'longitude': float(device_data['longitude'])
                                }

                    # Publish reading
                    device_channel.basic_publish(
                        exchange='device_events',
                        routing_key=f"device.{device_id}.temperature",
                        body=json.dumps(reading),
                        properties=pika.BasicProperties(
                            delivery_mode=2,
                            content_type='application/json'
                        )
                    )
                    
                    print(f"Published reading for device {device_id}: {temperature}°C")
                    time.sleep(frequency)
                    
                except pika.exceptions.AMQPConnectionError:
                    print(f"Connection lost for device {device_id}. Reconnecting...")
                    device_connection = pika.BlockingConnection(self.parameters)
                    device_channel = device_connection.channel()
                    time.sleep(5)
                except Exception as e:
                    print(f"Error in simulation for device {device_id}: {type(e).__name__} - {e}")
                    time.sleep(5)
                
        except Exception as e:
            print(f"Fatal error in device simulation: {type(e).__name__} - {e}")
        finally:
            if 'device_connection' in locals() and device_connection.is_open:
                device_connection.close()

    def start_device_simulation(self, devices):
        """Start simulating multiple devices"""
        for device in devices:
            if device.get('status') == 'active':
                # Start each device simulation in its own thread
                thread = Thread(
                    target=self.simulate_device_readings,
                    args=(device,),
                    daemon=True
                )
                thread.start()
                print(f"Started simulation thread for device {device.get('mac')}")

    def __del__(self):
        try:
            if hasattr(self, 'connection') and self.connection and self.connection.is_open:
                self.connection.close()
                print("RabbitMQ connection closed")
        except Exception as e:
            print(f"Error closing connection: {e}")

# Update device_manage.py to use this service
def start_device_simulations(devices):
    publisher = DeviceEventPublisher()
    simulation_thread = Thread(
        target=publisher.start_device_simulation,
        args=(devices,),
        daemon=True
    )
    simulation_thread.start()

# Test connection
try:
    params = pika.URLParameters('amqp://guest:guest@127.0.0.1:5672/%2F')
    connection = pika.BlockingConnection(params)
    print("Successfully connected to RabbitMQ")
    connection.close()
except Exception as e:
    print(f"Failed to connect: {e}")