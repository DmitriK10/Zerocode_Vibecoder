"""Strict JSON schema for the LLM extraction output.

Two levels of safety:

* ``extra="forbid"`` — any unexpected key is a hard error, so a
  ``prompt injection`` cannot smuggle new fields.
* ``model_validator`` — consistency checks that JSON Schema cannot express
  (e.g. ``needs_review=True`` requires a non-empty ``review_reason``).
"""

from __future__ import annotations

from datetime import date
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

PriorityLiteral = Literal["low", "medium", "high"]
SeverityLiteral = Literal["soft", "critical"]


class LLMActionItem(BaseModel):
    """A single action item as returned by the model."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=200)
    assignee: str | None = Field(default=None, max_length=120)
    due_date_raw: str | None = Field(default=None, max_length=120)
    due_date_iso: date | None = None
    priority: PriorityLiteral
    source_quote: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    needs_review: bool
    review_reason: str | None = None
    review_severity: SeverityLiteral | None = None

    @model_validator(mode="after")
    def _check_consistency(self) -> Self:
        if self.needs_review and not (self.review_reason or "").strip():
            raise ValueError(
                "needs_review=True requires a non-empty review_reason"
            )
        if self.review_severity is not None and not self.needs_review:
            raise ValueError(
                "review_severity must be null when needs_review is False"
            )
        return self


class LLMExtraction(BaseModel):
    """Root object returned by the model."""

    model_config = ConfigDict(extra="forbid")

    actions: list[LLMActionItem]