from datetime import timedelta
from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    decode_token,
    get_jwt,
    get_jwt_identity,
    jwt_required,
)
import redis
import bcrypt
from extensions import db
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
        logging.info("Redis connection successful")
        return redis_client
    except Exception as e:
        logging.error(f"Redis connection failed: {e}")
        return None

# Initialize Redis after app creation
redis_client = None
revoked_tokens = set()


def _token_key(jti: str) -> str:
    return f"token_{jti}"


def _jwt_expires_seconds() -> int:
    expires = current_app.config.get("JWT_ACCESS_TOKEN_EXPIRES", timedelta(hours=1))
    if isinstance(expires, timedelta):
        return max(int(expires.total_seconds()), 1)
    return max(int(expires), 1)


@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    jti = jwt_payload["jti"]
    if redis_client:
        token = redis_client.get(_token_key(jti))
        return token is None
    return jti in revoked_tokens


@jwt.revoked_token_loader
def revoked_token_callback(jwt_header, jwt_payload):
    return jsonify({"error": "Token has been revoked"}), 401


@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({"error": "Token has expired"}), 401

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password are required'}), 400
    
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
    if not data:
        return jsonify({"error": "Missing JSON body"}), 400
    logging.info(f"Login attempt with data: {data}")
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    user = User.query.filter_by(username=username).first()
    if not user:
        logging.error("User not found")
        return jsonify({"error": "Invalid credentials"}), 401

    if not bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
        logging.error("Password check failed")
        return jsonify({"error": "Invalid credentials"}), 401

    # Ensure identity is a string
    access_token = create_access_token(identity=str(user.id))

    token_data = decode_token(access_token)
    if redis_client:
        redis_client.setex(
            _token_key(token_data["jti"]),
            _jwt_expires_seconds(),
            str(user.id),
        )
    else:
        revoked_tokens.discard(token_data["jti"])

    return jsonify({"access_token": access_token}), 200

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    jti = get_jwt()["jti"]
    if redis_client:
        redis_client.delete(_token_key(jti))
    else:
        revoked_tokens.add(jti)
    return jsonify({"msg": "Successfully logged out"}), 200

@auth_bp.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200
