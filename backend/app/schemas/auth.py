from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from app.models.user import UserRole

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, description="Password must be at least 6 characters")
    first_name: str = Field(..., min_length=1)
    last_name: str = Field(..., min_length=1)
    role: UserRole = UserRole.RECRUITER

class UserOut(BaseModel):
    id: str
    email: EmailStr
    first_name: str
    last_name: str
    role: UserRole
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    email: str | None = None
    id: str | None = None
    role: str | None = None
