from flask import Flask, request, jsonify, Blueprint
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
import redis
import bcrypt
from datetime import timedelta
import os
from extensions import db  # Import db from extensions
from redis import Redis
from urllib.parse import urlparse
auth_bp = Blueprint('auth', __name__)

# Initialize extensions
jwt = JWTManager()

def init_redis(app):
    try:
        redis_url = urlparse(app.config['REDIS_URL'])
        redis_client = Redis(
            host=redis_url.hostname or 'localhost',
            port=redis_url.port or 6379,
            db=0,
            socket_timeout=5,
            decode_responses=True
        )
        redis_client.ping()  # Test connection
        return redis_client
    except Exception as e:
        print(f"Warning: Redis connection failed ({str(e)}). Some features may be limited.")
        return None

# Initialize Redis after app creation
redis_client = None

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 400
    
    hashed_password = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())
    new_user = User(username=data['username'], password=hashed_password)
    
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({'message': 'User created successfully'}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()
    
    if user and bcrypt.checkpw(data['password'].encode('utf-8'), user.password.encode('utf-8')):
        access_token = create_access_token(identity=user.username)
        # Store token in Redis
        redis_client.setex(
            f"token_{user.username}",
            auth_bp.config['JWT_ACCESS_TOKEN_EXPIRES'].total_seconds(),
            access_token
        )
        return jsonify({'token': access_token}), 200
    
    return jsonify({'error': 'Invalid credentials'}), 401
