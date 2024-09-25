from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional

class PaymentMethodsResponse(BaseModel):
    id: int
    method: str