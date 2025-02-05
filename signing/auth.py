from flask import Flask, request, jsonify, Blueprint
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt
import redis
import bcrypt
from datetime import timedelta
import os
from extensions import db  # Import db from extensions
from redis import Redis
from urllib.parse import urlparse
import logging

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

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    logging.info(f"Received registration attempt: {data}")
    if User.query.filter_by(username=data.get('username')).first():
        return jsonify({'error': 'Username already exists'}), 400
    
    hashed_password = bcrypt.hashpw(
        data['password'].encode('utf-8'), bcrypt.gensalt()
    ).decode('utf-8')
    
    new_user = User(
        username=data['username'], 
        password=hashed_password
    )
    
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({'message': 'User created successfully'}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    logging.info(f"Login attempt with data: {data}")
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()
    if not user:
        logging.error("User not found")
        return jsonify({"error": "Invalid credentials"}), 401

    if not bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
        logging.error("Password check failed")
        return jsonify({"error": "Invalid credentials"}), 401

    access_token = create_access_token(identity=user.id)
    return jsonify({"access_token": access_token}), 200

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    jti = get_jwt()["jti"]
    # Revoke the token by removing it from Redis
    redis_client.delete(f"token_{jti}")
    return jsonify({"msg": "Successfully logged out"}), 200

@auth_bp.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200
