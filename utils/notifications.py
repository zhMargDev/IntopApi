import shortuuid
import firebase_conf

from firebase_admin import auth, db, storage
from datetime import datetime, timedelta


async def check_date(date_str):
    # Convert the date string to a datetime object
    date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))

    # Get the current date
    now = datetime.now()

    # Calculate the difference between the two dates
    diff = now - date

    # Check if the date is today, yesterday, or earlier
    if diff < timedelta(days=1):
        return "today"
    elif diff < timedelta(days=2):
        return "yesterday"
    else:
        return "earlier"

async def add_new_notification(user_data, uid, message):
    # Добавляем уведомление
    if "notifications" not in user_data:
        user_data["notifications"] = []

    # Осздаём  уведомление
    new_notification = {
        "id": shortuuid.uuid(),
        "user_id": uid,
        "message": message,
        "created_at": datetime.now().isoformat()
    }

    user_data["notifications"].append(new_notification)

    return user_data

async def set_notifications_array(notifications):
    # Создаём объект с сегоднешними, вчерашними и остальными уведомлениями
    array = {
        "today": [],
        "yesterday": [],
        "earlier": []
    }

    # Проходимся по массиву уведомлений и расставляем по нужным блокам
    for notification in notifications:

        # Получаем данные пользователя от которого пришло уведомление
        rec_user_ref = db.reference(f"/users/{notification['user_id']}")
        rec_user_data = rec_user_ref.get()

        if not rec_user_data:
            continue

        avatar = rec_user_data["avatar"]
        username = rec_user_data["username"]
        
        # Составляем объект данных
        notification_dict = {
            "id": notification["id"],
            "user_id": notification["user_id"],
            "avatar": avatar,
            "title": username,
            "message": notification["message"],
            "created_at": notification["created_at"]
        }

        # Получаем ключ к дням
        key = await check_date(notification["created_at"])

        # Добавляем уведомление в нужный блок исходя из полученного дня
        array[key].append(notification_dict)

    return array

async def delete_notifications(notifications, ids):
    # Создаём новый массив без элементов с указанными ids
    new_array = []
    
    for notification in notifications:
        if notification["id"] not in ids:
            new_array.append(notification)

    return new_array