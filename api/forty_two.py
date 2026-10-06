import json
import os
import time
import urllib.parse
import requests
from dotenv import load_dotenv

# Load credentials from .env file
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


def fetch_campus_peers(use_fake: bool = False) -> list[dict]:
    """Fetch active 42 Madrid peers logged into workstation hosts and populate project history."""
    if use_fake:
        with open("tests/fake_data.json", "r") as f:
            return json.load(f)

    token = get_access_token()
    headers = {"Authorization": f"Bearer {token}"}

    active_peers = []
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

        for loc in batch:
            user_data = loc.get("user", {})
            user_id = user_data.get("id")
            login = user_data.get("login")

            if not user_id or not login:
                continue

            projects_data = []

            # Fetch detailed user profile to access full projects_users array
            try:
                user_detail_res = _rate_limited_request(
                    "GET",
                    f"https://api.intra.42.fr/v2/users/{user_id}",
                    headers=headers,
                    timeout=10,
                )
                full_user = user_detail_res.json()

                for pu in full_user.get("projects_users", []):
                    cursus_ids = pu.get("cursus_ids", [])
                    p_obj = pu.get("project", {})
                    p_name = p_obj.get("name") if isinstance(p_obj, dict) else str(p_obj)

                    if 9 not in cursus_ids and p_name:
                        p_lower = str(p_name).lower()
                        if not (p_lower.startswith("c ") or p_lower.startswith("shell") or "piscine" in p_lower):
                            projects_data.append({
                                "name": p_name,
                                "validated_at": pu.get("marked_at", "")[:10] if pu.get("marked_at") else None,
                                "status": pu.get("status"),
                            })
            except Exception:
                # Proceed with available data if user detail call fails
                pass

            active_peers.append({
                "login": login,
                "displayname": user_data.get("displayname", login),
                "host": loc.get("host", "f1r2p3"),
                "projects": projects_data,
            })

        if len(batch) < per_page:
            break

        page += 1

    return active_peers