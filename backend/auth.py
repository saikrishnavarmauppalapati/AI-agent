# auth.py
import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# ✅ Required scopes
SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",   # read-only (search, liked)
    "https://www.googleapis.com/auth/youtube.force-ssl"  # write actions (like, comment, subscribe)
]

TOKEN_FILE = "token.pkl"      # stores your credentials
CREDENTIALS_FILE = "client_secret.json"  # your OAuth2 credentials downloaded from Google

def get_credentials():
    creds = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as f:
            creds = pickle.load(f)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)  # opens browser for login

        # Save the credentials for next time
        with open(TOKEN_FILE, "wb") as f:
            pickle.dump(creds, f)

    return creds
