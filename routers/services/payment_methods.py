import firebase_conf

from fastapi import APIRouter, HTTPException, Depends, Request, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from firebase_admin import auth, db

from schemas.services.payment_methods import PaymentMethodsResponse\

router = APIRouter()

@router.get("/all", 
             summary="Получение всех способов оплаты.",
             description="Получение всех способов оплаты.",
             response_model=List[PaymentMethodsResponse])
async def get_all_payment_methods():
    # Получаем все способы оплаты
    payment_methods_ref = db.reference("/payments_methods")
    payment_methods_snapshot = payment_methods_ref.get()
    # Если данных не найдено
    if not payment_methods_snapshot:
        raise HTTPException(status_code=404, detail="Способов оплаты не найдено.")

    return payment_methods_snapshot