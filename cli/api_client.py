import httpx
from typing import Optional
from models import JobRequest
import json


class APIClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.Client(timeout=60.0)

    def analyze(self, request: JobRequest) -> dict:
        """Send analysis request to Backend API"""
        url = f"{self.base_url}/api/v1/analyze"
        
        try:
            response = self.client.post(url, json=request.model_dump())
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 422:
                error_detail = e.response.json()
                raise Exception(f"Validation error: {error_detail}")
            raise Exception(f"API returned error {e.response.status_code}: {e.response.text}")
        except httpx.RequestError as e:
            raise Exception(f"Failed to connect to API at {self.base_url}. Is the server running?")
        except Exception as e:
            raise Exception(f"Unexpected error: {str(e)}")

    def close(self):
        """Close the HTTP client"""
        self.client.close()

