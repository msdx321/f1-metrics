"""API response schemas."""

from pydantic import BaseModel
from typing import Optional, Dict, List, Any, Union


class MetricRequest(BaseModel):
    """Request model for metric calculations."""
    driver_id: Optional[int] = None
    constructor_id: Optional[int] = None
    season: Optional[int] = None
    race_ids: Optional[List[int]] = None


class MetricResponse(BaseModel):
    """Response model for metric results."""
    metric_name: str
    value: Optional[Union[float, int, Dict[str, Any]]]
    driver_id: Optional[int] = None
    driver_name: Optional[str] = None
    constructor_id: Optional[int] = None
    constructor_name: Optional[str] = None
    season: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class DriverInfo(BaseModel):
    """Driver information."""
    driver_id: int
    forename: str
    surname: str
    nationality: str
    dob: Optional[str] = None
    url: Optional[str] = None


class ConstructorInfo(BaseModel):
    """Constructor information."""
    constructor_id: int
    name: str
    nationality: str
    url: Optional[str] = None


class RaceInfo(BaseModel):
    """Race information."""
    race_id: int
    year: int
    round: int
    name: str
    date: str
    circuit_name: Optional[str] = None


class AvailableMetrics(BaseModel):
    """Available metrics information."""
    driver_metrics: List[str]
    constructor_metrics: List[str]
    comparison_metrics: List[str]


class HealthCheck(BaseModel):
    """Health check response."""
    status: str
    version: str
    timestamp: str
    cache_stats: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None