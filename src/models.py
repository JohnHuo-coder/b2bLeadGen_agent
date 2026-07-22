from typing import Literal

from pydantic import BaseModel, Field


class LeadRequest(BaseModel):
    target_company: str = Field(
        ...,
        description="Target company description / search keyword, e.g. 'AI startup', 'Luxury hotel'",
    )
    location: str = Field(..., description="Geographic location, e.g. 'San Francisco, USA'")
    company_count: int = Field(..., ge=1, le=1000, description="Number of companies to find")
    industry: list[int] | None = Field(
        None,
        description="Optional LinkedIn industry ID codes, e.g. [4, 13]. "
        "Only used when searching via LinkedIn.",
    )
    selected_source: Literal["google_maps", "linkedin", "both"] | None = Field(
        None,
        description="Optional pre-selected data source. When set, skips source inference "
        "and uses this source directly. When null, sources are inferred automatically.",
    )


class CompanyCandidate(BaseModel):
    place_id: str | None = None
    company_name: str
    website: str | None = None
    source: Literal["google_maps", "linkedin"]
    address: str | None = None
    phone: str | None = None
    lat: float | None = None
    lon: float | None = None
    linkedin_url: str | None = None
    industry: str | None = None
    employee_count: int | None = None
    employee_count_range_start: int | None = None
    employee_count_range_end: int | None = None
    company_type: str | None = None
    description: str | None = None


class SourceSelection(BaseModel):
    sources: list[Literal["google_maps", "linkedin"]]
    reasoning: str
    google_maps_search_term: str | None = None
    linkedin_search_query: str | None = None
    linkedin_industry_ids: list[int] = Field(default_factory=list)


class LeadGenerationResult(BaseModel):
    request: LeadRequest
    source_selection: SourceSelection
    candidates: list[CompanyCandidate]
    total_found: int


class LeadGenerationResponse(BaseModel):
    status: Literal["ok", "fail"]
    data: LeadGenerationResult | None = None
    detail: str | None = None
