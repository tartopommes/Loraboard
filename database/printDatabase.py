from database.gestion import database, USERS_DB, USERS_TABLE, SENSORS_TABLE, DATA_TABLE, read
from tabulate import tabulate


def print_tables(connection):
    """Read and print the content of all tables in the database.

    Args:
        connection: A sqlite3.Connection object.

    Returns:
        None.
    """
    # Get the names of all tables in the database.
    tables = [ table[0] for table in read(connection, 'SELECT name from sqlite_master where type="table"') ]

    # Iterate over all tables in the database.
    for table in tables:
        # Read the content of the table.
        content = read(connection, f'SELECT * FROM {table}')

        # Check if the table is the 'users' table.
        if table == USERS_TABLE:
            # Set the header for the table.
            header = ('id', 'email', 'username', 'password_hash')

            # Convert the rows to lists so that they can be modified.
            for row in range(len(content)):
                content[row] = list(content[row])

        elif table == SENSORS_TABLE:
            header = ('id', 'deveui', 'name', 'alert_value', 'lat', 'long')
            for row in range(len(content)):
                content[row] = list(content[row])

        elif table == DATA_TABLE:
            header = ('id', 'sensor_id', 'rssi', 'time', 'value')
            for row in range(len(content)):
                content[row] = list(content[row])
        
        else:
            # Raise an exception if the table is not 'users'.
            raise Exception(f"Table unwanted: {table}")

        # Format the table name and content for printing.
        frame = '-' * (len(table)+2)
        table_name = f'+{frame}+\n| {table.upper()} |'
        table_content = tabulate(content, header, tablefmt='pretty')

        # Print the table.
        print(table_name)
        print(table_content, '\n')


        

def main():
    
    connection = database.connect(USERS_DB)

    try:
        print_tables(connection)

    except Exception as error:
        print("[ERROR] : SQL connection failed, the database couldn't be printed:", error)

    finally:
        connection.close()


if __name__ == "__main__":
    main()