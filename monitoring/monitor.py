from flask import Flask, jsonify
from flask_socketio import SocketIO
from pymongo import MongoClient
import pika
import json
import threading

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# MongoDB connection
mongo_client = MongoClient('mongodb+srv://bakr:bakr1234@iotproject.dl598.mongodb.net/?retryWrites=true&w=majority&appName=IotProject')
db = mongo_client['iot_platform']
events_collection = db['device_events']

def consume_rabbitmq_messages():
    credentials = pika.PlainCredentials('bakr', 'bakr1234')
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='rabbitmq', credentials=credentials))
    channel = connection.channel()
    
    channel.queue_declare(queue='device_events')
    
    def callback(ch, method, properties, body):
        event_data = json.loads(body)
        
        # Store event in MongoDB
        events_collection.insert_one(event_data)
        
        # Emit event to connected clients
        socketio.emit('device_event', event_data)
    
    channel.basic_consume(
        queue='device_events',
        on_message_callback=callback,
        auto_ack=True
    )
    
    channel.start_consuming()

@app.route('/events/<device_id>', methods=['GET'])
def get_device_events(device_id):
    events = list(events_collection.find({'device_id': device_id}, {'_id': 0}))
    return jsonify(events)

@socketio.on('connect')
def handle_connect():
    print('Client connected')

def store_temperature_reading(data):
    events_collection.insert_one(data)
    socketio.emit('new_reading', data)

