import paho.mqtt.client as mqtt
import random
import time
from concurrent.futures import ThreadPoolExecutor
import requests
from datetime import datetime, timedelta
import json

MQTT_BROKER = "broker.hivemq.com"
MQTT_CLIENT_ID = "iot-device"
MQTT_USERNAME = "bakr"
MQTT_PASSWORD = "bakr" 
MQTT_BROKER_PORT = 1883
MQTT_TOPIC = "iot/temp"

class WeatherDataFetcher:
    def __init__(self):
        self.base_url = "https://archive-api.open-meteo.com/v1/archive"
        self.cache = {}
        
    def get_historical_data(self, latitude, longitude, start_date, end_date):
        cache_key = f"{latitude},{longitude},{start_date},{end_date}"
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        params = {
            'latitude': latitude,
            'longitude': longitude,
            'start_date': start_date,
            'end_date': end_date,
            'hourly': 'temperature_2m',
            'timezone': 'auto'
        }
        
        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            temperatures = data['hourly']['temperature_2m']
            timestamps = data['hourly']['time']
            
            processed_data = list(zip(timestamps, temperatures))
            self.cache[cache_key] = processed_data
            return processed_data
            
        except Exception as e:
            print(f"Error fetching weather data: {e}")
            return None

def simulate_temperature(device_info, weather_fetcher):
    """
    Simulate temperature using historical data and random fluctuations
    """
    if not device_info or 'location' not in device_info:
        return 25.0  # Default temperature if no location data
        
    current_time = datetime.now()
    previous_day = (current_time - timedelta(days=1)).strftime('%Y-%m-%d')
    current_day = current_time.strftime('%Y-%m-%d')
    
    historical_data = weather_fetcher.get_historical_data(
        device_info['location']['latitude'],
        device_info['location']['longitude'],
        previous_day,
        current_day
    )
    
    if historical_data:
        current_hour = current_time.strftime('%Y-%m-%dT%H:00')
        matching_temp = next(
            (temp for time, temp in historical_data if time.startswith(current_hour)),
            None
        )
        
        if matching_temp is not None:
            fluctuation = random.uniform(-0.5, 0.5)
            return round(matching_temp + fluctuation, 2)
    
    base_temp = 25.0
    latitude_factor = (device_info['location']['latitude'] - 37.7749) * 0.1
    base_temp += latitude_factor
    fluctuation = random.uniform(-2, 2)
    return round(base_temp + fluctuation, 2)

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"Successfully connected to MQTT broker with client ID: {MQTT_CLIENT_ID}")
        client.subscribe(MQTT_TOPIC)
    else:
        print(f"Failed to connect with result code: {rc}")

def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode('utf-8')
        print(f"Received message on {msg.topic}: {payload}")
    except Exception as e:
        print(f"Error processing message: {e}")

def on_publish(client, userdata, mid):
    print(f"Message {mid} published successfully")

def run_device(device_info, weather_fetcher):
    client = mqtt.Client(client_id=f"{MQTT_CLIENT_ID}-{device_info['mac']}")
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_publish = on_publish

    try:
        client.connect(MQTT_BROKER, MQTT_BROKER_PORT, 60)
        client.loop_start()

        while True:
            temperature = simulate_temperature(device_info, weather_fetcher)
            payload = {
                'device_id': device_info['mac'],
                'temperature': temperature,
                'location': device_info['location'],
                'timestamp': datetime.now().isoformat()
            }
            
            client.publish(device_info['topic'], json.dumps(payload))
            time.sleep(device_info['frequency'])

    except (KeyboardInterrupt, Exception) as e:
        print(f"Error in device {device_info['mac']}: {e}")
    finally:
        client.loop_stop()
        client.disconnect()
        return

if __name__ == "__main__":
    weather_fetcher = WeatherDataFetcher()
    
    devices = [
        {
            'mac': '00:00:00:00:00:01',
            'topic': 'iot/temp',
            'location': {
                'longitude': -122.4194,  # San Francisco
                'latitude': 37.7749
            },
            'frequency': 10
        },
        {
            'mac': '00:00:00:00:00:02',
            'topic': 'iot/temp',
            'location': {
                'longitude': -74.0060,  # New York
                'latitude': 40.7128
            },
            'frequency': 10
        }
    ]
    
    with ThreadPoolExecutor(max_workers=len(devices)) as executor:
        try:
            futures = [
                executor.submit(run_device, device, weather_fetcher) 
                for device in devices
            ]
            for future in futures:
                future.result()
        except KeyboardInterrupt:
            print("\nShutting down devices...")
