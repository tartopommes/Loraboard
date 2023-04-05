from database.gestion import database, USERS_DB, USERS_TABLE, SENSORS_TABLE, DATA_TABLE, write, read
from hashlib import sha256
from database.printDatabase import print_tables
from database.sensor import get_sensor_id, get_random_value
# from sys import argv
from traceback import print_exc
from scrapper.super_secret import device_ID



def create_tables(connection):
    """Create the tables in the database."""
    
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
                      name          text NOT NULL,
                      alert_value   text NOT NULL
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
                      unique(time, value)
                  );"""
    write(connection, request)
    connection.commit()
    



def fill_user(connection):
    """Fill the users table with some data."""

    # Add some users into users table
    request = f'INSERT INTO {USERS_TABLE} (email, username, password_hash) values(?, ?, ?)'
    data = [
        ('alexis.vandemoortele.av@gmail.com', 'a', sha256('a'.encode()).hexdigest()) ]
    write(connection, (request, data), many=True)

    # Add some sensors into sensors table
    request = f'INSERT INTO {SENSORS_TABLE} (name, alert_value) values(?, ?)'
    data = [ ('test_sensor', '14.7'), (device_ID, '5.0') ]
    write(connection, (request, data), many=True)

    # Add some data into data table
    request = f'INSERT INTO {DATA_TABLE} (sensor_id, rssi, time, value) values(?, ?, ?, ?)'
    sensor_id = get_sensor_id(connection, 'test_sensor')
    data = get_random_value(sensor_id)
    write(connection, (request, data), many=True)



def init_database(connection):
    """Initialise the database."""
    connection = database.connect(USERS_DB)
    try:
        create_tables(connection)
        fill_user(connection)
    except Exception as error:
        print_exc()
        print("[ERROR] : SQL connection failed, the database couldn't be initialised:", error)
    finally:
        connection.close()



def main():
    """Main function."""
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

    return



if __name__ == "__main__":
    main()
