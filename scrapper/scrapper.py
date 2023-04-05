from scrapper.super_secret import *

import paho.mqtt.client as mqtt
import json
import base64
from database.sensor import add_sensor_data
from datetime import datetime
from pytz import timezone

def on_connect(client: mqtt.Client, userdata, flags, rc: int):
    """The callback for when the client receives a CONNACK response from the server."""
    if   rc == 0: print('Connection successful', flush=True)
    elif rc == 1: print('Connection refused - incorrect protocol version', flush=True)
    elif rc == 2: print('Connection refused - invalid client identifier', flush=True)
    elif rc == 3: print('Connection refused - server unavailable', flush=True)
    elif rc == 4: print('Connection refused - bad username or password', flush=True)
    elif rc == 5: print('Connection refused - not authorised', flush=True)
    #6-255: Currently unused.
    client.subscribe('#', qos=0)



# https://pypi.org/project/paho-mqtt/#callbacks
def on_message(client: mqtt.Client, userdata, msg: str):
    """The callback for when a PUBLISH message is received from the server."""

    # Return -1 if the packet is invalid
    def invalid_packet(json_frame, obj:str) -> int:
        """Print the invalid packet and return -1."""
        print(f"Invalid packet received, {obj} is None payload:\n", json.dumps(json_frame, indent=2))
        return -1

    def get_field_from_json(json_object, field: str) -> str:
        """Get the field from the json object."""
        json_field = json_object.get(field)
        if not json_field: return invalid_packet(json_object, field)
        return json_field

    # Retrieve the data from the packet as a json object
    json_frame = json.loads(msg.payload)
    print("\n === Packet recevied! ===")

    # Check if the following fields are present in the packet
    end_device_ids = get_field_from_json(json_frame, 'end_device_ids')
    device_id = get_field_from_json(end_device_ids, 'device_id')
    print("End device ID :" + device_id)

    uplink_message = get_field_from_json(json_frame, 'uplink_message')
    frm_payload = get_field_from_json(uplink_message, 'frm_payload')
    rx_metadata = get_field_from_json(uplink_message, 'rx_metadata')
    rssi = get_field_from_json(rx_metadata[0], 'rssi')

    # Converte 4 bytes to int
    decoded_payload = int.from_bytes(base64.b64decode(frm_payload), 'big')
    # Extract and reconstruct in reverse (shiffting) the individual bytes of the decoded payload to obtain the final payload value
    payload_value =  ((decoded_payload >> 0)  & 0xFF) << 24
    payload_value += ((decoded_payload >> 8)  & 0xFF) << 16
    payload_value += ((decoded_payload >> 16) & 0xFF) << 8 
    payload_value += ((decoded_payload >> 24) & 0xFF) << 0 
    print("Payload (converted) :" + str(payload_value))

    time = datetime.now(timezone('America/Montreal')).strftime('%Y-%m-%d %H:%M:%S') # TODO : get the time from the packet with received_at obj.
    add_sensor_data(sensor_name=device_id, rssi=rssi, time=time, value=payload_value) # time must have the following format: '%Y-%m-%d %H:%M'

    # try:
    #     add_sensor_data(sensor_name=device_id, rssi=rssi, time=time, value=payload_value) # time must have the following format: '%Y-%m-%d %H:%M'
    # except Exception as e:
    #     print("[ERROR] Data already exist:", e)



### Create a client instance
mqttc = mqtt.Client(
    client_id=Username_ssh, 
    clean_session=True, 
    userdata=None, 
    protocol=mqtt.MQTTv311,
    transport="tcp"
)

mqttc.on_connect = on_connect
mqttc.on_message = on_message

mqttc.username_pw_set(Username, password=Password)

if __name__ == "__main__":
    ### Connect to broker
    mqttc.connect(
        public_address_url, 
        port=public_address_port, 
        keepalive=60, 
        bind_address=""
    )

    ### Main loop
    run = True
    while run:

        # loop wait for data
        mqttc.loop()