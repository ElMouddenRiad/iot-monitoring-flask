import paho.mqtt.client as mqtt
import random
import time
from concurrent.futures import ThreadPoolExecutor

MQTT_BROKER = "broker.hivemq.com"
MQTT_CLIENT_ID = "iot-device"
# MQTT_USERNAME = "bakr"
# MQTT_PASSWORD = "bakr"
MQTT_BROKER_PORT = 1883
MQTT_TOPIC = "iot/temp"

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload))

def on_publish(client, userdata, mid):
    print("Message "+str(mid)+" sent")

def simulate_temperature():
    """Simulate temperature between 20-30°C with random fluctuations"""
    base_temp = 25.0
    return round(base_temp + random.uniform(-5, 5), 2)

def main():
    client = mqtt.Client(client_id=MQTT_CLIENT_ID)
    # client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_publish = on_publish

    try:
        client.connect(MQTT_BROKER, MQTT_BROKER_PORT, 60)
        client.loop_start()

        while True:
            temperature = simulate_temperature()
            payload = f"{temperature}"
            client.publish(MQTT_TOPIC, payload)
            time.sleep(5)

    except KeyboardInterrupt:
        print("\nDisconnecting from broker")
        client.disconnect()
        client.loop_stop()

if __name__ == "__main__":
    devices = [
        {
            'mac': '00:00:00:00:00:01',
            'topic': 'iot/temp',
            'location':{
                'longitude': -122.4194,
                'latitude': 37.7749
            },
            'frequency': 60   
        },
        {
            'mac': '00:00:00:00:00:02',
            'topic': 'iot/temp',
            'location':{
                'longitude': -122.4194,
                'latitude': 37.7749
            },
            'frequency': 60   
        }
    ]
    with ThreadPoolExecutor() as executor:
        executor.submit(main)