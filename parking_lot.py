from datetime import datetime
from typing import Optional, Union
from enum import Enum
from uuid import uuid4, UUID
from pydantic import BaseModel

from fastapi import FastAPI, Request

from starlette.responses import JSONResponse
from dateutil import parser

app = FastAPI()

PARKED_CARS = {
    '27275d49-7556-448f-b0bc-9bb7770aa9f7': {'tariff': 'hourly', 'location': 7, 'start': '2022-06-25T17:21:33.913233', 'end': None, 'fee': None},
    '730d97b3-dfc7-4205-acee-811f57265bf1': {'tariff': 'daily', 'location': 14, 'start': '2022-06-25T17:23:24.428268', 'end': None, 'fee': None}
}
PARKING_LOT_CAPACITY = 14
ACCEPTED_TIME_DELAY = 900


class TariffName(str, Enum):
    hourly = "hourly"
    daily = "daily"


class Tariffs(str, Enum):
    hourly = 1
    daily = 8

class InvalidLocationException(Exception):
    def __init__(self, location):
        self.location = location

class LocationNotAvailableException(Exception):
    def __init__(self, location):
        self.location = location

class StartDateException(Exception):
    def __init__(self, start):
        self.start = start


class ParkedCar(BaseModel):
    car_id: UUID
    status: str
    tariff: TariffName
    location: int
    start: datetime
    end: datetime | None = None
    fee: float | None = None

@app.exception_handler(InvalidLocationException)
async def invalid_location_exception_handler(request: Request, exception: InvalidLocationException):
    return JSONResponse(status_code=422, content={"message": f"Cannot park your car there because location {exception.location} is invalid!"})

@app.exception_handler(LocationNotAvailableException)
async def location_not_available_exception_handler(request: Request, exception: LocationNotAvailableException):
    return JSONResponse(status_code=422, content={"message": f"Cannot park your car there because location {exception.location} is not available!"})

@app.exception_handler(StartDateException)
async def start_date_in_the_future(request: Request, exception: StartDateException):
    return JSONResponse(status_code=422, content={"message": f"Cannot part your car because date {exception.start} is invalid!"})


@app.get("/cars/")
async def get_cars():
    return PARKED_CARS


@app.get("/cars/{car_id}")
async def get_car(car_id: Optional[str] = None):
    return PARKED_CARS[car_id]


@app.post("/cars/")
async def add_car(parked_car: ParkedCar):
    if parked_car.location <= 0 or parked_car.location > PARKING_LOT_CAPACITY:
        raise InvalidLocationException(location=parked_car.location)

    if parked_car.location in [x.get('location') for x in PARKED_CARS.values()]:
        raise LocationNotAvailableException(location=parked_car.location)

    start_date = parked_car.start.replace(tzinfo=None)
    present = datetime.now()

    # print(f'{start_date=}')
    # print(f'{present=}')
    # print((present - start_date).total_seconds())

    if (present - start_date).total_seconds() > ACCEPTED_TIME_DELAY:
        raise StartDateException(start=parked_car.start)

    car_id = uuid4()
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
