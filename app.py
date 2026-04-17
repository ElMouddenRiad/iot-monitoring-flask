from datetime import datetime

import eventlet

eventlet.monkey_patch()

import pandas as pd
import openmeteo_requests
import requests_cache
from bson import ObjectId
from flask import Flask, jsonify, request
from flask.json.provider import JSONProvider
from retry_requests import retry

from config import configure_app
from device_management.device_manage import device_bp
from device_management.dal.dal import DeviceDAL
from device_management.models import init_test_devices
from extensions import db, init_socketio, socketio
from prediction_module import make_prediction, train_model
from signing import auth as auth_module


class CustomJSONProvider(JSONProvider):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


cache_session = requests_cache.CachedSession(".cache", expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)


def create_app():
    app = Flask(__name__)
    app.json_provider_class = CustomJSONProvider
    configure_app(app)

    db.init_app(app)
    auth_module.jwt.init_app(app)
    init_socketio(app)

    auth_module.redis_client = auth_module.init_redis(app)

    app.register_blueprint(auth_module.auth_bp, url_prefix="/auth")
    app.register_blueprint(device_bp, url_prefix="/api")

    @app.route("/health")
    def health_check():
        return jsonify({"status": "healthy"}), 200

    @app.route("/predict_device", methods=["POST"])
    def predict_device():
        try:
            payload = request.get_json(silent=True) or {}
            mac = payload.get("mac")
            if not mac:
                return jsonify({"error": "Le champ 'mac' est requis"}), 400

            device = DeviceDAL.get_device_by_mac(mac)
            if not device:
                return jsonify({"error": f"Aucun appareil trouvé pour la mac {mac}"}), 404

            location = device.location or {}
            if isinstance(location, str):
                import json

                try:
                    location = json.loads(location)
                except json.JSONDecodeError:
                    location = {}

            try:
                lat = float(location["latitude"])
                lon = float(location["longitude"])
            except (KeyError, TypeError, ValueError):
                return jsonify({"error": "Les informations de localisation de l'appareil sont manquantes ou invalides"}), 400

            params = {
                "latitude": lat,
                "longitude": lon,
                "current": ["temperature_2m", "relativehumidity_2m"],
                "hourly": ["temperature_2m", "relativehumidity_2m"],
                "timezone": "Europe/London",
            }

            responses = openmeteo.weather_api(app.config["OPENMETEO_URL"], params=params)
            if not responses:
                return jsonify({"error": "Aucune réponse de l'API Open-Meteo"}), 502

            response = responses[0]
            hourly = response.Hourly()
            hourly_data = {
                "date": pd.date_range(
                    start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
                    end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
                    freq=pd.Timedelta(seconds=hourly.Interval()),
                    inclusive="left",
                ),
                "temperature_2m": hourly.Variables(0).ValuesAsNumpy(),
                "relative_humidity_2m": hourly.Variables(1).ValuesAsNumpy(),
            }
            models = train_model(pd.DataFrame(hourly_data))

            current = response.Current()
            new_data = {
                "temperature_2m": current.Variables(0).Value(),
                "relative_humidity_2m": current.Variables(1).Value(),
            }
            pred_temp, pred_hum = make_prediction(models, new_data)
            return jsonify(
                {
                    "prediction_temperature": pred_temp,
                    "prediction_humidity": pred_hum,
                }
            )
        except Exception as exc:
            return jsonify({"error": str(exc)}), 500

    with app.app_context():
        if not app.config.get("SKIP_DATABASE_INIT", False):
            db.create_all()
            init_test_devices(app)

    return app


app = create_app()


if __name__ == "__main__":
    socketio.run(
        app,
        host="0.0.0.0",
        port=int(app.config.get("PORT", 5000)),
        debug=bool(app.config.get("FLASK_DEBUG", False)),
        use_reloader=False,
    )