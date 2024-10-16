import os
import shortuuid
import firebase_conf
import json

from firebase_admin import auth, db, storage
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    File,
    UploadFile,
    Form,
    Query,
    Header,
    Response
)
from datetime import datetime
from typing import List, Optional
from geopy.distance import geodesic

from firebase_conf import firebase
from documentation.services import services as services_documentation

from schemas.services.services import *
from utils.user import get_current_user
from utils.services_categories import get_services_categories
from utils.services import (
    get_payment_method,
    get_service_by_id,
    update_service_in_db,
    delete_service_from_db,
    upload_service_image
)
from utils.location import get_location_name

router = APIRouter()

async def getReviewsWithReviewers(reviews):
    data_array = []

    for review in reviews:
            
        # Получаем данные пользователя добавившего комментарий
        user_ref = db.reference(f'/users/{review["reviewer_uid"]}')
        user_data = user_ref.get()

        if user_data is not None:
            review["reviewer"] = {
                "avatar": user_data["avatar"] or None,
                "username": user_data["username"]
            }

        # Добавляем объект в массив для отправки
        data_array.append(review)
    return data_array
    

@router.get('/get_service_reviews',
    summary="Получение комментариев услуги.",
    description=services_documentation.get_service_reviews
)
async def get_service_reviews(
    service_id: str
):
    # Получаем услугу
    service_ref = db.reference(f'/services/{service_id}')
    service_data = service_ref.get()

    # Создаём пустой массив данных для отправки
    data_array = []
    
    if "reviews" in service_data:

        # Получаем массив с коментариями и данными пользователя
        data_array = await getReviewsWithReviewers(service_data["reviews"])

    # Отправляем массив
    return data_array

@router.post('/add_new_review',
    summary="Добавление комментария к усулге.",
    description=services_documentation.add_new_review
)
async def add_new_review(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    request_data = await request.json()
    uid = request_data.get('uid')
    service_id = request_data.get('service_id')
    rating = request_data.get('rating')
    message = request_data.get('message')

    print(request_data)
    # Провряем пользователя на авторизованность
    if uid != current_user["uid"]:
        raise HTTPException(status_code=403, detail="Неавторизованный пользователь.")
    
    # Получаем данные пользователя
    user_ref = db.reference(f'/users/{uid}')
    user_data = user_ref.get()

    # Проверка на существование пользователя
    if user_data is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # Получение услуги
    service_ref = db.reference(f'/services/{service_id}')
    service_data = service_ref.get()

    # Проверка на существование услуги
    if service_data is None:
        raise HTTPException(status_code=404, detail="Услуга не найдена.")
    
    # Проверка оставлял ли пользователь уже комментарий
    if "reviews" in service_data:
        for review in service_data["reviews"]:
            if review["reviewer_uid"] == user_data["uid"]:
                raise HTTPException(status_code=405, detail="Пользователь уже оставлял комментарий.")

    date_now = datetime.now().isoformat()

    # Создаём объект комментария
    new_review = {
        "reviewer_uid": user_data["uid"],
        "rating": rating,
        "created_at": date_now
    }

    if message is not None and message != 'null' and len(message) > 0:
        new_review["message"] = message

    # Обнавляем данные service_data
    if "reviews" not in service_data:
        service_data["reviews"] = []
    
    service_data["reviews"].append(new_review)

    service_ref.set(service_data)

    # Получаем массив с комментариями и информацией пользвоателя
    reviews_array = await getReviewsWithReviewers(service_data["reviews"])

    # Обнавляем последнюю активность пользователя

    # Обновляем время последней активности
    user_data["last_active"] = date_now

    # Записываем обновленные данные в базу
    user_ref.set(user_data)
    
    return reviews_array
