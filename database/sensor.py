import random
import pandas as pd
import plotly.graph_objs as go
from datetime import datetime, timedelta
from database.gestion import database, USERS_DB, SENSORS_TABLE, DATA_TABLE, write, read, List, Tuple
from scrapper.super_secret import device_ID


sensor_name_for_initial_plot = device_ID


def generate_table(df) -> str:
    """Generate an HTML table from a Pandas DataFrame
    
    Parameters
    ----------
    df : Pandas DataFrame
        The DataFrame to convert to an HTML table
        
    Returns
    -------
    table_html : str
    """

    # Initialize the HTML table
    table_html =  '<h3 class="mb-4 my-2">Live data</h3>'
    table_html += '<table class="table">'
    
    # Add the table headers
    table_html += '<thead>'
    table_html += '<tr>'
    for col in df.columns:
        table_html += f'<th scope="col">{col}</th>'
    table_html += '</tr>'
    table_html += '</thead>'
    
    # Add the table rows
    table_html += '<tbody>'
    for i, row in df.iterrows():
        table_html += '<tr>'
        for col in df.columns:
            table_html += f'<td>{row[col]}</td>'
        table_html += '</tr>'
    table_html += '</tbody>'
    
    # Finalize the HTML table
    table_html += '</table>'
    
    return table_html


def update_plot(plot: dict, limit: int = None) -> dict:
    """Update the Plotly plot object with the latest sensor data.
    
    Args:
        plot: A dictionary containing the Plotly plot object for the sensor data.
        
    Returns:
        The updated Plotly plot object.
    """

    if limit: plot['limit'] = limit

    # Get the sensor data from the database
    plot['dataframe'] = get_sensor_data(plot['sensor_name'])

    # Create a Plotly line plot, set the labels, and add a horizontal line at the alert limit
    plot['fig'] = go.Figure(data=go.Scatter(x=plot['dataframe']['Time'], y=plot['dataframe']['Value'], mode='lines'))
    plot['fig'].update_layout(title=plot['sensor_name'], xaxis_title='Time', yaxis_title='Value')
    plot['fig'].add_hline(y=plot['limit'], line_width=1, line_dash="dash", line_color="red", name="limit")

    # Convert the Plotly figure to an HTML string
    plot['html'] = plot['fig'].to_html(full_html=False)

    # Update the table
    plot['table'] = generate_table(plot['dataframe'])
    
    return plot



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
        time_str = current_time.strftime('%Y-%m-%d %H:%M:%S')
        rssi = int(random.uniform(-100.0, 100.0))
        value = int(random.uniform(0.0, 15.0))
        data.append((sensor_id, rssi, time_str, value))
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


def get_sensor_alert_value(sensor_name: str) -> int:
    """Get the alert value of a sensor from the database.

    Args:
        connection: A sqlite3.Connection object.
        sensor_name: A string representing the name of the sensor.

    Returns:
        An integer representing the limit of the sensor.
    """
    connection = database.Connection(USERS_DB)
    sensor_id = get_sensor_id(connection, sensor_name)
    request = (f'SELECT alert_value FROM {SENSORS_TABLE} WHERE id=?', (sensor_id, ))
    result = read(connection, request)
    connection.close()

    if not result: return -1

    return result[0][0]



def get_sensor_data(sensor_name: str) -> List[Tuple]:
    """Get the data of a sensor from the database.

    Args:
        connection: A sqlite3.Connection object.
        sensor_id: An integer representing the ID of the sensor.

    Returns:
        A list of tuples representing the data of the sensor.
    """
    # Get the ID of the sensor
    connection = database.Connection(USERS_DB)
    sensor_id = get_sensor_id(connection, sensor_name)

    request = (f'SELECT rssi, time, value FROM {DATA_TABLE} WHERE sensor_id=?', (sensor_id, ))
    result = read(connection, request)
    connection.close()

    # Convert the data to a pandas DataFrame
    rssi_list  = [int(row[0]) for row in result]
    time_list  = [datetime.strptime(row[1], '%Y-%m-%d %H:%M:%S') for row in result]
    value_list = [float(row[2]) for row in result]

    df = pd.DataFrame({'rssi': rssi_list, 'Time': time_list, 'Value': value_list})

    return df


def add_sensor_data(sensor_name: int, rssi:int, time: str, value: int):
    """Add the data of a sensor to the database.

    Args:
        connection: A sqlite3.Connection object.
        sensor_id: An integer representing the ID of the sensor.
        data: A list of tuples containing the data of the sensor.
    """
    connection = database.Connection(USERS_DB)

    query = f'INSERT INTO {DATA_TABLE} (sensor_id, rssi, time, value) VALUES (?, ?, ?, ?)'
    sensor_id = get_sensor_id(connection, sensor_name)
    data = (sensor_id, rssi, time, value)

    write(connection, (query, data))
    connection.close()

    # Update the plot for the web interface (even if it's not for the current sensor)
    update_plot(plot)
    print(f"[INFO] : The data {data} of the sensor {sensor_id} has been added to the database.")



def set_sensor_alert_value(sensor_name: str, alert_value: int):
    """Set the alert value of a sensor in the database.

    Args:
        connection: A sqlite3.Connection object.
        sensor_id: An integer representing the ID of the sensor.
        alert_value: An integer representing the alert value of the sensor.
    """
    connection = database.Connection(USERS_DB)

    query = f'UPDATE {SENSORS_TABLE} SET alert_value=? WHERE id=?'
    sensor_id = get_sensor_id(connection, sensor_name)
    data = (alert_value, sensor_id)

    write(connection, (query, data))
    connection.close()

    # Update the plot for the web interface (even if it's not for the current sensor)
    update_plot(plot, alert_value)
    print("[INFO] : The alert value of the sensor", sensor_id, "has been updated in the database.")



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
    

# Plotly plot object for the sensor data
plot = {
    'sensor_name': sensor_name_for_initial_plot,
    'dataframe': '',
    'fig': '',
    'html': '',
    'limit': '',
    'table': ''
}