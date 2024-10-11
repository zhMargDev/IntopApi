import datetime

from firebase_admin import db, storage

async def addChatToUsers(users_ids, chat_id):
    for user_id in users_ids:
        # Получаем данные пользователя
        user_ref = db.reference(f"/users/{user_id}")
        user_data = user_ref.get()

        # Проверяем, есть ли у пользователя массив `chats`
        if "chats" not in user_data:
            # Если массива `chats` нет, создаем его и добавляем `chat_id`
            user_data["chats"] = [chat_id]
        else:
            # Если массив `chats` уже существует, добавляем `chat_id` в него
            user_data["chats"].append(chat_id)

        # Сохраняем изменения в базе данных
        user_ref.set(user_data)

async def upload_picture_to_storage(picture, chat_id):
    bucket = storage.bucket()
    random_id = shortuuid.uuid()
    new_filename = f"{random_id}.jpg"
    file_path = f"chats/{chat_id}/pictures/{new_filename}"

    blob = bucket.blob(file_path)
    blob.upload_from_string(picture.file.read(), content_type=picture.content_type)

    # Make the file public for infinite access
    blob.make_public()

    new_image_url = blob.public_url

    return new_image_url

async def create_new_chat(user_id, recipient_id, last_action):
    # Генерация нового айди чата
    chat_id = db.reference("/chats").push().key

    # Создаём дату и время
    now = datetime.datetime.now().isoformat()

    # Создаём новый массив с чатом
    new_chat = {
        "chat_id": chat_id,
        "last_action_date": now,
        "last_action": last_action,
        "users": {
            user_id: {
                "uid": user_id,
                "last_action_viewed": True
            },
            recipient_id: {
                "uid": recipient_id,
                "last_action_viewed": True
            }
        },
        "messages": {}
    }

    # Сохраняем чат в базе данных
    db.reference(f"/chats/{chat_id}").set(new_chat)

    # Возвращаем айди нового чата
    return chat_id

async def add_message_to_chat(chat_id, sender_id, text, pictures=None):
    # Получаем текущую дату и время
    now = datetime.datetime.now()

    # Создаем новые данные сообщения
    new_message = {
        "sender_id": sender_id,
        "text": text,
        "timestamp": now.isoformat()
    }

    # Если есть картинки, добавляем их в данные сообщения
    if pictures:
        new_message["pictures"] = []
        for picture in pictures:
            # Загружаем картинку в Firebase Storage и получаем URL
            picture_url = await upload_picture_to_storage(picture=picture, chat_id=chat_id)
            new_message["pictures"].append(picture_url)

    # Получаем сообщения чата из базы данных
    chat_ref = db.reference(f"/chats/{chat_id}/messages")

    # Добавляем новое сообщение в чат
    chat_ref.push(new_message)

async def getChatByUserId(chats, user_id):
    # Функция проверки наличия чатов и чата с указанным пользователем
    if chats is None:
        return None

    for chat_id in chats:
        chat_ref = db.reference(f"/chats/{chat_id}")
        chat_data = chat_ref.get()

        # Проверяем есть ли чат с recipient_id пользователем
        for user in chat_data["users"].values():
            if user["uid"] == user_id:
                return chat_id

    return None