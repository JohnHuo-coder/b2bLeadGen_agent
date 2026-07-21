"""Source selection logic — rule-based with optional LLM enhancement."""

from __future__ import annotations

import json

from openai import OpenAI

from src.config import get_openai_api_key, get_openai_model
from src.industry_mapper import IndustryMapper
from src.models import LeadRequest, SourceSelection


SYSTEM_PROMPT = """You are a B2B lead generation strategist. The user provides a target company description
(a search keyword phrase, NOT a formal industry name). Examples:
- "AI startup"
- "Luxury hotel"
- "Medical device manufacturer"
- "Precision machining company"
- "Coworking space"

Given the target company description, location, and count, decide which data source(s) to use:

1. **google_maps** — Physical/local businesses with map listings: hotels, restaurants, clinics,
   gyms, salons, coworking spaces, retail stores, etc.

2. **linkedin** — B2B/professional companies: startups, manufacturers, SaaS, consulting firms,
   medical device makers, precision machining companies, etc.

3. **both** — When the phrase could match both, e.g. "medical center", "construction company",
   or ambiguous cases.

Use the user's phrase directly (or a slight simplification) as the search term for the chosen source(s).

Respond with JSON only:
{
  "sources": ["google_maps"] or ["linkedin"] or ["google_maps", "linkedin"],
  "reasoning": "brief explanation",
  "google_maps_search_term": "search term for Google Maps (if using google_maps)",
  "linkedin_search_query": "search query for LinkedIn (if using linkedin)"
}
"""


def select_sources(request: LeadRequest, mapper: IndustryMapper | None = None) -> SourceSelection:
    """Pick data source(s) and search parameters for the given request."""
    mapper = mapper or IndustryMapper()

    if get_openai_api_key():
        try:
            return _select_with_llm(request, mapper)
        except Exception:
            pass

    return _select_with_rules(request, mapper)


def _resolve_industry_ids(request: LeadRequest) -> list[str]:
    if not request.industry:
        return []
    return [code.strip() for code in request.industry.split(",") if code.strip()]


def _select_with_rules(request: LeadRequest, mapper: IndustryMapper) -> SourceSelection:
    sources, reasoning = mapper.suggest_sources(request.target_company)
    industry_ids = _resolve_industry_ids(request)
    gm_term, li_query = mapper.build_search_terms(request.target_company)

    if industry_ids:
        reasoning += f" LinkedIn industry filter: {industry_ids}."

    return SourceSelection(
        sources=sources,  # type: ignore[arg-type]
        reasoning=reasoning,
        google_maps_search_term=gm_term if "google_maps" in sources else None,
        linkedin_search_query=li_query if "linkedin" in sources else None,
        linkedin_industry_ids=industry_ids,
    )


def _select_with_llm(request: LeadRequest, mapper: IndustryMapper) -> SourceSelection:
    client = OpenAI(api_key=get_openai_api_key())
    industry_ids = _resolve_industry_ids(request)

    user_msg = (
        f"Target company: {request.target_company}\n"
        f"Location: {request.location}\n"
        f"Target company count: {request.company_count}\n"
        f"LinkedIn industry ID filter (optional): {request.industry or 'none'}"
    )

    response = client.chat.completions.create(
        model=get_openai_model(),
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
    )

    content = response.choices[0].message.content or "{}"
    data = json.loads(content)

    sources = data.get("sources", ["linkedin"])
    if not isinstance(sources, list) or not sources:
        sources = ["linkedin"]

    gm_default, li_default = mapper.build_search_terms(request.target_company)
    reasoning = data.get("reasoning", "LLM-selected sources")
    if industry_ids:
        reasoning += f" LinkedIn industry filter: {industry_ids}."

    return SourceSelection(
        sources=sources,  # type: ignore[arg-type]
        reasoning=reasoning,
        google_maps_search_term=data.get("google_maps_search_term", gm_default),
        linkedin_search_query=data.get("linkedin_search_query", li_default),
        linkedin_industry_ids=industry_ids,
    )
