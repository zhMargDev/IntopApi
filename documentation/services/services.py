get_all = """
Этот эндпоинт позволяет получить все объявления или отфильтровать их по указанным параметрам.

**Как можно запрос отправлять**:
- Для получения всех объявлений: `GET /services/all`
- Для получения конкретного объявления по id: `GET /services/all?id=2`
- Для фильтрации по другим параметрам: `GET /services/all?service_category_id=1&min_price=50&max_price=200&payment_method_id=2`

**Какие параметры можно указать**:
- `id`: (необязательный) ID объявления для фильтрации. Если указан, будет возвращено только объявление с этим ID.
- `service_category_id`: (необязательный) ID сервиса для фильтрации.
- `min_price`: (необязательный) Минимальная цена для фильтрации.
- `max_price`: (необязательный) Максимальная цена для фильтрации.
- `payment_method_id`: (необязательный) Метод оплаты для фильтрации.

**Пример ответа**:
```json
[
    {
        "id": 1,
        "name": "Объявление 1",
        "lat": 25.5,
        "lon": -24,
        "rating_count": 0,
        "views_count": 0,
        "description": "Описание объявления 1",
        "price": 100.0,
        "owner_id": 1,
        "is_active": true,
        "timer": 3600,
        "picture": "http://example.com/picture1.jpg",
        "service": {
            "id": 1,
            "title": "Сервис 1",
            "description": "Описание сервиса 1",
            "picture": "http://example.com/service_picture1.jpg"
        },
        "payment_method": {
            "id": 1,
            "name": "credit_card"
        }
    },
    ...
]

```
**Ответ:**
- `200 OK`: Успешный запрос, возвращает список объявлений или одно объявление.
- `400 Bad Request`: Минимальная цена больше максимальной цены.
- `404 Not` Found: Объявления не найдены или указанное объявление не найдено.
```
"""

get_services_by_filters = """
Этот эндпоинт позволяет пользователю получить услуги с применением различных фильтров.

**Как можно отправить запрос**:
- `GET /services/get_services_by_filters`

**Какие параметры можно указать**:
- `category_id`: (необязательный) ID категории услуги.
- `payment_method_id`: (необязательный) ID метода оплаты.
- `minPrice`: (необязательный) Минимальная цена услуги.
- `maxPrice`: (необязательный) Максимальная цена услуги.

**Пример запроса**:
```bash
curl -X GET "http://localhost:8000/services/get_services_by_filters" \
-H "Authorization: Bearer your_jwt_token" \
-H "Content-Type: application/json" \
-d '{
    "category_id": 1,
    "payment_method_id": 2,
    "minPrice": 100,
    "maxPrice": 500
}'
```
**Пример ответа:**
```
{
    "services": [
        {
            "id": 1,
            "name": "Услуга 1",
            "price": 200,
            "service_category_id": 1,
            "payment_method_id": 2
        },
        {
            "id": 2,
            "name": "Услуга 2",
            "price": 300,
            "service_category_id": 1,
            "payment_method_id": 2
        }
    ]
}
```
**Ответы:**
```
-` 200 OK: Успешный запрос, услуги успешно получены.
-` 403 Forbidden: Токен доступа отсутствует или недействителен, или у пользователя недостаточно прав.
-` 404 Not Found: Услуги не найдены.

"""

add_new_service = """
Этот эндпоинт позволяет добавить новую услугу.

**Как можно отправить запрос**:
```
- `POST /services/add`
```
**Какие параметры можно указать**:
```
- `'Authorization': `Bearer ${idToken}`
- `uid`: (обязательный) ID пользователя, который добавляет услугу. Должен иметь токен в header.
- `name`: (обязательный) Название услуги.
- `lat`: (обязательный) Широта местоположения услуги.
- `lon`: (обязательный) Долгота местоположения услуги.
- `description`: (обязательный) Описание услуги.
- `price`: (обязательный) Цена услуги.
- `currency`: (обязательный) Тип валюты.
- `date`: (опциональный) Дата добавления услуги (в формате Unix timestamp).
- `email`: (опциональный) Электронная почта владельца услуги.
- `phone_number`: (опциональный) Телефонный номер владельца услуги.
- `is_store`: (обязательный) Флаг, указывающий, является ли услуга магазином.
- `picture`: (обязательный) Изображение услуги в формате файла.
- `service_category_id`: (обязательный) Идентификатор категории услуги.
- `payment_method_id`: (опциональный) Идентификатор способа оплаты.
```
**Пример запроса**:
```bash
curl -X POST "http://localhost:8000/services/add" \
-F "uid=1wdfqwfqwf21r12r12" \
-F "name=Новая услуга" \
-F "lat=55.7558" \
-F "lon=37.6173" \
-F "description=Описание услуги" \
-F "price=100.0" \
-F "currency=\$" \
-F "date=1633072800" \
-F "email=example@example.com" \
-F "phone_number=+1234567890" \
-F "is_store=true" \
-F "picture=@/path/to/your/picture.jpg" \
-F "service_category_id=1" \
-F "payment_method_id=2"
```
**Пример ответа:**
```
{
    "message": "Услуга успешно добавлена",
    "service": {
        "id": "pCKYhFnMFPUyDsGQPcVT1M6BmhG2",
        "rating_count": 0,
        "views_count": 0,
        "is_active": false,
        "name": "Новая услуга",
        "lat": 55.7558,
        "lon": 37.6173,
        "description": "Описание услуги",
        "price": 100.0,
        "currency": "\$",
        "owner_id": "1wdfqwfqwf21r12r12",
        "date": 1633072800,
        "email": "example@example.com",
        "phone_number": "+1234567890",
        "is_store": true,
        "picture_url": "https://storage.googleapis.com/your-storage-bucket-name.appspot.com/services/pCKYhFnMFPUyDsGQPcVT1M6BmhG2/picture.jpg",
        "service_category_id": 1,
        "payment_method_id": 2,
        "created_at": "2023-10-01T12:00:00Z"
    }
}
```
**Ответ:**
```
- `200 OK: Успешный запрос, услуга успешно создана.
- `403 Forbidden: Токен доступа отсутствует или недействителен, или у пользователя недостаточно прав.
- `404 Not Found: Категория сервиса или способ оплаты не найдены.
- `422 Unprocessable Entity: Отправленные данные не соответствуют ожиданиям сервера.

"""

update_service = """
Этот эндпоинт позволяет обновить существующую услугу.

**Как можно отправить запрос**:
```
- `PUT /services/update`
```
**Какие параметры можно указать**:
```
- `'Authorization': `Bearer ${idToken}`
- `service_id`: (обязательный) ID услуги, которую нужно обновить.
- `uid`: (обязательный) ID пользователя, который обновляет услугу. Должен иметь токен в header.
- `name`: (необязательный) Новое название услуги.
- `lat`: (необязательный) Новая широта местоположения услуги.
- `lon`: (необязательный) Новая долгота местоположения услуги.
- `description`: (необязательный) Новое описание услуги.
- `price`: (необязательный) Новая цена услуги.
- `date`: (необязательный) Новая дата добавления услуги (в формате Unix timestamp).
- `picture`: (необязательный) Новое изображение услуги в формате файла.
- `phone_number`: (необязательный) Новый телефонный номер владельца услуги.
- `email`: (необязательный) Новая электронная почта владельца услуги.
```
**Пример запроса**:
```bash
curl -X PUT "http://localhost:8000/services/update" \
-H "Authorization: Bearer your_jwt_token" \
-F "service_id=1" \
-F "name=Обновленная услуга" \
-F "lat=24.24" \
-F "lon=-12.42" \
-F "description=Обновленное описание услуги" \
-F "price=150.0" \
-F "date=1633072800" \
-F "phone_number=+1234567890" \
-F "email=new_email@example.com" \
-F "picture=@/path/to/your/new_picture.jpg"
```
**Пример ответа:**
```
{
    "message": "Сервис успешно обновлен",
    "service": {
        "id": "pCKYhFnMFPUyDsGQPcVT1M6BmhG2",
        "rating_count": 0,
        "views_count": 0,
        "is_active": false,
        "name": "Обновленная услуга",
        "lat": 24.24,
        "lon": -12.42,
        "description": "Обновленное описание услуги",
        "price": 150.0,
        "currency": "\$",
        "owner_id": "1wdfqwfqwf21r12r12",
        "date": 1633072800,
        "email": "new_email@example.com",
        "phone_number": "+1234567890",
        "is_store": true,
        "picture_url": "https://storage.googleapis.com/your-storage-bucket-name.appspot.com/services/pCKYhFnMFPUyDsGQPcVT1M6BmhG2/new_picture.jpg",
        "service_category_id": 1,
        "payment_method_id": 2,
        "created_at": "2023-10-01T12:00:00Z"
    }
}
```
**Ответ:**
```
- `200 OK: Успешный запрос, услуга успешно обновлена.
- `403 Forbidden: Токен доступа отсутствует или недействителен, или у пользователя недостаточно прав.
- `404 Not Found: Услуга не найдена.
- `422 Unprocessable Entity: Отправленные данные не соответствуют ожиданиям сервера.
"""

delete_service = """
Этот эндпоинт позволяет удалить существующую услугу.

**Как можно отправить запрос**:
```
- `DELETE /services/delete`
```
**Какие параметры можно указать**:
```
- `'Authorization': `Bearer ${idToken}`
- `service_id`: (обязательный) ID услуги, которую нужно удалить.
- `uid`: (обязательный) ID пользователя, который удаляет услугу. Должен иметь токен в header.
```
**Пример запроса**:
```bash
curl -X DELETE "http://localhost:8000/services/delete" \
-H "Authorization: Bearer your_jwt_token" \
-H "Content-Type: application/json" \
-d '{
    "service_id": "1"
}'
```
**Пример ответа:**
```
{
    "message": "Сервис успешно удален"
}
```
**Ответ:**
```
- `200 OK: Успешный запрос, услуга успешно удалена.
- `403 Forbidden: Токен доступа отсутствует или недействителен, или у пользователя недостаточно прав.
- `404 Not Found: Услуга не найдена. 
"""

book_service = """
Этот эндпоинт позволяет пользователю забронировать услугу.

**Как можно отправить запрос**:
- `POST /book_service`

**Какие параметры можно указать**:
- `'Authorization': `Bearer ${idToken}`
- `user_id`: (обязательный) ID пользователя, который бронирует услугу. Должен совпадать с ID пользователя в токене.
- `service_id`: (обязательный) ID объявления, которое бронируется.
- `date`: (обязательный) Дата бронирования в формате YYYY-MM-DD.
- `time`: (обязательный) Время бронирования в формате HH:MM.

**Пример запроса**:
```bash
curl -X POST "http://localhost:8000/services/book_service" \
-H "Authorization: Bearer your_jwt_token" \
-H "Content-Type: application/json" \
-d '{
    "user_id": 1,
    "service_id": 1,
    "date": "2023-10-01",
    "time": "14:00"
}'
```
Пример ответа:
```
json
{
    "message": "Услуга успешно забронирована",
    "booking_id": 1
}

```
**Ответы:**
```
- `200 OK`: Успешный запрос, услуга успешно забронирована.
- `403 Forbidden`: Токен доступа отсутствует или недействителен, или у пользователя недостаточно прав.
- `404 Not` Found: Пользователь или объявление не найдены.
"""