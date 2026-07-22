"""LinkedIn Company Search via Apify."""

from __future__ import annotations

from apify_client import ApifyClient

from src.config import LINKEDIN_COMPANY_ACTOR_ID, get_apify_token
from src.models import CompanyCandidate
from src.tools.apify_utils import get_default_dataset_id


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
    dataset_id = get_default_dataset_id(run)

    candidates: list[CompanyCandidate] = []
    for item in client.dataset(dataset_id).iterate_items():
        name = item.get("name")
        if not name:
            continue

        employee_count = _parse_employee_count(item.get("employeeCount"))
        range_start, range_end = _parse_employee_count_range(item.get("employeeCountRange"))
        company_type = item.get("companyType")
        if not isinstance(company_type, str) or not company_type.strip():
            company_type = None

        place_id = item.get("id")
        candidates.append(
            CompanyCandidate(
                place_id=str(place_id) if place_id is not None else None,
                company_name=name,
                website=item.get("website"),
                source="linkedin",
                linkedin_url=item.get("linkedinUrl") or item.get("url"),
                industry=_extract_industry(item),
                employee_count=employee_count,
                employee_count_range_start=range_start,
                employee_count_range_end=range_end,
                company_type=company_type,
                description=item.get("tagline") or item.get("description"),
            )
        )

        if len(candidates) >= max_results:
            break

    return candidates


def _parse_employee_count(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, str):
        if not value.isdigit():
            return None
        value = int(value)
    if isinstance(value, (int, float)):
        count = int(value)
        if count <= 0:
            return None
        return count
    return None


def _parse_employee_count_range(value: object) -> tuple[int | None, int | None]:
    if not isinstance(value, dict):
        return None, None

    start = _parse_range_bound(value.get("start"))
    end = _parse_range_bound(value.get("end"))
    return start, end


def _parse_range_bound(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, str):
        if not value.isdigit():
            return None
        value = int(value)
    if isinstance(value, (int, float)):
        bound = int(value)
        if bound <= 0:
            return None
        return bound
    return None


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
