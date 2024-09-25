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
from routers.location.data import router as location_router

app = FastAPI()

# Настройка CORS
origins = [
    "https://intop.uz",
    "http://localhost",
    "http://127.0.0.1:8000",  # Порт по умолчанию для FastAPI
    "http://localhost:8080",
    "http://localhost:8080/",
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],  # Позволяет все HTTP-методы
    allow_headers=["*"],  # Позволяет все заголовки
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


@app.get("/file/{folder}/{filename}",
         tags=["Получение картинок."],
         summary="Получение картинки по URL.",
         description="""
            Указывается URL адрес картинки к примеру <domain>/file/<папка>/<название картинки.расширение>.
            В ответе будет получена картинка.
        """)
async def get_image(folder: str, filename: str):
    # Формируем полный путь к файлу
    file_path = os.path.join("static", folder, filename)

    # Проверяем, существует ли файл
    if not os.path.exists(file_path):
        return Response(content="File not found", status_code=404)

    # Возвращаем файл как ответ
    return FileResponse(file_path)

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
app.include_router(store_router, prefix="/stores",
                   tags=["Магазины и компании"])
# Сервисы
app.include_router(services_categories_router,
                   prefix="/services_categories", tags=["Категории Сервисов"])
# Объявления сервисов
app.include_router(services_router, prefix="/services", tags=["Сервисы"])
# Объявления способов оплаты
app.include_router(payment_methods_router,
                   prefix="/payment_methods", tags=["Способы оплаты"])
# Объявление локаций
app.include_router(location_router, prefix="/location", tags=["Локации"])
