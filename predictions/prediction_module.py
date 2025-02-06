# prediction_module.py
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error
import pandas as pd
from flask import Blueprint
from flask import Blueprint, jsonify, request
from device_management.device_manage import DeviceDAL
import pandas as pd
import openmeteo_requests
import requests_cache


from retry_requests import retry

# Initialisation du Blueprint
prediction_bp = Blueprint('prediction', __name__)

# Configuration Open-Meteo
cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)
OPENMETEO_URL = "https://api.open-meteo.com/v1/forecast"

@prediction_bp.route('/predict_device', methods=['POST'])
def predict_device():
    try:
        payload = request.get_json()
        if not payload or "mac" not in payload:
            return jsonify({"error": "Le champ 'mac' est requis"}), 400

        mac = payload["mac"]
        device = DeviceDAL.get_device_by_mac(mac)
        if not device:
            return jsonify({"error": f"Aucun appareil trouvé pour la MAC {mac}"}), 404

        try:
            lat = device.location["latitude"]
            lon = device.location["longitude"]
        except (KeyError, TypeError):
            return jsonify({"error": "Les informations de localisation de l'appareil sont manquantes ou invalides"}), 400

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
        hourly = response.Hourly()
        hourly_temperature = hourly.Variables(0).ValuesAsNumpy()
        hourly_humidity = hourly.Variables(1).ValuesAsNumpy()

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

        models = train_model(df)

        current = response.Current()
        current_temperature = current.Variables(0).Value()
        current_humidity = current.Variables(1).Value()

        new_data = {
            "temperature_2m": current_temperature,
            "relative_humidity_2m": current_humidity
        }

        pred_temp, pred_hum = make_prediction(models, new_data)
        return jsonify({
            "prediction_temperature": pred_temp,
            "prediction_humidity": pred_hum
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def train_model(data):
    # On s'assure que les colonnes attendues sont présentes
    if 'temperature_2m' not in data.columns or 'relative_humidity_2m' not in data.columns:
        raise ValueError("Les données doivent contenir 'temperature_2m' et 'relative_humidity_2m'")
    
    X = data[['temperature_2m', 'relative_humidity_2m']]
    y_temperature = data['temperature_2m']
    y_humidity = data['relative_humidity_2m']

    X_train, X_test, y_temp_train, y_temp_test, y_hum_train, y_hum_test = train_test_split(
        X, y_temperature, y_humidity, test_size=0.2, random_state=42
    )

    model_temperature = LinearRegression()
    model_humidity = LinearRegression()

    model_temperature.fit(X_train, y_temp_train)
    model_humidity.fit(X_train, y_hum_train)

    # Affichage d'un indicateur de performance pour le debug
    y_temp_pred = model_temperature.predict(X_test)
    y_hum_pred = model_humidity.predict(X_test)
    mse_temp = mean_squared_error(y_temp_test, y_temp_pred)
    mse_hum = mean_squared_error(y_hum_test, y_hum_pred)
    print(f'MSE Temperature: {mse_temp} - MSE Humidity: {mse_hum}')

    return model_temperature, model_humidity

def make_prediction(models, new_data):
    import pandas as pd
    X_new = pd.DataFrame([new_data])
    prediction_temperature = models[0].predict(X_new)
    prediction_humidity = models[1].predict(X_new)
    return prediction_temperature[0], prediction_humidity[0]
