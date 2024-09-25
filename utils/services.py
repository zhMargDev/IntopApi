import firebase_conf

from firebase_admin import db, storage

async def get_payment_method(id: int):
    # Получаем все способы оплаты и переобразуем в массив
    payment_method_ref = db.reference("/payments_methods")
    payment_method_snapshot = payment_method_ref.get()

    # Ищем способ оплаты по указанному id и возвращаем
    for method in payment_method_snapshot:
        if method['id'] == id:
            return method
    
    # Если ничего не найдену то возвращаем none
    return None

# Пример функции для получения сервиса по service_id
async def get_service_by_id(service_id: str):
    ref = db.reference(f'/services/{service_id}')
    return ref.get()

# Пример функции для обновления сервиса в базе данных
async def update_service_in_db(service_id: str, updated_data: dict):
    ref = db.reference(f'/services/{service_id}')
    ref.update(updated_data)

# Пример функции для удаления сервиса из базы данных
async def delete_service_from_db(service_id: str):
    ref = db.reference(f'/services/{service_id}')
    ref.delete()

