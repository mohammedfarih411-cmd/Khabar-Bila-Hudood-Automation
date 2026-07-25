from google_auth_oauthlib.flow import InstalledAppFlow
import json

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

client_config = {
    "installed": {
        "client_id": "YOUR_CLIENT_ID",
        "client_secret": "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",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token"
    }
}

flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
creds = flow.run_local_server(port=0)

print("\n==============================")
print("YOUTUBE_TOKEN:")
print(creds.refresh_token)
print("==============================")
