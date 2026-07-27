"""Create a local YouTube OAuth token without storing credentials in Git.

Required environment variables:
    YOUTUBE_CLIENT_ID
    YOUTUBE_CLIENT_SECRET

The generated token is written to ``youtube_token.json`` (gitignored). Never
commit that file or print refresh tokens in CI logs.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
TOKEN_PATH = Path("youtube_token.json")


def require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise SystemExit(f"Missing required environment variable: {name}")
    return value


def main() -> None:
    client_config = {
        "installed": {
            "client_id": require_env("YOUTUBE_CLIENT_ID"),
            "client_secret": require_env("YOUTUBE_CLIENT_SECRET"),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }

    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
    credentials = flow.run_local_server(port=0)
    TOKEN_PATH.write_text(credentials.to_json(), encoding="utf-8")
    print(f"OAuth token saved locally to {TOKEN_PATH}.")
    print("Keep this file private and store production credentials as secrets.")


if __name__ == "__main__":
    main()
