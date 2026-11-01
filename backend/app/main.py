from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import ALLOWED_ORIGINS
from .model_service import load_artifacts
from .schemas import VerifyRequest, VerifyResponse
from .prediction import predict_claim
from .retriever import retrieve_live_evidence

artifacts = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global artifacts
    artifacts = load_artifacts()
    yield

app = FastAPI(
    title="TruthGraph API",
    description="Claim verification API for the TruthGraph prototype.",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

@app.get("/")
def root():
    return {"name": "TruthGraph API", "docs": "/docs", "health": "/api/health"}

@app.get("/api/health")
def health():
    loaded = bool(artifacts and artifacts.loaded)
    return {
        "status": "ok",
        "service": "truthgraph-api",
        "model_loaded": loaded,
        "model_message": None if loaded else (artifacts.load_error if artifacts else "Model loading has not completed.")
    }

@app.post("/api/verify", response_model=VerifyResponse)
def verify(request: VerifyRequest):
    claim = request.claim.strip()
    if len(claim) < 5:
        raise HTTPException(status_code=422, detail="Please enter a claim with at least 5 characters.")

    evidence = list(request.evidence)

    if not evidence and request.auto_retrieve:
        evidence = retrieve_live_evidence(claim)

    if not evidence:
        raise HTTPException(
            status_code=400,
            detail="No evidence provided and live web retrieval could not find relevant sources. Please provide manual evidence."
        )

    result = predict_claim(claim, evidence, artifacts)
    return result

