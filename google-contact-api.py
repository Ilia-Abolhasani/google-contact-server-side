import argparse
import json
import requests
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

def read_credentials_from_file(token_path):
    with open(token_path, 'r') as token_file:
        token_data = json.load(token_file)
        access_token = token_data['access_token']
        refresh_token = token_data['refresh_token']
        expires_in = token_data['expires_in']

        credentials = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri='https://oauth2.googleapis.com/token',
            client_id='',  # Since client_id is not provided in token.json
            client_secret='',  # Since client_secret is not provided in token.json
            scopes=[token_data['scope']]
        )
        credentials.expiry = None  # Set expiry to None since it's not included in token.json
    return credentials, expires_in

def create_contact(credentials, expires_in, name, last_name, phone, email):
    # Check if the access token is expired        
    if credentials.expired != False:
        credentials.refresh(Request())

        # Update token.json with refreshed token
        with open('token.json', 'w') as token_file:
            token_data = {
                'access_token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'expires_in': expires_in,  # Assuming the token expires in the same duration as before
                'token_type': 'Bearer',
                'scope': credentials.scopes[0],  # Assuming there's only one scope
                'expireTime': None,  # Setting expireTime to None since it's not included in token.json
                # Include other fields like 'Issued' and 'IssuedUtc' if needed
            }
            json.dump(token_data, token_file)

    access_token = credentials.token

    CONTACTS_API_URL = 'https://people.googleapis.com/v1/people:createContact'

    contact_data = {
        "names": [
            {
                "givenName": name,
                "familyName": last_name
            }
        ],
        "phoneNumbers": [
            {
                "value": phone
            }
        ],
        "emailAddresses": [
            {
                "value": email
            }
        ]
    }

    # Construct the request headers with Authorization
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    response = requests.post(CONTACTS_API_URL, headers=headers, json=contact_data)

    if response.status_code == 200:
        print("Contact added successfully.")
    else:
        print("Error adding contact:", response.text)

def main():
    parser = argparse.ArgumentParser(description='Create a contact in Google Contacts.')
    parser.add_argument('--token-path', required=True, help='Path to the JSON token file')
    parser.add_argument('--name', required=True, help='First name of the contact')
    parser.add_argument('--last-name', required=True, help='Last name of the contact')
    parser.add_argument('--phone', required=True, help='Phone number of the contact')
    parser.add_argument('--email', required=False, help='Email address of the contact')
    args = parser.parse_args()

    credentials, expires_in = read_credentials_from_file(args.token_path)
    
    create_contact(credentials, expires_in, args.name, args.last_name, args.phone, args.email)

if __name__ == "__main__":
    main()
