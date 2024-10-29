from flask import Flask, request, jsonify, Blueprint
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import json
import datetime

TOKEN_PATH = "./token.json"
api_bp = Blueprint("api", __name__, url_prefix="/raman")


def get_credentials():
    current_time = datetime.datetime.utcnow()
    with open(TOKEN_PATH, "r") as token_file:
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
        with open(TOKEN_PATH, "w") as token_file:
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


@api_bp.route("/test", methods=["GET"])
def test_api():
    return jsonify({"message": "API is working!"}), 200


@api_bp.route("/create", methods=["POST"])
def create_contact():
    data = request.json
    credentials = get_credentials()
    service = build("people", "v1", credentials=credentials)
    contact_data = {
        "names": [{"givenName": data["first_name"], "familyName": data["last_name"]}],
        "organizations": [{"name": data["company"]}],
        "phoneNumbers": [{"value": phone} for phone in data["mobile_list"]],
        "emailAddresses": [{"value": data["email"]}],
        "biographies": [{"value": data["note"]}],
    }
    result = service.people().createContact(body=contact_data).execute()
    print(result)
    return jsonify({"resource_name": result.get("resourceName", "")})


@api_bp.route("/edit", methods=["PUT"])
def edit_contact():
    data = request.json
    credentials = get_credentials()
    service = build("people", "v1", credentials=credentials)
    personFields = "names,phoneNumbers,emailAddresses,organizations,biographies"
    contact = (
        service.people()
        .get(resourceName=data["resource_name"], personFields=personFields)
        .execute()
    )

    contact["names"][0]["givenName"] = data["first_name"]
    contact["names"][0]["familyName"] = data["last_name"]
    contact["phoneNumbers"] = [{"value": phone} for phone in data["mobile_list"]]
    contact["emailAddresses"][0]["value"] = data["email"]
    contact["organizations"][0]["name"] = data["company"]
    contact["biographies"][0]["value"] = data["note"]

    result = (
        service.people()
        .updateContact(
            resourceName=data["resource_name"],
            body=contact,
            updatePersonFields=personFields,
        )
        .execute()
    )
    return jsonify({"success": True})


@api_bp.route("/delete", methods=["DELETE"])
def delete_contact():
    data = request.json
    credentials = get_credentials()
    service = build("people", "v1", credentials=credentials)
    result = (
        service.people().deleteContact(resourceName=data["resource_name"]).execute()
    )
    return jsonify({"success": True})


if __name__ == "__main__":
    app = Flask(__name__)
    app.register_blueprint(api_bp)
    app.run(debug=False, host="0.0.0.0", port=5000)
