import json
import logging

import paho.mqtt.client as paho_mqtt

from monitoring.monitor import store_temperature_reading


logger = logging.getLogger(__name__)

def on_connect(client, userdata, flags, rc):
    app = userdata
    if rc == 0:
        logger.info("Connected to MQTT broker")
        client.subscribe(app.config['MQTT_TOPIC'])
    else:
        logger.warning("Failed to connect to MQTT broker: rc=%s", rc)

def on_message(client, userdata, msg):
    try:
        raw_payload = msg.payload.decode(errors="replace")
        if raw_payload == "Offline":
            return
        payload = json.loads(raw_payload)
        logger.debug("Received MQTT payload from %s: %s", msg.topic, payload)
        store_temperature_reading(payload)
    except json.JSONDecodeError as exc:
        logger.warning("Invalid JSON payload received on %s: %s", msg.topic, exc)
    except Exception as e:
        logger.exception("Error processing MQTT message: %s", e)

def start_mqtt_client(app):
    if not app.config.get('ENABLE_MQTT_CLIENT', False):
        logger.info("MQTT client disabled by configuration")
        return None

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
        return client
    except Exception as e:
        logger.exception("Error connecting to MQTT broker: %s", e)
        return None