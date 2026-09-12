"""Доменные модели процесса обработки обращений.

Здесь живёт строгая схема результата LLM и запись журнала аудита.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Dict, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Category(str, Enum):
    BILLING = "billing"
    TECHNICAL = "technical"
    DELIVERY = "delivery"
    COMPLAINT = "complaint"
    OTHER = "other"


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Confidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ProcessingStatus(str, Enum):
    PROCESSED = "processed"
    ESCALATED = "escalated"
    ERROR = "error"


class LLMResult(BaseModel):
    """Строгая схема ответа LLM. Лишние поля запрещены."""

    model_config = ConfigDict(extra="forbid", use_enum_values=False)

    category: Category
    summary: str = Field(min_length=1, max_length=500)
    priority: Priority
    next_action: str = Field(min_length=1, max_length=500)
    fields: Dict[str, str] = Field(default_factory=dict)
    confidence: Confidence
    escalate: bool

    @model_validator(mode="after")
    def _enforce_escalation_rule(self) -> "LLMResult":
        """Правило контроля качества: confidence=low всегда ведёт к эскалации."""
        if self.confidence == Confidence.LOW and not self.escalate:
            self.escalate = True
        return self


class ProcessingRecord(BaseModel):
    """Запись журнала аудита."""

    model_config = ConfigDict(extra="forbid")

    id: Optional[int] = None
    created_at: datetime
    raw_input: str
    result: Optional[LLMResult] = None
    status: ProcessingStatus
    error: Optional[str] = None
    model: Optional[str] = None