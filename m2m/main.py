import os
import requests
from dotenv import load_dotenv

# load .env
load_dotenv()

AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
CLIENT_ID = os.getenv("AUTH0_CLIENT_ID")
CLIENT_SECRET = os.getenv("AUTH0_CLIENT_SECRET")
AUDIENCE = os.getenv("AUTH0_AUDIENCE")
BACKEND_URL = os.getenv("BACKEND_URL")


def get_m2m_token():
    url = f"https://{AUTH0_DOMAIN}/oauth/token"

    payload = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "audience": AUDIENCE,
        "grant_type": "client_credentials",
    }

    res = requests.post(url, json=payload)

    if res.status_code != 200:
        raise Exception(f"Token fetch failed: {res.text}")

    return res.json()["access_token"]


def call_backend():
    token = get_m2m_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    res = requests.get(BACKEND_URL, headers=headers)

    print("Status Code:", res.status_code)
    print("Response:")
    print(res.text)


if __name__ == "__main__":
    call_backend()
