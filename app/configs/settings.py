import os
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# --- Facebook API Credentials ---
FACEBOOK_APP_ID = os.getenv("FACEBOOK_APP_ID")
FACEBOOK_APP_SECRET = os.getenv("FACEBOOK_APP_SECRET")
FACEBOOK_PAGE_ID = os.getenv("FACEBOOK_PAGE_ID")
FACEBOOK_USER_ACCESS_TOKEN = os.getenv("FACEBOOK_USER_ACCESS_TOKEN")

# --- OpenAI API Key ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# --- Scheduler Settings ---
# Default to a set schedule if not provided
_post_schedule_hours_str = os.getenv("POST_SCHEDULE_HOURS", "9,12,15,18,21")
POST_SCHEDULE_HOURS = [int(h.strip()) for h in _post_schedule_hours_str.split(',')]

# --- Application Settings ---
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# --- Validation ---
# Ensure critical secrets are loaded
if not all([FACEBOOK_PAGE_ID, FACEBOOK_USER_ACCESS_TOKEN, OPENAI_API_KEY]):
    raise ValueError(
        "Missing critical environment variables. "
        "Please check your .env file and ensure FACEBOOK_PAGE_ID, "
        "FACEBOOK_USER_ACCESS_TOKEN, and OPENAI_API_KEY are set."
    )