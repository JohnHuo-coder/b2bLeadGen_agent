"""Google Maps scraper via Apify."""

from __future__ import annotations

from apify_client import ApifyClient

from src.config import GOOGLE_MAPS_ACTOR_ID, get_apify_token
from src.models import CompanyCandidate
from src.tools.apify_utils import get_default_dataset_id


def scrape_google_maps(
    search_term: str,
    location: str,
    max_results: int,
) -> list[CompanyCandidate]:
    """Run Apify Google Maps Scraper and return normalized candidates."""
    client = ApifyClient(get_apify_token())

    run_input = {
        "searchStringsArray": [search_term],
        "locationQuery": location,
        "maxCrawledPlacesPerSearch": max_results,
        "language": "en",
        "skipClosedPlaces": True,
        "scrapePlaceDetailPage": False,
    }

    run = client.actor(GOOGLE_MAPS_ACTOR_ID).call(run_input=run_input)
    dataset_id = get_default_dataset_id(run)

    candidates: list[CompanyCandidate] = []
    for item in client.dataset(dataset_id).iterate_items():
        name = item.get("title") or item.get("name")
        if not name:
            continue

        place_id = item.get("placeId") or item.get("place_id")
        candidates.append(
            CompanyCandidate(
                place_id=str(place_id) if place_id is not None else None,
                company_name=name,
                website=item.get("website") or item.get("domain"),
                source="google_maps",
                address=item.get("address") or item.get("street"),
                phone=item.get("phone") or item.get("phoneUnformatted"),
                industry=item.get("categoryName") or item.get("category"),
            )
        )

        if len(candidates) >= max_results:
            break

    return candidates
