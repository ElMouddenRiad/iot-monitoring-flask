from flask import Flask, jsonify, render_template, request
from datetime import datetime, timedelta
from functools import wraps
from signing.auth import auth_bp, db, jwt
from device_management.device_manage import device_bp
from monitoring.monitor import socketio, store_temperature_reading, init_socketio
import os
import pika
import json
import threading
import paho.mqtt.client as paho_mqtt
from bson import ObjectId
from flask.json.provider import JSONProvider
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
# Initialize socketio with our main app
init_socketio(app)

class CustomJSONProvider(JSONProvider):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

app.json_provider_class = CustomJSONProvider

app.config['MQTT_BROKER_URL'] = 'broker.hivemq.com'
app.config['MQTT_BROKER_PORT'] = 1883
app.config['MQTT_USERNAME'] = 'bakr'
app.config['MQTT_PASSWORD'] = 'bakr'
app.config['MQTT_REFRESH_TIME'] = 1.0  # refresh time in seconds
app.config['SECRET_KEY'] = os.urandom(24)
app.config['MAX_STORED_MESSAGES'] = 1000  # Limit stored messages
app.config['API_KEY_REQUIRED'] = os.getenv('API_KEY_REQUIRED', 'False').lower() == 'true'
app.config['API_KEY'] = os.getenv('API_SECRET_KEY', 'your-secret-key')
app.config['RABBITMQ_HOST'] = 'localhost'
app.config['RABBITMQ_QUEUE'] = 'device_events'
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://admin:admin123@localhost:5432/iot_platform"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MQTT_TOPIC'] = 'iot/temp'
app.config['MQTT_CLIENT_ID'] = 'server-subscriber'
app.config['JWT_SECRET_KEY'] = 'your-secret-key'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)

messages = []  # Store received messages
devices = {}

# Initialize extensions with the app
db.init_app(app)
jwt.init_app(app)

# Register blueprint
app.register_blueprint(auth_bp)
app.register_blueprint(device_bp)

# MQTT callbacks
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"Connected to MQTT Broker!")
        client.subscribe(app.config['MQTT_TOPIC'])
    else:
        print(f"Failed to connect, return code {rc}")
        # Add specific error messages
        error_codes = {
            1: "Incorrect protocol version",
            2: "Invalid client identifier",
            3: "Server unavailable",
            4: "Bad username or password",
            5: "Not authorized"
        }
        print(f"Error: {error_codes.get(rc, 'Unknown error')}")

def on_message(client, userdata, msg):
    try:
        # Add debug print to see raw message
        print(f"Raw message received: {msg.payload}")
        
        # Check if payload is empty
        if not msg.payload:
            print("Empty payload received")
            return
            
        # Decode and parse payload with error handling
        try:
            payload = json.loads(msg.payload.decode('utf-8'))
        except json.JSONDecodeError as e:
            print(f"Invalid JSON received: {msg.payload.decode('utf-8')}")
            print(f"JSON decode error: {e}")
            return
            
        if not isinstance(payload, dict):
            print(f"Invalid message format: {payload}")
            return
            
        # Process valid message
        if 'timestamp' not in payload:
            payload['timestamp'] = datetime.now().isoformat()
            
        message_data = {
            'device_id': payload.get('device_id'),
            'temperature': payload.get('temperature'),
            'location': payload.get('location'),
            'timestamp': payload.get('timestamp')
        }
        
        # Validate required fields
        if not all(message_data.get(field) for field in ['device_id', 'temperature']):
            print(f"Missing required fields in message: {message_data}")
            return
            
        messages.append(message_data)
        
        if len(messages) > app.config['MAX_STORED_MESSAGES']:
            messages.pop(0)
            
        store_temperature_reading(message_data)
        
    except Exception as e:
        print(f"Error processing message: {e}")

def on_disconnect(client, userdata, rc):
    print(f'Disconnected with result code {rc}')
    if rc != 0:
        print("Unexpected disconnection. Attempting to reconnect...")

@app.route('/')
def index():
    return render_template('dashboard.html', 
                         latest_readings=messages[-10:],
                         total_readings=len(messages))

@app.route('/api/data')
def get_data():
    try:
        return jsonify([{
            'device_id': msg.get('device_id'),
            'temperature': msg.get('temperature'),
            'location': msg.get('location'),
            'timestamp': msg.get('timestamp')
        } for msg in messages])
    except Exception as e:
        print(f"Error serializing data: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/latest')
def get_latest():
    return jsonify(messages[-1] if messages else {'error': 'No data available'})

@app.route('/api/stats')
def get_stats():
    if not messages:
        return jsonify({'error': 'No data available'})
    
    temperatures = [m['temperature'] for m in messages]
    return jsonify({
        'average_temp': round(sum(temperatures) / len(temperatures), 2),
        'max_temp': max(temperatures),
        'min_temp': min(temperatures),
        'num_readings': len(temperatures),
        'last_updated': messages[-1]['timestamp'] if messages else None
    })

def publish_event(event_type, device_data):
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=app.config['RABBITMQ_HOST'])
        )
        channel = connection.channel()
        
        # Declare queue
        channel.queue_declare(queue=app.config['RABBITMQ_QUEUE'])
        
        # Prepare message
        message = {
            'event_type': event_type,
            'timestamp': datetime.now().isoformat(),
            'device_data': device_data
        }
        
        # Publish message
        channel.basic_publish(
            exchange='',
            routing_key=app.config['RABBITMQ_QUEUE'],
            body=json.dumps(message)
        )
        
        connection.close()
    except Exception as e:
        print(f"Error publishing to RabbitMQ: {e}")

@app.route('/api/devices', methods=['GET'])
def get_devices():
    search_term = request.args.get('search', '').lower()
    if search_term:
        filtered_devices = {
            device_id: device for device_id, device in devices.items()
            if search_term in device_id.lower() or 
            search_term in device.get('name', '').lower()
        }
        return jsonify(filtered_devices)
    return jsonify(devices)

@app.route('/api/devices/<device_id>', methods=['GET'])
def get_device(device_id):
    device = devices.get(device_id)
    if device is None:
        return jsonify({'error': 'Device not found'}), 404
    return jsonify(device)

@app.route('/api/devices', methods=['POST'])
def add_device():
    device_data = request.get_json()
    
    # Validate required fields
    required_fields = ['mac', 'name', 'location']
    if not all(field in device_data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    device_id = device_data['mac']
    if device_id in devices:
        return jsonify({'error': 'Device already exists'}), 409
    
    # Add default values
    device_data['created_at'] = datetime.now().isoformat()
    device_data['status'] = 'active'
    
    devices[device_id] = device_data
    
    # Publish event to RabbitMQ
    publish_event('device_added', device_data)
    
    return jsonify(device_data), 201

@app.route('/api/devices/<device_id>', methods=['PUT'])
def update_device(device_id):
    if device_id not in devices:
        return jsonify({'error': 'Device not found'}), 404
    
    device_data = request.get_json()
    
    # Don't allow updating the MAC address
    device_data.pop('mac', None)
    
    # Update device
    devices[device_id].update(device_data)
    devices[device_id]['updated_at'] = datetime.now().isoformat()
    
    # Publish event to RabbitMQ
    publish_event('device_updated', devices[device_id])
    
    return jsonify(devices[device_id])

@app.route('/api/devices/<device_id>', methods=['DELETE'])
def delete_device(device_id):
    if device_id not in devices:
        return jsonify({'error': 'Device not found'}), 404
    
    device_data = devices.pop(device_id)
    
    # Publish event to RabbitMQ
    publish_event('device_deleted', {'mac': device_id})
    
    return jsonify({'message': 'Device deleted successfully'})

def start_mqtt_client():
    try:
        # Create client with clean_session=True to avoid stale sessions
        client = paho_mqtt.Client(client_id=app.config['MQTT_CLIENT_ID'], clean_session=True)
        
        # Set callbacks
        client.on_connect = on_connect
        client.on_message = on_message
        client.on_disconnect = on_disconnect

        # Set credentials
        client.username_pw_set(app.config['MQTT_USERNAME'], app.config['MQTT_PASSWORD'])
        
        # Set keepalive to a lower value
        client.keepalive = 30
        
        # Enable automatic reconnection with shorter delays
        client.reconnect_delay_set(min_delay=1, max_delay=30)
        
        # Set will message for clean disconnection
        client.will_set(app.config['MQTT_TOPIC'], payload="Offline", qos=1, retain=True)
        
        # Connect with clean_session=True
        client.connect(app.config['MQTT_BROKER_URL'], app.config['MQTT_BROKER_PORT'], keepalive=30)
        
        # Use loop_start for better reconnection handling
        client.loop_start()

    except Exception as e:
        print(f"Error connecting to MQTT broker: {e}")

@app.route('/health')
def health_check():
    return {'status': 'healthy'}, 200

def create_app():
    with app.app_context():
        db.create_all()
    
    # Start MQTT client in a separate thread
    mqtt_thread = threading.Thread(target=start_mqtt_client)
    mqtt_thread.daemon = True
    mqtt_thread.start()
    
    return app

if __name__ == '__main__':
    try:
        app = create_app()
        socketio.run(app, host='0.0.0.0', port=5000, debug=True)
    except KeyboardInterrupt:
        print("Shutting down gracefully...")
    except Exception as e:
        print(f"Error: {e}")