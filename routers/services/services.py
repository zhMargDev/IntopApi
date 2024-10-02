import os
import shortuuid
import firebase_conf

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
)
from sqlalchemy.orm import Session, joinedload
from starlette.responses import JSONResponse
from datetime import datetime
from typing import List, Optional
from geopy.distance import geodesic

from firebase_conf import firebase
from documentation.services import services as services_documentation
from database import get_db
from models.models import (
    Service,
    User,
    BookedService,
    ServicesCategories,
    PaymentMethod,
)
from schemas.services.services import *
from utils.files import add_domain_to_picture
from utils.token import decode_access_token, update_token
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
from utils.main import delete_picture_from_storage

router = APIRouter()


async def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Рассчитывает расстояние между двумя географическими точками в километрах.

    Args:
        lat1 (float): Широта первой точки.
        lon1 (float): Долгота первой точки.
        lat2 (float): Широта второй точки.
        lon2 (float): Долгота второй точки.

    Returns:
        float: Расстояние между точками в километрах.
    """

    # Создаем координаты точек
    coords_1 = (lat1, lon1)
    coords_2 = (lat2, lon2)

    # Рассчитываем расстояние по большой окружности
    return geodesic(coords_1, coords_2).kilometers


@router.get(
    "/by_filters",
    summary="Получение услуг по фильтрам.",
    description=services_documentation.get_services_by_filters,
)
async def get_services_by_filters(filters: ServicesGetByFilters = Depends()):
    filters.to_int_fields()
    py_db = firebase.database()

    # Get services
    services_ref = py_db.child("services").get()
    services = services_ref.val() or {}

    filtered_services = []
    for service_id, service_data in services.items():
        # Filter based on non-null and non-'null' filter values
        include_service = True
        if filters.category_id is not None and filters.category_id != "null":
            include_service &= (
                service_data.get("service_category_id",
                                 None) == filters.category_id
            )
        if (
            filters.payment_method_id is not None
            and filters.payment_method_id != "null"
        ):
            include_service &= (
                service_data.get("payment_method_id",
                                 None) == filters.payment_method_id
            )
        if filters.minPrice is not None and filters.minPrice != "null":
            service_price = service_data.get("price", None)
            include_service &= (
                service_price is not None and service_price >= filters.minPrice
            )
        if filters.maxPrice is not None and filters.maxPrice != "null":
            service_price = service_data.get("price", None)
            include_service &= (
                service_price is not None and service_price <= filters.maxPrice
            )

        # Filter by location if lat, lon, and distance are provided
        if (
            include_service
            and filters.lat is not None
            and filters.lon is not None
            and filters.distance is not None
        ):
            service_lat = service_data.get("lat", None)
            service_lon = service_data.get("lon", None)
            if service_lat is not None and service_lon is not None:
                distance_km = await calculate_distance(
                    filters.lat, filters.lon, service_lat, service_lon
                )
                include_service &= distance_km <= filters.distance

        # Add service to filtered list if all conditions are met
        if include_service:
            filtered_services.append(service_data)

    return filtered_services


@router.get(
    "/all",
    summary="Получение всех сервисов или конкретного сервиса по id",
    description=services_documentation.get_all,
    response_model=List[ServiceSchema],
)
async def get_services(
    id: Optional[str] = Query(None, description="ID сервиса для фильтрации"),
):
    # Если указан id, находим и возвращаем услугу по id
    if id is not None:
        ref = db.reference(f"/services/{id}")
        data = ref.get()

        if not data:
            raise HTTPException(
                status_code=404, detail="Услуга по указанному id не найдена."
            )

        return [data]

    # Получаем ссылку на узел услуг
    ref = db.reference("/services")
    data = ref.get()

    if not data:
        raise HTTPException(status_code=404, detail="Услуги не найдены.")

    # Преобразуем данные в список
    services = list(data.values())

    return services


@router.post(
    "/add",
    summary="Добавление новой услуги.",
    description=services_documentation.add_new_service,
)
async def add_new_service(
    current_user: dict = Depends(get_current_user),
    uid: str = Form(...),
    name: str = Form(...),
    lat: float = Form(...),
    lon: float = Form(...),
    description: str = Form(...),
    price: int = Form(...),
    currency: str = Form(...),
    pictures: List[UploadFile] = File(None),
    service_category_id: int = Form(...),
    payment_method_id: int = Form(None),
    start_time: str = Form(...),
    end_time: str = Form(...)
):
    # Проверка пользователя на авторизованность
    if uid != current_user["uid"]:
        raise HTTPException(
            status_code=401, detail="Неиндентифицированный пользователь."
        )

    # Проверка существования категории сервиса
    service_category = await get_services_categories(id=service_category_id)
    if not service_category:
        raise HTTPException(
            status_code=404, detail="Категория сервиса не найдена"
        )

    # Проверка существования способа оплаты, если указан
    if payment_method_id:
        if not get_payment_method(payment_method_id):
            raise HTTPException(
                status_code=404, detail="Такой способа оплаты не найдено."
            )

    # Генерация уникального идентификатора для нового сервиса
    service_id = shortuuid.uuid()

    def check_id_unique(service_id):
        # Проверка существования идентификатора в базе данных
        if db.reference(f"/services/{service_id}").get() is not None:
            return check_id_unique(shortuuid.uuid())
        return service_id

    service_id = check_id_unique(service_id)

    if pictures:
        # Загрузка картинок в Firebase Storage
        picture_urls = []
        for picture in pictures:
            # Чтение содержимого файла
            picture.file.seek(0)
            res_content = picture.file.read()

            # Загрузка файла и получение URL-адреса
            new_image_url = await upload_service_image(res_content, service_id, picture.content_type)
            picture_urls.append(new_image_url)
    
    location_name = await get_location_name(lat, lon)

    # Сохранение информации о новой услуге в базу данных
    service_data = {
        "id": service_id,
        "rating_count": 0,
        "views_count": 0,
        "is_active": True,
        "name": name,
        "lat": lat,
        "lon": lon,
        "description": description,
        "price": price,
        "currency": currency,
        "owner_id": uid,
        "is_store": False,
        "service_category_id": service_category_id,
        "location_name":location_name,
        "start_time": start_time,
        "end_time": end_time,
        "created_at": datetime.now().isoformat(),
    }

    if pictures:
        service_data["pictures"] = picture_urls
    # Если имеются время работы то добавляем их
    if payment_method_id:
        service_data["payment_method_id"] = payment_method_id

    # Добавляем новую запись в Firebase Realtime Database
    db.reference(f"/services/{service_id}").set(service_data)

    # Обновление данных пользователя
    user_ref = db.reference(f"/users/{uid}")
    user_data = user_ref.get()
    if "services" not in user_data:
        user_data["services"] = []
    user_data["services"].append(service_id)
    user_ref.set(user_data)

    return {"message": "Услуга успешно добавлена", "service": service_data}

@router.put(
    "/update",
    summary="Обновление сервиса.",
    description=services_documentation.update_service,
)
async def update_service(
    current_user: dict = Depends(get_current_user),
    uid: str = Form(...),
    service_id: str = Form(...),
    name: str = Form(...),
    lat: float = Form(...),
    lon: float = Form(...),
    description: str = Form(...),
    price: int = Form(...),
    currency: str = Form(...),
    new_pictures: List[UploadFile] = File(None),
    old_pictures: List[str] = Form(None),
    service_category_id: int = Form(...),
    payment_method_id: int = Form(None),
    start_time: str = Form(...),
    end_time: str = Form(...)
):
    # Получаем сервис по service_id
    service = await get_service_by_id(service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Сервис не найден.")

    # Проверяем, что owner_id сервиса совпадает с uid текущего пользователя
    if service.get("owner_id") != uid or uid != current_user["uid"]:
        raise HTTPException(
            status_code=403, detail="У вас нет прав для обновления этого сервиса."
        )
    
    location_name = await get_location_name(lat, lon)
    print(location_name)

    # Обновляем данные сервиса, которые были переданы в запросе
    updated_data = {
        "id": service_id,
        "rating_count": 0,
        "views_count": 0,
        "is_active": True,
        "name": name,
        "lat": lat,
        "lon": lon,
        "description": description,
        "price": price,
        "currency": currency,
        "location_name": location_name,
        "owner_id": uid,
        "is_store": False,
        "service_category_id": service_category_id,
        "start_time": start_time,
        "end_time": end_time
    }

    picture_urls = []

    bucket = storage.bucket()
    current_pictures = service.get("pictures", [])

    # Проверка и удаление старых картинок которых нету в old_pictures
    print(old_pictures)
    for picture_url in current_pictures:
        print(picture_url)
        if old_pictures:
            if picture_url not in old_pictures:    
                blob = bucket.blob(f'services/{service_id}/' + picture_url.split('/')[-1])
                blob.delete()
            else:
                # Сохраняем адреса картинок которые не были удалены
                picture_urls.append(picture_url)
        else:
            picture_urls.append(picture_url)

    # Добавление новых картинок
    if new_pictures:
        for picture in new_pictures:
            # Чтение содержимого файла
            picture.file.seek(0)
            res_content = picture.file.read()

            # Загрузка файла и получение URL-адреса
            new_image_url = await upload_service_image(res_content, service_id, picture.content_type)
            picture_urls.append(new_image_url)

    updated_data['pictures'] = picture_urls

    # Если имеются время работы то добавляем их
    if payment_method_id:
        updated_data["payment_method_id"] = payment_method_id

    # Обновляем сервис в базе данных
    await update_service_in_db(service_id, updated_data)

    return {
        "message": "Сервис успешно обновлен",
        "service": {**service, **updated_data},
    }

@router.delete(
    "/delete",
    summary="Удаление сервиса.",
    description=services_documentation.delete_service,
)
async def delete_service(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    request_data = await request.json()
    uid = request_data.get("uid")
    service_id = request_data.get("service_id")

    # Получаем сервис по service_id
    service = await get_service_by_id(service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Сервис не найден.")

    # Проверяем, что owner_id сервиса совпадает с uid текущего пользователя
    if service.get("owner_id") != uid or uid != current_user["uid"]:
        raise HTTPException(
            status_code=403, detail="У вас нет прав для удаления этого сервиса."
        )

    # Удаляем папку с картинками, связанные с услугой
    bucket = storage.bucket()
    blobs = bucket.list_blobs(prefix=f"services/{service_id}")
    for blob in blobs:
        blob.delete()

    # Удаляем сервис из базы данных
    await delete_service_from_db(service_id)

    # Обновление данных пользователя
    user_ref = db.reference(f"/users/{uid}")
    user_data = user_ref.get()
    if "services" in user_data:
        user_data["services"].remove(service_id)
    user_ref.set(user_data)

    return {"message": "Сервис успешно удален"}


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
            status_code=401, details="Неиндентифицированный пользователь."
        )

    # Проверяем чтобы пользователь не был владельцем объявления
    if db.reference(f"/services/{service_id}").get()["owner_id"] == uid:
        raise HTTPException(
            status_code=401, details="Владелец не может забронировать.")

    # Генерация индетфикатора
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
        "tile": time,
    }

    # Добавляем новую запись в Firebase Realtime Database
    db.reference(f"/booking_services/{booking_id}").set(booking_data)

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

    booked_services_ids = user_data['booked_services']
    data = []

    for service_id in booked_services_ids:
        # Получаем данные услуги
        service_ref = db.reference(f'/services/{service_id}')
        service_data = service_ref.get()

        if service_data is None:
            # если услуга не найдена, удаляем её из списка забронированных услуг пользователя
            booked_services_ids.remove(service_id)
            ref.update({'booked_services': booked_services_ids})
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
            'owner': owner_data
        })
    if len(data) < 1:
        raise HTTPException(
            status_code=404, detail="Забронированных услуг не найдено")

    return data

@router.get('/get_my_services',
            summary="Получение всех услуг авторизованного пользователя.")
async def get_my_services(
    uid: str,
    current_user: dict = Depends(get_current_user)
):
    # Проверка пользователя на авторизованность
    if uid != current_user["uid"]:
        raise HTTPException(
            status_code=401, detail="Неиндентифицированный пользователь."
        )

    py_db = firebase.database()

    # Получение данных из Firebase
    services_ref = py_db.child("services").order_by_child("owner_id").equal_to(uid).get()

    if not services_ref.val():
        raise HTTPException(
            status_code=404, detail="Услуги не найдены."
        )

    # Преобразование данных в список и сортировка в обратном порядке
    services = list(services_ref.val().values())
    services.reverse()

    return services