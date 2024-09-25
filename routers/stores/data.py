import shutil, os

from fastapi import APIRouter, Depends, HTTPException, Request, File, UploadFile, Form, Query
from sqlalchemy.orm import Session, joinedload
from starlette.responses import JSONResponse
from datetime import datetime

from database import get_db
from models.models import User, Store
from schemas.store import StoreResponse
from utils.token import decode_access_token, update_token
from config import BASE_DIR
from documentation.stores import data as stores_documentation

router = APIRouter()

@router.post('/create', summary="Создание нового магазина",
            description=stores_documentation.create_store)
async def create(
        request: Request,
        user_id: int = Form(...), # Id пользователя
        name: str = Form(...),  # Обязательное поле
        short_name: str = Form(...),  # Обязательное поле
        llc_name: str = Form(None),  # Опционально
        store_main_picture: UploadFile = File(None),  # Опционально
        address: str = Form(None),  # Опционально
        region_id: int = Form(None),  # Опционально
        category_id: int = Form(...),  # Обязательное поле
        db: Session = Depends(get_db)
    ):
    # Извлечение токена из куки
    token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(status_code=401, detail="Токен доступа отсутствует")

    # Получение user_id из токена
    try:
        payload = decode_access_token(token)
        token_user_id = int(payload['sub'])
    except HTTPException:
        raise HTTPException(status_code=401, detail="Недействительный токен")
    
    # Найти пользователя по user_id
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    # Проверка наличия магазина с таким же name, short_name или llc_name
    existing_store = db.query(Store).filter(
        (Store.name == name) |
        (Store.short_name == short_name) |
        (Store.llc_name == llc_name)
    ).first()
    
    if existing_store:
        if existing_store.name == name:
            raise HTTPException(status_code=400, detail="name")
        if existing_store.short_name == short_name:
            raise HTTPException(status_code=400, detail="short_name")
        if existing_store.llc_name == llc_name:
            raise HTTPException(status_code=400, detail="llc_name")

    # Ставим данные для нового магазина
    store = Store(
        name=name,
        short_name=short_name,
        category_id=category_id,
        owner_id=user_id,
    )
    if llc_name:
        store.llc_name = llc_name
    if address:
        store.address = address
    if region_id:
        store.region_id = region_id

    store.created_at = datetime.now()
    store.last_active = datetime.now()

    # Если отправленка картинка, то сохраняем его
    if store_main_picture:
        # Создание пути для картинки
        filename = f"{token_user_id}{os.path.splitext(store_main_picture.filename)[1]}"  # Сохранение оригинального расширения
        path = os.path.join(BASE_DIR, 'static', 'store_pictures', filename)

        # Сохранение картинки
        with open(path, 'wb') as out_file:
            shutil.copyfileobj(store_main_picture.file, out_file)

        # Обновляем путь к аватарке в базе данных
        store.store_main_picture = f"/static/users_avatars/{filename}"

    # Создаём магазин
    db.commit()
    db.refresh(store)

    # Переоброзование времени последней активности и даты создания в строку для передачи через json ! не сохраняем в базе
    store.last_active = store.last_active.isoformat()
    store.created_at = store.created_at.isoformat()

    # Создаем ответ с использованием UserResponse
    store_response = StoreResponse.from_orm(store)

    # Обновляем токен и устанавливаем его в куки
    response = JSONResponse(content=store_response.dict())
    response = update_token(response, user.id)

    return response