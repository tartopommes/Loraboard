import random
from datetime import datetime, timedelta
import pandas as pd
from database.gestion import database, USERS_DB, USERS_TABLE, SENSORS_TABLE, DATA_TABLE, write, read, List, Tuple


def get_random_value(sensor_id, start_time = None, end_time = None) -> List[Tuple]:
    """Generate a random value between 0 and 15."""
    # Define the start and end times for the data
    if start_time is None:
        start_time = datetime(2023, 4, 1, 10, 0) # 2023-04-01 00:00:00
    if end_time is None:
        end_time = datetime(2023, 4, 1, 13, 25) # 2023-04-01 13:25:00

    # Define the time step for the data (every 5 minutes)
    time_step = timedelta(minutes=5)

    # Generate the data as a list of tuples
    data = []
    current_time = start_time
    while current_time <= end_time:
        time_str = current_time.strftime('%Y-%m-%d %H::%S')
        value = round(random.uniform(0.0, 15.0), 1)
        data.append((sensor_id, time_str, value))
        current_time += time_step
    return data


def get_sensor_id(connection: database.Connection, sensor_name: str) -> int:
    """Get the ID of a sensor from the database.

    Args:
        connection: A sqlite3.Connection object.
        sensor_name: A string representing the name of the sensor.

    Returns:
        An integer representing the ID of the sensor.
    """
    request = (f'SELECT id FROM {SENSORS_TABLE} WHERE name=?', (sensor_name, ))
    result = read(connection, request)

    if not result: return -1

    return result[0][0]



def get_sensor_data(connection: database.Connection, sensor_name: str) -> List[Tuple]:
    """Get the data of a sensor from the database.

    Args:
        connection: A sqlite3.Connection object.
        sensor_id: An integer representing the ID of the sensor.

    Returns:
        A list of tuples containing the data of the sensor.
    """

    # Get the ID of the sensor
    sensor_id = get_sensor_id(connection, sensor_name)
    request = (f'SELECT time, value FROM {DATA_TABLE} WHERE sensor_id=?', (sensor_id, ))
    result = read(connection, request)

    # Convert the data to a pandas DataFrame
    time_list = [datetime.strptime(t[0], '%Y-%m-%d %H:%M:%S') for t in result]
    value_list = [float(t[1]) for t in result]

    df = pd.DataFrame({'Time': time_list, 'Value': value_list})

    return df


def add_sensor_data(sensor_name: int, time: str, value: float):
    """Add the data of a sensor to the database.

    Args:
        connection: A sqlite3.Connection object.
        sensor_id: An integer representing the ID of the sensor.
        data: A list of tuples containing the data of the sensor.
    """
    connection = database.Connection(USERS_DB)

    query = f'INSERT INTO {DATA_TABLE} (sensor_id, time, value) VALUES (?, ?, ?)'
    sensor_id = get_sensor_id(connection, sensor_name)
    data = (sensor_id, time, value) # Add the sensor ID to the data (time, value)

    write(connection, (query, data))

    connection.close()
    print("[INFO] : The data of the sensor", sensor_id, "has been added to the database.")



def simulate_received_date(connection: database.Connection):
    """Simulate the reception of data from a sensor."""

    # Get the last data of the sensor
    sensor_name = 'test_sensor'

    # Generate the new data
    sensor_last_data = get_sensor_data(connection, sensor_name).iloc[-1]
    last_time = sensor_last_data['Time'].to_pydatetime()
    new_time = last_time + timedelta(minutes=5)

    # Add the data to the database
    add_sensor_data(sensor_name,
                    new_time.strftime('%Y-%m-%d %H:%M:%S'), 
                    round(random.uniform(0.0, 15.0), 1))