import firebase_conf

from firebase_admin import db, storage

# Пример функции для удаления картинки из Firebase Storage
async def delete_picture_from_storage(picture_url: str):
    bucket = storage.bucket()
    blob = bucket.blob(picture_url.split('/')[-1])
    blob.delete()