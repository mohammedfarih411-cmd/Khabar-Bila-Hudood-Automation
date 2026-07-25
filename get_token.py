from google_auth_oauthlib.flow import InstalledAppFlow
import json

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

client_config = {
    "installed": {
        "client_id": "581582198590-i6gm7fko8btt1b8rruf2ne2knvv6824v.apps.googleusercontent.com",

        "client_secret": "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",

        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token"
    }
}

flow = InstalledAppFlow.from_client_config(client_config, SCOPES)

creds = flow.run_local_server(port=0)

with open("token.json", "w") as f:
    f.write(creds.to_json())

print("token.json created")
