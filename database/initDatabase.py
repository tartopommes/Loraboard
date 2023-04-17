"""This module contains the functions related to the database initialization."""

from database.gestion import database, USERS_DB, USERS_TABLE, SENSORS_TABLE, DATA_TABLE, write
from hashlib import sha256
from database.printDatabase import print_tables
from traceback import print_exc



def create_tables(connection: database.Connection):
    """Create the tables in the database.
    
    Args:
        connection (database.Connection): a SQLite3 database connection object"""
    
    # if len(argv) == 4 and argv[3]:
    #     if argv[3] == 'reset':
    #         print('[INFO] The database has been reset')
    #         cursor.execute('DROP TABLE IF EXISTS users')

    write(connection, f'DROP TABLE IF EXISTS {USERS_TABLE}')
    write(connection, f'DROP TABLE IF EXISTS {SENSORS_TABLE}')
    write(connection, f'DROP TABLE IF EXISTS {DATA_TABLE}')
    print('[INFO] The database has been reset') 
    
    # Create the users table
    request = f"""CREATE TABLE IF NOT EXISTS {USERS_TABLE} (
                      id            integer PRIMARY KEY,
                      email         text NOT NULL,
                      username      text NOT NULL,
                      password_hash text NOT NULL
                  );"""
    write(connection, request)
    connection.commit()

    # Create the sensors table
    request = f"""CREATE TABLE IF NOT EXISTS {SENSORS_TABLE} (
                      id            integer PRIMARY KEY,
                      deveui        text NOT NULL,
                      name          text NOT NULL,
                      alert_value   text NOT NULL,
                      lat           real NOT NULL,
                      long          real NOT NULL
                  );"""
    write(connection, request)
    connection.commit()

    # Create the data table
    request = f"""CREATE TABLE IF NOT EXISTS {DATA_TABLE} (
                      id            integer PRIMARY KEY,
                      sensor_id     text NOT NULL,
                      rssi          text NOT NULL,
                      time          text NOT NULL,
                      value         text NOT NULL,
                      unique(sensor_id, time, value)
                  );"""
    write(connection, request)
    connection.commit()




def fill_user(connection: database.Connection):
    """Fill the users table with some data.
    
    Args:
        connection (database.Connection): a SQLite3 database connection object"""

    # Add some users into users table
    request = f'INSERT INTO {USERS_TABLE} (email, username, password_hash) values(?, ?, ?)'
    data = [
        ('alexis.vandemoortele.av@gmail.com', 'a', sha256('a'.encode()).hexdigest()) ]
    write(connection, (request, data), many=True)

    # Add some sensors into sensors table
    request = f'INSERT INTO {SENSORS_TABLE} (deveui, name, alert_value, lat, long) values(?, ?, ?, ?, ?)'
    data = [ 
        # ('test_sensor',          'test_sensor', '14', 48.420258, -71.048619),
        ('eui-a8610a34351b7a0f', 'Newton',      '5' , 48.426258, -71.058619),
        ('eui-aaaaaabbbbbbbbbb', 'Racine',      '6' , 48.420672, -71.043423),
        ('eui-abababababababab', 'Chenevert',   '7' , 48.427633, -71.061468),
    ]
    write(connection, (request, data), many=True)

    # Add some fake data into data table for test_sensor sensor
    # request = f'INSERT INTO {DATA_TABLE} (sensor_id, rssi, time, value) values(?, ?, ?, ?)'
    # sensor_id = get_sensor_id(connection, 'test_sensor')
    # data = get_random_value(sensor_id)
    # write(connection, (request, data), many=True)



def init_database(connection: database.Connection):
    """Initialise the database.
    
    Args:
        connection (database.Connection): a SQLite3 database connection object"""
    connection = database.connect(USERS_DB)
    try:
        create_tables(connection)
        fill_user(connection)
    except Exception as error:
        print_exc()
        print("[ERROR] : SQL connection failed, the database couldn't be initialised:", error)
    finally:
        connection.close()



if __name__ == "__main__":
    """Initialise the database."""
    connection = database.connect(USERS_TABLE) # create if doesn't exist

    try:
        create_tables(connection)
        fill_user(connection)
        print_tables(connection)

    except Exception as error:
        print_exc()
        print("[ERROR] : SQL connection failed, the database couldn't be initialised:", error)

    finally:
        connection.close()