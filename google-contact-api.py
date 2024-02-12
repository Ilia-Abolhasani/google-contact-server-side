import datetime
import json
import argparse
import requests
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request


def credentials(token_path):
    current_time = datetime.datetime.utcnow()
    with open(token_path, "r") as token_file:
        token_data = json.load(token_file)
        access_token = token_data["access_token"]
        refresh_token = token_data["refresh_token"]
        expires_in = int(token_data["expires_in"])
        client_id = token_data["client_id"]
        client_secret = token_data["client_secret"]
        expire_time = token_data["expireTime"]
        if not expire_time:
            expire_time = current_time - datetime.timedelta(seconds=10)
        else:
            expire_time = datetime.datetime.fromisoformat(expire_time)            
        credentials = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret,
            scopes=[token_data["scope"]],
            expiry=expire_time,
        )

    if credentials.expired:
        credentials.refresh(Request())
        expiration_time = current_time + datetime.timedelta(seconds=expires_in)
        expiration_time_str = expiration_time.isoformat()
        with open(token_path, "w") as token_file:
            token_data = {
                "access_token": credentials.token,
                "refresh_token": credentials.refresh_token,
                "expires_in": expires_in,
                "token_type": "Bearer",
                "scope": credentials.scopes[0],
                "expireTime": expiration_time_str,
                "client_id": client_id,
                "client_secret": client_secret,
            }
            json.dump(token_data, token_file)
    access_token = credentials.token
    return access_token


def create_contact(access_token, name, last_name, phone, email):
    api_url = "https://people.googleapis.com/v1/people:createContact"

    contact_data = {
        "names": [{"givenName": name, "familyName": last_name}],
        "phoneNumbers": [{"value": phone}],
        "emailAddresses": [{"value": email}],
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    response = requests.post(api_url, headers=headers, json=contact_data)

    if response.status_code == 200:
        print("Contact added successfully.")
    else:
        print("Error adding contact:", response.text)


def main():
    parser = argparse.ArgumentParser(description="Create a contact in Google Contacts.")
    parser.add_argument(
        "--token-path", required=True, help="Path to the JSON token file"
    )
    parser.add_argument("--name", required=True, help="First name of the contact")
    parser.add_argument("--last-name", required=True, help="Last name of the contact")
    parser.add_argument("--phone", required=True, help="Phone number of the contact")
    parser.add_argument("--email", required=False, help="Email address of the contact")
    args = parser.parse_args()

    access_token = credentials(args.token_path)

    create_contact(access_token, args.name, args.last_name, args.phone, args.email)


if __name__ == "__main__":
    main()
