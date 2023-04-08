import random
import pandas as pd
import plotly.graph_objs as go
from datetime import datetime, timedelta

from database.gestion import database, USERS_DB, SENSORS_TABLE, DATA_TABLE, write, read, List, Tuple, socketio
#from database.mail import send_mail_to_all

# Sensors object
class Sensor:
    def __init__(self, id, name, dataframe, fig, html_plot, alert_value, table, lat, long):
        self.id = id
        self.name = name
        self.dataframe = dataframe
        self.fig = fig
        self.html_plot = html_plot
        self.alert_value = alert_value
        self.table = table
        self.lat = lat
        self.long = long

    def __str__(self):
        return f"Sensor {self.id} ({self.name})"


def make_table(df) -> str:
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
    table_html =  '<h4 class="mb-4 my-2">Live data</h4>'
    table_html += '<div style="border-radius: 10px; background-color: #fafafa;">'
    table_html += '<table class="table">'
    
    # Add the table headers
    table_html += '<thead>'
    table_html += '<tr>'
    for col in df.columns:
        table_html += f'<th scope="col">{col}</th>'
    table_html += '</tr>'
    table_html += '</thead>'
    
    # Add the table rows (10 max) from the most recent to the oldest
    table_html += '<tbody>'
    for i, row in df.iloc[-1:-10:-1].iterrows():
        table_html += '<tr>'
        for col in df.columns:
            table_html += f'<td>{row[col]}</td>'
        table_html += '</tr>'
    table_html += '</tbody>'
    
    # Finalize the HTML table
    table_html += '</table>'
    table_html += '</div>'
    
    return table_html


def make_figure(df, sensor_name: str, limit: int) -> go.Figure:
    """Generate a Plotly figure from a Pandas DataFrame
    
    Parameters
    ----------
    df : Pandas DataFrame
        The DataFrame to convert to a Plotly figure
        
    Returns
    -------
    fig : Plotly Figure
    """

    # Create a Plotly line plot, set the labels, and add a horizontal line at the alert limit
    fig = go.Figure(
        data=go.Scatter(
            x=df['Time'], 
            y=df['Value'], 
            mode='markers',
            marker=dict(color='blue'),
            fill='tozeroy'),  # fill the area under the line
        layout=go.Layout(
            title=sensor_name,
            xaxis_title='Time',
            yaxis_title='People',
            margin=dict(l=0, r=10, t=75, b=0))
    )

    fig.add_hline(y=limit, line_width=1, line_dash="dash", line_color="red", name="limit")

    # Add range slider
    fig.update_layout(
        xaxis=dict(
            rangeselector=dict(
                buttons=list([
                    dict(count=1,
                        label="1m",
                        step="month",
                        stepmode="backward"),
                    dict(count=6,
                        label="6m",
                        step="month",
                        stepmode="backward"),
                    dict(count=1,
                        label="YTD",
                        step="year",
                        stepmode="todate"),
                    dict(count=1,
                        label="1y",
                        step="year",
                        stepmode="backward"),
                    dict(step="all")
                ])
            ),
            rangeslider=dict(
                visible=True
            ),
            type="date"
        )
    )
    
    return fig


def update_plot(sensor: Sensor, alert_value: int = None) -> Sensor:
    """Update the plot object with the sensor data from the database.

    Parameters
    ----------
    sensor : Sensor
        The sensor object to update
    limit : int, optional
        The alert limit to set, by default None

    Returns
    -------
    sensor : Sensor
        The updated sensor object
    """

    if alert_value:
        sensor.alert_value = alert_value
        set_sensor_alert_value(sensor.name, alert_value)

    # Get the sensor data from the database, then make a figure to html and make a table
    sensor.dataframe = get_sensor_data(sensor.name)
    sensor.fig = make_figure(sensor.dataframe, sensor.name, sensor.alert_value) 
    sensor.html_plot = sensor.fig.to_html(full_html=False)
    sensor.table = make_table(sensor.dataframe)

    socketio.emit('update', {'sensor_id': sensor.id, 'html_plot': sensor.html_plot, 'table': sensor.table})
    print('[INFO] Plot object updated')
    return sensor



def get_random_value(sensor_id, start_time = None, end_time = None) -> List[Tuple]:
    """Generate a random value between 0 and 15.
    
    Parameters
    ----------
    sensor_id : int
        The ID of the sensor
    start_time : datetime, optional
        The start time of the data, by default None
    end_time : datetime, optional
        The end time of the data, by default None
    
    Returns
    -------
    data : List[Tuple]
        A list of tuples containing the sensor ID, RSSI, time, and value
    """
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

    Parameters
    ----------
    connection : database.Connection
        The database connection
    sensor_name : str
        The name of the sensor

    Returns
    -------
    int
        The ID of the sensor

    Raises
    ------
    ValueError
        If the sensor name is not in the database

    Examples
    --------
    >>> get_sensor_id(connection, 'sensor1')
    1
    """
    request = (f'SELECT id FROM {SENSORS_TABLE} WHERE name=?', (sensor_name, ))
    result = read(connection, request)

    if not result: return -1

    return result[0][0]



def get_sensor_name_from_deveui(deveui: str) -> str:
    """Get the name of a sensor from the database.

    Args:
        deveui: A string representing the EUI of the sensor.

    Returns:
        A string representing the name of the sensor.
    """
    connection = database.Connection(USERS_DB)

    request = (f'SELECT name FROM {SENSORS_TABLE} WHERE deveui=?', (deveui, ))
    result = read(connection, request)

    connection.close()

    if not result: return None

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



def add_sensor_data(deveui: int, rssi:int, time: str, value: int):
    """Add the data of a sensor to the database.

    Args:
        sensor_id: An integer representing the ID of the sensor.
        rssi: An integer representing the RSSI of the sensor.
        data: A list of tuples containing the data of the sensor.
        value: An integer representing the value of the sensor.
    """
    SENSORS = get_sensors()
    # Prepare the query with the data for the database
    connection = database.Connection(USERS_DB)
    query = f'INSERT INTO {DATA_TABLE} (sensor_id, rssi, time, value) VALUES (?, ?, ?, ?)'

    sensor_name = get_sensor_name_from_deveui(deveui) # device id is the deveui
    sensor_id = get_sensor_id(connection, sensor_name)
    data = (sensor_id, rssi, time, value)
    
    # Add the data to the database
    write(connection, (query, data))
    connection.close()

    # Retrieve alert value from deveui in databse
    alert_value = get_sensor_alert_value(sensor_name)

    # If alert
    if float(value) >= float(alert_value):
        #send_mail_to_all("IoT Alert", f"The sensor {sensor_name} has exceeded the threshold {alert_value} with a value of {value}!")
        socketio.emit('alert', {
            'sensor_id': sensor_id,
            'message': f'''
                <div class="alert alert-warning alert-dismissible fade show" role="alert">
					<strong>Treshold alert!</strong> The {sensor_name} sensor value (<strong>{value}</strong>) has exceeded the threshold you set (<strong>{alert_value}</strong>).
					<button type="button" class="close" data-dismiss="alert" aria-label="Close">
					  	<span aria-hidden="true">&times;</span>
					</button>
				</div>
            '''
        })
        print('[INFO]: Mail alert sent!')

    # Update the plot for the web interface (even if it's not for the current sensor)
    update_plot(SENSORS[sensor_id-1])
    print(f"[INFO] The data {data} of the sensor {sensor_id} has been added to the database.")



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

    print("[INFO] The alert value of the sensor", sensor_id, "has been updated in the database.")



def get_sensors():
    """Get all the sensors from the database.

    Returns:
        A list of Sensor objects.
    """
    connection = database.Connection(USERS_DB)
    result = read(connection, f'SELECT id, name, alert_value, lat, long FROM {SENSORS_TABLE}')
    connection.close()

    sensors = []
    for row in result: # We only want the 1st 3 items for the demo
        sensor_id = row[0]
        sensor_name = row[1]
        alert_value = row[2]
        dataframe = get_sensor_data(sensor_name)
        fig = make_figure(dataframe, sensor_name, alert_value)
        html_plot = fig.to_html(full_html=False)
        table = make_table(dataframe)
        lat = row[3]
        long = row[4]
        sensor = Sensor(sensor_id, sensor_name, dataframe, fig, html_plot, alert_value, table, lat, long)
        sensors.append(sensor)

    return sensors