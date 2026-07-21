"""Main B2B lead generation agent."""

from __future__ import annotations

from src.industry_mapper import IndustryMapper
from src.models import CompanyCandidate, LeadGenerationResult, LeadRequest
from src.source_selector import select_sources
from src.tools.google_maps import scrape_google_maps
from src.tools.linkedin import scrape_linkedin_companies


class LeadGenAgent:
    """Agent that selects data sources and fetches company candidates."""

    def __init__(self, industry_mapper: IndustryMapper | None = None):
        self.mapper = industry_mapper or IndustryMapper()

    def run(self, request: LeadRequest) -> LeadGenerationResult:
        selection = select_sources(request, self.mapper)

        candidates: list[CompanyCandidate] = []
        target = request.company_count

        if "google_maps" in selection.sources and selection.google_maps_search_term:
            per_source = target if len(selection.sources) == 1 else (target + 1) // 2
            gm_results = scrape_google_maps(
                search_term=selection.google_maps_search_term,
                location=request.location,
                max_results=per_source,
            )
            candidates.extend(gm_results)

        if "linkedin" in selection.sources and selection.linkedin_search_query:
            remaining = target - len(candidates)
            if remaining > 0:
                li_results = scrape_linkedin_companies(
                    search_query=selection.linkedin_search_query,
                    location=request.location,
                    max_results=remaining,
                    industry_ids=selection.linkedin_industry_ids or None,
                )
                candidates.extend(li_results)

        # Deduplicate by company name (case-insensitive)
        seen: set[str] = set()
        unique: list[CompanyCandidate] = []
        for c in candidates:
            key = c.company_name.lower().strip()
            if key not in seen:
                seen.add(key)
                unique.append(c)
            if len(unique) >= target:
                break

        return LeadGenerationResult(
            request=request,
            source_selection=selection,
            candidates=unique[:target],
            total_found=len(unique[:target]),
        )
