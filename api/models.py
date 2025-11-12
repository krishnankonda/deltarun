from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
import re


class JobData(BaseModel):
    location: str = Field(..., description="Data location in format provider:service:region (e.g., 'aws:s3:us-east-1')")
    size_gb: float = Field(..., gt=0, description="Data size in gigabytes")

    @field_validator('location')
    @classmethod
    def validate_location_format(cls, v: str) -> str:
        pattern = r'^[a-z0-9]+:[a-z0-9]+:[a-z0-9-]+$'
        if not re.match(pattern, v):
            raise ValueError('location must be in format provider:service:region (e.g., "aws:s3:us-east-1")')
        return v


class JobCompute(BaseModel):
    gpu_type: str = Field(..., description="GPU type (e.g., 'H100', 'A100')")
    gpu_count: int = Field(..., gt=0, description="Number of GPUs required")
    gpu_memory_gb: Optional[int] = Field(None, gt=0, description="Optional: GPU memory in GB")
    interconnect: Optional[str] = Field(None, description="Optional: Interconnect type (e.g., 'infiniband', 'ethernet')")


class JobOutput(BaseModel):
    location: str = Field(..., description="Output location in format provider:service:region")
    path: str = Field(..., description="Storage path (e.g., 's3://bucket/path/')")


class JobRequest(BaseModel):
    job_name: str = Field(..., description="Unique name for the job")
    data: JobData
    compute: JobCompute
    output: Optional[JobOutput] = Field(None, description="Optional output configuration (for MVP 3, ignored in MVP 1)")


class AnalysisOption(BaseModel):
    provider: str
    region: str
    instance_type: Optional[str] = None
    compute_cost_per_hour: float
    one_time_egress_cost: float
    break_even_hours: Optional[float] = None
    advisory_message: str
    is_spot_instance: bool = False
    interruption_risk: Optional[str] = Field(None, description="Risk level: LOW, MEDIUM, or HIGH")


class AnalysisResponse(BaseModel):
    data_local_option: AnalysisOption
    remote_options: List[AnalysisOption]

