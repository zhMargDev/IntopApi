import firebase_conf
import datetime

from firebase_admin import db, storage
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
    Response
)
from typing import List

from utils.user import get_current_user
from utils.chats import addChatToUsers, upload_picture_to_storage, create_new_chat, add_message_to_chat, getChatByUserId
from documentation.chats import chats as chats_ducumentation

router = APIRouter()

@router.post('/send_new_message',
    summary="Эндпоинт для добавления нового сообщения в базу.",
    description=chats_ducumentation.send_new_message)
async def send_new_message(
    current_user: dict = Depends(get_current_user),
    text: str = Form(...),
    uid: str = Form(...),
    selected_chat_id: str = Form(None),
    recipient_id: str = Form(None),
    pictures: List[UploadFile] = File(None)
):
    # Проверяем чтобы присутствовало или chat_id или recipient_id
    if not selected_chat_id and not recipient_id:
        raise HTTPException(status_code=403, detail="Нужно указать id чата или id получателя.")

    # Проверяем пользователя на авторизованность
    if uid != current_user["uid"]:
        raise HTTPException(status_code=403, detail="Пользователь не идентефицирован.")

    # Получаем данные пользователя
    user_ref = db.reference(f"/users/{uid}")
    user_data = user_ref.get()

    if not user_data:
        raise HTTPException(status_code=403, detail="Пользователь не найден.")

    # Проверяем чтобы получатель не был отправителем
    if recipient_id and recipient_id == uid:
        raise HTTPException(status_code=405, detail="Нельзя отправлять сообщение самому себе.")
    else:
        # Получаем данные поулчателя сообщений чтобы узнатть существует ли он
        recipient_user_ref = db.reference(f"/users/{recipient_id}")
        recipient_user_data = recipient_user_ref.get()

        if not recipient_user_data:
            raise HTTPException(status_code=404, detail="Пользователь не найден.")

    chat_id = selected_chat_id

    if recipient_id and selected_chat_id is None:
        # Получаем список чатов пользователя для дальнейшей проверки
        users_chats = user_data.get("chats", [])

        # Находим данные чатов пользователя
        chat_id = await getChatByUserId(users_chats, recipient_id)

    # Если чата не найдено то создаем его
    if chat_id is None:
        chat_id = await create_new_chat(user_id=uid, recipient_id=recipient_id, last_action=text)
        # Добавляем чат к обеим пользователям
        await addChatToUsers(users_ids=[uid, recipient_id], chat_id=chat_id)

    # Добавляем сообщение в чат
    await add_message_to_chat(chat_id=chat_id, text=text, sender_id=uid, pictures=pictures)

    return {"message": "Сообщение успешно отправлено."}