"""LinkedIn Company Search via Apify."""

from __future__ import annotations

from apify_client import ApifyClient

from src.config import LINKEDIN_COMPANY_ACTOR_ID, get_apify_token
from src.models import CompanyCandidate


def scrape_linkedin_companies(
    search_query: str,
    location: str,
    max_results: int,
    industry_ids: list[int] | None = None,
) -> list[CompanyCandidate]:
    """Run Apify LinkedIn Company Search and return normalized candidates."""
    client = ApifyClient(get_apify_token())

    run_input: dict = {
        "scraperMode": "full",
        "maxItems": max_results,
        "searchQuery": search_query,
        "locations": [location],
    }
    if industry_ids:
        # Apify schema expects industryIds as string array, e.g. ["4", "13"]
        run_input["industryIds"] = [str(industry_id) for industry_id in industry_ids]

    run = client.actor(LINKEDIN_COMPANY_ACTOR_ID).call(run_input=run_input)
    dataset_id = run["defaultDatasetId"]

    candidates: list[CompanyCandidate] = []
    for item in client.dataset(dataset_id).iterate_items():
        name = item.get("name")
        if not name:
            continue

        employee_count = item.get("employeeCount")
        if isinstance(employee_count, str) and employee_count.isdigit():
            employee_count = int(employee_count)

        place_id = item.get("id")
        candidates.append(
            CompanyCandidate(
                place_id=str(place_id) if place_id is not None else None,
                company_name=name,
                website=item.get("website"),
                source="linkedin",
                linkedin_url=item.get("linkedinUrl") or item.get("url"),
                industry=_extract_industry(item),
                employee_count=employee_count if isinstance(employee_count, int) else None,
                description=item.get("tagline") or item.get("description"),
            )
        )

        if len(candidates) >= max_results:
            break

    return candidates


def _extract_industry(item: dict) -> str | None:
    industries = item.get("industries") or item.get("industry")
    if isinstance(industries, list) and industries:
        first = industries[0]
        if isinstance(first, dict):
            return first.get("name") or first.get("label")
        return str(first)
    if isinstance(industries, str):
        return industries
    return None
