from scrapper.super_secret import *

import paho.mqtt.client as mqtt
import json
import base64
from database.sensor import add_sensor_data, get_sensor_name_from_deveui
from datetime import datetime
from pytz import timezone

def on_connect(client: mqtt.Client, userdata, flags, rc: int):
    """The callback for when the client receives a CONNACK response from the server."""
    if   rc == 0: print('[MQTT] Connection successful', flush=True)
    elif rc == 1: print('[MQTT] Connection refused - incorrect protocol version', flush=True)
    elif rc == 2: print('[MQTT] Connection refused - invalid client identifier', flush=True)
    elif rc == 3: print('[MQTT] Connection refused - server unavailable', flush=True)
    elif rc == 4: print('[MQTT] Connection refused - bad username or password', flush=True)
    elif rc == 5: print('[MQTT] Connection refused - not authorised', flush=True)
    #6-255: Currently unused.
    client.subscribe('#', qos=0)

# https://pypi.org/project/paho-mqtt/#callbacks
def on_message(client: mqtt.Client, userdata, msg: str):
    """The callback for when a PUBLISH message is received from the server."""

    # Return -1 if the packet is invalid
    def invalid_packet(json_frame, obj:str) -> int:
        """Print the invalid packet and return -1."""
        print(f"Invalid packet received, {obj} is None payload:\n", json.dumps(json_frame, indent=2))
        return None

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
    if not end_device_ids: return
    
    device_id = get_field_from_json(end_device_ids, 'device_id')
    if not device_id: return
    print("End device ID :" + device_id)

    uplink_message = get_field_from_json(json_frame, 'uplink_message')
    if not uplink_message: return

    frm_payload = get_field_from_json(uplink_message, 'frm_payload')
    if not frm_payload: return

    rx_metadata = get_field_from_json(uplink_message, 'rx_metadata')
    if not rx_metadata: return

    rssi = get_field_from_json(rx_metadata[0], 'rssi')
    if not rssi: return

    # Converte 4 bytes to int
    decoded_payload = int.from_bytes(base64.b64decode(frm_payload), 'big')
    # Extract and reconstruct in reverse (shiffting) the individual bytes of the decoded payload to obtain the final payload value
    payload_value =  ((decoded_payload >> 0)  & 0xFF) << 24
    payload_value += ((decoded_payload >> 8)  & 0xFF) << 16
    payload_value += ((decoded_payload >> 16) & 0xFF) << 8 
    payload_value += ((decoded_payload >> 24) & 0xFF) << 0 
    print("Payload (converted) :" + str(payload_value))

    fake_db_upload(deveui=device_id, rssi=rssi, value=payload_value) # time must have the following format: '%Y-%m-%d %H:%M'

test_sensor_rssi = "0"
test_sensor_payload_value = 0
a8610a34351b7a0f_rssi = "0"
a8610a34351b7a0f_payload_value = 0
aaaaaabbbbbbbbbb_rssi = "0"
aaaaaabbbbbbbbbb_payload_value = 0
abababababababab_rssi = "0"
abababababababab_payload_value = 0

def fake_db_upload(deveui:str, rssi:str, value:int):
    global test_sensor_rssi, test_sensor_payload_value, a8610a34351b7a0f_rssi, a8610a34351b7a0f_payload_value, aaaaaabbbbbbbbbb_rssi, aaaaaabbbbbbbbbb_payload_value, abababababababab_rssi, abababababababab_payload_value
    if deveui == 'test_sensor':
        test_sensor_rssi = rssi
        test_sensor_payload_value = value
    elif deveui == 'eui-a8610a34351b7a0f':
        a8610a34351b7a0f_rssi = rssi
        a8610a34351b7a0f_payload_value = value
    elif deveui == 'eui-aaaaaabbbbbbbbbb':
        aaaaaabbbbbbbbbb_rssi = rssi
        aaaaaabbbbbbbbbb_payload_value = value
    elif deveui == 'eui-abababababababab':
        abababababababab_rssi = rssi
        abababababababab_payload_value = value
    else:
        print(f"Unknown device eui : {deveui}")
        
def real_db_upload():
    global test_sensor_rssi, test_sensor_payload_value, a8610a34351b7a0f_rssi, a8610a34351b7a0f_payload_value, aaaaaabbbbbbbbbb_rssi, aaaaaabbbbbbbbbb_payload_value, abababababababab_rssi, abababababababab_payload_value
    time = datetime.now(timezone('America/Montreal')).strftime('%Y-%m-%d %H:%M:%S') # TODO : get the time from the packet with received_at obj.
            
    add_sensor_data(deveui='test_sensor', rssi=test_sensor_rssi, time=time, value=test_sensor_payload_value)
    add_sensor_data(deveui='eui-a8610a34351b7a0f', rssi=a8610a34351b7a0f_rssi, time=time, value=a8610a34351b7a0f_payload_value)
    add_sensor_data(deveui='eui-aaaaaabbbbbbbbbb', rssi=aaaaaabbbbbbbbbb_rssi, time=time, value=aaaaaabbbbbbbbbb_payload_value)
    add_sensor_data(deveui='eui-abababababababab', rssi=abababababababab_rssi, time=time, value=abababababababab_payload_value)

    test_sensor_rssi = "0"
    test_sensor_payload_value = 0
    a8610a34351b7a0f_rssi = "0"
    a8610a34351b7a0f_payload_value = 0
    aaaaaabbbbbbbbbb_rssi = "0"
    aaaaaabbbbbbbbbb_payload_value = 0
    abababababababab_rssi = "0"
    abababababababab_payload_value = 0


def run():
    
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
    
    # connect to the MQTT broker
    mqttc.connect(
        public_address_url, 
        port=public_address_port, 
        keepalive=60, 
        bind_address="")

    import time
    last_time = time.time()
    DELAY = 10

    # loop wait for data
    while True:
        if (last_time + DELAY < time.time()):
            real_db_upload()
            last_time = time.time()

        mqttc.loop()

        # try:
        #     mqttc.loop()
        # except Exception as error:
        #     print("[ERROR] : MQTT eror:", error, "Continuing loop...")    

if __name__ == "__main__":
    run()