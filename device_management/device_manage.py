from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, jwt_required
from flask import Blueprint, jsonify, request
from .dal.dal import DeviceDAL
import pika
import json
from datetime import datetime

device_bp = Blueprint('device', __name__)
RABBITMQ_HOST = 'localhost'

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
    search_term = request.args.get('search')
    devices = DeviceDAL.get_devices(search_term)
    return jsonify(devices)

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