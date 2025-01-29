import eventlet
eventlet.monkey_patch()

from flask import Flask
from flask_cors import CORS
from extensions import socketio, db
from signing.auth import auth_bp, jwt, init_redis
from device_management.device_manage import device_bp
from monitoring.monitor import store_temperature_reading
from config import configure_app  # Import from config instead of app
from device_management.models import init_test_devices  # Add this import

def create_app():
    app = Flask(__name__)
    
    # More permissive CORS configuration for development
    CORS(app, 
        resources={r"/*": {
            "origins": ["http://localhost:3000", "http://192.168.56.1:3000"],  # Add all your frontend URLs
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

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(device_bp)

    # Initialize database and test data
    with app.app_context():
        # Drop all tables and recreate them
        db.drop_all()
        db.create_all()
        init_test_devices(app)

    # Initialize Redis
    global redis_client
    redis_client = init_redis(app)

    return app

if __name__ == '__main__':
    app = create_app()
    socketio.run(app, 
        host='0.0.0.0', 
        port=5000,  # You can change this to another port if needed
        debug=True,
        use_reloader=False
    ) 