import warnings
warnings.filterwarnings('ignore')

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


def create_contact(access_token, first_name, last_name, company, mobile, email, note):
    api_url = "https://people.googleapis.com/v1/people:createContact"

    contact_data = {
        "names": [{"givenName": first_name, "familyName": last_name}],
        "organizations": [{"name": company}],
        "phoneNumbers": [{"value": mobile}],
        "emailAddresses": [{"value": email}],
        "biographies": [{"value": note}],
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    response = requests.post(api_url, headers=headers, json=contact_data)

    if response.status_code == 200:
        contact_details = response.json()
        contact_id = contact_details.get("resourceName", "")
        contact_id = contact_id.replace("people/","")
        print("Contact added successfully. Contact ID:", contact_id)

    else:
        print("Error adding contact:", response.text)

def edit_contact(access_token, contact_id, first_name, last_name, company, mobile, email, note):
    api_url = f"https://people.googleapis.com/v1/people/{contact_id}:updateContact"

    contact_data = {
        "names": [{"givenName": first_name, "familyName": last_name}],
        "organizations": [{"name": company}],
        "phoneNumbers": [{"value": mobile}],
        "emailAddresses": [{"value": email}],
        "biographies": [{"value": note}],
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    response = requests.put(api_url, headers=headers, json=contact_data)

    if response.status_code == 200:
        print("Contact updated successfully.")
    else:
        print("Error updating contact:", response.text)

def delete_contact(access_token, contact_id):
    api_url = f"https://people.googleapis.com/v1/people/{contact_id}:deleteContact"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    response = requests.delete(api_url, headers=headers)

    if response.status_code == 200:
        print("Contact deleted successfully.")
    else:
        print("Error deleting contact:", response.text)


def main():
    parser = argparse.ArgumentParser(description="Manage Google Contacts.")
    parser.add_argument(
        "--token-path", required=True, help="Path to the JSON token file"
    )
    subparsers = parser.add_subparsers(dest="operation", help="Operation to perform")

    # Create sub-command
    create_parser = subparsers.add_parser("create", help="Create a new contact")
    create_parser.add_argument("--first-name", required=True, help="First name of the contact")
    create_parser.add_argument("--last-name", required=True, help="Last name of the contact")
    create_parser.add_argument("--company", required=True, help="Company of the contact")
    create_parser.add_argument("--mobile", required=True, help="Mobile number of the contact")
    create_parser.add_argument("--email", required=False, help="Email address of the contact")
    create_parser.add_argument("--note", required=False, help="Note about the contact")

    # Edit sub-command
    edit_parser = subparsers.add_parser("edit", help="Edit an existing contact")
    edit_parser.add_argument("contact_id", help="ID of the contact to edit")
    edit_parser.add_argument("--first-name", required=True, help="First name of the contact")
    edit_parser.add_argument("--last-name", required=True, help="Last name of the contact")
    edit_parser.add_argument("--company", required=True, help="Company of the contact")
    edit_parser.add_argument("--mobile", required=True, help="Mobile number of the contact")
    edit_parser.add_argument("--email", required=False, help="Email address of the contact")
    edit_parser.add_argument("--note", required=False, help="Note about the contact")

    # Delete sub-command
    delete_parser = subparsers.add_parser("delete", help="Delete an existing contact")
    delete_parser.add_argument("contact_id", help="ID of the contact to delete")

    args = parser.parse_args()

    access_token = credentials(args.token_path)

    if args.operation == "create":
        create_contact(
            access_token, 
            args.first_name, 
            args.last_name, 
            args.company, 
            args.mobile, 
            args.email, 
            args.note
        )
    elif args.operation == "edit":
        edit_contact(
            access_token, 
            args.contact_id, 
            args.first_name, 
            args.last_name, 
            args.company, 
            args.mobile, 
            args.email, 
            args.note
        )
    elif args.operation == "delete":
        delete_contact(access_token, args.contact_id)


if __name__ == "__main__":
    main()
