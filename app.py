from flask import Flask, jsonify
from flask_mqtt import Mqtt

app = Flask(__name__)
app.config['MQTT_BROKER_URL'] = 'broker.hivemq.com'
app.config['MQTT_BROKER_PORT'] = 1883
app.config['MQTT_USERNAME'] = ''
app.config['MQTT_PASSWORD'] = ''
app.config['MQTT_REFRESH_TIME'] = 1.0  # refresh time in seconds

mqtt = Mqtt(app)
MQTT_TOPIC = 'iot/temp'
@mqtt.on_connect()
def connect_callback(client, userdata, flags, rc):
    if rc == 0:
        print('Connected with result code '+str(rc))
        mqtt.subscribe(MQTT_TOPIC)
    else:
        print('Failed to connect with result code '+str(rc))

@mqtt.on_connect()
def connect_callback(client, userdata, flags, rc):
    print('Connected with result code '+str(rc))

@mqtt.on_disconnect()
def disconnect_callback(client, userdata, rc):
    print('Disconnected with result code '+str(rc))

@mqtt.on_message()
def message_callback(client,userdate, msg):
    print(msg.topic+' '+str(msg.payload))
    if msg.topic == MQTT_TOPIC:
        print('Published: '+msg.topic+' '+str(msg.payload.decode('utf-8')))
        print(f'message received: {msg.topic} {msg.payload}')
        mqtt.publish(MQTT_TOPIC, msg.payload)
    else:
        return jsonify(msg.topic)

@mqtt.on_publish()
def publish_callback(client, msg):
    print(msg.topic+' '+str(msg.payload))
    mqtt.publish(msg.topic, msg.payload)

@app.route('/mqtt')
def mqtt():
    return jsonify(mqtt.messages)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)