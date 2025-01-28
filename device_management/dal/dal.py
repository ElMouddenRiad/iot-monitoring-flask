import openmeteo_requests

import requests_cache
import pandas as pd
from retry_requests import retry

# Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
openmeteo = openmeteo_requests.Client(session = retry_session)

# Make sure all required weather variables are listed here
# The order of variables in hourly or daily is important to assign them correctly below
url = "https://api.open-meteo.com/v1/forecast"
params = {
	"latitude": 52.52,
	"longitude": 13.41,
	"current": ["temperature_2m", "is_day", "rain"],
	"hourly": "temperature_2m",
	"timezone": "Europe/London"
}
responses = openmeteo.weather_api(url, params=params)

# Process first location. Add a for-loop for multiple locations or weather models
response = responses[0]
print(f"Coordinates {response.Latitude()}°N {response.Longitude()}°E")
print(f"Elevation {response.Elevation()} m asl")
print(f"Timezone {response.Timezone()} {response.TimezoneAbbreviation()}")
print(f"Timezone difference to GMT+0 {response.UtcOffsetSeconds()} s")


# Current values. The order of variables needs to be the same as requested.
current = response.Current()

current_temperature_2m = current.Variables(0).Value()

current_is_day = current.Variables(1).Value()

current_rain = current.Variables(2).Value()

print(f"Current time {current.Time()}")

print(f"Current temperature_2m {current_temperature_2m}")
print(f"Current is_day {current_is_day}")
print(f"Current rain {current_rain}")
# Process hourly data. The order of variables needs to be the same as requested.
hourly = response.Hourly()
hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()

hourly_data = {"date": pd.date_range(
	start = pd.to_datetime(hourly.Time(), unit = "s", utc = True),
	end = pd.to_datetime(hourly.TimeEnd(), unit = "s", utc = True),
	freq = pd.Timedelta(seconds = hourly.Interval()),
	inclusive = "left"
)}

hourly_data["temperature_2m"] = hourly_temperature_2m

hourly_dataframe = pd.DataFrame(data = hourly_data)
print(hourly_dataframe)

# Data Access Layer for device management
from flask_sqlalchemy import SQLAlchemy
from redis import Redis
import json
from ..models import Device  # Import Device from models
from extensions import db

db = SQLAlchemy()
redis_client = Redis(host='localhost', port=6379, db=0)

class DeviceDAL:
    @staticmethod
    def get_devices(search_term=None):
        query = Device.query
        if search_term:
            query = query.filter(Device.name.ilike(f'%{search_term}%'))
        return query.all()

    @staticmethod
    def add_device(device_data):
        device = Device(
            mac=device_data['mac'],
            name=device_data['name'],
            location=device_data['location']
        )
        db.session.add(device)
        db.session.commit()
        return device

    @staticmethod
    def update_device(mac, device_data):
        try:
            device = Device.query.filter_by(mac=mac).first()
            
            if device:
                if 'name' in device_data:
                    device.name = device_data['name']
                if 'location' in device_data:
                    device.latitude = device_data['location']['latitude']
                    device.longitude = device_data['location']['longitude']
                if 'status' in device_data:
                    device.status = device_data['status']
                
                db.session.commit()
                redis_client.delete('devices_list')
                return device
            return None
            
        except Exception as e:
            db.session.rollback()
            raise e

    @staticmethod
    def delete_device(mac):
        try:
            device = Device.query.filter_by(mac=mac).first()
            if device:
                db.session.delete(device)
                db.session.commit()
                redis_client.delete('devices_list')
                return device
            return None
            
        except Exception as e:
            db.session.rollback()
            raise e
