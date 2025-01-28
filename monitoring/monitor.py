from flask import Flask, jsonify
from pymongo import MongoClient
import pika
import json
import threading
from extensions import socketio  # Import from extensions instead

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
    print('Client connected')

def store_temperature_reading(data):
    result = readings_collection.insert_one(data)
    emit_data = data.copy()
    emit_data['_id'] = str(result.inserted_id)
    socketio.emit('new_temperature', emit_data)

