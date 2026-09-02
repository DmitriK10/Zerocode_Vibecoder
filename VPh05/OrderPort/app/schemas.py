import json
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, field_serializer

# ---------- Lead ----------
class LeadCreate(BaseModel):
    contact_data: Dict[str, Any]
    business_info: Optional[str] = None
    budget: Optional[str] = None
    preferred_contact: Optional[str] = None
    comments: Optional[str] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    referer: Optional[str] = None
    session_id: Optional[str] = None
    page_load_time: Optional[float] = None
    service_id: Optional[int] = None

class LeadResponse(BaseModel):
    id: int
    contact_data: Dict[str, Any]
    business_info: Optional[str] = None
    budget: Optional[str] = None
    preferred_contact: Optional[str] = None
    comments: Optional[str] = None
    created_at: datetime
    service_id: Optional[int] = None

    @field_serializer('contact_data')
    def serialize_contact_data(self, value):
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return {}
        return value

    class Config:
        from_attributes = True

# ---------- AdminSettings ----------
class AdminSettingsCreate(BaseModel):
    services: str
    budget_range: str

class AdminSettingsResponse(BaseModel):
    id: int
    services: str
    budget_range: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# ---------- BehaviorMetrics ----------
class BehaviorMetricsCreate(BaseModel):
    lead_id: int
    page_load_time: Optional[float] = None
    session_duration: Optional[float] = None
    clicks: Optional[int] = None
    scroll_depth: Optional[int] = None
    other_metrics: Optional[Dict[str, Any]] = None

class BehaviorMetricsResponse(BaseModel):
    id: int
    lead_id: int
    page_load_time: Optional[float] = None
    session_duration: Optional[float] = None
    clicks: Optional[int] = None
    scroll_depth: Optional[int] = None
    other_metrics: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True

# ---------- Analysis ----------
class AnalysisResponse(BaseModel):
    lead_id: int
    analysis: str