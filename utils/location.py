from geopy.geocoders import Nominatim

async def get_location_name(lat, lon):
    # Получение названия локации по координатам
    geolocator = Nominatim(user_agent="your_app_name")
    location = geolocator.reverse((lat, lon), language="ru")
    location_name = location.address if location else "Неизвестное местоположение"
    return location_name