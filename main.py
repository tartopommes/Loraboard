from database.gestion import database, USERS_DB
from database.initDatabase import init_database, read_tables
from database.mail import get_all_emails, send_email, get_creds
from database.addUser import add_user
from database.deleteUser import delete_user
from server.website import app
from scrapper.scrapper import mqttc, public_address_url, public_address_port
from threading import Thread



# 🚧                                                                                     🚧
# 🚧               BEFORE RUNNING, GO TO GESTION AND PUT YOUR GMAIL ADRESS               🚧
# 🚧 FOR THE FIRST RUN, YOU WILL NEED TO ACCEPT THE GOOGLE AUTHORIZATION IN YOUR BROWSER 🚧
# 🚧                                                                                     🚧


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

    connection = database.connect(USERS_DB)
    try:
        #init_database(connection)
        read_tables(connection)
    except Exception as error:
        print("[ERROR] : SQL connection failed:", error)
    finally:
        connection.close()

    

    # create a new thread and pass the mqttc object as an argument
    thread = Thread(target=mqtt_thread, args=(mqttc,))
    # start the thread
    thread.start()

    # mqtt_thread(mqttc)

    # Run website
    app.run(debug=True)