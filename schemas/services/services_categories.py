from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional

class ServiceCategoryResponse(BaseModel):
    id: int
    title: str
    description: str
    picture: str
    subcats: List['ServiceCategoryResponse'] = []

    class Config:
        from_attributes = True