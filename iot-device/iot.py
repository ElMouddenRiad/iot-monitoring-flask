import paho.mqtt.client as mqtt
import random
import time
from concurrent.futures import ThreadPoolExecutor

MQTT_BROKER = "broker.hivemq.com"
MQTT_CLIENT_ID = "iot-device"
MQTT_USERNAME = "bakr"
MQTT_PASSWORD = "bakr" 
MQTT_BROKER_PORT = 1883
MQTT_TOPIC = "iot/temp"

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

def simulate_temperature(device_info=None):
    """
    Simulate temperature between 20-30°C with random fluctuations
    Takes into account device location for more realistic simulation
    """
    base_temp = 25.0
    if device_info and 'location' in device_info:
        # Adjust base temperature based on latitude
        latitude_factor = (device_info['location']['latitude'] - 37.7749) * 0.1
        base_temp += latitude_factor
    
    fluctuation = random.uniform(-2, 2)  # Smaller fluctuations for more realistic data
    return round(base_temp + fluctuation, 2)

def run_device(device_info):
    client = mqtt.Client(client_id=f"{MQTT_CLIENT_ID}-{device_info['mac']}")
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_publish = on_publish

    try:
        client.connect(MQTT_BROKER, MQTT_BROKER_PORT, 60)
        client.loop_start()

        while True:
            temperature = simulate_temperature(device_info)
            payload = {
                'device_id': device_info['mac'],
                'temperature': temperature,
                'location': device_info['location'],
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            # Convert payload to string for publishing
            payload_str = str(payload)
            client.publish(device_info['topic'], payload_str)
            time.sleep(device_info['frequency'])

    except (KeyboardInterrupt, Exception) as e:
        print(f"Error in device {device_info['mac']}: {e}")
    finally:
        client.loop_stop()
        client.disconnect()
        return  # Ensure the thread exits

if __name__ == "__main__":
    devices = [
        {
            'mac': '00:00:00:00:00:01',
            'topic': 'iot/temp',
            'location':{
                'longitude': -122.4194,
                'latitude': 37.7749
            },
            'frequency': 15   
        },
        {
            'mac': '00:00:00:00:00:02',
            'topic': 'iot/temp',
            'location':{
                'longitude': -122.4194,
                'latitude': 37.7749
            },
            'frequency': 15   
        }
    ]
    
    for device in devices:
        run_device(device)
