import os

from fastapi import FastAPI, Response, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse

from routers.users.auth import router as auth_router
from routers.users.data import router as data_router
from routers.users.rating import router as rating_router

from routers.categories.data import router as categories_router
from routers.stores.data import router as store_router

from routers.services.services_categories import router as services_categories_router
from routers.services.services import router as services_router
from routers.services.payment_methods import router as payment_methods_router
from routers.services.bookings import router as service_bookings_router
from routers.services.reviews import router as service_reviews_router

from routers.location.data import router as location_router
from routers.chats import router as chats_router

from routers.notifications import router as notifications_router

app = FastAPI()

# Настройка CORS
origins = [
    "http://localhost",
    "http://127.0.0.1",
    "http://127.0.0.1:8080",
    "http://localhost:8080",
    "https://intop-project.web.app",
    "http://intop-project.web.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS", "DELETE", "PATCH", "PUT"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "Set-Cookie",
        "Access-Control-Allow-Credentials",
        "Access-Control-Allow-Origin",
        "Access-Control-Allow-Headers",
        "Access-Control-Allow-Methods",
    ],
)


@app.get("/", tags=["Основная"],
         summary="Основная информация для перехода в документацию.")
def read_item(request: Request):
    base_url = request.base_url
    docs_url = f"{base_url}docs"
    return {
        "data": "Documentation is available at /docs",
        "link": docs_url
    }

# Авторизация
app.include_router(auth_router, prefix="/users", tags=["Авторизация"])
# Получение или изменения данных пользователей
app.include_router(data_router, prefix="/users", tags=["Пользователи"])
# Оценка пользователей
app.include_router(rating_router, prefix="/users",
                   tags=["Рейтинг пользователей"])
# Категории
app.include_router(categories_router, prefix="/category", tags=["Категории"])
# Магазины
app.include_router(store_router, prefix="/stores", tags=["Магазины и компании"])
# Сервисы
app.include_router(services_categories_router,
                   prefix="/services_categories", tags=["Категории Сервисов"])
# Объявления сервисов
app.include_router(services_router, prefix="/services", tags=["Сервисы"])

app.include_router(service_bookings_router, prefix="/services", tags=["Сервисы"])

app.include_router(service_reviews_router, prefix="/services", tags=["Сервисы"])

# Объявления способов оплаты
app.include_router(payment_methods_router,
                   prefix="/payment_methods", tags=["Способы оплаты"])
# Объявление локаций
app.include_router(location_router, prefix="/location", tags=["Локации"])

# Объявляем чаты
app.include_router(chats_router, prefix="/chats", tags=["Чаты"])

# Объявляем роутер уведомлений
app.include_router(notifications_router, prefix="/notifications", tags=["Уведомления"])