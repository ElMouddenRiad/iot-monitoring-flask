import paho.mqtt.client as mqtt
import random
import time
from concurrent.futures import ThreadPoolExecutor
import requests
from datetime import datetime, timedelta
import json
import logging
import psycopg2
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Configuration
CONFIG = {
    'MQTT_BROKER': "test.mosquitto.org",
    'MQTT_PORT': 1883,
    'MQTT_TOPIC': "iot/temp",
    'MQTT_QOS': 1,
    'RECONNECT_DELAY': 5,
    'MAX_RETRIES': 3,
    'DB_URL': 'postgresql://admin:admin123@localhost:5432/iot_platform'
}

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_active_devices():
    """Fetch active devices from PostgreSQL database"""
    engine = create_engine(CONFIG['DB_URL'])
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Query for active devices
        result = session.execute(text("SELECT * FROM devices WHERE status = 'active'"))
        devices = []
        for row in result:
            devices.append({
                'mac': row.mac,
                'name': row.name,
                'topic': 'iot/temp',
                'location': {
                    'latitude': row.latitude,
                    'longitude': row.longitude
                },
                'frequency': 40  # Default frequency
            })
        return devices
    except Exception as e:
        logging.error(f"Error fetching devices from database: {e}")
        return []
    finally:
        session.close()

class WeatherDataFetcher:
    def __init__(self):
        self.base_url = "https://api.open-meteo.com/v1/forecast"
        self.cache = {}
        self.cache_duration = timedelta(hours=1)
        self.last_update = {}
        
    def get_historical_data(self, latitude, longitude, start_date, end_date):
        cache_key = f"{latitude},{longitude},{start_date},{end_date}"
        
        if (cache_key in self.cache and 
            cache_key in self.last_update and 
            datetime.now() - self.last_update[cache_key] < self.cache_duration):
            return self.cache[cache_key]
        
        try:
            response = requests.get(self.base_url, params={
                'latitude': latitude,
                'longitude': longitude,
                'hourly': 'temperature_2m',
                'timezone': 'auto',
                'past_days': 1,
                'forecast_days': 1
            }, timeout=10)
            
            response.raise_for_status()
            data = response.json()
            
            processed_data = list(zip(data['hourly']['time'], data['hourly']['temperature_2m']))
            self.cache[cache_key] = processed_data
            self.last_update[cache_key] = datetime.now()
            
            return processed_data
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching weather data: {e}")
            return self.cache.get(cache_key)

def simulate_temperature(device_info, weather_fetcher):
    if not device_info or 'location' not in device_info:
        return 25.0
        
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

def run_device(device_info, weather_fetcher):
    client = mqtt.Client(client_id=f"{CONFIG['MQTT_TOPIC']}-{device_info['mac']}")
    
    def on_disconnect(client, userdata, rc):
        if rc != 0:
            logging.warning(f"Unexpected disconnection. Attempting to reconnect...")
            time.sleep(CONFIG['RECONNECT_DELAY'])
            client.reconnect()

    client.on_connect = lambda c,u,f,rc: logging.info(f"Connected with result code {rc}")
    client.on_disconnect = on_disconnect
    client.on_publish = lambda c,u,m: logging.debug(f"Message {m} published")

    retries = 0
    while retries < CONFIG['MAX_RETRIES']:
        try:
            client.connect(CONFIG['MQTT_BROKER'], CONFIG['MQTT_PORT'], 60)
            client.loop_start()
            break
        except Exception as e:
            retries += 1
            logging.error(f"Connection attempt {retries} failed: {e}")
            if retries == CONFIG['MAX_RETRIES']:
                logging.error("Max retries reached. Exiting.")
                return
            time.sleep(CONFIG['RECONNECT_DELAY'])

    try:
        while True:
            temperature = simulate_temperature(device_info, weather_fetcher)
            payload = {
                'device_id': device_info['mac'],
                'temperature': temperature,
                'location': device_info['location'],
                'timestamp': datetime.now().isoformat()
            }
            
            result = client.publish(
                device_info['topic'], 
                json.dumps(payload), 
                qos=CONFIG['MQTT_QOS']
            )
            
            if result.rc == 0:
                logging.info(f"Message published successfully: {payload}")
            else:
                logging.error(f"Failed to publish message. RC: {result.rc}")
            
            time.sleep(device_info['frequency'])

    except KeyboardInterrupt:
        logging.info(f"Shutting down device {device_info['mac']}")
    except Exception as e:
        logging.error(f"Error in device {device_info['mac']}: {e}")
    finally:
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    weather_fetcher = WeatherDataFetcher()
    
    while True:
        try:
            # Fetch active devices from database
            devices = get_active_devices()
            
            if not devices:
                logging.info("No active devices found. Waiting before retry...")
                time.sleep(30)
                continue
                
            logging.info(f"Starting simulation for {len(devices)} active devices")
            
            with ThreadPoolExecutor(max_workers=len(devices)) as executor:
                futures = [
                    executor.submit(run_device, device, weather_fetcher) 
                    for device in devices
                ]
                for future in futures:
                    future.result()
                    
        except KeyboardInterrupt:
            logging.info("\nShutting down all devices...")
            break
        except Exception as e:
            logging.error(f"Error in main loop: {e}")
            time.sleep(CONFIG['RECONNECT_DELAY'])
