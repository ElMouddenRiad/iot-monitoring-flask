from flask import Flask, jsonify, render_template, request
from flask_mqtt import Mqtt
from datetime import datetime
from functools import wraps
from signing.auth import auth_bp, db
from device_management.device_manage import device_bp
from monitoring.monitor import socketio, store_temperature_reading
import os
import pika
import json
import threading
import paho.mqtt.client as mqtt

app = Flask(__name__)

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
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://bakr:bakr1234@localhost/iot_platform'
app.config['MQTT_TOPIC'] = 'iot/temp'
app.config['MQTT_CLIENT_ID'] = 'server-subscriber'

mqtt = Mqtt(app)
MQTT_TOPIC = 'iot/temp'
messages = []  # Store received messages
devices = {}

@mqtt.on_connect()
def connect_callback(client, userdata, flags, rc):
    if rc == 0:
        print('Connected with result code '+str(rc))
        mqtt.subscribe(MQTT_TOPIC)
    else:
        print('Failed to connect with result code '+str(rc))

@mqtt.on_disconnect()
def disconnect_callback(client, userdata, rc):
    print('Disconnected with result code '+str(rc))

@mqtt.on_message()
def message_callback(client, userdata, msg):
    if msg.topic == MQTT_TOPIC:
        try:
            payload = eval(msg.payload.decode('utf-8'))  # Convert string representation back to dict
            
            # Add timestamp and validate data
            if 'temperature' not in payload:
                raise ValueError("Missing temperature data")
                
            payload['timestamp'] = datetime.now().isoformat()
            messages.append(payload)
            
            # Limit stored messages
            if len(messages) > app.config['MAX_STORED_MESSAGES']:
                messages.pop(0)
                
            print(f'Received temperature data: {payload}')
            
            # Store the temperature reading and broadcast to connected clients
            store_temperature_reading(payload)
        except Exception as e:
            print(f'Error processing message: {e}')

# Add basic auth decorator
def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not app.config['API_KEY_REQUIRED']:
            return f(*args, **kwargs)
            
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({
                'error': 'Missing API key',
                'message': 'Please provide an API key using the X-API-Key header'
            }), 401
            
        if api_key != app.config['API_KEY']:
            return jsonify({
                'error': 'Invalid API key',
                'message': 'The provided API key is not valid'
            }), 401
            
        return f(*args, **kwargs)
    return decorated

@app.route('/')
def index():
    return render_template('dashboard.html', 
                         latest_readings=messages[-10:],
                         total_readings=len(messages))

@app.route('/api/data')
@require_api_key
def get_data():
    return jsonify(messages)

@app.route('/api/latest')
@require_api_key
def get_latest():
    return jsonify(messages[-1] if messages else {'error': 'No data available'})

@app.route('/api/stats')
@require_api_key
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
    client = mqtt.Client(app.config['MQTT_CLIENT_ID'])
    client.username_pw_set(app.config['MQTT_USERNAME'], app.config['MQTT_PASSWORD'])
    client.on_connect = connect_callback
    client.on_message = message_callback

    try:
        client.connect(app.config['MQTT_BROKER'], app.config['MQTT_PORT'], 60)
        client.loop_forever()
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
    app = create_app()
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)