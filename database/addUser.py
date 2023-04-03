from hashlib import sha256
from getpass import getpass
from database.gestion import database, USERS_DB, USERS_TABLE, read, write, exit_error, return_error
from re import search



def verify_email(email: str):
    """Check if the given email address is valid.

    Args:
        email: A string representing the email.


    Raises:
        SystemExit: If the email doesnt not match email type.
    """
    # Regex pattern for email validation
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    # Use the search method to check if the email matches the pattern
    if not search(pattern, email):
        exit_error("[ERROR] Email address is not valid, please try again.")



def verify_username(connection: database.Connection, username: str) -> bool:
    """Verify if a username already exists in the database.

    Args:
        connection: A sqlite3.Connection object.
        username: A string representing the username to check.

    Returns:
        Bool: True if the username does not exist, False otherwise.

    Raises:
        SystemExit: If the username already exists in the database.
    """
    request = (f'SELECT username FROM {USERS_TABLE} WHERE username=?', (username, ))
    result = read(connection, request)

    if result:
        return return_error("[ERROR] Username already exists, please choose another one.", False)
    return True



def verify_password(password: str, confirmation: str) -> bool:
    """Verify if two passwords match.

    Args:
        password: A string representing the password.
        confirmation: A string representing the confirmation of the password.

    Returns:
        Bool: True if the passwords match, False otherwise.

    Raises:
        SystemExit: If the passwords do not match.
    """
    if password != confirmation:
        return return_error("[ERROR] Password doesn't match.", False)
    return True



def hash_password(password: str) -> str:
    """Hash a password using SHA256.

    Args:
        password: A string representing the password.

    Returns:
        A string representing the hashed password.
    """
    return sha256(password.encode()).hexdigest()



def get_username(connection: database.Connection, user_id: int) -> str:
    """Get the username of a user from the database.

    Args:
        connection: A sqlite3.Connection object.
        user_id: An integer representing the ID of the user.

    Returns:
        A string representing the username of the user.
    """
    request = (f'SELECT username FROM {USERS_TABLE} WHERE id=?', (user_id, ))
    result = read(connection, request)

    return result[0][0]



def add_user(connection: database.Connection, email: str, username: str, password: str):
    """Add a new user to the database.

    Args:
        connection: A sqlite3.Connection object.
        email: A string representing the email of the user.
        username: A string representing the username of the user.
        password: A string representing the password of the user.

    Returns:
        None.
    """
    password_hash = hash_password(password)
    data = (email, username, password_hash)
    request = f'INSERT INTO {USERS_TABLE}(email, username, password_hash) VALUES(?, ?, ?)'

    write(connection, (request, data))
    print(f"[INFO] The user '{username}' has been added to the database.")


    

def create_user():

    connection = database.connect(USERS_DB)

    try:

        email = input('Email: ')
        verify_email(email)

        username = input('Username: ')
        verify_username(connection, username)

        password = getpass('Password: ')
        passwordConfirmation = getpass('Confirm your password: ')
        verify_password(password, passwordConfirmation)

        add_user(connection, email, username, password)
    
    except Exception as error:
        print("[ERROR] : SQL connection failed, no user added to the database:", error)

    finally:
        connection.close()



def main():
    create_user()



if __name__ == "__main__":
    main()