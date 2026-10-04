import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
TESTS_DIR = BASE_DIR / "tests"


def fetch_logged_in_user(use_fake: bool = True) -> dict:
    """Fetch profile data for the active user."""
    if use_fake:
        user_file = TESTS_DIR / "fake_user.json"
        with open(user_file, "r", encoding="utf-8") as f:
            return json.load(f)

    # TODO: Implement live OAuth 2.0 API call once credentials arrive
    # requests.get("https://api.intra.42.fr/v2/me", headers=...)
    raise NotImplementedError("Live 42 API credentials not configured yet.")


def fetch_campus_peers(use_fake: bool = True) -> list[dict]:
    """Fetch active campus peers logged into workstation hosts."""
    if use_fake:
        data_file = TESTS_DIR / "fake_data.json"
        with open(data_file, "r", encoding="utf-8") as f:
            return json.load(f)

    # TODO: Implement live locations endpoint call once credentials arrive
    # requests.get("https://api.intra.42.fr/v2/campus/22/locations?filter[active]=true", ...)
    raise NotImplementedError("Live 42 API credentials not configured yet.")