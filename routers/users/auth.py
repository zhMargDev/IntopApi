import firebase_admin
import uuid
import requests

from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, Request, status, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from firebase_admin import auth, db, credentials, messaging, storage
from firebase_admin.exceptions import FirebaseError

from firebase_conf import firebase, FIREBASE_API_KEY
from database import get_db
from models.models import User, Role
from schemas.user import *
from utils.token import decode_access_token, update_token
from utils.user import update_last_active, upload_user_avatar
from schemas.sms import *
from documentation.users import auth as authorization_documentation
from utils.user import get_current_user

router = APIRouter()

# Инициализация CryptContext для хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password):
    # Хеширование пароля
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    # Проверка 2х паролей с хешированием
    return pwd_context.verify(plain_password, hashed_password)


@router.get("/protected",
            summary="Проверка пользователя на аутентификацию",
            description="Описание защищенного маршрута")
async def protected_route(current_user: dict = Depends(get_current_user)):
    # Получаем ссылку на узел пользователей
    ref = db.reference(f'users/{current_user["uid"]}')
    user_data = ref.get()

    if not user_data:
        raise HTTPException(status_code=404, detail="Пользователь не найден.")

    # Обновляем последнюю активность пользователя
    await update_last_active(uid=current_user["uid"])

    return {"message": "This is a protected route", "user": user_data}


@router.post("/refresh_token",
              summary="Обнавление токена пользователя.",
              description=authorization_documentation.refresh_token)
async def refresh_token(request: RefreshTokenRequest):
    try:
        py_auth = firebase.auth()
        # Обновление токена с использованием refresh token
        new_token = py_auth.refresh(request.refresh_token)
        print (new_token)

        return {"id_token": new_token['idToken'], "refresh_token": new_token['refreshToken']}
    except auth.InvalidSessionCookieError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/register_with_email",
             summary="Регистрация через email.",
             description=authorization_documentation.register_with_phone_number_description)
async def register_with_email(data: User):
    try:
        # создание нового пользователя в firebase с флагом is_verified = false
        user = auth.create_user(
            email=data.email,
            password=data.password,
            email_verified=False
        )

        data.created_at = data.created_at.isoformat()
        data.last_active = data.last_active.isoformat()

        # преобразование модели user в словарь для записи в realtime database
        # исключаем пароль из данных для записи
        user_data_dict = data.dict(exclude={"password"})
        user_data_dict["uid"] = user.uid
        user_data_dict["username"] = data.username

        # сохранение всех данных в realtime database
        db.reference("users").child(user.uid).set(user_data_dict)

        # получение экземпляра аутентификации
        py_auth = firebase.auth()

        # выполнение входа пользователя для получения токена
        user_credentials = py_auth.sign_in_with_email_and_password(
            data.email, data.password)

        print(user_credentials)
        id_token = user_credentials['idToken']

        # отправка письма с кодом подтверждения
        try:
            py_auth.send_email_verification(id_token)
            print("письмо с кодом подтверждения отправлено на", data.email)
        except exception as e:
            print("ошибка при отправке письма:", str(e))

        # возврат сообщения об успешной регистрации
        return {"message": "пользователь успешно зарегистрирован. пожалуйста, проверьте вашу почту для подтверждения."}
    except FirebaseError as e:
        raise httpexception(status_code=400, detail=str(e))

@router.post("/auth_with_phone",
             summary="Регистрация через номер телефона.",
             description=authorization_documentation.register_with_email_description)
async def auth_with_phone(data: User):
    try:
        # Проверяем, чтобы был отправлен номер телефона
        if data.phone_number is None:
            raise HTTPException(status_code=422, detail="Номер не указан.")

        # Проверяем, существует ли аккаунт пользователя в узле users/uid в Realtime Database
        user_ref = db.reference("users").order_by_child("phone_number").equal_to(data.phone_number).get()

        # Если аккаунт с указанным номером телефона существует, возвращаем сообщение
        if user_ref:
            return {"message": "Аккаунт с указанным номером телефона уже существует."}

        # Получение данных пользователя из Firebase Authentication
        user_record = auth.get_user_by_phone_number(data.phone_number)

        data.created_at = data.created_at.isoformat()
        data.last_active = data.last_active.isoformat()

        # Преобразование модели User в словарь для записи в Realtime Database
        user_data_dict = data.dict()
        user_data_dict["uid"] = user_record.uid
        user_data_dict["username"] = data.username

        # Сохранение всех данных в Realtime Database
        db.reference("users").child(user_record.uid).set(user_data_dict)

        # Возврат сообщения об успешной регистрации
        return {"message": "Аккаунт успешно зарегистрирован."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login_with_email",
             summary="Вход через email.",
             description=authorization_documentation.login_with_email_description)
async def login_with_email(data: EmailRegistration, response: Response):
    try:
        py_auth = firebase.auth()
        # Выполнение входа пользователя для получения токена
        user_credentials = py_auth.sign_in_with_email_and_password(
            data.email, data.password)
        id_token = user_credentials['idToken']
        refresh_token = user_credentials['refreshToken']

        # Получение пользователя по email
        user = auth.get_user_by_email(data.email)

        if not user.email_verified:
            raise HTTPException(
                status_code=403, detail="Пользователь не верифицирован. Пожалуйста, проверьте вашу почту для подтверждения.")

        # Установка токена в куки
        response = JSONResponse(content={
                                "message": "Пользователь авторизован.", "user": user.uid, "jwtToken": id_token, "refresh_token": refresh_token})

        return response
    except FirebaseError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post('/auth_with_google',
             summary="Авторизация через гугл аккаунт.",
             description="Пусто")
async def auth_with_google(data: GoogleAccountUser):
    try:
        # Подготавливаем данные для записи в базу данных
        user_data_dict = data.dict()
        user_data_dict['last_active'] = datetime.now().isoformat()

        # Проверяем, существует ли пользователь
        existing_user_data = db.reference("users").child(data.uid).get()

        
        # Скачиваем изображение и загружаем его в Firebase Storage (Заборожен)
        #avatar_url = data.avatar
        #response = requests.get(avatar_url)
        #if not existing_user_data or 'avatar' not in existing_user_data:
        #    if response.status_code == 200:
        #        res = await upload_user_avatar(response.content, data.uid)
        #        if not res:
        #            raise HTTPException(
        #                status_code=400, details="Ошибка при добавлении картинки.")
        #        user_data_dict['avatar'] = res

        # Если пользователь существует, обновляем только измененные поля
        if existing_user_data:
            # Создаем словарь с изменениями
            updates = {k: v for k, v in user_data_dict.items() if v !=
                       existing_user_data.get(k)}
            # Обеспечиваем обновление last_active
            updates['last_active'] = user_data_dict['last_active']

            # Сохраняем существующую роль, если она не была передана в запросе
            if 'role' in existing_user_data:
                updates['role'] = existing_user_data.get('role')

            db.reference("users").child(data.uid).update(updates)
        # Иначе создаем нового пользователя с ролью "buyer"
        else:
            user_data_dict['created_at'] = datetime.now().isoformat()
            user_data_dict['role'] = 'buyer'  # Присваиваем роль по умолчанию
            db.reference("users").child(data.uid).set(user_data_dict)

        # Получаем обновленные данные пользователя из базы данных
        updated_user_data = db.reference("users").child(data.uid).get()

        return {"message": "Данные пользователя успешно обновлены", "user": updated_user_data}

    except firebase_admin.exceptions.FirebaseError as e:
        raise HTTPException(status_code=400, detail=str(e))

# Телеграм авторизация


@router.post("/tg_authorization",
             summary="Авторизация через Telegram",
             description=authorization_documentation.tg_authorization)
async def tg_authorization(init_data: TelegramInitData, db: Session = Depends(get_db)):
    # Поиск пользователя по Telegram ID
    user = db.query(User).filter(User.telegram_id == str(init_data.id)).first()

    if user:
        # Обновление информации о существующем пользователе
        user.first_name = init_data.first_name
        user.second_name = init_data.last_name
        user.username = init_data.username
        user.last_active = datetime.now()  # Обновляем время последнего действия

        # Проверка и обновление состояния is_active
        if not user.is_active:
            user.is_active = True

        db.commit()
        db.refresh(user)
    else:
        # Создание нового пользователя
        user = User(
            telegram_id=str(init_data.id),
            first_name=init_data.first_name,
            second_name=init_data.last_name,
            username=init_data.username,
            last_active=datetime.now(),  # Обновляем время последнего действия
            created_at=datetime.now(),  # Добавляет дату создания аккаунта
            is_active=True  # Устанавливаем is_active в True для нового пользователя
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # Переоброзование времени последней активности в строку для передачи через json
    user.last_active = user.last_active.isoformat()
    # Создаем ответ с использованием UserResponse
    user_response = UserResponse.from_orm(user)

    # Обновляем токен и устанавливаем его в куки
    response = JSONResponse(content=user_response.dict())
    response = update_token(response, user.id)

    return response
