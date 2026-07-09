"""User Pydantic schemas"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "doctor"
    linked_patient_id: Optional[int] = None


class UserLogin(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    role: str
    linked_patient_id: Optional[int]
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None
