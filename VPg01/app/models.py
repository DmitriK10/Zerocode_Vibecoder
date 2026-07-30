from pydantic import BaseModel
from typing import List

class StructuredResponse(BaseModel):
    theses: List[str]
    message: str