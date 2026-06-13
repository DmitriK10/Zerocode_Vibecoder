from pydantic import BaseModel
from datetime import datetime

class MessageResponse(BaseModel):
    message: str

class DateTimeResponse(BaseModel):
    current_datetime: datetime
    timestamp: float