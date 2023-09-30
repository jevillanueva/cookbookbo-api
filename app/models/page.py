from datetime import datetime
from typing import Optional

from bson import ObjectId
from pydantic import ConfigDict, BaseModel, Field

from app.utils.mongo_validator import PyObjectId
from app.models.base import Base

class Page(Base):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    slug: str
    title: str
    html: str = """<!DOCTYPE html>
                <html>
                <body>
                </body>
                </html>"""


class PageInDB(Page):
    disabled: Optional[bool] = False
    date_insert: Optional[datetime] = None
    date_update: Optional[datetime] = None
    username_insert: Optional[str] = None
    username_update: Optional[str] = None
