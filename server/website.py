from flask import render_template, request, redirect, url_for
from werkzeug.exceptions import NotFound

from database.gestion import database, USERS_DB, app, socketio
from database.addUser import hash_password, verify_password, verify_username, get_username, add_user
from database.deleteUser import get_user_id, delete_user
from database.sensor import update_plot, get_sensors


# User object for the current user (used for the login and register pages as well as in the navbar and index page)
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



# ------------------------------------------------------ #
# ---------------------- SOCKET ------------------------ #
# ------------------------------------------------------ #


@socketio.on('set_alert_value')
def handle_set_alert_value(data):
    SENSORS = get_sensors()
    sensor = SENSORS[data['sensor_id']-1]
    alert_value = data['alert_value']
    print(f'alert_value: {alert_value} for sensor {sensor}', flush=True)
    update_plot(sensor, alert_value)



# ----------------------------------------------------- #
# ---------------------- PAGES ------------------------ #
# ----------------------------------------------------- #


# Index page
@app.route('/')
def index():
    current_user['delete_success'] = False
    
    if current_user['is_authenticated']:
        # intialize Sensors after generating a database

        SENSORS = get_sensors()


        markers=[]
        for sensor in SENSORS:
            if (len(sensor.dataframe["Time"]) > 0):
                markers.append({
                    'id':sensor.id, 
                    'lat':sensor.lat, 
                    'lon':sensor.long, 
                    'name':sensor.name,
                    'time':sensor.dataframe["Time"].iloc[-1],
                    'value':sensor.dataframe["Value"].iloc[-1],
                })
            else:
                markers.append({
                    'id':sensor.id, 
                    'lat':sensor.lat, 
                    'lon':sensor.long, 
                    'name':sensor.name,
                    'time':'no data',
                    'value':'no data',
                })

        return render_template('index.html', current_user=current_user, sensors=SENSORS, markers=markers)

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
        return redirect(url_for('index'))
    
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





# ------------------------------------------------------ #
# ---------------------- ERRORS ------------------------ #
# ------------------------------------------------------ # 


# Error handler for 404 errors
@app.errorhandler(NotFound)
def page_not_found(error):
    return redirect(url_for('index'))



if __name__ == '__main__':
    app.run(debug=True)
