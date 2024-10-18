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
from datetime import datetime, timedelta
from typing import List, Optional

from firebase_conf import firebase
from utils.user import get_current_user
from utils.notifications import set_notifications_array, delete_notifications
from documentation.users import notifications as notifications_documentation

router = APIRouter()


@router.get('/all',
    summary="Получение всех уведомлений пользователя.",
    description=notifications_documentation.get_all_user_notifications)
async def get_all_user_notifications(
    uid: str,
    current_user: dict = Depends(get_current_user),
):
    if current_user["uid"] != uid:
        raise HTTPException(
            status_code=403, detail="Неиндентифицированный пользователь."
        )

    # Получаем данные пользователя
    user_ref = db.reference(f"/users/{uid}")
    user_data = user_ref.get()

    if not user_data:
        raise HTTPException(
            status_code=404, detail="Пользователь не найден."
        )
    
    if "notifications" not in user_data:
       raise HTTPException(
            status_code=405, detail="Уведомлений не найдено."
        ) 
    notifications = await set_notifications_array(user_data["notifications"])
    # Возвращаем данные
    return notifications

@router.delete('/by_ids_array',
    summary="Удаление уведомлений пользователя по массиву с id.",
    description=notifications_documentation.by_ids_array
)

async def delete_selected_norifications(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    request_data = await request.json()
    uid = request_data.get("uid")
    ids = request_data.get('ids')

    if current_user["uid"] != uid or not uid:
        raise HTTPException(
            status_code=403, detail="Неиндентифицированный пользователь."
        )

    if not ids or len(ids) < 1:
        raise HTTPException(
            status_code=404, detail="Массив с id уведомлений не найден."
        )

    # Получаем данные пользователя
    user_ref = db.reference(f"/users/{uid}")
    user_data = user_ref.get()

    if not user_data:
        raise HTTPException(
            status_code=404, detail="Пользователь не найден."
        )
    
    if "notifications" not in user_data:
       raise HTTPException(
            status_code=405, detail="Уведомлений не найдено."
        ) 

    # Удаляем ненужные
    new_array = await delete_notifications(user_data["notifications"], ids)

    # Сохраняем новый массив
    user_data["notifications"] = new_array

    # Сохарняем данные в базе
    user_ref.set(user_data)

    # Генерируем новые данные
    notifications = await set_notifications_array(user_data["notifications"])

    # Возвращаем данные
    return notifications