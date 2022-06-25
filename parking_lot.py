from datetime import datetime
from typing import Optional, Union
from enum import Enum
import uuid
from pydantic import BaseModel

from fastapi import FastAPI

app = FastAPI()

PARKED_CARS = {
    '27275d49-7556-448f-b0bc-9bb7770aa9f7': {'tariff': 'hourly', 'location': 7, 'start': '2022-06-25T17:21:33.913233', 'end': None, 'fee': None},
    '730d97b3-dfc7-4205-acee-811f57265bf1': {'tariff': 'daily', 'location': 14, 'start': '2022-06-25T17:23:24.428268', 'end': None, 'fee': None}
}


class TariffName(str, Enum):
    hourly = "hourly"
    daily = "daily"


class ParkedCar(BaseModel):
    car_id: str
    status: str
    tariff: str
    location: int
    start: datetime
    end: datetime | None = None
    fee: float | None = None


@app.get("/cars/")
async def get_cars():
    return PARKED_CARS


@app.get("/cars/{car_id}")
async def get_car(car_id: Optional[str] = None):
    return PARKED_CARS[car_id]


@app.post("/cars/")
async def add_car(parked_car: ParkedCar):
    car_id = uuid.uuid4()
    PARKED_CARS[car_id] = {'status': 'success', 'tariff': parked_car.tariff, 'location': parked_car.location, 'start': parked_car.start, 'end': None, 'fee': None}
    return PARKED_CARS[car_id]


@app.patch("/cars/{car_id}")
async def remove_car(car_id: str, location: int, end: datetime):
    PARKED_CARS[car_id] = {'location': location, 'end': end}
    return PARKED_CARS[car_id]


@app.delete("/cars/{car_id}")
async def delete_car(car_id):
    del PARKED_CARS[car_id]
    return f'Car {car_id} deleted.'
