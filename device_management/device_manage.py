from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, jwt_required
from flask import Blueprint, jsonify, request
from .dal.dal import DeviceDAL
from .models import Device  # Import Device from models
import pika
import json
from datetime import datetime
from extensions import db  # Move db to extensions.py
from pymongo import MongoClient

device_bp = Blueprint('device', __name__)
RABBITMQ_HOST = 'localhost'
mongo_client = MongoClient('mongodb+srv://bakr:bakr1234@iotproject.dl598.mongodb.net/?retryWrites=true&w=majority&appName=IotProject')
db = mongo_client['iot_platform']
readings_collection = db['temperature_readings']

def publish_device_event(event_type, device_data):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
    channel = connection.channel()
    channel.queue_declare(queue='device_events')
    
    message = {
        'event_type': event_type,
        'device_data': device_data
    }
    
    channel.basic_publish(
        exchange='',
        routing_key='device_events',
        body=json.dumps(message)
    )
    connection.close()

@device_bp.route('/api/devices', methods=['GET'])
def get_devices():
    try:
        devices = Device.query.all()
        return jsonify([{
            'id': device.id,
            'name': device.name,
            'mac': device.mac,
            'location': json.loads(device.location) if device.location else None,
            'status': device.status
        } for device in devices])
    except Exception as e:
        print(f"Error getting devices: {e}")
        return jsonify({'error': str(e)}), 500

@device_bp.route('/api/devices', methods=['POST'])
def add_device():
    device_data = request.get_json()
    
    # Validate required fields
    required_fields = ['mac', 'name', 'location']
    if not all(field in device_data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    try:
        device = DeviceDAL.add_device(device_data)
        
        # Prepare response data
        response_data = {
            'mac': device.mac,
            'name': device.name,
            'location': {
                'latitude': device.latitude,
                'longitude': device.longitude
            },
            'status': device.status
        }
        
        # Publish event to RabbitMQ
        publish_device_event('device_added', response_data)
        
        return jsonify(response_data), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@device_bp.route('/api/devices/<mac>', methods=['PUT'])
def update_device(mac):
    device_data = request.get_json()
    device = DeviceDAL.update_device(mac, device_data)
    
    if device:
        response_data = {
            'mac': device.mac,
            'name': device.name,
            'location': {
                'latitude': device.latitude,
                'longitude': device.longitude
            },
            'status': device.status
        }
        publish_device_event('device_updated', response_data)
        return jsonify(response_data)
    
    return jsonify({'error': 'Device not found'}), 404

@device_bp.route('/api/devices/<mac>', methods=['DELETE'])
def delete_device(mac):
    device = DeviceDAL.delete_device(mac)
    if device:
        publish_device_event('device_deleted', {'mac': mac})
        return jsonify({'message': 'Device deleted successfully'})
    return jsonify({'error': 'Device not found'}), 404

@device_bp.route('/api/stats', methods=['GET'])
def get_stats():
    try:
        # Get device stats
        devices = Device.query.all()
        total_devices = len(devices)
        active_devices = len([d for d in devices if d.status == 'active'])
        
        # Get temperature stats from MongoDB
        pipeline = [
            {
                '$group': {
                    '_id': None,
                    'average_temp': {'$avg': '$temperature'},
                    'max_temp': {'$max': '$temperature'},
                    'min_temp': {'$min': '$temperature'},
                    'num_readings': {'$sum': 1},
                    'last_updated': {'$max': '$timestamp'}
                }
            }
        ]
        
        print("Fetching temperature readings from MongoDB...")
        readings = list(readings_collection.find().sort('timestamp', -1).limit(1))
        print(f"Recent readings: {readings}")
        
        if readings:
            # Get all temperature readings for statistics
            all_readings = list(readings_collection.find({}, {'temperature': 1, '_id': 0}))
            temperatures = [r['temperature'] for r in all_readings if 'temperature' in r]
            
            stats = {
                'total_devices': total_devices,
                'active_devices': active_devices,
                'inactive_devices': total_devices - active_devices,
                'average_temp': sum(temperatures) / len(temperatures) if temperatures else 0.0,
                'max_temp': max(temperatures) if temperatures else 0.0,
                'min_temp': min(temperatures) if temperatures else 0.0,
                'num_readings': len(temperatures),
                'last_updated': readings[0].get('timestamp', datetime.now().isoformat())
            }
        else:
            stats = {
                'total_devices': total_devices,
                'active_devices': active_devices,
                'inactive_devices': total_devices - active_devices,
                'average_temp': 0.0,
                'max_temp': 0.0,
                'min_temp': 0.0,
                'num_readings': 0,
                'last_updated': datetime.now().isoformat()
            }
        
        print(f"Returning stats: {stats}")
        return jsonify(stats)
        
    except Exception as e:
        print(f"Error getting stats:", str(e))
        return jsonify({
            'total_devices': 0,
            'active_devices': 0,
            'inactive_devices': 0,
            'average_temp': 0.0,
            'max_temp': 0.0,
            'min_temp': 0.0,
            'num_readings': 0,
            'last_updated': datetime.now().isoformat()
        }), 500

@device_bp.route('/api/readings/recent', methods=['GET'])
def get_recent_readings():
    try:
        # Get last 50 readings from MongoDB
        readings = list(readings_collection.find(
            {},
            {'_id': 0}
        ).sort('timestamp', -1).limit(50))
        
        return jsonify(readings)
    except Exception as e:
        print(f"Error getting recent readings: {e}")
        return jsonify({'error': str(e)}), 500