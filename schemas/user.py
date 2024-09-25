import re

from pydantic import BaseModel, EmailStr, Field, validator
from typing import List, Optional
from datetime import datetime


class PhoneVerificationRequest(BaseModel):
    phone_number: str


class EmailRegistration(BaseModel):
    email: str
    password: str


class PhoneVerification(BaseModel):
    phone_number: str
    code: Optional[str] = None
    password: str


class User(BaseModel):
    uid: Optional[str] = None
    username: str
    email: Optional[EmailStr] = None
    role: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    avatar: Optional[str] = None
    rating: int = Field(default=0)
    region_id: Optional[int] = None
    is_verified: Optional[bool] = None
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.now)
    last_active: datetime = Field(default_factory=datetime.now)
    password: str
    verification_id: Optional[str] = None
    verification_code: Optional[str] = None


class GoogleAccountUser(BaseModel):
    username: str
    email: str
    uid: str
    avatar: str
    role: Optional[str] = None

# Pydantic модель для получения данных


class TelegramInitData(BaseModel):
    id: int
    first_name: str
    last_name: str
    username: str


class RatingCreate(BaseModel):
    rater_id: int
    rated_id: int
    # Предполагаем, что рейтинг от 1 до 5
    rating: float = Field(..., gt=0, lt=6)


class UserGetByFilters(BaseModel):
    uid: Optional[str] = None
    role: Optional[str] = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    region_id: Optional[int] = None


class UserResponse(BaseModel):
    id: int
    telegram_id: int
    role_id: Optional[int] = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    second_name: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    avatar: Optional[str] = None
    rating: Optional[float] = None
    region_id: Optional[int] = None
    is_verified: Optional[bool] = None
    is_active: bool
    created_at: str
    last_active: str

    class Config:
        from_attributes = True


class EmailRegistrationRequest(BaseModel):
    email: EmailStr
    password: str
    username: str = None
    first_name: str = None
    second_name: str = None

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Пароль должен быть длиной не менее 8 символов')
        if not re.search(r'[A-Z]', v):
            raise ValueError(
                'Пароль должен содержать хотя бы одну заглавную букву')
        if not re.search(r'[a-z]', v):
            raise ValueError(
                'Пароль должен содержать хотя бы одну строчную букву')
        if not re.search(r'[0-9]', v):
            raise ValueError('Пароль должен содержать хотя бы одну цифру')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError(
                'Пароль должен содержать хотя бы один специальный символ')
        return v


class EmailLoginRequest(BaseModel):
    email: EmailStr = Field(..., description="Электронная почта пользователя")
    password: str = Field(..., min_length=8, description="Пароль пользователя")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "test@example.com",
                "password": "Testing123!"
            }
        }


class EmailSMSRequest(BaseModel):
    email: EmailStr = Field(..., description="Электронная почта пользователя")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "test@example.com"
            }
        }
