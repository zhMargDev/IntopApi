from fastapi import APIRouter, Depends, HTTPException, Request, File, UploadFile, Form, Query, Header
from geopy.geocoders import Nominatim

from documentation.location import data as location_documentation

router = APIRouter()

@router.get("/get_location_name",
            summary="Возвращает локацию пользователя.",
            description=location_documentation.get_location_by_coord)
def get_location_name(latitude: float = Query(..., description="Широта"),
                      longitude: float = Query(..., description="Долгота"),
                      language: str = Query('en', description="Языковой код")):
    geolocator = Nominatim(user_agent="geoapiExercises")
    location = geolocator.reverse((latitude, longitude), language=language)
    if location:
        return {"location_name": location.address}
    else:
        return {"location_name": "Location not found"} 