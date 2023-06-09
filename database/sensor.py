"""This module contains the functions related to the sensors.
Sensor object and functions to manage the sensors in the database."""

import random
import base64
import pandas as pd
import plotly.graph_objs as go
import plotly.io as pio
from datetime import datetime, timedelta

from database.gestion import database, USERS_DB, SENSORS_TABLE, DATA_TABLE, write, read, List, Tuple, socketio
### DISABLE MAIL ###
from database.mail import send_mail_to_all

# Sensors object
class Sensor:
    """Sensor object.
    
    Attributes:
        id (int): Sensor id.
        name (str): Sensor name.
        dataframe (pandas.DataFrame): Dataframe containing the data of the sensor.
        fig (plotly.graph_objs.Figure): Plotly figure.
        html_plot (str): Plotly figure in html format.
        alert_value (float): Alert value of the sensor.
        table (str): Table containing the data of the sensor.
        lat (float): Latitude of the sensor.
        long (float): Longitude of the sensor.
        
    Methods:
        update_alert_value(self, alert_value): Update the alert value of the sensor.
        add_data(self, data): Add data to the sensor.
        __str__(self): Return the string representation of the sensor.
    """
    
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

    # def update_alert_value(self, alert_value):
    #     self.alert_value = alert_value
    #     self.fig.update_layout(shapes=[dict(type="line", yref="y", y0=self.alert_value, y1=self.alert_value)])
    #     self.html_plot = self.fig.to_html(full_html=False) # include_plotlyjs='cdn'
    #     set_sensor_alert_value(self.name, self.alert_value)

    # def add_data(self, data):
    #     deveui, rssi, time, value = data
    #     add_sensor_data(deveui, rssi, time, value)
    #     check_for_alert(self.id, self.name, self.alert_value, value)

    def __str__(self):
        return f"Sensor {self.id} ({self.name})"
    

# def check_for_alert(sensor_id, sensor_name, alert_value, value):
#     """Check if the sensor value exceeds the threshold and send an alert if it does"""

#     # If not exeeding threshold, return
#     if float(value) < float(alert_value): 
#         return

#     # Send an alert to the user
#     send_mail_to_all("IoT Alert", f"The sensor {sensor_name} has exceeded the threshold {alert_value} with a value of {value}!")
#     socketio.emit('alert', {
#         'sensor_id': sensor_id,
#         'message': f'''
#             <div class="alert alert-warning alert-dismissible fade show" role="alert">
#                 <strong>Treshold alert!</strong> The {sensor_name} sensor value (<strong>{value}</strong>) has exceeded the threshold you set (<strong>{alert_value}</strong>).
#                 <button type="button" class="close" data-dismiss="alert" aria-label="Close">
#                     <span aria-hidden="true">&times;</span>
#                 </button>
#             </div>
#         '''
#     })
#     print('[INFO]: Mail alert sent!')


def make_table(df: pd.DataFrame) -> str:
    """Generate an HTML table from a Pandas DataFrame
    
    Args:
        df (Pandas Dataframe) - The DataFrame to convert to an HTML table

    Returns:
        table_html (String) - The HTML table
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


def make_figure(df: pd.DataFrame, sensor_name: str, limit: int) -> go.Figure:
    """Generate a Plotly figure from a Pandas DataFrame
    
    Args:
        df (Pandas Dataframe) - The DataFrame to convert to a Plotly figure
        sensor_name (String) - The name of the sensor
        limit (Integer) - The alert limit

    Returns:
        fig (Plotly Figure) - The Plotly figure
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
                    dict(count=1, label="1m",  step="month", stepmode="backward"),
                    dict(count=6, label="6m",  step="month", stepmode="backward"),
                    dict(count=1, label="YTD", step="year",  stepmode="todate"),
                    dict(count=1, label="1y",  step="year",  stepmode="backward"),
                    dict(step="all")
                ])
            ),
            rangeslider=dict(visible=True),
            type="date"
        )
    )
    
    return fig



def get_html_fig(fig: go.Figure) -> str:
    """Convert a Plotly figure to HTML
    
    Args:
        fig (Plotly Figure) - The Plotly figure to convert to HTML

    Returns:
        fig (String) - The HTML figure
    """

    # Render the plot as a static image
    image_bytes = pio.to_image(fig, format='png')

    # Convert the image bytes to a base64-encoded string
    image_str = 'data:image/png;base64,' + base64.b64encode(image_bytes).decode()

    fig = f'<img src="{image_str}" alt="My Plot">'

    return fig



def update_plot(sensor: Sensor, alert_value: int = None) -> Sensor:
    """Update the plot object with the sensor data from the database.

    Args:
        sensor (Sensor) - The sensor object to update
        alert_value (int) - The new alert value to set

    Returns:
        sensor (Sensor) - The updated sensor object
    """

    if alert_value:
        sensor.alert_value = alert_value
        set_sensor_alert_value(sensor.name, alert_value)

    # Get the sensor data from the database, then make a figure to html and make a table
    sensor.dataframe = get_sensor_data(sensor.name)
    sensor.fig = make_figure(sensor.dataframe, sensor.name, sensor.alert_value) 
    sensor.html_plot = get_html_fig(sensor.fig)
    sensor.table = make_table(sensor.dataframe)

    socketio.emit('update', {'sensor_id': sensor.id, 'html_plot': sensor.html_plot, 'table': sensor.table})
    print('[INFO] Plot object updated')
    return sensor



def get_random_value(sensor_id: int, start_time: datetime = None, end_time: datetime = None) -> List[Tuple]:
    """Generate a random value between 0 and 15.
    
    Args:
        sensor_id (Integer) - The ID of the sensor
        start_time (Datetime) - The start time for the data
        end_time (Datetime) - The end time for the data

    Returns:
        data (List of tuples) - The list of tuples containing the sensor ID, time, and value
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

    Args:
        connection (Database Connection): The database connection.
        sensor_name (String): The name of the sensor.

    Returns:
        result (Integer): The ID of the sensor.


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
        deveui (String): The deveui of the sensor.

    Returns:
        result (String): The name of the sensor.
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
        connection (Database Connection): The database connection.
        sensor_name (String): The name of the sensor.

    Returns:
        result (Integer): The alert value of the sensor.
    """
    connection = database.Connection(USERS_DB)
    sensor_id = get_sensor_id(connection, sensor_name)
    request = (f'SELECT alert_value FROM {SENSORS_TABLE} WHERE id=?', (sensor_id, ))
    result = read(connection, request)
    connection.close()

    if not result: return -1

    return result[0][0]



def get_sensor_data(sensor_name: str) -> pd.DataFrame:
    """Get the data of a sensor from the database.

    Args:
        sensor_name (String): The name of the sensor.

    Returns:
        df (Pandas Dataframe): The data of the sensor.
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
        deveui (Integer): The deveui of the sensor.
        rssi (Integer): The fm rssi of the sensor (<= 0)
        time (String): The time of the data.
        value (Integer): The value of the data.
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
        ### DISABLE MAIL ###
        send_mail_to_all("IoT Alert", f"The sensor {sensor_name} has exceeded the threshold {alert_value} with a value of {value}!")
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
        sensor_name (String): The name of the sensor.
        alert_value (Integer): The alert value of the sensor.
    """
    connection = database.Connection(USERS_DB)

    query = f'UPDATE {SENSORS_TABLE} SET alert_value=? WHERE id=?'
    sensor_id = get_sensor_id(connection, sensor_name)
    data = (alert_value, sensor_id)

    write(connection, (query, data))
    connection.close()

    print("[INFO] The alert value of the sensor", sensor_id, "has been updated in the database.")



def get_sensors() -> List[Sensor]:
    """Get all the sensors from the database.

    Returns:
        sensors (List[Sensor]): The list of all the sensors.
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
        html_plot = fig.to_html(full_html=False, include_plotlyjs='cdn')
        table = make_table(dataframe)
        lat = row[3]
        long = row[4]
        sensor = Sensor(sensor_id, sensor_name, dataframe, fig, html_plot, alert_value, table, lat, long)
        sensors.append(sensor)

    return sensors