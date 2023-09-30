from datetime import datetime
from typing import Optional

from bson import ObjectId
from pydantic import ConfigDict, BaseModel
from pydantic.fields import Field
from app.models.base import Base
from app.utils.mongo_validator import PyObjectId


class Token(Base):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    username: str
    token: str
    jti: Optional[str] = None
    expires: Optional[datetime] = None
    disabled: Optional[bool] = False
    date_insert: Optional[datetime] = None
    date_update: Optional[datetime] = None
    username_insert: Optional[str] = None
    username_update: Optional[str] = None
