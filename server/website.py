import plotly.graph_objs as go

from flask import Flask, render_template, request, redirect, url_for, jsonify
from werkzeug.exceptions import NotFound

from database.gestion import database, USERS_DB
from database.mail import get_all_emails, send_email
from database.addUser import hash_password, verify_password, verify_username, get_username, add_user
from database.deleteUser import get_user_id, delete_user
from database.sensor import get_sensor_data, simulate_received_date as simulate_data
from scrapper.super_secret import device_ID

current_user = {
    'is_authenticated': False,
    'login_failed': False,
    'register_failed': {
        'username': False,
        'passwoed': False,
    },
    'delete_failed': False,
    'delete_success': False,
}

plot = {
    'dataframe': '',
    'fig': '',
    'html': '',
    'limit': 14.7,
}

app = Flask(__name__)



# ----------------------------------------------------- #
# ---------------------- PAGES ------------------------ #
# ----------------------------------------------------- #


# Index page
@app.route('/')
def index():
    current_user['delete_success'] = False
    
    if current_user['is_authenticated']:

        # Get the sensor data from the database
        connection = database.connect(USERS_DB)
        plot['dataframe'] = get_sensor_data(connection, device_ID)

        # Create a Plotly line plot, set the labels, and add a horizontal line at the alert limit
        plot['fig'] = go.Figure(data=go.Scatter(x=plot['dataframe']['Time'], y=plot['dataframe']['Value'], mode='lines'))
        plot['fig'].update_layout(title='Test sensor', xaxis_title='Time', yaxis_title='Value')
        plot['fig'].add_hline(y=plot['limit'], line_width=1, line_dash="dash", line_color="red", name="limit")

        # Convert the Plotly figure to an HTML string
        plot['html'] = plot['fig'].to_html(full_html=False)
        return render_template('index.html', current_user=current_user, plot=plot)

    return render_template('index.html', current_user=current_user)



# Register page
@app.route('/register', methods=['GET', 'POST'])
def register():
    current_user['register_failed']['password'] = False
    current_user['register_failed']['username'] = False

    # If the user is already logged in, redirect to the index page
    if current_user['is_authenticated']:
        return redirect(url_for('index'))
    
    # If the user is not logged in, display the register page
    if request.method == 'POST':
        # retrieve form data
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        connection = database.connect(USERS_DB)
        # Check if the username is already taken
        if not verify_username(connection, username):
            current_user['register_failed']['username'] = True
            return render_template('register.html', current_user=current_user)
        # Check if the password is valid
        if not verify_password(password, confirm_password):
            current_user['register_failed']['password'] = True
            return render_template('register.html', current_user=current_user)
        # Add the user to the database
        add_user(connection, email, username, password)

        current_user['is_authenticated'] = True
        current_user['username'] = username
        return render_template('index.html', current_user=current_user)
    
    else:
        return render_template('register.html', current_user=current_user)



# Login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user['is_authenticated']:
        return redirect(url_for('index'))

    if request.method == 'POST':
        # retrieve form data
        username = request.form['username']
        password = request.form['password']

        # Check if the user exists in the database
        connection = database.connect(USERS_DB)
        password_hash = hash_password(password)
        user_id = get_user_id(connection, username, password_hash)

        # If login successful
        if user_id != -1:
            current_user['is_authenticated'] = True
            current_user['username'] = get_username(connection, user_id)
            connection.close()
            return redirect(url_for('index'))

        # If login failed
        connection.close()
        current_user['login_failed'] = True
        return render_template('login.html', current_user=current_user)

    else:
        current_user['login_failed'] = False
        return render_template('login.html', current_user=current_user)



# ------------------------------------------------------- #
# ---------------------- BUTTONS ------------------------ #
# ------------------------------------------------------- # 


# Logout button
@app.route('/logout', methods=['GET', 'POST'])
def logout():
    current_user['is_authenticated'] = False
    return redirect(url_for('index'))



# Delete account button
@app.route('/delete_account', methods=['GET', 'POST'])
def delete_account():
    current_user['delete_failed'] = False

    if current_user['is_authenticated'] == False:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = current_user['username']
        password = request.form['password']
        password_hash = hash_password(password)

        connection = database.connect(USERS_DB)
        user_id = get_user_id(connection, username, password_hash)

        if user_id == -1:
            current_user['delete_failed'] = True
            print(f"current_user['is_authenticated'] = {current_user['is_authenticated']}")
            return render_template('delete_account.html', current_user=current_user)

        current_user['is_authenticated'] = False
        delete_user(connection, user_id)
        current_user['delete_success'] = True
        return render_template('index.html', current_user=current_user)
    
    return render_template('delete_account.html', current_user=current_user)



@app.route('/send_test_mail', methods=['POST'])
def send_test_mail():
    try: # send notification to all users      
        connection = database.connect(USERS_DB)
        email_list = get_all_emails(connection)
        for email in email_list:
            send_email(email, "Notification", "Hello, this is a notification")

    except Exception as error:
        print("[ERROR] : SQL connection failed:", error)

    finally:
        connection.close()
    return redirect(url_for('index'))



@app.route('/simulate_received_data', methods=['POST'])
def simulate_received_data():
    connection = database.connect(USERS_DB)
    simulate_data(connection)
    plot['dataframe'] = get_sensor_data(connection, 'test_sensor')
    plot['fig'] = go.Figure(data=go.Scatter(x=plot['dataframe']['Time'], y=plot['dataframe']['Value'], mode='lines'))
    plot['fig'].update_layout(title='Test sensor', xaxis_title='Time', yaxis_title='Value')
    plot['fig'].add_hline(y=plot['limit'], line_width=1, line_dash="dash", line_color="red", name="limit")
    plot['html'] = plot['fig'].to_html(full_html=False)
    connection.close()
    return redirect(url_for('index'))



@app.route("/update", methods=["POST"])
def update():
    plot['limit'] = request.form["data"]
    plot['fig'] = go.Figure(data=go.Scatter(x=plot['dataframe']['Time'], y=plot['dataframe']['Value'], mode='lines'))
    plot['fig'].update_layout(title='Test sensor', xaxis_title='Time', yaxis_title='Value')
    plot['fig'].add_hline(y=plot['limit'], line_width=1, line_dash="dash", line_color="red", name="limit")
    plot['html'] = plot['fig'].to_html(full_html=False)

    return {'limit': plot['limit'], 'plot': plot['html']}


# Endpoint to return new data for the Plotly trace
@app.route('/data')
def data():
    # Get the up to date data from the database
    connection = database.connect(USERS_DB)
    plot['dataframe'] = get_sensor_data(connection, device_ID)

    # Recreate the plot
    plot['fig'] = go.Figure(data=go.Scatter(x=plot['dataframe']['Time'], y=plot['dataframe']['Value'], mode='lines'))
    plot['fig'].update_layout(title='Test sensor', xaxis_title='Time', yaxis_title='Value')
    plot['fig'].add_hline(y=plot['limit'], line_width=1, line_dash="dash", line_color="red", name="limit")

    # Convert the Plotly figure to an HTML string
    plot['html'] = plot['fig'].to_html(full_html=False)

    # Return the data as a JSON object
    return jsonify(plot=plot['html'])



# ------------------------------------------------------ #
# ---------------------- ERRORS ------------------------ #
# ------------------------------------------------------ # 


# Error handler for 404 errors
@app.errorhandler(NotFound)
def page_not_found(error):
    return redirect(url_for('index'))



if __name__ == '__main__':
    app.run(debug=True)
