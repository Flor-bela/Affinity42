import json
import os
import time
import urllib.parse
import requests
from dotenv import load_dotenv
import streamlit as st

load_dotenv()

CLIENT_ID = os.getenv("UID")
CLIENT_SECRET = os.getenv("SECRET")
MADRID_CAMPUS_ID = 22
REDIRECT_URI = "http://localhost:8501"

_TOKEN_CACHE = {"access_token": None, "expires_at": 0}
_LAST_REQUEST_TIME = 0.0


def _rate_limited_request(method: str, url: str, **kwargs) -> requests.Response:
    """Executes HTTP requests while enforcing the 2 requests/second limit."""
    global _LAST_REQUEST_TIME

    elapsed = time.time() - _LAST_REQUEST_TIME
    if elapsed < 0.5:
        time.sleep(0.5 - elapsed)

    _LAST_REQUEST_TIME = time.time()

    res = requests.request(method, url, **kwargs)

    if res.status_code == 429:
        retry_after = float(res.headers.get("Retry-After", 1.0))
        time.sleep(retry_after)
        return _rate_limited_request(method, url, **kwargs)

    res.raise_for_status()
    return res


def get_access_token() -> str:
    """Obtain or reuse a valid Application Client Credentials OAuth2 token."""
    now = time.time()
    if _TOKEN_CACHE["access_token"] and _TOKEN_CACHE["expires_at"] > now:
        return _TOKEN_CACHE["access_token"]

    if not CLIENT_ID or not CLIENT_SECRET:
        raise ValueError("UID and SECRET must be defined in your .env file.")

    res = _rate_limited_request(
        "POST",
        "https://api.intra.42.fr/oauth/token",
        data={
            "grant_type": "client_credentials",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        },
        timeout=10,
    )
    payload = res.json()

    _TOKEN_CACHE["access_token"] = payload["access_token"]
    _TOKEN_CACHE["expires_at"] = now + payload.get("expires_in", 7200) - 60
    return _TOKEN_CACHE["access_token"]


def get_authorization_url() -> str:
    """Generate 42 Intra OAuth2 login URL for user authentication."""
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "public",
    }
    return f"https://api.intra.42.fr/oauth/authorize?{urllib.parse.urlencode(params)}"


def exchange_code_for_token(code: str) -> str:
    """Exchange user authorization code for a user-specific OAuth access token."""
    res = _rate_limited_request(
        "POST",
        "https://api.intra.42.fr/oauth/token",
        data={
            "grant_type": "authorization_code",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "code": code,
            "redirect_uri": REDIRECT_URI,
        },
        timeout=10,
    )
    return res.json()["access_token"]


def fetch_logged_in_user(use_fake: bool = False, user_token: str = None) -> dict:
    """Fetch profile data for the active user."""
    if use_fake:
        with open("tests/fake_user.json", "r") as f:
            return json.load(f)

    if not user_token:
        raise ValueError("A valid user_token is required to fetch real user profile data.")

    headers = {"Authorization": f"Bearer {user_token}"}
    res = _rate_limited_request("GET", "https://api.intra.42.fr/v2/me", headers=headers, timeout=10)
    return res.json()

# para evitar tener que hacer más peticiones con la API
@st.cache_data(ttl=300)

def fetch_campus_peers(use_fake: bool = False) -> list[dict]:
    if use_fake:
        with open("tests/fake_data.json", "r") as f:
            return json.load(f)

    token = get_access_token()
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Obtener usuarios activos
    active_peers_dict = {}
    page = 1
    per_page = 100

    while True:
        url = f"https://api.intra.42.fr/v2/campus/{MADRID_CAMPUS_ID}/locations"
        params = {
            "filter[active]": "true",
            "page[size]": per_page,
            "page[number]": page,
        }

        res = _rate_limited_request("GET", url, headers=headers, params=params, timeout=10)
        batch = res.json()
        
        if not batch:
            break

        for loc in batch:
            user_data = loc.get("user", {})
            uid = user_data.get("id")
            if uid:
                active_peers_dict[uid] = {
                    "login": user_data.get("login"),
                    "displayname": user_data.get("displayname", user_data.get("login")),
                    "host": loc.get("host", "f1r2p3"),
                    "projects": []
                }

        if len(batch) < per_page:
            break
        page += 1

    # 2. Obtener proyectos de esos usuarios en bloques de 50 (como en tu Flask)
    user_ids = list(active_peers_dict.keys())
    chunk_size = 50

    for i in range(0, len(user_ids), chunk_size):
        chunk = user_ids[i:i + chunk_size]
        ids_str = ",".join(map(str, chunk))
        
        p_page = 1
        while True:
            p_url = f"https://api.intra.42.fr/v2/projects_users"
            p_params = {
                "filter[user_id]": ids_str,
                "page[size]": 100,
                "page[number]": p_page
            }
            
            p_res = _rate_limited_request("GET", p_url, headers=headers, params=p_params, timeout=10)
            p_data = p_res.json()
            
            if not p_data:
                break
                
            for pu in p_data:
                uid = pu.get("user", {}).get("id")
                if uid in active_peers_dict:
                    cursus = pu.get("cursus_ids", [])
                    if 21 in cursus and pu.get("validated?") is True:
                        proj_name = pu.get("project", {}).get("name")
                        if proj_name:
                            active_peers_dict[uid]["projects"].append({
                                "name": proj_name,
                                "marked_at": pu.get("marked_at")
                            })
                        
            p_page += 1

    return list(active_peers_dict.values())