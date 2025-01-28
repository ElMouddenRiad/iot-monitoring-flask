from flask import Flask, jsonify
from datetime import datetime, timedelta
from functools import wraps
from signing.auth import auth_bp, jwt
from device_management.device_manage import device_bp
from monitoring.monitor import store_temperature_reading
from extensions import socketio, init_socketio, db
import os
import pika
import json
import threading
import paho.mqtt.client as paho_mqtt
from bson import ObjectId
from flask.json.provider import JSONProvider
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:3000"],
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type"]
    }
})

# Initialize SocketIO right after creating the Flask app
socketio = init_socketio(app)

class CustomJSONProvider(JSONProvider):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

app.json_provider_class = CustomJSONProvider

# Configuration
app.config.update(
    MQTT_BROKER_URL='broker.hivemq.com',
    MQTT_BROKER_PORT=1883,
    # MQTT_USERNAME='bakr',
    # MQTT_PASSWORD='bakr',
    MQTT_REFRESH_TIME=1.0,
    SECRET_KEY=os.urandom(24),
    MAX_STORED_MESSAGES=1000,
    API_KEY_REQUIRED=os.getenv('API_KEY_REQUIRED', 'False').lower() == 'true',
    API_KEY=os.getenv('API_SECRET_KEY', 'your-secret-key'),
    RABBITMQ_HOST='localhost',
    RABBITMQ_QUEUE='device_events',
    SQLALCHEMY_DATABASE_URI="postgresql://admin:admin123@localhost:5432/iot_platform",
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    MQTT_TOPIC='iot/temp',
    MQTT_CLIENT_ID='server-subscriber',
    JWT_SECRET_KEY='your-secret-key',
    JWT_ACCESS_TOKEN_EXPIRES=timedelta(hours=1)
)

# Initialize extensions
db.init_app(app)
jwt.init_app(app)

# Register blueprints
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
        # Skip processing "Offline" messages
        if msg.payload.decode() == "Offline":
            return
            
        payload = json.loads(msg.payload.decode())
        print(f"Received `{payload}` from `{msg.topic}` topic")
        store_temperature_reading(payload)
    except json.JSONDecodeError as e:
        print(f"Invalid message format: {msg.payload.decode()}")
    except Exception as e:
        print(f"Error processing message: {e}")

def on_disconnect(client, userdata, rc):
    print(f"Disconnected with result code {rc}")
    if rc != 0:
        print("Unexpected disconnection. Attempting to reconnect...")
        client.reconnect()

def start_mqtt_client():
    try:
        client = paho_mqtt.Client(client_id=app.config['MQTT_CLIENT_ID'], clean_session=True)
        # client.username_pw_set(app.config['MQTT_USERNAME'], app.config['MQTT_PASSWORD'])
        
        # Set callbacks
        client.on_connect = on_connect
        client.on_message = on_message
        client.on_disconnect = on_disconnect
        
        # Set will message
        client.will_set(app.config['MQTT_TOPIC'], payload="Offline", qos=1, retain=True)
        
        # Enable automatic reconnection
        client.reconnect_delay_set(min_delay=1, max_delay=30)
        
        # Connect with shorter keepalive
        client.connect(app.config['MQTT_BROKER_URL'], app.config['MQTT_BROKER_PORT'], keepalive=30)
        
        # Use loop_start instead of loop_forever for better reconnection handling
        client.loop_start()
        
    except Exception as e:
        print(f"Error connecting to MQTT broker: {e}")

@app.route('/health')
def health_check():
    return {'status': 'healthy'}, 200

def create_app():
    with app.app_context():
        db.create_all()  # This will create all tables
        
    # Start MQTT client in a separate thread
    mqtt_thread = threading.Thread(target=start_mqtt_client)
    mqtt_thread.daemon = True
    mqtt_thread.start()
    
    return app

if __name__ == '__main__':
    try:
        app = create_app()
        socketio.run(app, 
            host='0.0.0.0', 
            port=5000, 
            debug=True,
            allow_unsafe_werkzeug=True
        )
    except Exception as e:
        print(f"Error: {e}")