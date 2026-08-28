import json
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, field_serializer

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

class LeadResponse(BaseModel):
    id: int
    contact_data: Dict[str, Any]
    business_info: Optional[str] = None
    budget: Optional[str] = None
    preferred_contact: Optional[str] = None
    comments: Optional[str] = None
    created_at: datetime

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