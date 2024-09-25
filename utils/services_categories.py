import firebase_conf

from fastapi import HTTPException
from typing import Optional
from firebase_admin import db

from utils.categories import find_category_by_id

async def get_services_categories(id: Optional[int] = None):
    # Получаем все категории сервисов
    services_categories_ref = db.reference("/services_categories")
    services_categories_snapshot = services_categories_ref.get()

    # Если данных не найдено
    if not services_categories_snapshot:
        raise HTTPException(status_code=404, detail="Категорий для услуг не найдено.")

    if id:
        category = find_category_by_id(services_categories_snapshot, id)

        # Если функция не вернула категорию
        if not category:
            raise HTTPException(status_code=404, detail="Категорий для услуг по указанному id не найдено.")
        else:
            return [category]
    return services_categories_snapshot