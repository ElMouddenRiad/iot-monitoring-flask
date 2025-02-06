# app.py
from flask import Flask, jsonify, request
from datetime import datetime, timedelta
from signing.auth import auth_bp, jwt
from device_management.device_manage import device_bp
from monitoring.monitor import store_temperature_reading
from extensions import socketio, init_socketio, db
import os
import json
import threading
import time
import eventlet
eventlet.monkey_patch()

# Import du module de prédiction
import pandas as pd
from predictions.prediction_module import train_model, make_prediction

# Import du DAL pour accéder aux informations d'appareil
from device_management.device_manage import DeviceDAL

# Import des modules Open-Meteo
import openmeteo_requests
import requests_cache
from retry_requests import retry

# Configuration du client Open-Meteo avec cache et gestion des retries
cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)
OPENMETEO_URL = "https://api.open-meteo.com/v1/forecast"

app = Flask(__name__)
app.config.update(
    MQTT_BROKER_URL='test.mosquitto.org',
    MQTT_BROKER_PORT=1883,
    MQTT_REFRESH_TIME=1.0,
    SECRET_KEY=os.urandom(24),
    SQLALCHEMY_DATABASE_URI="postgresql://admin:admin123@localhost:5432/iot_platform",
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    JWT_SECRET_KEY='your-secret-key',
    JWT_ACCESS_TOKEN_EXPIRES=timedelta(hours=1)
)
socketio = init_socketio(app)

# Exemple de provider JSON personnalisé
from bson import ObjectId
from flask.json.provider import JSONProvider

class CustomJSONProvider(JSONProvider):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

app.json_provider_class = CustomJSONProvider

# Enregistrement des blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(device_bp)

@app.route('/health')
def health_check():
    return jsonify({"status": "healthy"}), 200

@app.route('/predict_device', methods=['POST'])
def predict_device():
    """
    Payload attendu (JSON) :
    {
        "mac": "AA:BB:CC:DD:EE:FF"
    }
    Le endpoint récupère les informations de localisation de l'appareil,
    interroge l'API Open-Meteo pour récupérer les données horaires (température et humidité),
    entraîne un modèle sur ces données, puis effectue une prédiction à partir des valeurs actuelles.
    """
    try:
        payload = request.get_json()
        if not payload or "mac" not in payload:
            return jsonify({"error": "Le champ 'mac' est requis"}), 400

        mac = payload["mac"]
        # Récupérer l'appareil via le DAL
        device = DeviceDAL.get_device_by_mac(mac)
        if not device:
            return jsonify({"error": f"Aucun appareil trouvé pour la mac {mac}"}), 404

        # On suppose que device.location est un dictionnaire avec 'latitude' et 'longitude'
        try:
            lat = device.location["latitude"]
            lon = device.location["longitude"]
        except (KeyError, TypeError):
            return jsonify({"error": "Les informations de localisation de l'appareil sont manquantes ou invalides"}), 400

        # Préparer les paramètres pour Open-Meteo : on demande à la fois la température et l'humidité relative
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": ["temperature_2m", "relativehumidity_2m"],
            "hourly": ["temperature_2m", "relativehumidity_2m"],
            "timezone": "Europe/London"
        }

        responses = openmeteo.weather_api(OPENMETEO_URL, params=params)
        if not responses:
            return jsonify({"error": "Aucune réponse de l'API Open-Meteo"}), 500

        response = responses[0]

        # Récupérer les données horaires
        hourly = response.Hourly()
        hourly_temperature = hourly.Variables(0).ValuesAsNumpy()
        hourly_humidity = hourly.Variables(1).ValuesAsNumpy()

        # Créer un DataFrame avec ces données
        hourly_data = {
            "date": pd.date_range(
                start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
                end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
                freq=pd.Timedelta(seconds=hourly.Interval()),
                inclusive="left"
            ),
            "temperature_2m": hourly_temperature,
            "relative_humidity_2m": hourly_humidity
        }
        df = pd.DataFrame(data=hourly_data)

        # Entraîner le modèle sur ces données
        models = train_model(df)

        # Récupérer les valeurs actuelles pour réaliser la prédiction
        current = response.Current()
        # On récupère dans le même ordre que pour le DataFrame
        current_temperature = current.Variables(0).Value()
        current_humidity = current.Variables(1).Value()

        new_data = {
            "temperature_2m": current_temperature,
            "relative_humidity_2m": current_humidity
        }

        # Réaliser la prédiction
        pred_temp, pred_hum = make_prediction(models, new_data)
        return jsonify({
            "prediction_temperature": pred_temp,
            "prediction_humidity": pred_hum
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def create_app():
    with app.app_context():
        db.create_all()  # Créer les tables en base de données
    return app

if __name__ == '__main__':
    try:
        app = create_app()
        socketio.run(app,
            host='0.0.0.0',
            port=5000,
            debug=True,
            use_reloader=False
        )
    except Exception as e:
        print(f"Error: {e}")