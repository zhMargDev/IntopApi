from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime

class StoreResponse(BaseModel):
    id: int
    name: str
    short_name: str
    llc_name: Optional[str] = None
    store_main_picture: Optional[str] = None
    address: Optional[str] = None
    region_id: Optional[int] = None
    category_id: int
    owner_id: int  
    rating: Optional[float] = None
    is_verified: Optional[bool] = None  
    created_at: str
    last_active: str
    
    class Config:
        from_attributes = True
        from_attributes=True