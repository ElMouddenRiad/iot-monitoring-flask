"""Data access helpers for device persistence."""

from __future__ import annotations

import logging
import os

from redis import Redis

from ..models import Device
from extensions import db


logger = logging.getLogger(__name__)
redis_client = Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))


def fetch_weather_snapshot(latitude=52.52, longitude=13.41, timezone="Europe/London"):
    """Fetch a weather snapshot from Open-Meteo on demand.

    The old module executed network calls during import, which slowed down app
    startup and made failures hard to trace. This helper keeps the capability
    available without side effects.
    """

    import openmeteo_requests
    import pandas as pd
    import requests_cache
    from retry_requests import retry

    cache_dir = os.getenv("OPEN_METEO_CACHE_DIR", ".cache")
    expire_after = int(os.getenv("OPEN_METEO_CACHE_TTL", "3600"))
    retries = int(os.getenv("OPEN_METEO_RETRIES", "5"))
    backoff_factor = float(os.getenv("OPEN_METEO_BACKOFF_FACTOR", "0.2"))

    cache_session = requests_cache.CachedSession(cache_dir, expire_after=expire_after)
    retry_session = retry(cache_session, retries=retries, backoff_factor=backoff_factor)
    client = openmeteo_requests.Client(session=retry_session)

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": ["temperature_2m", "is_day", "rain"],
        "hourly": "temperature_2m",
        "timezone": timezone,
    }

    responses = client.weather_api(url, params=params)
    response = responses[0]

    current = response.Current()
    hourly = response.Hourly()
    hourly_dataframe = pd.DataFrame(
        data={
            "date": pd.date_range(
                start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
                end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
                freq=pd.Timedelta(seconds=hourly.Interval()),
                inclusive="left",
            ),
            "temperature_2m": hourly.Variables(0).ValuesAsNumpy(),
        }
    )

    return {
        "coordinates": {
            "latitude": response.Latitude(),
            "longitude": response.Longitude(),
        },
        "current": {
            "time": current.Time(),
            "temperature_2m": current.Variables(0).Value(),
            "is_day": current.Variables(1).Value(),
            "rain": current.Variables(2).Value(),
        },
        "hourly_dataframe": hourly_dataframe,
    }


class DeviceDAL:
    @staticmethod
    def get_devices(search_term=None):
        query = Device.query
        if search_term:
            query = query.filter(Device.name.ilike(f"%{search_term}%"))
        return query.all()

    @staticmethod
    def get_device_by_mac(mac):
        return Device.query.filter_by(mac=mac).first()

    @staticmethod
    def add_device(device_data):
        device = Device(
            mac=device_data["mac"],
            name=device_data["name"],
            location=device_data["location"],
        )
        db.session.add(device)
        db.session.commit()
        return device

    @staticmethod
    def update_device(mac, device_data):
        try:
            device = Device.query.filter_by(mac=mac).first()
            if device:
                if "name" in device_data:
                    device.name = device_data["name"]
                if "location" in device_data:
                    device.location = device_data["location"]
                if "status" in device_data:
                    device.status = device_data["status"]
                db.session.commit()
                redis_client.delete("devices_list")
                return device
            return None
        except Exception:
            db.session.rollback()
            logger.exception("Error updating device %s", mac)
            raise

    @staticmethod
    def delete_device(mac):
        try:
            device = Device.query.filter_by(mac=mac).first()
            if device:
                db.session.delete(device)
                db.session.commit()
                redis_client.delete("devices_list")
                return device
            return None
        except Exception:
            db.session.rollback()
            logger.exception("Error deleting device %s", mac)
            raise