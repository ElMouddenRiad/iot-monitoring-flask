from flask import Flask, jsonify
from pymongo import MongoClient
import pika
import json
import threading
from extensions import socketio  # Import from extensions instead
from datetime import datetime

# MongoDB Configuration
mongo_client = MongoClient('mongodb+srv://bakr:bakr1234@iotproject.dl598.mongodb.net/?retryWrites=true&w=majority&appName=IotProject')
db = mongo_client['iot_platform']
readings_collection = db['temperature_readings']

def handle_device_event(ch, method, properties, body):
    event = json.loads(body)
    socketio.emit('device_event', event)

def start_rabbitmq_consumer():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='device_events')
    channel.basic_consume(
        queue='device_events',
        on_message_callback=handle_device_event,
        auto_ack=True
    )
    channel.start_consuming()

@socketio.on('connect')
def handle_connect():
    print('Client connected to Socket.IO')
    socketio.emit('connection_response', {'status': 'connected'})

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected from Socket.IO')

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
        print(f"Emitting temperature reading: {formatted_data}")
        socketio.emit('new_reading', formatted_data)  # Removed broadcast parameter
        
        return True
    except Exception as e:
        print(f"Error in store_temperature_reading: {e}")
        print(f"Received data: {data}")
        return False

