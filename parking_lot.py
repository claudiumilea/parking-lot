from datetime import datetime
from typing import Optional, Union
from enum import Enum
from pydantic import BaseModel, Field, ValidationError, validator
from fastapi import FastAPI, Request, status

from starlette.responses import JSONResponse

import math

app = FastAPI()

PARKED_CARS = {
    'X773HY97': {'tariff': 'hourly', 'location': 7, 'start': '2022-06-25T17:21:33.913233', 'end': None, 'fee': None},
    'G737TT97': {'tariff': 'daily', 'location': 14, 'start': '2022-06-25T17:23:24.428268', 'end': None, 'fee': None}
}
PARKING_LOT_CAPACITY = 14
ACCEPTED_TIME_DELAY = 900
FREE_PARKING_TIME = 900


class TariffName(str, Enum):
    hourly = "hourly"
    daily = "daily"


class Tariffs(int, Enum):
    hourly = 2.5
    daily = 21


class InvalidLocationException(Exception):
    def __init__(self, location):
        self.location = location


class LocationNotAvailableException(Exception):
    def __init__(self, location):
        self.location = location


class StartDateException(Exception):
    def __init__(self, start):
        self.start = start


class CarIdExistsException(Exception):
    def __init__(self, car_id):
        self.car_id = car_id


class CarIdDoesNotExistException(Exception):
    def __init__(self, car_id):
        self.car_id = car_id


class ParkedCar(BaseModel):
    car_id: str = Field(
        default=None, title="The licence plate of the car", max_length=8
    )
    status: str = Field(default=None)
    tariff: TariffName | None
    location: int = Field(ge=0, lt=PARKING_LOT_CAPACITY, description=f"The location must be between 0 and {PARKING_LOT_CAPACITY}")
    start: datetime | None
    end: datetime | None = None
    fee: float | None = Field(default=None, ge=0, description=f"The fee must be greater or equal to 0.")

    @validator('location')
    def location_must_be_greater_than_zero(cls, v) -> int:
        if v < 0:
            raise ValueError('must be greater than zero')
        return v

    def get_exit_fee(self, start, end) -> float:
        start_date = start.replace(tzinfo=None)
        time_spent_when_parked = (end - start_date).total_seconds()

        if time_spent_when_parked > FREE_PARKING_TIME:
            exit_fee = math.ceil(time_spent_when_parked/3600) * Tariffs.hourly
        else:
            exit_fee = 0

        print(f'{start_date=}')
        print(f'{end=}')
        print(f'{time_spent_when_parked=}')
        print(f'{exit_fee=}')

        return exit_fee


@app.exception_handler(InvalidLocationException)
async def invalid_location_exception_handler(request: Request, exception: InvalidLocationException):
    return JSONResponse(status_code=422, content={"status": "error", "message": f"Cannot park your car there because location {exception.location} is invalid!"})


@app.exception_handler(LocationNotAvailableException)
async def location_not_available_exception_handler(request: Request, exception: LocationNotAvailableException):
    return JSONResponse(status_code=422, content={"status": "error", "message": f"Cannot park your car there because location {exception.location} is not available!"})


@app.exception_handler(StartDateException)
async def start_date_in_the_future(request: Request, exception: StartDateException):
    return JSONResponse(status_code=422, content={"status": "error", "message": f"Cannot part your car because date {exception.start} is invalid!"})


@app.exception_handler(CarIdExistsException)
async def car_id_already_exists(request: Request, exception: CarIdExistsException):
    return JSONResponse(status_code=422, content={"status": "error", "message": f"Car {exception.car_id} is already parked!"})


@app.exception_handler(CarIdDoesNotExistException)
async def car_id_does_not_exist(request: Request, exception: CarIdDoesNotExistException):
    return JSONResponse(status_code=422, content={"status": "error", "message": f"Car {exception.car_id} is not in the parking lot!!"})


@app.get("/cars/")
async def get_cars():
    return PARKED_CARS


@app.get("/cars/{car_id}", status_code=status.HTTP_200_OK)
async def get_car(car_id: Optional[str] = None):
    return PARKED_CARS[car_id]


@app.post("/cars/", status_code=status.HTTP_201_CREATED)
async def add_car(parked_car: ParkedCar):
    if parked_car.location <= 0 or parked_car.location > PARKING_LOT_CAPACITY:
        raise InvalidLocationException(location=parked_car.location)

    if parked_car.location in [x.get('location') for x in PARKED_CARS.values()]:
        raise LocationNotAvailableException(location=parked_car.location)

    start_date = parked_car.start.replace(tzinfo=None)
    present = datetime.now()

    if (present - start_date).total_seconds() > ACCEPTED_TIME_DELAY:
        raise StartDateException(start=parked_car.start)

    if parked_car.car_id in PARKED_CARS.keys():
        raise CarIdExistsException(car_id=parked_car.car_id)

    PARKED_CARS[parked_car.car_id] = {'status': 'success', 'tariff': parked_car.tariff, 'location': parked_car.location, 'start': parked_car.start, 'end': None, 'fee': None}
    return PARKED_CARS[parked_car.car_id]


@app.put("/cars/{car_id}", status_code=status.HTTP_200_OK)
async def remove_car(car_id: str, parked_car: ParkedCar):
    if car_id not in PARKED_CARS.keys():
        raise CarIdDoesNotExistException(car_id=car_id)

    PARKED_CARS[car_id] = {'status': 'success', 'tariff': parked_car.tariff, 'location': parked_car.location, 'start': parked_car.start, 'end': datetime.now(),
                           'fee': parked_car.get_exit_fee(start=parked_car.start, end=datetime.now())}
    return PARKED_CARS[car_id]
