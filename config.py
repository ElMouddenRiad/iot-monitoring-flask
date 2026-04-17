from datetime import timedelta
import os
import secrets


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return int(value)


def _env_timedelta_seconds(name: str, default_seconds: int) -> timedelta:
    return timedelta(seconds=_env_int(name, default_seconds))


def configure_app(app):
    database_url = os.getenv(
        "DATABASE_URL",
        "sqlite:///iot_platform.db",
    )
    secret_key = os.getenv("SECRET_KEY") or secrets.token_urlsafe(32)
    jwt_secret = os.getenv("JWT_SECRET_KEY") or secret_key

    app.config.update(
        SECRET_KEY=secret_key,
        JWT_SECRET_KEY=jwt_secret,
        JWT_ACCESS_TOKEN_EXPIRES=_env_timedelta_seconds("JWT_ACCESS_TOKEN_EXPIRES", 3600),
        SQLALCHEMY_DATABASE_URI=database_url,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        REDIS_URL=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        RABBITMQ_HOST=os.getenv("RABBITMQ_HOST", "localhost"),
        RABBITMQ_PORT=_env_int("RABBITMQ_PORT", 5672),
        RABBITMQ_QUEUE=os.getenv("RABBITMQ_QUEUE", "device_events"),
        RABBITMQ_EXCHANGE=os.getenv("RABBITMQ_EXCHANGE", "device_events"),
        MQTT_BROKER_URL=os.getenv("MQTT_BROKER_URL", "test.mosquitto.org"),
        MQTT_BROKER_PORT=_env_int("MQTT_BROKER_PORT", 1883),
        MQTT_REFRESH_TIME=float(os.getenv("MQTT_REFRESH_TIME", "1.0")),
        MQTT_TOPIC=os.getenv("MQTT_TOPIC", "iot/temp"),
        MQTT_CLIENT_ID=os.getenv("MQTT_CLIENT_ID", "server-subscriber"),
        MAX_STORED_MESSAGES=_env_int("API_MAX_STORED_MESSAGES", 1000),
        API_KEY_REQUIRED=_env_bool("API_KEY_REQUIRED", False),
        API_KEY=os.getenv("API_SECRET_KEY", ""),
        ENABLE_MQTT_CLIENT=_env_bool("ENABLE_MQTT_CLIENT", False),
        SKIP_DATABASE_INIT=_env_bool("SKIP_DATABASE_INIT", False),
        OPENMETEO_URL=os.getenv("OPENMETEO_URL", "https://api.open-meteo.com/v1/forecast"),
    )

    if app.config["ENABLE_MQTT_CLIENT"]:
        from mqtt_client import start_mqtt_client

        start_mqtt_client(app)