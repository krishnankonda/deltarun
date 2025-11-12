from typing import Optional
from pydantic import BaseModel, Field


class JobData(BaseModel):
    location: str = Field(..., description="Data location in format provider:service:region")
    size_gb: float = Field(..., gt=0)


class JobCompute(BaseModel):
    gpu_type: str
    gpu_count: int = Field(..., gt=0)
    gpu_memory_gb: Optional[int] = Field(None, gt=0)
    interconnect: Optional[str] = None


class JobOutput(BaseModel):
    location: str
    path: str


class JobRequest(BaseModel):
    job_name: str
    data: JobData
    compute: JobCompute
    output: Optional[JobOutput] = None

