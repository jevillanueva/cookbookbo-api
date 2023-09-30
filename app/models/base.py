from datetime import datetime
from typing import Optional

from bson import ObjectId
from pydantic import ConfigDict, BaseModel


class Base(BaseModel):
    pass
