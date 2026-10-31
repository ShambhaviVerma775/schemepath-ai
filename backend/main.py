"""
SchemePathAI — FastAPI entry point.

Endpoints:
  POST /api/discover   — Discover eligible government schemes for a student profile
  POST /api/apply      — Automate scheme application via browser agent
  GET  /api/schemes/{session_id} — Retrieve cached results for a session
  GET  /health         — Health check
"""

import logging
import uvicorn
from contextlib import asynccontextmanager
from typing import Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from agents.scheme_agent import run_scheme_agent
from agents.browser_agent import run_browser_agent
from models.schemas import (
    SchemeDiscoveryRequest,
    SchemeDiscoveryResponse,
    ApplicationRequest,
    ApplicationResponse,
)

# ─── Logging ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("schemepath.main")

# ─── In-memory session store ───────────────────────────────────────────────────

sessions: Dict[str, SchemeDiscoveryResponse] = {}

# ─── Lifespan ─────────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup / shutdown lifecycle."""
    logger.info("SchemePathAI backend starting up…")
    yield
    logger.info("SchemePathAI backend shutting down — clearing %d sessions.", len(sessions))
    sessions.clear()


# ─── App factory ──────────────────────────────────────────────────────────────

app = FastAPI(
    title="SchemePathAI",
    description="Autonomous student government scheme navigator powered by LangGraph + Gemini + ChromaDB.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Routes ───────────────────────────────────────────────────────────────────


@app.get("/health", tags=["Meta"])
async def health_check() -> dict:
    """Lightweight health probe used by load-balancers and CI checks."""
    return {
        "status": "ok",
        "service": "SchemePathAI",
        "active_sessions": len(sessions),
    }


@app.post("/api/discover", response_model=SchemeDiscoveryResponse, tags=["Schemes"])
async def discover_schemes(request: SchemeDiscoveryRequest) -> SchemeDiscoveryResponse:
    """
    Run the LangGraph scheme-discovery agent against a student profile and
    return a ranked list of eligible government schemes.
    """
    logger.info(
        "Discover request received for student '%s' (state=%s, category=%s).",
        request.profile.name,
        request.profile.state,
        request.profile.category,
    )

    try:
        response: SchemeDiscoveryResponse = await run_scheme_agent(request)
    except Exception as exc:
        logger.exception("Scheme agent failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Scheme agent error: {exc}") from exc

    # Cache result keyed by session_id so subsequent GET calls are fast
    sessions[response.session_id] = response
    logger.info(
        "Session %s created — %d eligible schemes found.",
        response.session_id,
        response.total_found,
    )
    return response


@app.post("/api/apply", response_model=ApplicationResponse, tags=["Applications"])
async def apply_to_scheme(request: ApplicationRequest) -> ApplicationResponse:
    """
    Trigger the Playwright browser agent to fill and submit a scheme application
    on behalf of the student.
    """
    logger.info(
        "Apply request for scheme_id=%s in session %s.",
        request.scheme_id,
        request.session_id,
    )

    # Validate that the session and scheme exist
    session_data = sessions.get(request.session_id)
    if session_data is None:
        raise HTTPException(
            status_code=404,
            detail=f"Session '{request.session_id}' not found. Run /api/discover first.",
        )

    scheme = next(
        (s for s in session_data.eligible_schemes if s.scheme_id == request.scheme_id),
        None,
    )
    if scheme is None:
        raise HTTPException(
            status_code=404,
            detail=f"Scheme '{request.scheme_id}' not found in session '{request.session_id}'.",
        )

    try:
        response: ApplicationResponse = await run_browser_agent(request, scheme)
    except Exception as exc:
        logger.exception("Browser agent failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Browser agent error: {exc}") from exc

    logger.info(
        "Application for scheme_id=%s completed — success=%s.",
        request.scheme_id,
        response.success,
    )
    return response


@app.get(
    "/api/schemes/{session_id}",
    response_model=SchemeDiscoveryResponse,
    tags=["Schemes"],
)
async def get_session_schemes(session_id: str) -> SchemeDiscoveryResponse:
    """
    Return previously cached scheme-discovery results for a given session ID.
    """
    session_data = sessions.get(session_id)
    if session_data is None:
        raise HTTPException(
            status_code=404,
            detail=f"No session found for id '{session_id}'.",
        )
    return session_data


# ─── Dev entrypoint ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
