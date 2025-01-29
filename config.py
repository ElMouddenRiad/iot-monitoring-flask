from datetime import timedelta
import os

def configure_app(app):
    # Configuration
    app.config.update(
        MQTT_BROKER_URL='test.mosquitto.org',
        MQTT_BROKER_PORT=1883,
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
        JWT_ACCESS_TOKEN_EXPIRES=timedelta(hours=1),
        REDIS_URL=os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    )

    # Start MQTT client
    from mqtt_client import start_mqtt_client
    start_mqtt_client(app) 