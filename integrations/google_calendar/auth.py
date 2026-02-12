"""Google Calendar OAuth2 authentication helpers."""

import json
import logging
import os
from pathlib import Path

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

TOKEN_FILENAME = "google_calendar_token.json"


def _get_client_config() -> dict | None:
    """Build OAuth client config from environment variables.

    Returns None if required env vars are missing.
    """
    client_id = os.getenv("GOOGLE_CALENDAR_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CALENDAR_CLIENT_SECRET")

    if not client_id or not client_secret:
        return None

    return {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"],
        }
    }


def load_credentials(base_dir: Path) -> Credentials | None:
    """Load and refresh credentials from the saved token file.

    Returns valid Credentials or None if unavailable.
    """
    token_path = base_dir / TOKEN_FILENAME

    if not token_path.exists():
        logger.debug("No Google Calendar token file found")
        return None

    try:
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    except (json.JSONDecodeError, ValueError, KeyError):
        logger.warning("Invalid Google Calendar token file")
        return None

    if creds.valid:
        return creds

    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            # Save refreshed token
            token_path.write_text(creds.to_json())
            logger.info("Google Calendar token refreshed")
            return creds
        except RefreshError:
            logger.warning("Failed to refresh Google Calendar token — re-auth required")
            return None

    return None


def run_auth_flow(base_dir: Path) -> Credentials | None:
    """Run interactive OAuth desktop flow (opens browser).

    Returns Credentials on success, None on failure.
    """
    client_config = _get_client_config()
    if client_config is None:
        logger.error(
            "GOOGLE_CALENDAR_CLIENT_ID and GOOGLE_CALENDAR_CLIENT_SECRET must be set in .env"
        )
        return None

    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
    creds = flow.run_local_server(port=0)

    # Save token
    token_path = base_dir / TOKEN_FILENAME
    token_path.write_text(creds.to_json())
    logger.info(f"Google Calendar token saved to {token_path}")

    return creds
