import eventlet
eventlet.monkey_patch()

from flask import Flask, request, jsonify
from flask_cors import CORS
from extensions import socketio, db
from signing.auth import auth_bp, jwt, redis_client, init_redis
from device_management.device_manage import device_bp
from monitoring.monitor import store_temperature_reading
from config import configure_app
from device_management.models import init_test_devices
from device_management.device_manage import test_rabbitmq_connection
import logging
from flask_jwt_extended import JWTManager
from predictions.prediction_module import train_model, make_prediction, prediction_bp
import pandas as pd
import openmeteo_requests as openmeteo
import requests_cache
from retry_requests import retry
from device_management.device_manage import DeviceDAL


OPENMETEO_URL = "https://api.open-meteo.com/v1/forecast"
# Set up logging
logging.basicConfig(level=logging.INFO)


# Fallback in-memory storage for revoked tokens
revoked_tokens = set()
# Callback to check if a token is revoked
@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    jti = jwt_payload["jti"]
    if redis_client:
        token = redis_client.get(f"token_{jti}")
        return token is None  # If token not found in Redis, it's revoked
    else:
        # Fallback to in-memory storage
        return jti in revoked_tokens
    
# Handle revoked token response
@jwt.revoked_token_loader
def revoked_token_callback(jwt_header, jwt_payload):
    return jsonify({"error": "Token has been revoked"}), 401

# Handle expired token response
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({"error": "Token has expired"}), 401

def create_app():
    app = Flask(__name__)
    
    # CORS configuration
    CORS(app, 
        resources={r"/*": {
            "origins": ["http://localhost:3000", "http://192.168.56.1:3000"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "expose_headers": ["Content-Range", "X-Content-Range"],
            "supports_credentials": True
        }}
    )

    configure_app(app)
    
    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    socketio.init_app(app)

    # Initialize Redis
    global redis_client
    redis_client = init_redis(app)
    if redis_client:
        auth_bp.redis_client = redis_client
    else:
        logging.error("Failed to initialize Redis client")

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(device_bp, url_prefix='/api')
    app.register_blueprint(prediction_bp, url_prefix='/prediction')

    # Initialize database and test data
    with app.app_context():
        # **Remove the following lines in production**
        db.drop_all()
        db.create_all()
        init_test_devices(app)

        # Test RabbitMQ connection
        test_rabbitmq_connection()
    
    

    return app



if __name__ == '__main__':
    app = create_app()
    # Use eventlet's WSGI server instead of Flask's default
    eventlet.wsgi.server(eventlet.listen(('0.0.0.0', 5000)), app) 