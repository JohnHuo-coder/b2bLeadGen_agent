"""FastAPI backend entry point for the B2B Lead Generation Agent."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from src.agent import LeadGenAgent
from src.models import LeadGenerationResult, LeadRequest

app = FastAPI(
    title="B2B Lead Generation Agent",
    description="Find company candidates via Apify Google Maps and LinkedIn scrapers.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = LeadGenAgent()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/leads/generate", response_model=LeadGenerationResult)
def generate_leads(request: LeadRequest) -> LeadGenerationResult:
    """Generate company candidates based on target company, location, and count."""
    try:
        return agent.run(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
