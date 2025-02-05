from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
import eventlet
eventlet.monkey_patch()

# Create shared instances
db = SQLAlchemy()
jwt = JWTManager()
socketio = SocketIO(
    cors_allowed_origins=["http://localhost:3000", "http://192.168.56.1:3000"],  # Add all your frontend URLs
    async_mode='eventlet',
    logger=True,
    engineio_logger=True,
    ping_timeout=60,
    ping_interval=25,
    manage_session=False,
    always_connect=True,
    transports=['websocket', 'polling']
)

def init_socketio(app):
    socketio.init_app(app, 
        cors_allowed_origins="*",  # Allow all origins
        async_mode='eventlet'
    )
    return socketio 