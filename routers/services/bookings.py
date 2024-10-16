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

from firebase_conf import firebase
from documentation.services import services as services_documentation

from schemas.services.services import *
from utils.user import get_current_user

router = APIRouter()


@router.post(
    "/book_service",
    summary="Бронирование услуги.",
    description=services_documentation.book_service,
)
async def book_service(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    request_data = await request.json()
    uid = request_data.get("uid")
    service_id = request_data.get("service_id")
    date = request_data.get("date")
    time = request_data.get("time")

    if current_user["uid"] != uid:
        raise HTTPException(
            status_code=401, detail="Неиндентифицированный пользователь."
        )

    if not date or not service_id:
        raise HTTPException(
            status_code=422, detail="Неправильные данные."
        )

    # Получаем данные пользователя
    user_ref = db.reference(f"/users/{uid}")
    user_data = user_ref.get()

    if user_data is None:
        raise HTTPException(
            status_code=404, detail="Пользователь не найден."
        )

    # Проверяем, не бронировал ли пользователь уже эту услугу
    if "booked_services" in user_data:
        for booking in user_data["booked_services"]:
            if booking["service_id"] == service_id:
                raise HTTPException(
                    status_code=401, detail="Вы уже бронировали эту услугу."
                )

    # Проверяем, чтобы пользователь не был владельцем объявления
    service = db.reference(f"/services/{service_id}").get()
    if not service:
        raise HTTPException(
            status_code=404, detail="Услуга не найдена."
        )

    if service["owner_id"] == uid:
        raise HTTPException(
            status_code=401, detail="Владелец не может забронировать."
        )

    # Генерация идентификатора
    booking_id = shortuuid.uuid()

    def check_id_unique(booking_id):
        # Проверка существования идентификатора в базе данных
        if db.reference(f"/booking_services/{booking_id}").get() is not None:
            return check_id_unique(shortuuid.uuid())
        return booking_id

    booking_id = check_id_unique(booking_id)

    # Сохранение информации о новой услуге в базу данных
    booking_data = {
        "id": booking_id,
        "user_id": uid,
        "service_id": service_id,
        "date": date,
        "service_owner_id": service["owner_id"],
        "booked_at": datetime.now().isoformat(),
        "status": "booked"
    }

    if time is not None:
        booking_data["time"] = time

    # Добавляем новую запись в Firebase Realtime Database
    db.reference(f"/booked_services/{booking_id}").set(booking_data)

    # Добавляем идентификатор бронирования в список booked_services пользователя
    if "booked_services" not in user_data:
        user_data["booked_services"] = []
    user_data["booked_services"].append(booking_data)
    user_ref.set(user_data)

    return {"message": "Услуга успешно забронирована", "booking": booking_data}


@router.get(
    "/get_user_booked_services",
    summary="Получение забронированных услуг пользователем.",
    description=services_documentation.get_user_booked_services
)
async def get_user_booked_services(current_user: dict = Depends(get_current_user)):
    # Проверка на существование пользователя из токена
    # Получаем данные текущего пользователя из Realtime Database
    ref = db.reference(f'/users/{current_user["uid"]}')
    user_data = ref.get()

    if user_data is None:
        raise HTTPException(status_code=403, detail="Недействительный токен")

    if 'booked_services' not in user_data:
        raise HTTPException(
            status_code=404, detail="Забронированных услуг не найдено")

    booked_services = user_data['booked_services']
    data = []

    for booking in booked_services:
        # Получаем данные услуги
        service_ref = db.reference(f'/services/{booking["service_id"]}')
        service_data = service_ref.get()

        if service_data is None:
            # если услуга не найдена, удаляем её из списка забронированных услуг пользователя
            booked_services.remove(booking)
            ref.update({'booked_services': booked_services})
            continue

        # Получаем данные владельца услуги
        owner_id = service_data.get('owner_id')
        if owner_id:
            owner_ref = db.reference(f'/users/{owner_id}')
            owner_data = owner_ref.get()
        else:
            owner_data = None

        # Формируем данные для ответа
        data.append({
            'service': service_data,
            'owner': owner_data,
            'booking': booking
        })
    if len(data) < 1:
        raise HTTPException(
            status_code=404, detail="Забронированных услуг не найдено")

    return data

@router.delete('/cancel_booking',
    summary="Отмена бронирования."
)
async def cancel_booking(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    request_data = await request.json()
    uid = request_data.get("uid")
    booking_id = request_data.get("booking_id")
    if not uid or uid != current_user["uid"]:
        raise HTTPException(status_code=403, detail="Неидентифицированный пользователь.")
    
    if not booking_id:
        raise HTTPException(status_code=422, detail="Id бронирования не указан.")
        
    user_ref = db.reference(f"/users/{uid}")
    user_data = user_ref.get()
    if user_data is None:
        raise HTTPException(status_code=403, detail="Неидентифицированный пользователь.")
        
    owner_id = None
    # Проверяем есть ли у пользователя бронь данного сервиса
    if "booked_services" in user_data:
        for booking in user_data["booked_services"]:
            if booking["id"] == booking_id:
                owner_id = booking["service_owner_id"]
                user_data["booked_services"].remove(booking)
                break
    
    # Сохраняем изменения в базе данных Firebase
    user_ref.set(user_data)
    if owner_id is not None:
        owner_ref = db.reference(f'/users/{owner_id}')
        owner_data = owner_ref.get()
        if owner_data is not None and "my_booked_services" in owner_data:
            for booking in owner_data["my_booked_services"]:
                if booking["id"] == booking_id:
                    owner_data["my_booked_services"].remove(booking)
    return {"message": "Бронирование успешнно удалено."}
    try:
        pass
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Error: {e}")