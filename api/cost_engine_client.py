import httpx
from typing import Optional
from models import JobRequest, AnalysisResponse


class CostEngineClient:
    def __init__(self, base_url: str = "http://cost-engine:8080"):
        self.base_url = base_url
        self.client = httpx.Client(timeout=30.0)

    def analyze(self, request: JobRequest) -> AnalysisResponse:
        """Send analysis request to Cost Engine"""
        url = f"{self.base_url}/analyze"
        
        try:
            response = self.client.post(url, json=request.model_dump())
            response.raise_for_status()
            return AnalysisResponse(**response.json())
        except httpx.HTTPStatusError as e:
            raise Exception(f"Cost Engine returned error {e.response.status_code}: {e.response.text}")
        except httpx.RequestError as e:
            raise Exception(f"Failed to connect to Cost Engine: {str(e)}")
        except Exception as e:
            raise Exception(f"Unexpected error: {str(e)}")

    def close(self):
        """Close the HTTP client"""
        self.client.close()

