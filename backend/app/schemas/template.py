from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.models.application import TemplateType

class PromptTemplateCreate(BaseModel):
    skill: str
    level: str
    type: TemplateType
    template_text: str

class PromptTemplateUpdate(BaseModel):
    skill: Optional[str] = None
    level: Optional[str] = None
    type: Optional[TemplateType] = None
    template_text: Optional[str] = None

class PromptTemplateOut(BaseModel):
    id: str
    skill: str
    level: str
    type: TemplateType
    template_text: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
