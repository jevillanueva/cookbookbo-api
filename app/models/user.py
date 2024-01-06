from datetime import datetime
from typing import Optional

from pydantic import Field

from app.models.base import Base
from app.utils.mongo_validator import PyObjectId


class User(Base):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    username: str
    email: Optional[str] = None
    picture: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    disabled: Optional[bool] = False
    admin: Optional[bool] = False


class UserInDB(User):
    hashed_password: Optional[str] = None
    date_insert: Optional[datetime] = None
    date_update: Optional[datetime] = None
