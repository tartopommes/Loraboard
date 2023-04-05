from database.gestion import database, USERS_DB
from database.initDatabase import init_database, print_tables
from database.sensor import update_plot, plot, get_sensor_alert_value
from server.website import app
from scrapper.scrapper import mqttc, public_address_url, public_address_port
from threading import Thread
from os.path import getsize
from traceback import print_exc



# 🚧                                                                                     🚧
# 🚧               BEFORE RUNNING, GO TO GESTION AND PUT YOUR GMAIL ADRESS               🚧
# 🚧 FOR THE FIRST RUN, YOU WILL NEED TO ACCEPT THE GOOGLE AUTHORIZATION IN YOUR BROWSER 🚧
# 🚧            s                                                                         🚧


def mqtt_thread(mqttc):
    # connect to the MQTT broker
    mqttc.connect(
        public_address_url, 
        port=public_address_port, 
        keepalive=60, 
        bind_address="")

    # loop wait for data
    while True:
        mqttc.loop()


if __name__ == "__main__":

    # Connection to the database
    connection = database.connect(USERS_DB)

    # Initialise the database if it doesn't exist, and print the tables
    
    try:
        if getsize(USERS_DB) == 0: init_database(connection)
        else: print("[INFO] : Database already exists")
        # print_tables(connection)
        update_plot(plot, get_sensor_alert_value(plot['sensor_name']))

    except Exception as error:
        print_exc()
        print("[ERROR] : SQL connection failed:", error)

    finally:
        connection.close()

    
    # create a new thread and pass the mqttc object as an argument
    thread = Thread(target=mqtt_thread, args=(mqttc,))
    thread.start()

    # Run website
    app.run(debug=True)
