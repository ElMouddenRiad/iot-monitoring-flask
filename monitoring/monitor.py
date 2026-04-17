import os
import logging
from pymongo import MongoClient
import pika
import json
from extensions import socketio  # Import from extensions instead


logger = logging.getLogger(__name__)

# MongoDB Configuration
mongo_client = MongoClient(os.getenv('MONGODB_URI', 'mongodb://localhost:27017/iot_platform'))
mongo_db = mongo_client[os.getenv('MONGODB_DATABASE', 'iot_platform')]
readings_collection = mongo_db['temperature_readings']

def handle_device_event(ch, method, properties, body):
    try:
        event = json.loads(body)
        socketio.emit('device_event', event)
    except json.JSONDecodeError:
        logger.warning("Received invalid RabbitMQ event payload")

def start_rabbitmq_consumer():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=os.getenv('RABBITMQ_HOST', 'localhost'),
            port=int(os.getenv('RABBITMQ_PORT', '5672')),
            credentials=pika.PlainCredentials(
                os.getenv('RABBITMQ_USERNAME', 'guest'),
                os.getenv('RABBITMQ_PASSWORD', 'guest'),
            ),
        )
    )
    channel = connection.channel()
    queue_name = os.getenv('RABBITMQ_QUEUE', 'device_events')
    channel.queue_declare(queue=queue_name, durable=False)
    channel.basic_consume(
        queue=queue_name,
        on_message_callback=handle_device_event,
        auto_ack=True,
    )
    logger.info("RabbitMQ consumer started for queue %s", queue_name)
    channel.start_consuming()

@socketio.on('connect')
def handle_connect():
    logger.info('Client connected to Socket.IO')
    socketio.emit('connection_response', {'status': 'connected'})

@socketio.on('disconnect')
def handle_disconnect():
    logger.info('Client disconnected from Socket.IO')

def store_temperature_reading(data):
    try:
        # Format the data
        formatted_data = {
            'device_id': data['device_id'],
            'temperature': data['temperature'],
            'timestamp': data['timestamp'],
            'location': data['location']
        }
        
        # Store in MongoDB
        readings_collection.insert_one(formatted_data)
        
        # Emit the data to all connected clients
        logger.debug("Emitting temperature reading: %s", formatted_data)
        socketio.emit('new_reading', formatted_data)
        
        return True
    except Exception as e:
        logger.exception("Error in store_temperature_reading: %s", e)
        logger.debug("Received data: %s", data)
        return False

