from datetime import datetime
import pika
import json
import logging
import random
import time
import os
from threading import Thread
from concurrent.futures import ThreadPoolExecutor


logger = logging.getLogger(__name__)


def _build_rabbitmq_parameters():
    rabbitmq_url = os.getenv("RABBITMQ_URL")
    if rabbitmq_url:
        return pika.URLParameters(rabbitmq_url)

    host = os.getenv("RABBITMQ_HOST", "localhost")
    port = os.getenv("RABBITMQ_PORT", "5672")
    username = os.getenv("RABBITMQ_USERNAME", "guest")
    password = os.getenv("RABBITMQ_PASSWORD", "guest")
    return pika.URLParameters(f"amqp://{username}:{password}@{host}:{port}/%2F")

class DeviceEventPublisher:
    def __init__(self):
        try:
            self.parameters = _build_rabbitmq_parameters()

            logger.info("Attempting to connect to RabbitMQ")
            self.connection = pika.BlockingConnection(self.parameters)
            self.channel = self.connection.channel()
            
            # Declare exchange
            self.channel.exchange_declare(
                exchange='device_events',
                exchange_type='topic',
                durable=True
            )
            logger.info("Successfully connected to RabbitMQ")
            
        except Exception as e:
            logger.exception("Error initializing RabbitMQ connection: %s", e)

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
            logger.error("Failed to connect to RabbitMQ: %s", e)
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
            
            logger.info("Published temperature %s for device %s", temperature, device['mac'])
            connection.close()
            
        except Exception as e:
            logger.exception("Error publishing temperature: %s", e)

    def simulate_device_readings(self, device_data):
        try:
            # Set default values and validate data
            base_temp = 20.0
            
            # Get frequency from device data
            try:
                frequency = int(device_data.get('frequency', 30))
            except (TypeError, ValueError):
                frequency = 30
                logger.warning(
                    "Invalid frequency for device %s, using default %s",
                    device_data.get('mac'),
                    frequency,
                )

            device_id = device_data.get('mac', 'unknown')
            logger.info("Starting simulation for device %s with frequency %ss", device_id, frequency)

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
                            logger.warning("Error parsing location for device %s: %s", device_id, e)
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
                    
                    logger.debug("Published reading for device %s: %s°C", device_id, temperature)
                    time.sleep(frequency)
                    
                except pika.exceptions.AMQPConnectionError:
                    logger.warning("Connection lost for device %s. Reconnecting...", device_id)
                    device_connection = pika.BlockingConnection(self.parameters)
                    device_channel = device_connection.channel()
                    time.sleep(5)
                except Exception as e:
                    logger.exception("Error in simulation for device %s: %s", device_id, e)
                    time.sleep(5)
                
        except Exception as e:
            logger.exception("Fatal error in device simulation: %s", e)
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
                logger.info("Started simulation thread for device %s", device.get('mac'))

    def __del__(self):
        try:
            if hasattr(self, 'connection') and self.connection and self.connection.is_open:
                self.connection.close()
                logger.info("RabbitMQ connection closed")
        except Exception as e:
            logger.exception("Error closing connection: %s", e)

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
    params = _build_rabbitmq_parameters()
    connection = pika.BlockingConnection(params)
    logger.info("Successfully connected to RabbitMQ")
    connection.close()
except Exception as e:
    logger.exception("Failed to connect: %s", e)