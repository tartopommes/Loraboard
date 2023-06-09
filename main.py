"""
Main file of the project, it will initialise the database and the API credentials if they don't exist, and run the website and the scrapper.


:author: AlexisV, ErwanR, TheoD
:date: 2023-04-17
"""


from threading import Thread
from os.path import getsize, exists
from traceback import print_exc

from database.gestion import database, USERS_DB, API_TOKEN
from database.initDatabase import init_database, print_tables
### DISABLE MAIL ###
from database.mail import get_creds
from server.website import app
from scrapper.scrapper import run



# 🚧                                                                                     🚧
# 🚧               BEFORE RUNNING, GO TO GESTION AND PUT YOUR GMAIL ADRESS               🚧
# 🚧 FOR THE FIRST RUN, YOU WILL NEED TO ACCEPT THE GOOGLE AUTHORIZATION IN YOUR BROWSER 🚧
# 🚧                                                                                     🚧

""""""

if __name__ == "__main__":
    
    # Connection to the database
    connection = database.connect(USERS_DB)

    try:
        # Initialise the database if it doesn't exist, and print the tables
        if getsize(USERS_DB) == 0: 
            init_database(connection)
        else: 
            print("[INFO] : Database already exists")
        
        
        print_tables(connection)

        # Initialise the API credentials if they don't exist
        if not exists(API_TOKEN):
            ### DISABLE MAIL ###
            get_creds()
            print("[INFO] API credentials created")

    except Exception as error:
        print_exc()
        print("[ERROR] : SQL connection failed:", error)

    finally:
        connection.close()

    
    # create a new thread and pass the mqttc object as an argument
    thread = Thread(target=run)
    thread.start()

    # Run website
    app.run(debug=True, use_reloader=False, host='0.0.0.0')
