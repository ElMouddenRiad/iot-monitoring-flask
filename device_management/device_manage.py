import time
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
import socketio
import logging
from sqlalchemy import create_engine, Column, String, DateTime, Float, Integer, Text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from .business.device_service import start_device_simulations
import os
from eventlet.db_pool import ConnectionPool
from eventlet import spawn_n

device_bp = Blueprint('device_bp', __name__)
RABBITMQ_HOST = 'localhost'
# MongoDB configuration
mongo_client = MongoClient('mongodb+srv://bakr:bakr1234@iotproject.dl598.mongodb.net/?retryWrites=true&w=majority&appName=IotProject')
db = mongo_client['iot_platform']
readings_collection = db['temperature_readings']

# Database configuration
DATABASE_URL = 'postgresql://admin:admin123@localhost:5432/iot_platform'
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600
)
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False
)
Base = declarative_base()

# Device Model for PostgreSQL
class Device(Base):
    __tablename__ = 'devices'

    mac = Column(String(17), primary_key=True)
    name = Column(String(100), nullable=False)
    location = Column(String(200))
    latitude = Column(Float)
    longitude = Column(Float)
    status = Column(String(20), default='inactive')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    frequency = Column(Integer, default=30)  # Add frequency column

    def to_dict(self):
        return {
            'mac': self.mac,
            'name': self.name,
            'location': self.location,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'frequency': self.frequency
        }

# Drop existing table if it exists and create new one
# Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

# RabbitMQ connection (using docker-compose service name)
def get_rabbitmq_connection():
    try:
        # Use 'rabbitmq' if running in Docker, otherwise 'localhost'
        host = 'rabbitmq' if os.getenv('DOCKER_ENV') else 'localhost'
        
        credentials = pika.PlainCredentials('guest', 'guest')
        parameters = pika.ConnectionParameters(
            host=host,
            port=5672,
            credentials=credentials
        )
        connection = pika.BlockingConnection(parameters)
        return connection
    except Exception as e:
        print(f"Failed to connect to RabbitMQ: {e}")
        return None

def test_rabbitmq_connection():
    connection_urls = [
        'amqp://guest:guest@127.0.0.1:5672/%2F',
        'amqp://guest:guest@0.0.0.0:5672/%2F',
        'amqp://guest:guest@172.17.0.2:5672/%2F'
    ]
    
    for url in connection_urls:
        try:
            print(f"Testing connection to {url}")
            params = pika.URLParameters(url)
            connection = pika.BlockingConnection(params)
            print(f"Successfully connected to RabbitMQ using {url}")
            connection.close()
            return True
        except Exception as e:
            print(f"Failed to connect using {url}: {e}")
            continue
    
    print("Failed to connect to RabbitMQ using any available URLs")
    return False

def publish_device_event(event_type, device_data):
    try:
        connection = get_rabbitmq_connection()
        if connection:
            channel = connection.channel()
            channel.exchange_declare(
                exchange='device_events',
                exchange_type='topic',
                durable=True
            )
            
            message = {
                'event_type': event_type,
                'timestamp': datetime.utcnow().isoformat(),
                'device': device_data
            }
            
            channel.basic_publish(
                exchange='device_events',
                routing_key=f'device.{event_type}',
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Make message persistent
                    content_type='application/json'
                )
            )
            connection.close()
            logging.info(f"Published {event_type} event for device {device_data.get('mac')}")
    except Exception as e:
        logging.error(f"Failed to publish device event: {e}")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        print(f"Received `{payload}` from `{msg.topic}` topic")

        # Format the temperature reading
        reading = {
            'device_id': payload.get('device_id', 'unknown'),
            'temperature': payload.get('temperature'),
            'timestamp': datetime.now().isoformat()
        }

        # Store in MongoDB
        readings_collection.insert_one(reading)

        # Emit to connected clients via Socket.IO
        socketio.emit('new_reading', reading)

        # Update statistics
        update_stats()

    except Exception as e:
        print(f"Error processing message: {e}")

@device_bp.route('/api/devices', methods=['GET'])
def get_devices():
    try:
        # Use a new session for each request
        with SessionLocal() as db:
            devices = db.query(Device).all()
            return jsonify([device.to_dict() for device in devices])
    except Exception as e:
        logging.error(f"Error fetching devices: {e}")
        return jsonify({'error': str(e)}), 500

@device_bp.route('/api/devices', methods=['POST'])
def create_device():
    db = SessionLocal()
    try:
        data = request.json
        
        if not all(k in data for k in ['mac', 'name']):
            return jsonify({'error': 'Missing required fields'}), 400
    
        new_device = Device(
            mac=data['mac'],
            name=data['name'],
            location=data.get('location'),
            latitude=data.get('latitude'),
            longitude=data.get('longitude'),
            status=data.get('status', 'inactive'),
            frequency=data.get('frequency', 30)  # Default to 30 seconds
        )
        
        db.add(new_device)
        db.commit()
        
        device_data = new_device.to_dict()
        
        # Publish device_created event to RabbitMQ
        publish_device_event('created', device_data)
        
        # Start simulation if device is active
        if device_data['status'] == 'active':
            start_device_simulations([device_data])
            
        return jsonify(device_data), 201
        
    except Exception as e:
        db.rollback()
        logging.error(f"Error creating device: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@device_bp.route('/api/devices/<mac>', methods=['PUT'])
def update_device(mac):
    db = SessionLocal()
    try:
        device = db.query(Device).get(mac)
        if not device:
            return jsonify({'error': 'Device not found'}), 404
            
        data = request.json
        
        device.name = data.get('name', device.name)
        device.location = data.get('location', device.location)
        device.latitude = data.get('latitude', device.latitude)
        device.longitude = data.get('longitude', device.longitude)
        device.status = data.get('status', device.status)
        device.frequency = data.get('frequency', device.frequency)
        device.updated_at = datetime.utcnow()
        
        db.commit()
        
        device_data = device.to_dict()
        
        # Publish device_updated event to RabbitMQ
        publish_device_event('updated', device_data)
        
        return jsonify(device_data)
        
    except Exception as e:
        db.rollback()
        logging.error(f"Error updating device: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@device_bp.route('/api/devices/<mac>', methods=['DELETE'])
def delete_device(mac):
    db = SessionLocal()
    try:
        device = db.query(Device).get(mac)
        if not device:
            return jsonify({'error': 'Device not found'}), 404
            
        device_data = device.to_dict()
        db.delete(device)
        db.commit()
        
        # Publish device_deleted event to RabbitMQ
        publish_device_event('deleted', device_data)
        
        return jsonify({'message': 'Device deleted successfully'})
        
    except Exception as e:
        db.rollback()
        logging.error(f"Error deleting device: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@device_bp.route('/api/stats', methods=['GET'])
def get_stats():
    db_session = SessionLocal()  # Create a new session for SQLAlchemy
    try:
        # Get device stats from PostgreSQL
        devices = db_session.query(Device).all()
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
        
        temp_stats = list(readings_collection.aggregate(pipeline))
        
        stats = {
            'total_devices': total_devices,
            'active_devices': active_devices,
            'inactive_devices': total_devices - active_devices,
            'average_temp': float(temp_stats[0]['average_temp']) if temp_stats else 0.0,
            'max_temp': float(temp_stats[0]['max_temp']) if temp_stats else 0.0,
            'min_temp': float(temp_stats[0]['min_temp']) if temp_stats else 0.0,
            'num_readings': temp_stats[0]['num_readings'] if temp_stats else 0,
            'last_updated': temp_stats[0]['last_updated'] if temp_stats else datetime.utcnow().isoformat()
        }
        
        return jsonify(stats)
        
    except Exception as e:
        logging.error(f"Error getting stats: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        db_session.close()  # Close SQLAlchemy session
    
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

def update_stats():
    try:
        # Use a new session
        with SessionLocal() as db:
            devices = db.query(Device).all()
            total_devices = len(devices)
            active_devices = len([d for d in devices if d.status == 'active'])
            
            # Get temperature stats from MongoDB
            all_readings = list(readings_collection.find({}, {'temperature': 1, '_id': 0}))
            temperatures = [r['temperature'] for r in all_readings if 'temperature' in r]
            
            if temperatures:
                stats = {
                    'total_devices': total_devices,
                    'active_devices': active_devices,
                    'inactive_devices': total_devices - active_devices,
                    'average_temp': sum(temperatures) / len(temperatures),
                    'max_temp': max(temperatures),
                    'min_temp': min(temperatures),
                    'num_readings': len(temperatures),
                    'last_updated': datetime.now().isoformat()
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
            
            # Emit updated stats via Socket.IO
            socketio.emit('stats_updated', stats)
            return stats
            
    except Exception as e:
        print(f"Error updating stats: {e}")
        return None

@device_bp.route('/api/devices/start-simulation', methods=['POST'])
def start_simulation():
    try:
        # Use a new session for each request
        with SessionLocal() as db:
            active_devices = db.query(Device).filter(Device.status == 'active').all()
            devices_data = [device.to_dict() for device in active_devices]
            
            if not devices_data:
                return jsonify({'message': 'No active devices to simulate'}), 200
                
            # Start simulation in a new greenlet
            spawn_n(start_device_simulations, devices_data)
            return jsonify({'message': f'Started simulation for {len(devices_data)} devices'})
            
    except Exception as e:
        logging.error(f"Error starting device simulation: {e}")
        return jsonify({'error': str(e)}), 500

# Add this model class for end devices
class EndDevice(Base):
    __tablename__ = 'end_devices'

    mac = Column(String(17), primary_key=True)
    name = Column(String(100), nullable=False)
    ip_address = Column(String(45))  # IPv4 or IPv6
    os = Column(String(50))
    os_version = Column(Text)
    processor = Column(String(100))
    machine = Column(String(50))
    status = Column(String(20), default='inactive')
    device_type = Column(String(20), default='computer')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_seen = Column(DateTime)

    def to_dict(self):
        return {
            'mac': self.mac,
            'name': self.name,
            'ip_address': self.ip_address,
            'os': self.os,
            'os_version': self.os_version,
            'processor': self.processor,
            'machine': self.machine,
            'status': self.status,
            'device_type': self.device_type,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None
        }

# Create the end devices table
Base.metadata.create_all(bind=engine)

# Add these new endpoints
@device_bp.route('/api/end-devices/register', methods=['POST'])
def register_end_device():
    db = SessionLocal()
    try:
        data = request.json
        
        # Check if device already exists
        existing_device = db.query(EndDevice).get(data['mac'])
        if existing_device:
            # Update existing device
            existing_device.name = data['name']
            existing_device.ip_address = data['ip_address']
            existing_device.os = data['os']
            existing_device.os_version = data['os_version']
            existing_device.processor = data['processor']
            existing_device.machine = data['machine']
            existing_device.status = 'active'
            existing_device.last_seen = datetime.utcnow()
            db.commit()
            return jsonify(existing_device.to_dict()), 200
            
        # Create new device
        new_device = EndDevice(
            mac=data['mac'],
            name=data['name'],
            ip_address=data['ip_address'],
            os=data['os'],
            os_version=data['os_version'],
            processor=data['processor'],
            machine=data['machine'],
            status='active',
            last_seen=datetime.utcnow()
        )
        
        db.add(new_device)
        db.commit()
        
        return jsonify(new_device.to_dict()), 201
        
    except Exception as e:
        db.rollback()
        logging.error(f"Error registering end device: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@device_bp.route('/api/end-devices', methods=['GET'])
def get_end_devices():
    db = SessionLocal()
    try:
        devices = db.query(EndDevice).all()
        return jsonify([device.to_dict() for device in devices])
    except Exception as e:
        logging.error(f"Error fetching end devices: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@device_bp.route('/api/end-devices/metrics', methods=['POST'])
def receive_end_device_metrics():
    db = SessionLocal()
    try:
        metrics = request.json
        device_id = metrics.get('device_id')
        
        # Update device status in PostgreSQL
        if device_id:
            device = db.query(EndDevice).get(device_id)
            if device:
                device.last_seen = datetime.utcnow()
                device.status = 'active'
                db.commit()
        
        # Store metrics in MongoDB
        metrics['timestamp'] = datetime.utcnow()
        readings_collection.insert_one(metrics)
        
        return jsonify({'status': 'success'}), 200
        
    except Exception as e:
        db.rollback()
        logging.error(f"Error processing end device metrics: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@device_bp.route('/api/end-devices/<mac>', methods=['DELETE'])
def delete_end_device(mac):
    db = SessionLocal()
    try:
        device = db.query(EndDevice).get(mac)
        if not device:
            return jsonify({'error': 'End device not found'}), 404
            
        db.delete(device)
        db.commit()
        
        return jsonify({'message': 'End device deleted successfully'})
        
    except Exception as e:
        db.rollback()
        logging.error(f"Error deleting end device: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@device_bp.route('/api/end-devices/metrics/<mac>', methods=['GET'])
def get_end_device_metrics(mac):
    try:
        # Get the latest metrics for the device from MongoDB
        metrics = readings_collection.find(
            {'device_id': mac},
            {'_id': 0}
        ).sort('timestamp', -1).limit(100)  # Get last 100 readings
        
        return jsonify(list(metrics))
        
    except Exception as e:
        logging.error(f"Error fetching end device metrics: {e}")
        return jsonify({'error': str(e)}), 500