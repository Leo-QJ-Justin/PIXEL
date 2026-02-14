"""One-time Google Calendar OAuth2 authentication.

Usage:
    uv run python scripts/auth_google_calendar.py

Opens a browser window for Google OAuth consent, then saves the token
to google_calendar_token.json in the project root.
"""

import os
import sys
from pathlib import Path


def main():
    # Ensure project root is on sys.path
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    sys.path.insert(0, str(project_root))

    from dotenv import load_dotenv

    load_dotenv()

    from integrations.google_calendar.auth import load_credentials, run_auth_flow

    creds = load_credentials(project_root)
    if creds is not None:
        print("Existing Google Calendar credentials are still valid.")
        return

    print("Starting Google Calendar authentication...")
    print("A browser window will open for you to authorize access.\n")

    creds = run_auth_flow(project_root)
    if creds is not None:
        print("\nSuccess! Google Calendar token saved.")
    else:
        print("\nAuthentication failed. Check your .env has:")
        print("  GOOGLE_CALENDAR_CLIENT_ID=...")
        print("  GOOGLE_CALENDAR_CLIENT_SECRET=...")
        sys.exit(1)


if __name__ == "__main__":
    main()
