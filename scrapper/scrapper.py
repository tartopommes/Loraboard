from scrapper.super_secret import *
import paho.mqtt.client as mqtt
import json
import base64
from database.sensor import add_sensor_data
from time import time, gmtime, strftime


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

    json_frame = json.loads(msg.payload)
    print("\n === Packet recevied! ===")

    # Check if the packet is a valid LoRaWAN packet
    if not (json_frame.get('end_device_ids') is None):
        if not (json_frame['end_device_ids'].get('device_id') is None):
            device_id = json_frame['end_device_ids']['device_id']
            print("End device ID :" + device_id)

    # Retrieve the payload if it exists
    if not (json_frame.get('uplink_message') is None):
        if not (json_frame['uplink_message'].get('frm_payload') is None):

            # Convert the payload to an int
            base64_payload = json_frame['uplink_message']['frm_payload']
            str_payload = base64.b64decode(base64_payload)
            int_payload = int.from_bytes(str_payload, 'big')
            
            print("Payload (debug) :" + str(int_payload))

            current_timestamp = time()
            delay_array = []
            
            # Extract the delays
            while int_payload != 0:
                temp = int_payload & 0xFFFFFFFF
                int_payload = int_payload >> 32

                int_value = ((temp >> 0) & 0xFF) << 24
                int_value += ((temp >> 8) & 0xFF) << 16
                int_value += ((temp >> 16) & 0xFF) << 8
                int_value += ((temp >> 24) & 0xFF) << 0
                delay_array.append(int_value)

                time_struct = gmtime(current_timestamp - int_value/1000)
                time_str = strftime('%Y-%m-%d %H:%M', time_struct)
                add_sensor_data(sensor_name=device_id, time=time_str, value=1.0) # time must have the following format: '%Y-%m-%d %H:%M'


            print("Payload (extracted) :" + str(delay_array))

            return

    print("Payload (debug) : None")
    print(json_frame.get('uplink_message'))
    print(json_frame['uplink_message'].get('frm_payload'))
    
    print(json.dumps(json_frame, indent=2))




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