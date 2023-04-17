"""This module contains the functions related to delete a user from the database."""

from database.gestion import USERS_DB, USERS_TABLE, database, exit_error, return_error, read, write
from getpass import getpass
from hashlib import sha256
from traceback import print_exc



def hash_password(password: str) -> str:
    """Hash a password using SHA256.

    Args:
        password (str): A string representing the password.

    Returns:
        A string representing the hashed password.
    """
    return sha256(password.encode()).hexdigest()



def get_user_id(connection: database.Connection, username: str, password_hash: str) -> int:
    """
    Checks if the user is in the database and if the hash of the input password matches the hash in the database.

    Args:
        connection (sqlite3.Connection): Connection object to the database.
        username (str): Username of the user attempting to log in.
        password_hash (str): Hashed password of the user attempting to log in.

    Returns:
        int: The user's ID if creds are valids, -1 otherwise.
    """

    # Prepare the database query
    query = f'SELECT id, password_hash FROM {USERS_TABLE} WHERE username=?'
    data = (username,)

    # Execute the query and fetch the result
    result = read(connection, (query, data))

    # If the result is empty, the user account was not found
    if not result:
        return return_error('Account not found.', -1)
    
    # Extract the user's ID and password hash from the result
    user_id, fetched_hash = result[0]

    # Compare the password hash from the database to the input password hash
    if fetched_hash != password_hash:
        return return_error('Login failed.', -1)

    # If the password hashes match, the login was successful
    print("[INFO] : Login successful.")
    return user_id



def delete_user(connection: database.Connection, user_id: int):
    """
    Deletes a user from the database.

    Args:
        connection (sqlite3.Connection): Connection object to the database.
        user_id (int): ID of the user to be deleted.
    """

    # Prepare the database query to delete the user
    query = f'DELETE FROM {USERS_TABLE} WHERE id = ?'
    data = (user_id, )

    # Execute the query
    write(connection, (query, data))

    print("[INFO] : The user", user_id, "has been deleted from the database.")

    

if __name__ == "__main__":
    """Delete a user from the database."""

    username = input('Username: ')
    password = getpass('Password: ')

    connection = database.connect(USERS_DB)
    
    try:
        # Get and save user ID
        userID = get_user_id(connection, username, hash_password(password))

        delete_user(connection, userID)
    
    except Exception as error:
        print("[ERROR] : SQL connection failed, the user has not been deleted from the database:", error)
        print_exc()

    finally:
        connection.close()