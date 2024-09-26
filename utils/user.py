import firebase_conf

from fastapi import HTTPException, Header, Depends, status
from firebase_admin import auth, credentials, db, storage
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Функция для получения текущего пользователя на основе токена авторизации


def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        # Проверка токена Firebase
        decoded_token = auth.verify_id_token(token)
        uid = decoded_token.get("uid")
        if not uid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return {"uid": uid}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


async def update_last_active(uid: str):
    """
    Обновляет поле last_active для пользователя по UID.

    Args:
        db: Ссылка на корневой узел базы данных Firebase.
        uid: UID пользователя.
    """

    # Получение ссылки на узел пользователя по UID
    user_ref = db.reference(f"users/{uid}")

    # Словарь с новыми данными
    new_data = {"last_active": datetime.now().isoformat()}

    # Обновление данных пользователя
    user_ref.update(new_data)


async def upload_user_avatar(res_content, uid):
    bucket = storage.bucket()
    blob = bucket.blob(f'users/avatars/{uid}.jpg')
    blob.upload_from_string(res_content, content_type='image/jpeg')
    new_avatar_url = blob.generate_signed_url(
        timedelta(seconds=300), method='GET')

    return new_avatar_url
