import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api import scamwatch, currencyguard, fraudgraph
from backend.config import get_settings

settings = get_settings()

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="SENTINEL API",
    description="Digital Public Safety Intelligence Platform",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scamwatch.router, prefix="/api/scamwatch", tags=["SCAMWatch"])
app.include_router(currencyguard.router, prefix="/api/currencyguard", tags=["CURRENCYGuard"])
app.include_router(fraudgraph.router, prefix="/api/fraudgraph", tags=["FRAUDGraph"])

@app.get("/")
def root():
    return {"status": "SENTINEL operational", "version": "1.0.0"}

@app.get("/health")
def health():
    return {"status": "healthy"}
