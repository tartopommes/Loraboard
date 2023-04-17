"""This module contains functions to read and write to the database, as well as functions to hash passwords and verify email addresses."""

import sqlite3 as database
from typing import List, Tuple, Union
from flask import Flask
from flask_socketio import SocketIO


# DATABASE
USERS_TABLE = 'users' # table name
SENSORS_TABLE = 'sensors' # table name
DATA_TABLE = 'data' # table name
USERS_DB = 'database/users.db' #database file name

# MAILS
SENDER = 'comando117000@gmail.com' # set your email address here, must belong to gmail.com
API_CREDS = 'database/credentials.json' #TODO(developer) set your credentials.json file here
API_SCOPES = ['https://www.googleapis.com/auth/gmail.send'] # If modifying these scopes, delete the file token.json. 
                                                            # The scope is used to give access on what we can do with the gmail API (edit, read, etc).
API_TOKEN = 'database/token.json' # The token is used to store the credentials of the user (email, password, etc).
                                  # The file token.json stores the user's access and refresh tokens, and is
                                  # created automatically when the authorization flow completes for the first
                                  # time.

# website
WEBSITE_MODULE_NAME = 'server.website'
app = Flask(WEBSITE_MODULE_NAME)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)


def read(connection: database.Connection, request: Union[Tuple, str], many: bool = False) -> List[Tuple]:
    """
    Executes a SELECT statement on the database and returns the results as a list of tuples.
    
    Args:
        connection (database.Connection): a SQLite3 database connection object
        request (Union[Tuple, str]): the SQL SELECT statement to execute
        many (bool): True if the statement should be executed multiple times with different data, False otherwise
        
    Returns:
        a list of tuples containing the results of the SELECT statement
    """
    cursor = connection.cursor()

    # If the request is a tuple, assume that it contains a prepared statement and data to execute it with
    if isinstance(request, tuple):
        statement, data = request
        if many: return cursor.executemany(statement, data).fetchall()
        else:    return cursor.execute(statement, data).fetchall()

    # If the request is not a tuple, assume that it is a raw SQL statement to execute
    else:
        if many: return cursor.executemany(request).fetchall()
        else:    return cursor.execute(request).fetchall()

    
def write(connection: database.Connection, request: Union[Tuple, str], many: bool = False):
    """
    Executes an INSERT, UPDATE, or DELETE statement on the database and commits the changes.
    
    Args:
        connection (database.Connection): a SQLite3 database connection object
        request (Union[Tuple, str]): the SQL INSERT, UPDATE, or DELETE statement to execute
        many (bool): True if the statement should be executed multiple times with different data, False otherwise
    """
    cursor = connection.cursor()

    # If the request is a tuple, assume that it contains a prepared statement and data to execute it with
    if isinstance(request, tuple):
        statement, data = request
        if many: cursor.executemany(statement, data)
        else:    
            cursor.execute(statement, data)

    # If the request is not a tuple, assume that it is a raw SQL statement to execute
    else:
        if many: cursor.executemany(request)
        else:    cursor.execute(request)

    # Commit the changes to the database
    connection.commit()



def return_error(message: str, objectToReturn: int = 1):
    """
    Print an error message and return an object.

    Args:
        message (str): A string representing the error message.
        objectToReturn (int): An object to return when exiting the program.

    Returns:
        objectToReturn (int): An object to return when exiting the program.
    """
    print(f'[Error] : {message}')
    return objectToReturn
    
    

def exit_error(message: str, objectToReturn: int = 1) -> None:
    """
    Print an error message and exit the program.

    Args:
        message (str): A string representing the error message.
        objectToReturn (int): An object to return when exiting the program.

    Returns:
        None.

    Raises:
        systemExit: An exception that exits the program with the objectToReturn code.
    """
    print(f'[Error] : {message}')
    exit(objectToReturn)

