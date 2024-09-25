import firebase_conf

from fastapi import APIRouter, HTTPException, Depends, Request, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from firebase_admin import auth, db

from database import get_db
from models.models import ServicesCategories
from utils.token import decode_access_token, update_token
from documentation.services import services_categories as services_categories_documentation
from schemas.services.services_categories import *
from utils.files import add_domain_to_picture
from utils.categories import find_category_by_id
from utils.services_categories import get_services_categories

router = APIRouter()

@router.get("/all", 
             summary="Получение всех сервисов или конкретного сервиса по id",
             description=services_categories_documentation.get_all_services_categories,
             response_model=List[ServiceCategoryResponse])
async def get_all_services_categories(
        id: Optional[int] = Query(None, description="ID сервиса для фильтрации")
    ):
    # Для получения категорий был преднозначен отдельный метод чтобы его можно было потом использовать в других эдпоинтах
    return await get_services_categories(id=id)