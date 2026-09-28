"""
Pydantic data models for the thermal anomaly classification system.

These models are the shared contract between the detection pipeline,
the anomaly / classification workers, and the API layer. Keep this file
as the single source of truth for field names and types - everything
downstream (mock data, API responses, future DB models) should derive
from it rather than redefining fields ad hoc.
"""
from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field




class AnomalyType(str, Enum):
    NEW = "new"
    PERSISTENT = "persistent"
    FLARE_UP = "flare_up"
    SEASONAL = "seasonal"
    DECLINING = "declining"


class CoverageStatus(str, Enum):
    FULL = "full"
    PARTIAL = "partial"
    INSUFFICIENT = "insufficient"


class ClassLabel(str, Enum):
    INDUSTRIAL = "industrial"
    GAS_FLARE = "gas_flare"
    VOLCANO = "volcano"
    AGRICULTURAL_BURNING = "agricultural_burning"
    WILDFIRE = "wildfire"
    UNKNOWN = "unknown"


class AssessmentStatus(str, Enum):
    COMPLETE = "complete"
    PENDING = "pending"
    NEEDS_REVIEW = "needs_review"


class PriorityTier(str, Enum):
    P1 = "P1"  
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"  


class Detection(BaseModel):

    model_config = ConfigDict(str_strip_whitespace=True)

    detection_id: str
    source_id: Optional[str] = Field(
        default=None, description="Set once the detection has been clustered into a Source"
    )
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    utm_x: float
    utm_y: float
    brightness_temp_k: float = Field(..., gt=0)
    frp_mw: float = Field(..., ge=0, description="Fire Radiative Power, megawatts")
    sensor: str
    acq_datetime_utc: datetime
    acq_datetime_ist: datetime
    confidence: float = Field(..., ge=0, le=100)


class Source(BaseModel):

    source_id: str
    centroid_lat: float = Field(..., ge=-90, le=90)
    centroid_lon: float = Field(..., ge=-180, le=180)
    first_seen: datetime
    last_seen: datetime
    detection_count: int = Field(..., ge=1)
    sensor_mix: List[str] = Field(..., description="Distinct sensors contributing detections")
    footprint_radius_m: float = Field(..., ge=0)
    history_days: int = Field(..., ge=0, description="Days of detection history available for this source")


class AnomalyScore(BaseModel):

    source_id: str
    as_of_date: date
    anomaly_type: AnomalyType
    statistic: float = Field(..., description="Raw anomaly statistic (e.g. z-score)")
    confidence: float = Field(..., ge=0, le=1)
    coverage_status: CoverageStatus
    baseline_days: int = Field(..., ge=0, description="Days of history used to build the baseline")


class ClassifiedSource(BaseModel):

    source_id: str
    class_label: ClassLabel
    class_probs: Dict[str, float] = Field(
        ..., description="Full class -> probability distribution, should sum to ~1.0"
    )
    top_features: List[str] = Field(..., description="Top features driving the classification")
    facility_name: Optional[str] = None
    facility_distance_m: Optional[float] = Field(default=None, ge=0)
    land_cover_class: Optional[str] = None
    vnf_bt_match: Optional[bool] = Field(
        default=None, description="Whether brightness temp matches VIIRS Nightfire (VNF) expectations"
    )
    confidence: float = Field(..., ge=0, le=1)
    assessment_status: AssessmentStatus


class ThermalSourceAssessment(BaseModel):

    source_id: str
    classification: ClassifiedSource
    anomaly: AnomalyScore
    evidence_complete: bool
    priority_tier: PriorityTier
    priority_rationale: str
    last_updated: datetime
