"""Simple prediction helpers for environmental readings."""

import logging

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error
import pandas as pd


logger = logging.getLogger(__name__)

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

    y_temp_pred = model_temperature.predict(X_test)
    y_hum_pred = model_humidity.predict(X_test)
    mse_temp = mean_squared_error(y_temp_test, y_temp_pred)
    mse_hum = mean_squared_error(y_hum_test, y_hum_pred)
    logger.debug("Model evaluation completed", extra={
        "mse_temperature": mse_temp,
        "mse_humidity": mse_hum,
    })

    return model_temperature, model_humidity

def make_prediction(models, new_data):
    import pandas as pd
    X_new = pd.DataFrame([new_data])
    prediction_temperature = models[0].predict(X_new)
    prediction_humidity = models[1].predict(X_new)
    return prediction_temperature[0], prediction_humidity[0]
