from pydantic import BaseModel, Field, field_validator

class LeadIn(BaseModel):
    """Входная схема для POST /lead"""
    name: str = Field(..., min_length=1, description="Имя клиента")
    contact: str = Field(..., min_length=1, description="Контакт (телефон/email)")
    source: str = Field(..., min_length=1, description="Источник заявки")
    comment: str = Field(default="", description="Комментарий")

    @field_validator('contact')
    @classmethod
    def contact_not_empty(cls, v: str) -> str:
        """Проверяет, что контакт не пустой и не состоит из пробелов"""
        if not v or not v.strip():
            raise ValueError('Контакт не может быть пустым')
        return v.strip()

class LeadOut(BaseModel):
    """Выходная схема при успешном создании"""
    id: int
    message: str = "Lead saved successfully"