from fastapi import Request

def add_domain_to_picture(request: Request, picture_path: str) -> str:
    """Добавляет домен и префикс /file/ к пути изображения."""
    domain = request.base_url.scheme + "://" + request.headers['host']  # Получаем домен из запроса
    return f"{domain}/file/{picture_path}"