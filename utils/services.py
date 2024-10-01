import firebase_conf
import shortuuid

from firebase_admin import db, storage
from datetime import timedelta
from urllib.parse import urlparse

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

bucket = storage.bucket()

def extract_file_path_from_url(url):
    parsed_url = urlparse(url)
    path = parsed_url.path
    # Удаляем префикс "/"
    file_path = path[1:]
    return file_path

async def delete_service_image(file_url):
    file_path = extract_file_path_from_url(file_url)
    blob = bucket.blob(file_path)
    blob.delete()
    print(f"File {file_path} deleted successfully.")

async def upload_service_image(res_content, service_id, content_type):
    bucket = storage.bucket()
    random_id = shortuuid.uuid()
    new_filename = f"{service_id}_{random_id}.jpg"
    file_path = f"services/{service_id}/{new_filename}"

    blob = bucket.blob(file_path)
    blob.upload_from_string(res_content, content_type=content_type)

    # Make the file public for infinite access
    blob.make_public()

    new_image_url = blob.public_url

    return new_image_url
