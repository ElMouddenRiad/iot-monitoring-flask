import paho.mqtt.client as paho_mqtt
import json
import threading
from monitoring.monitor import store_temperature_reading

def on_connect(client, userdata, flags, rc):
    app = userdata
    if rc == 0:
        print(f"Connected to MQTT Broker!")
        client.subscribe(app.config['MQTT_TOPIC'])
    else:
        print(f"Failed to connect, return code {rc}")

def on_message(client, userdata, msg):
    try:
        if msg.payload.decode() == "Offline":
            return
        payload = json.loads(msg.payload.decode())
        print(f"Received `{payload}` from `{msg.topic}` topic")
        store_temperature_reading(payload)
    except Exception as e:
        print(f"Error processing message: {e}")

def start_mqtt_client(app):
    client = paho_mqtt.Client(
        client_id=app.config['MQTT_CLIENT_ID'], 
        clean_session=True,
        userdata=app
    )
    
    client.on_connect = on_connect
    client.on_message = on_message
    
    client.will_set(app.config['MQTT_TOPIC'], payload="Offline", qos=1, retain=True)
    client.reconnect_delay_set(min_delay=1, max_delay=30)
    
    try:
        client.connect(app.config['MQTT_BROKER_URL'], app.config['MQTT_BROKER_PORT'], keepalive=30)
        client.loop_start()
    except Exception as e:
        print(f"Error connecting to MQTT broker: {e}") 