from email.mime.text import MIMEText

import os.path
import base64

from database.gestion import database, read, exit_error, SENDER, USERS_TABLE, API_CREDS, API_SCOPES, API_TOKEN

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# see https://developers.google.com/gmail/api/quickstart/python?hl=fr



def get_creds() -> Credentials:
    """
    Gets the credentials from the user's machine.
    """
    creds = None

    if os.path.exists(API_TOKEN):
        creds = Credentials.from_authorized_user_file(API_TOKEN, API_SCOPES)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())

        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                API_CREDS, API_SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the credentials for the next run
        with open(API_TOKEN, 'w') as token:
            token.write(creds.to_json())

    return creds




def send_email(recipient: str, subject: str, body: str):
    """
    Sends an email to the specified recipient using the Gmail API.

    Args:
        recipient (string): email that will receive the notification.
        subject (string): subject of the notification.
        body (string): body the notification.
    """
    creds = get_creds()

    try:
        # Call the Gmail API
        service = build('gmail', 'v1', credentials=creds)
        
        # Set the default sender of the email

        # Create a message object and encode it as a base64 string
        message = MIMEText(body)
        message['to'] = recipient
        message['subject'] = subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

        # Send the email using the Gmail API
        send_message = service.users().messages().send(userId=SENDER, body={'raw': raw}).execute()
        print(F'sent message to {recipient} Message Id: {send_message["id"]}')

    except HttpError as error:
        # TODO(developer) - Handle errors from gmail API.
        print(f'An error occurred: {error}')



def get_all_emails(connection: database.Connection) -> list[str]:
    """
    Gets the email addresses of all users from the database.

    Args:
        connection (sqlite3.Connection): Connection object to the database.

    Returns:
        list: A list of all the user's email addresses.
    """

    # Prepare the database query
    request = f'SELECT email FROM {USERS_TABLE}'

    # Execute the request and fetch the result
    result = read(connection, request)

    # If the result is empty, the user account was not found
    if not result:
        exit_error('Account not found.')

    # Extract the user's email address from the result
    emails = [email[0] for email in result]

    return emails




if __name__ == "__main__":
    recipient_email = 'comando117000@gmail.com'
    subject = 'Test email'
    body = 'This is a test email.'

    send_email(recipient_email, subject, body)
