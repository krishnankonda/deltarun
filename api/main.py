from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from models import JobRequest, AnalysisResponse
from cost_engine_client import CostEngineClient
import os

app = FastAPI(title="FinOps Orchestrator API", version="0.1.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Cost Engine client
cost_engine_url = os.getenv("COST_ENGINE_URL", "http://cost-engine:8080")
cost_engine_client = CostEngineClient(base_url=cost_engine_url)


@app.post("/api/v1/analyze", response_model=AnalysisResponse)
def analyze(job_request: JobRequest) -> AnalysisResponse:
    """
    Analyze cost profile for a job configuration.
    
    Validates the job request and forwards it to the Cost Engine for analysis.
    """
    try:
        response = cost_engine_client.analyze(job_request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.on_event("shutdown")
def shutdown():
    """Cleanup on shutdown"""
    cost_engine_client.close()

