import typer
import yaml
import os
from pathlib import Path
from typing import Optional
from models import JobRequest
from api_client import APIClient
from formatter import format_analysis_response, format_error

app = typer.Typer(help="FinOps Orchestrator CLI - Analyze cloud compute costs")


@app.command()
def analyze(
    file: Path = typer.Option(..., "--file", "-f", help="Path to job.yaml file"),
    api_url: Optional[str] = typer.Option(None, "--api-url", help="Backend API URL (default: http://localhost:8000)"),
):
    """
    Analyze cost profile for a job defined in job.yaml.
    
    Example:
        finops-analyze -f job.yaml
    """
    # Validate file exists
    if not file.exists():
        format_error(f"File not found: {file}")
        raise typer.Exit(1)
    
    # Parse YAML
    try:
        with open(file, 'r') as f:
            yaml_data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        format_error(f"Invalid YAML file: {e}")
        raise typer.Exit(1)
    except Exception as e:
        format_error(f"Failed to read file: {e}")
        raise typer.Exit(1)
    
    # Validate required keys
    required_keys = {
        "job_name": "job_name",
        "data.location": ("data", "location"),
        "data.size_gb": ("data", "size_gb"),
        "compute.gpu_type": ("compute", "gpu_type"),
        "compute.gpu_count": ("compute", "gpu_count"),
    }
    
    missing_keys = []
    for key_name, key_path in required_keys.items():
        if isinstance(key_path, tuple):
            current = yaml_data
            for part in key_path:
                if not isinstance(current, dict) or part not in current:
                    missing_keys.append(key_name)
                    break
                current = current[part]
        elif key_path not in yaml_data:
            missing_keys.append(key_name)
    
    if missing_keys:
        format_error(f"Missing required keys: {', '.join(missing_keys)}")
        raise typer.Exit(1)
    
    # Create JobRequest
    try:
        job_request = JobRequest(**yaml_data)
    except Exception as e:
        format_error(f"Invalid job configuration: {e}")
        raise typer.Exit(1)
    
    # Get API URL
    base_url = api_url or os.getenv("FINOPS_API_URL", "http://localhost:8000")
    
    # Send request to API
    client = APIClient(base_url=base_url)
    try:
        response = client.analyze(job_request)
        format_analysis_response(response, job_request.job_name)
    except Exception as e:
        format_error(str(e))
        raise typer.Exit(1)
    finally:
        client.close()


if __name__ == "__main__":
    app()

