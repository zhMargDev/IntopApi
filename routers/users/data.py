import shutil
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
    Response,
)
from sqlalchemy.orm import Session, joinedload
from starlette.responses import JSONResponse
from datetime import datetime

from firebase_conf import firebase
from database import get_db
from models.models import User
from schemas.user import UserGetByFilters
from utils.token import decode_access_token, update_token
from config import BASE_DIR
from documentation.users import data as user_documentation
from schemas.user import *
from utils.user import get_current_user, update_last_active, upload_user_avatar_with_file, delete_picture_from_storage


router = APIRouter()


@router.put(
    "/change_location",
    summary="Изменение локации пользователя",
    description=user_documentation.update_user_location,
)
async def change_user_location(
    request: Request, current_user: dict = Depends(get_current_user)
):
    request_data = await request.json()
    uid = request_data.get("uid")
    lat = request_data.get("lat")
    lon = request_data.get("lon")

    # Проверка данных на правильность
    if not uid or uid != current_user["uid"]:
        raise HTTPException(
            status_code=403, detail="Пользователь не идентифицирован.")
    if not lat or not lon:
        raise HTTPException(
            status_code=422, detail="Неправильные данные локации.")

    # Проверка локации на тип float
    try:
        lat = float(lat)
        lon = float(lon)
    except:
        raise HTTPException(
            status_code=422, detail="Лоакция должна быть в формате цифры с запятой."
        )

    try:
        # Получение пользователя
        user_ref = db.reference(f'users/{current_user["uid"]}')
        user = user_ref.get()

        if not user:
            raise HTTPException(
                status_code=404, detail="Пользователь не найден.")

        # Обновляем или создаем локацию
        user_ref.update({"location": {"lat": float(lat), "lon": float(lon)}})

        return {"message": "Локация пользователя обновлена."}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Ошибка доступа к базе данных: {e}"
        )


@router.put(
    "/update",
    summary="Обновление данных пользователя",
    description=user_documentation.update_user,
)
async def update_user(
    current_user: dict = Depends(get_current_user),
    uid: str = Form(None),
    username: str = Form(None),
    avatar: UploadFile = File(None),
    old_password: str = Form(None),
    new_password: str = Form(None)
):
    try:
        if current_user["uid"] != uid:
            raise HTTPException(
                status_code=403, detail="Неидентифицированный пользователь."
            )

        # Получаем данные пользователя из Realtime Database
        user_ref = db.reference(f"users/{uid}")
        user_data = user_ref.get()

        update_status = {
            "username": "no",
            "avatar": "no",
            "password": "no"
        }

        # Проверяем отправлен ли параметр и изменяем его
        if username:
            user_data["username"] = username
            update_status["username"] = "success"
        else:
            update_status["username"] = "Имя не указано."

        if avatar:
            # Если у пользователя была картинка, удаляем её
            if user_data.get("avatar"):
                await delete_picture_from_storage(user_data["avatar"])

            user_avatar_url = await upload_user_avatar_with_file(avatar, uid)
            user_data["avatar"] = user_avatar_url
            update_status["avatar"] = "success"

        py_auth = firebase.auth()

        if new_password:
            if not old_password:
                update_status["password"] = "Необходимо указать старый пароль для изменения пароля"
            else:
                # Проверяем старый пароль
                try:
                    # Повторная аутентификация с использованием старого пароля
                    user = py_auth.sign_in_with_email_and_password(
                        user_data["email"], old_password)
                    # Обновление пароля
                    auth.update_user(uid, password=new_password)
                    update_status["password"] = "success"
                except Exception as e:
                    update_status["password"] = "Действующий пароль указан неверно."

        # Обновляем время последней активности
        user_data["last_active"] = datetime.now().isoformat()

        # Записываем обновленные данные в базу
        user_ref.set(user_data)

        return update_status
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Ошибка на стороне сервера: {str(e)}")


@router.delete(
    "/deactivate",
    summary="Деактивация (удаление) аккаунта пользователя",
    description=user_documentation.deactivate_user,
)
async def deactivate_account(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    try:
        if current_user["uid"] != request.uid:
            raise HTTPException(
                status_code=401, details="Неидентифицированный пользователь."
            )
        # Получить пользователя по UID
        user = auth.get_user(request.uid)

        # Деактивировать пользователя
        user.disabled = True
        user.update()

        return {"message": "Аккаунт успешно удалён."}

    except:
        raise HTTPException(status_code=401, detail="Недействительный UID")


@router.get(
    "/by_filters",
    summary="Получение пользователей по фильтрам",
    description=user_documentation.get_users_by_filters,
)
async def get_users_by_filters(
    filters: UserGetByFilters = Depends(),
):
    """Получает пользователей из Firebase Realtime Database по заданным фильтрам.

    Аргументы:
        filters: Объект с фильтрами для поиска пользователей.

    Возвращает:
        Список объектов User, соответствующих фильтрам.
        Если пользователей не найдено, выбрасывается исключение HTTPException с кодом 404.
    """

    # Получаем ссылку на узел пользователей
    ref = db.reference("/users")

    query = ref

    # Применяем фильтры
    if filters.uid is not None:
        query = query.order_by_child("uid").equal_to(filters.uid)
    if filters.role is not None:
        query = query.order_by_child("role").equal_to(filters.role)
    if filters.username:
        query = (
            query.order_by_child("username")
            .start_at(filters.username)
            .end_at(filters.username + "\uf8ff")
        )
    if filters.first_name:
        query = (
            query.order_by_child("first_name")
            .start_at(filters.first_name)
            .end_at(filters.first_name + "\uf8ff")
        )
    if filters.last_name:
        query = (
            query.order_by_child("last_name")
            .start_at(filters.last_name)
            .end_at(filters.last_name + "\uf8ff")
        )
    if filters.phone_number:
        query = (
            query.order_by_child("phone_number")
            .start_at(filters.phone_number)
            .end_at(filters.phone_number + "\uf8ff")
        )
    if filters.email:
        query = (
            query.order_by_child("email")
            .start_at(filters.email)
            .end_at(filters.email + "\uf8ff")
        )
    if filters.region_id is not None:
        query = query.order_by_child("region_id").equal_to(filters.region_id)

    # Получаем результаты
    snapshot = await query.get()

    # Преобразуем результаты в объекты User, исключая пароль
    users = []
    async for user_data in snapshot.each():
        user_data = user_data.val()
        # Удаляем поле password, если оно существует
        user_data.pop("password", None)
        user = User(**user_data)
        users.append(user)

    if not users:
        raise HTTPException(status_code=404, detail="Пользователи не найдены")

    return users


@router.get(
    "/get_by_id",
    summary="Получение пользователь по UID.",
    description=user_documentation.get_by_id,
)
async def getUserById(uid: str):
    try:
        # Получаем ссылку на узел пользователей
        ref = db.reference(f"/users/{uid}")

        # Получаем данные пользователя
        user_data = ref.get()

        if user_data is None:
            raise HTTPException(
                status_code=404, detail="Пользователь не найден")

        # Удаляем поле пароля
        if "password" in user_data:
            del user_data["password"]

        return user_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/like_user_event",
    summary="Добавление или удаление пользователя из лайков.",
    description=user_documentation.like_user_event,
)
async def likeUserEvent(
    request: Request, current_user: dict = Depends(get_current_user)
):
    try:
        # Получаем uid из POST запроса
        data = await request.json()
        uid = data.get("uid")

        if not uid:
            raise HTTPException(status_code=400, detail="UID не предоставлен")

        # Пользователь с префиксом U_ это тот кого добавляют или удаляют из лайков
        # Проверка на существования пользователя по отправленному uid
        u_ref = db.reference(f"/users/{uid}")
        u_user_data = u_ref.get()

        if u_user_data is None:
            raise HTTPException(
                status_code=404, detail="Пользователь не найден")

        # Получаем данные текущего пользователя из Realtime Database
        ref = db.reference(f'/users/{current_user["uid"]}')
        user_data = ref.get()

        if user_data is None:
            raise HTTPException(
                status_code=403, detail="Недействительный токен")

        # Проверяем, есть ли список liked_users
        if "liked_users" not in user_data:
            user_data["liked_users"] = []

        res_status_code = 200
        res_text = ""

        # Проверяем, есть ли uid в списке liked_users
        if uid in user_data["liked_users"]:
            user_data["liked_users"].remove(uid)
            res_status_code = 200
            res_text = "Пользователь удален из лайков"
        else:
            # Если пользователя не было в массиве, то добавляем
            user_data["liked_users"].append(uid)
            res_status_code = 201
            res_text = "Пользователь добавлен в лайки"

        # Обновляем данные пользователя в базе данных
        ref.update(user_data)
        
        return Response(
            status_code=res_status_code,
            content=json.dumps({"message": res_text}),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post('/save_workgin_days',
             summary="Изменение рабочих дней пользователя.",
             description=user_documentation.save_working_days)
async def save_workgin_days(
    request: Request, 
    current_user: dict = Depends(get_current_user)
):
    try:
        # Проверяем чтобы пользователь был авторизованным и тем кто должен быть
        request_data = await request.json()
        uid = request_data.get('uid')
        working_week_days = request_data.get('working_week_days')

        user_ref = db.reference(f'users/{current_user["uid"]}')
        user_data = user_ref.get()

        if not uid or uid != current_user["uid"] or not user_data:
            raise HTTPException(status_code=403, detials="Неидентифицированный пользователь.")
        
        if not working_week_days:
            raise HTTPException(status_code=404, details="Рабочие дни не отправлены.")
        
        if len(working_week_days) != 7:
            raise HTTPException(status_code=402, details="Неправильное количество дней в неделе.")
        
        keys = ["title", "active", "start_time", "end_time"]
        # Проверка формата данных в массиве
        for day in working_week_days:
            for key in keys:
                if not key in day:
                    raise HTTPException(status_code=422, detail="Неправильный формат данных.")
        
        # Регулярное выражение для проверки формата HH:MM
        time_pattern = re.compile(r'^([01][0-9]|2[0-3]):[0-5][0-9]$')

        data = []
        # Проверяем чтобы все данные в working_week_days были правильными
        for day in working_week_days:
            title = day["title"]

            start_time_flag = False
            end_time_flag = False

            if day["active"]:
                start_time_flag = time_pattern.match(day["start_time"])
                end_time_flag = time_pattern.match(day["end_time"])

            if day["active"] and start_time_flag and end_time_flag:
                data.append({
                    "title": title,
                    "active": True,
                    "start_time": day["start_time"],
                    "end_time": day["end_time"]
                })
            else:
                data.append({
                    "title": title,
                    "active": False,
                    "start_time": "",
                    "end_time": ""
                })
            
        user_data["working_week_days"] = data
        user_ref.update(user_data)


        return Response(
            status_code=200,
            content=json.dumps({"data": working_week_days}),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))