from datetime import datetime
from typing import List, Literal, Optional

from bson import ObjectId
from pydantic import BaseModel
from pydantic.fields import Field

from app.models.base import Base
from app.utils.mongo_validator import PyObjectId


class Ingredient(BaseModel):
    name: str
    optional: bool = False
    quantity_si: float
    unit_si: Literal["kg","g","mg","l","dl","cl","ml","unit","unknow"]
    quantity_equivalence: float
    unit_equivalence: str


class Step(BaseModel):
    detail: str


class Preparation(BaseModel):
    name: str = "principal"
    ingredients: List[Ingredient]
    steps: List[Step]


class Recipe(Base):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    name: Optional[str] = None
    description: Optional[str] = None
    lang: Optional[str] = None
    owner: Optional[str] = None
    publisher: Optional[str] = None
    tags: List[str]
    year: int = 0
    location: Optional[str] = None
    category: List[str] = ["unknow"]
    portion: int = 0
    preparation_time_minutes: int = 0
    calification: int = 0
    preparation: List[Preparation]
    image_url: Optional[str] = None


class RecipeInDB(Recipe):
    disabled: Optional[bool] = False
    date_insert: Optional[datetime] = None
    date_update: Optional[datetime] = None
    username_insert: Optional[str] = None
    username_update: Optional[str] = None
