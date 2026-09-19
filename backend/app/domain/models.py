from enum import Enum
from typing import Any, Literal
from pydantic import BaseModel, Field, model_validator

class FuelType(str, Enum):
    petrol="petrol"; diesel="diesel"; hybrid="hybrid"; electric="electric"; other="other"

class TransmissionType(str, Enum):
    manual="manual"; automatic="automatic"; robot="robot"; cvt="cvt"; other="other"

class DrivetrainType(str, Enum):
    fwd="fwd"; rwd="rwd"; awd="awd"; other="other"

class AspirationType(str, Enum):
    na="na"; turbo="turbo"; twin_turbo="twin_turbo"; supercharger="supercharger"; other="other"

class EngineLayout(str, Enum):
    single="single"; twin="twin"
    inline_3="inline_3"; inline_4="inline_4"; inline_5="inline_5"; inline_6="inline_6"; inline_8="inline_8"
    v4="v4"; v6="v6"; v8="v8"; v10="v10"; v12="v12"; v16="v16"
    flat_2="flat_2"; flat_4="flat_4"; flat_6="flat_6"; flat_8="flat_8"
    vr5="vr5"; vr6="vr6"; vr8="vr8"
    w8="w8"; w12="w12"; w16="w16"
    rotary="rotary"; electric_motor="electric_motor"; other="other"

class FilterOperator(str, Enum):
    eq="eq"; ne="ne"; gt="gt"; gte="gte"; lt="lt"; lte="lte"
    in_="in"; not_in="not_in"; contains="contains"; not_contains="not_contains"
    starts_with="starts_with"; ends_with="ends_with"; exists="exists"; between="between"

class FilterCondition(BaseModel):
    field: str = Field(min_length=1)
    operator: FilterOperator
    value: Any = None

class FilterGroup(BaseModel):
    logic: Literal["and", "or"] = "and"
    conditions: list[FilterCondition | "FilterGroup"] = Field(default_factory=list)

class SearchQuery(BaseModel):
    brand: str|None=None
    model: str|None=None
    generation: str|None=None
    body_type: str|None=None
    engine_code: str|None=None
    engine_family: str|None=None
    engine_layout: EngineLayout|None=None
    year_min: int|None=Field(None, ge=1886)
    year_max: int|None=Field(None, ge=1886)
    price_min: int|None=Field(None, ge=0)
    price_max: int|None=Field(None, ge=0)
    mileage_min: int|None=Field(None, ge=0)
    mileage_max: int|None=Field(None, ge=0)
    fuel: FuelType|None=None
    displacement_min_l: float|None=Field(None, ge=0)
    displacement_max_l: float|None=Field(None, ge=0)
    cylinders_min: int|None=Field(None, ge=1)
    cylinders_max: int|None=Field(None, ge=1)
    power_min_hp: int|None=Field(None, ge=0)
    power_max_hp: int|None=Field(None, ge=0)
    torque_min_nm: int|None=Field(None, ge=0)
    torque_max_nm: int|None=Field(None, ge=0)
    transmission: TransmissionType|None=None
    drivetrain: DrivetrainType|None=None
    aspiration: AspirationType|None=None
    region: str|None=None
    radius_km: int|None=Field(None, ge=1)
    keywords: list[str]=Field(default_factory=list)
    exclude_keywords: list[str]=Field(default_factory=list)
    sources: list[str]=Field(default_factory=list)
    filters: FilterGroup|None=None
    limit: int=Field(50, ge=1, le=200)
    sort: Literal["relevance","price_asc","price_desc","year_desc","mileage_asc"]="relevance"

    @model_validator(mode="after")
    def validate_ranges(self):
        for lo, hi, name in [
            (self.year_min,self.year_max,"year"), (self.price_min,self.price_max,"price"),
            (self.mileage_min,self.mileage_max,"mileage"), (self.displacement_min_l,self.displacement_max_l,"displacement"),
            (self.cylinders_min,self.cylinders_max,"cylinders"), (self.power_min_hp,self.power_max_hp,"power"),
            (self.torque_min_nm,self.torque_max_nm,"torque"),
        ]:
            if lo is not None and hi is not None and lo > hi:
                raise ValueError(f"{name}_min cannot be greater than {name}_max")
        return self

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
    trim: str|None=None
    doors: int|None=None
    seats: int|None=None
    steering_side: Literal["left","right","unknown"]|None=None
    engine_code: str|None=None
    engine_family: str|None=None
    engine_layout: EngineLayout|None=None
    fuel: FuelType|None=None
    displacement_l: float|None=None
    cylinders: int|None=None
    power_hp: int|None=None
    torque_nm: int|None=None
    transmission: TransmissionType|None=None
    drivetrain: DrivetrainType|None=None
    aspiration: AspirationType|None=None
    region: str|None=None
    description: str|None=None
    images: list[str]=Field(default_factory=list)
    seller_type: str|None=None
    seller_name: str|None=None
    owner_count: int|None=None
    accident: str|None=None
    condition: str|None=None
    customs_status: str|None=None
    vin_available: bool|None=None
    discovered_at: str|None=None
    raw_url: str|None=None

class SearchResponse(BaseModel):
    query: SearchQuery
    total: int
    listings: list[Listing]
