from datetime import datetime
from typing import Optional

from bson import ObjectId
from pydantic import BaseModel


class Base(BaseModel):
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
