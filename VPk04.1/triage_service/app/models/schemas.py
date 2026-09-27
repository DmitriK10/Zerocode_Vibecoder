from pydantic import BaseModel, Field, field_validator
from typing import Literal


class TriageRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)
    channel: Literal["email", "form", "chat"]
    client_id: str

    @field_validator("text")
    @classmethod
    def text_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("text не может быть пустым")
        return v.strip()


class TriageResponse(BaseModel):
    category: Literal["billing", "support", "complaint", "other"]
    draft_reply: str
    confidence: Literal["high", "medium", "low"]
    escalate: bool