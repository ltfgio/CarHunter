from enum import Enum
from pydantic import BaseModel, Field

class FuelType(str, Enum):
    petrol="petrol"; diesel="diesel"; hybrid="hybrid"; electric="electric"; other="other"

class TransmissionType(str, Enum):
    manual="manual"; automatic="automatic"; robot="robot"; cvt="cvt"; other="other"

class DrivetrainType(str, Enum):
    fwd="fwd"; rwd="rwd"; awd="awd"; other="other"

class AspirationType(str, Enum):
    na="na"; turbo="turbo"; twin_turbo="twin_turbo"; supercharger="supercharger"; other="other"

class SearchQuery(BaseModel):
    brand: str|None=None
    model: str|None=None
    generation: str|None=None
    body_type: str|None=None
    year_min: int|None=Field(None, ge=1886)
    year_max: int|None=Field(None, ge=1886)
    price_min: int|None=Field(None, ge=0)
    price_max: int|None=Field(None, ge=0)
    mileage_max: int|None=Field(None, ge=0)
    fuel: FuelType|None=None
    displacement_min_l: float|None=Field(None, ge=0)
    displacement_max_l: float|None=Field(None, ge=0)
    cylinders_min: int|None=Field(None, ge=1)
    cylinders_max: int|None=Field(None, ge=1)
    power_min_hp: int|None=Field(None, ge=0)
    power_max_hp: int|None=Field(None, ge=0)
    transmission: TransmissionType|None=None
    drivetrain: DrivetrainType|None=None
    aspiration: AspirationType|None=None
    region: str|None=None
    keywords: list[str]=Field(default_factory=list)
    exclude_keywords: list[str]=Field(default_factory=list)
    sources: list[str]=Field(default_factory=list)
    limit: int=Field(50, ge=1, le=200)

class Listing(BaseModel):
    source: str
    source_id: str
    url: str
    title: str
    price_rub: int|None=None
    year: int|None=None
    mileage_km: int|None=None
    brand: str|None=None
    model: str|None=None
    generation: str|None=None
    body_type: str|None=None
    fuel: FuelType|None=None
    displacement_l: float|None=None
    cylinders: int|None=None
    power_hp: int|None=None
    transmission: TransmissionType|None=None
    drivetrain: DrivetrainType|None=None
    aspiration: AspirationType|None=None
    region: str|None=None
    description: str|None=None

class SearchResponse(BaseModel):
    query: SearchQuery
    total: int
    listings: list[Listing]
