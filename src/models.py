from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class DataSource(str, Enum):
    GOOGLE_MAPS = "google_maps"
    LINKEDIN = "linkedin"
    BOTH = "both"


class LeadRequest(BaseModel):
    target_company: str = Field(
        ...,
        description="Target company description / search keyword, e.g. 'AI startup', 'Luxury hotel'",
    )
    location: str = Field(..., description="Geographic location, e.g. 'San Francisco, USA'")
    company_count: int = Field(..., ge=1, le=1000, description="Number of companies to find")
    industry: str | None = Field(
        None,
        description="Optional LinkedIn industry ID code(s), e.g. '4' or '4,13'. "
        "Only used when searching via LinkedIn.",
    )


class CompanyCandidate(BaseModel):
    company_name: str
    website: str | None = None
    source: Literal["google_maps", "linkedin"]
    address: str | None = None
    phone: str | None = None
    linkedin_url: str | None = None
    industry: str | None = None
    employee_count: int | None = None
    description: str | None = None


class SourceSelection(BaseModel):
    sources: list[Literal["google_maps", "linkedin"]]
    reasoning: str
    google_maps_search_term: str | None = None
    linkedin_search_query: str | None = None
    linkedin_industry_ids: list[str] = Field(default_factory=list)


class LeadGenerationResult(BaseModel):
    request: LeadRequest
    source_selection: SourceSelection
    candidates: list[CompanyCandidate]
    total_found: int
