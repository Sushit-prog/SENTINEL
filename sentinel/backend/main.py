"""SENTINEL — Digital Public Safety Intelligence Platform.

An AI-powered platform equipping law enforcement, financial institutions, and citizens
with proactive tools to detect, disrupt, and respond to digital fraud networks,
counterfeit currency circulation, and organised scam operations. Built for the
ET AI Hackathon 2.0 — AI for Digital Public Safety.
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api import scamwatch, currencyguard, fraudgraph
from backend.api.intelligence import router as intelligence_router
from backend.api.geo import router as geo_router
from backend.config import get_settings

settings = get_settings()

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="SENTINEL API",
    description=(
        "SENTINEL is a Digital Public Safety Intelligence Platform that combines "
        "AI-powered scam detection (SCAMWatch), computer vision currency authentication "
        "(CURRENCYGuard), graph-based fraud network mapping (FRAUDGraph), geospatial "
        "threat intelligence (GeoIntel), and a cross-module intelligence dashboard. "
        "All modules share a ChromaDB intelligence store for cross-module correlation "
        "and predictive threat neutralisation."
    ),
    version="0.3",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    scamwatch.router,
    prefix="/api/scamwatch",
    tags=["SCAMWatch"],
)
app.include_router(
    currencyguard.router,
    prefix="/api/currencyguard",
    tags=["CURRENCYGuard"],
)
app.include_router(
    fraudgraph.router,
    prefix="/api/fraudgraph",
    tags=["FRAUDGraph"],
)
app.include_router(intelligence_router)
app.include_router(geo_router)


@app.get("/", tags=["System"])
def root():
    """SENTINEL platform root — confirms API is operational."""
    return {"status": "SENTINEL operational", "version": "0.3"}


@app.get("/health", tags=["System"])
def health():
    """Health check endpoint for monitoring and load balancers."""
    return {"status": "healthy"}
