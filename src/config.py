import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()

GOOGLE_MAPS_ACTOR_ID = "compass/crawler-google-places"
LINKEDIN_COMPANY_ACTOR_ID = "harvestapi/linkedin-company-search"


@lru_cache
def get_apify_token() -> str:
    token = os.getenv("APIFY_API_TOKEN", "").strip()
    if not token:
        raise ValueError(
            "APIFY_API_TOKEN is required. Set it in .env or environment variables. "
            "Get your token at https://console.apify.com/account/integrations"
        )
    return token


def get_openai_api_key() -> str | None:
    key = os.getenv("OPENAI_API_KEY", "").strip()
    return key or None


def get_openai_model() -> str:
    return os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
