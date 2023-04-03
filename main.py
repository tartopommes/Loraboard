from database.gestion import database, USERS_DB
from database.initDatabase import init_database, read_tables
from database.mail import get_all_emails, send_email, get_creds
from database.addUser import add_user
from database.deleteUser import delete_user
from server.website import app


# 🚧                                                                                     🚧
# 🚧               BEFORE RUNNING, GO TO GESTION AND PUT YOUR GMAIL ADRESS               🚧
# 🚧 FOR THE FIRST RUN, YOU WILL NEED TO ACCEPT THE GOOGLE AUTHORIZATION IN YOUR BROWSER 🚧
# 🚧                                                                                     🚧


if __name__ == "__main__":

    connection = database.connect(USERS_DB)

    try:
        init_database(connection)
        # add_user(connection, 'comando117000@gmail.com', "comando117000", "supermdp")
        # delete_user(connection, 1)
        read_tables(connection)

    except Exception as error:
        print("[ERROR] : SQL connection failed:", error)

    finally:
        connection.close()

    # Run website
    app.run(debug=True)