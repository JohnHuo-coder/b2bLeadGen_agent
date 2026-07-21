"""FastAPI backend entry point for the B2B Lead Generation Agent."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.agent import LeadGenAgent
from src.models import LeadGenerationResponse, LeadRequest

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


@app.exception_handler(HTTPException)
async def http_exception_handler(_request: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "fail", "data": None, "detail": detail},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"status": "fail", "data": None, "detail": str(exc.errors())},
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/leads/generate", response_model=LeadGenerationResponse)
def generate_leads(request: LeadRequest) -> LeadGenerationResponse:
    """Generate company candidates based on target company, location, and count."""
    try:
        result = agent.run(request)
        return LeadGenerationResponse(status="ok", data=result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
