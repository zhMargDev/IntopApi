from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime

# Схема для ответа по категории
class CategoryOut(BaseModel):
    id: int
    name: str
    subcategories: List['CategoryOut'] = []

    class Config:
        from_attributes = True
