import warnings
warnings.filterwarnings('ignore')

import datetime
import json
import argparse
import requests
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build


def get_credentials(token_path):
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

    if credentials.expired or True:
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
    return credentials


def create_contact(credentials, first_name, last_name, company, mobile_list, email, note):
    service = build('people', 'v1', credentials=credentials)
    contact_data = {
        "names": [{"givenName": first_name, "familyName": last_name}],
        "organizations": [{"name": company}],
        "phoneNumbers": [{"value": phone} for phone in mobile_list],
        "emailAddresses": [{"value": email}],
        "biographies": [{"value": note}],
    }    
    result = service.people().createContact(body=contact_data).execute()
    resource_name = result.get("resourceName", "")
    print(resource_name)


def edit_contact(credentials, resource_name, first_name, last_name, company, mobile_list, email, note):
    service = build('people', 'v1', credentials=credentials)
    personFields = 'names,phoneNumbers,emailAddresses,organizations,biographies'
    contact = service.people().get(
        resourceName = resource_name, 
        personFields = personFields
    ).execute()
    #### update info 
    names = contact['names']
    names[0]['givenName'] = first_name
    names[0]['familyName'] = last_name
    names[0]['displayName'] = f'{first_name} {last_name}'
    names[0]['displayNameLastFirst'] = f'{last_name}, {first_name}'
    names[0]['unstructuredName'] = f'{first_name} {last_name}'
    contact['names'] = names
    ## phoneNumbers           
    phones  = []
    for phone_number in mobile_list:
        phones.append({"value":phone_number})    
    contact['phoneNumbers'] = phones 
    ## emailAddresses
    emails = contact['emailAddresses']
    emails[0]['value'] = email
    contact['emailAddresses'] = emails
    ## organizations    
    if "organizations" in contact:
        organizations = contact['organizations']
        organizations[0]['name'] = company
        contact['organizations'] = organizations    
    elif company:
        contact['organizations'] = [{'name':company}]

    ## biographies    
    if "biographies" in contact:
        biographies = contact['biographies']
        biographies[0]['value'] = note
        contact['biographies'] = biographies
    elif note:
        contact['biographies'] = [{'value':note}]

        
    result = service.people().updateContact(
        resourceName =  resource_name, 
        body = contact, 
        updatePersonFields = personFields
    ).execute()


def delete_contact(credentials, resource_name):
    service = build('people', 'v1', credentials=credentials)
    result = service.people().deleteContact(resourceName=resource_name).execute()

    if result:
        print("Contact deleted successfully.")
    else:
        print("Error deleting contact:", result)


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
    create_parser.add_argument("--company", required=False, help="Company of the contact")
    create_parser.add_argument("--mobile", nargs='+', required=True, help="Mobile number of the contact")
    create_parser.add_argument("--email", required=False, help="Email address of the contact")
    create_parser.add_argument("--note", required=False, help="Note about the contact")

    # Edit sub-command
    edit_parser = subparsers.add_parser("edit", help="Edit an existing contact")
    edit_parser.add_argument("resource_name", help="ID of the contact to edit")
    edit_parser.add_argument("--first-name", required=True, help="First name of the contact")
    edit_parser.add_argument("--last-name", required=True, help="Last name of the contact")
    edit_parser.add_argument("--company", required=False, help="Company of the contact")
    edit_parser.add_argument("--mobile", nargs='+', required=True, help="Mobile number of the contact")
    edit_parser.add_argument("--email", required=False, help="Email address of the contact")
    edit_parser.add_argument("--note", required=False, help="Note about the contact")

    # Delete sub-command
    delete_parser = subparsers.add_parser("delete", help="Delete an existing contact")
    delete_parser.add_argument("resource_name", help="ID of the contact to delete")

    args = parser.parse_args()

    credentials = get_credentials(args.token_path)

    if args.operation == "create":
        create_contact(
            credentials, 
            args.first_name, 
            args.last_name, 
            args.company, 
            args.mobile, 
            args.email, 
            args.note
        )
    elif args.operation == "edit":
        edit_contact(
            credentials, 
            args.resource_name, 
            args.first_name, 
            args.last_name, 
            args.company, 
            args.mobile, 
            args.email, 
            args.note
        )
    elif args.operation == "delete":
        delete_contact(credentials, args.resource_name)


if __name__ == "__main__":
    main()
