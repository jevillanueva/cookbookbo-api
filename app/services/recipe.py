from datetime import datetime
from typing import List

from pymongo.collection import ReturnDocument

from app.core.database import db
from app.models.recipe import Recipe, RecipeInDB
from app.utils.mongo_validator import PyObjectId


class RecipeService:
    TABLE = db.recipe

    @classmethod
    def insert(cls, item: RecipeInDB) -> Recipe | None:
        item.date_insert = datetime.utcnow()
        item.disabled = False
        if hasattr(item, "date_update"):
            delattr(item, "date_update")
        if hasattr(item, "id"):
            delattr(item, "id")
        if hasattr(item, "username_update"):
            delattr(item, "username_update")
        inserted = cls.TABLE.insert_one(item.dict(by_alias=True))
        ret = cls.get(PyObjectId(inserted.inserted_id))
        return ret

    @classmethod
    def update(cls, item: RecipeInDB) -> Recipe | None:
        if hasattr(item, "date_insert"):
            delattr(item, "date_insert")
        if hasattr(item, "username_insert"):
            delattr(item, "username_insert")
        if hasattr(item, "disabled"):
            delattr(item, "disabled")
        item.date_update = datetime.utcnow()
        ret = cls.TABLE.find_one_and_update(
            {"_id": item.id, "disabled": False},
            {"$set": item.dict(by_alias=True)},
            return_document=ReturnDocument.AFTER,
        )
        if ret is not None:
            return Recipe(**ret)
        else:
            return None

    @classmethod
    def delete(cls, item: RecipeInDB) -> Recipe | None:
        item.date_update = datetime.utcnow()
        ret = cls.TABLE.find_one_and_update(
            {"_id": item.id, "disabled": False},
            {
                "$set": {
                    "disabled": True,
                    "date_update": item.date_update,
                    "username_update": item.username_update,
                }
            },
            return_document=ReturnDocument.AFTER,
        )
        if ret is not None:
            return Recipe(**ret)
        else:
            return None
        
    @classmethod
    def publish(cls, item: RecipeInDB, published: bool) -> Recipe | None:
        item.date_update = datetime.utcnow()
        ret = cls.TABLE.find_one_and_update(
            {"_id": item.id, "disabled": False},
            {
                "$set": {
                    "published": published,
                    "date_update": item.date_update,
                    "username_update": item.username_update,
                }
            },
            return_document=ReturnDocument.AFTER,
        )
        if ret is not None:
            return Recipe(**ret)
        else:
            return None

    @classmethod
    def get(cls, id: PyObjectId) -> Recipe | None:
        search = cls.TABLE.find_one({"_id": id, "disabled": False})
        if search is not None:
            return Recipe(**search)
        else:
            return None
        
    @classmethod
    def get_public(cls, id: PyObjectId) -> Recipe | None:
        search = cls.TABLE.find_one({"_id": id, "disabled": False, "published": True})
        if search is not None:
            return Recipe(**search)
        else:
            return None

    @classmethod
    def list(cls, page_number: int = 0, n_per_page: int = 100) -> List[Recipe]:
        search = (
            cls.TABLE.find({"disabled": False})
            .skip(((page_number - 1) * n_per_page) if page_number > 0 else 0)
            .limit(n_per_page)
        )
        items = []
        for find in search:
            items.append(Recipe(**find))
        return items
    
    @classmethod
    def list_public(cls, page_number: int = 0, n_per_page: int = 100, published: bool = True) -> List[Recipe]:
        search = (
            cls.TABLE.find({"disabled": False, "published": published})
            .skip(((page_number - 1) * n_per_page) if page_number > 0 else 0)
            .limit(n_per_page)
        )
        items = []
        for find in search:
            items.append(Recipe(**find))
        return items

    @classmethod
    def search(
        cls, q: str, page_number: int = 0, n_per_page: int = 100
    ) -> List[Recipe]:
        search = (
            cls.TABLE.find(
                {
                    "$and": [
                        {"disabled": False},
                        {
                            "$or": [
                                {
                                    "description": {
                                        "$regex": q,
                                        "$options": "i",
                                    }
                                },
                                {"name": {"$regex": q, "$options": "i"}},
                            ]
                        },
                    ]
                }
            )
            .skip(((page_number - 1) * n_per_page) if page_number > 0 else 0)
            .limit(n_per_page)
        )
        items = []
        for find in search:
            items.append(Recipe(**find))
        return items
    
    @classmethod
    def search_public(
        cls, q: str, page_number: int = 0, n_per_page: int = 100, published: bool = True
    ) -> List[Recipe]:
        search = (
            cls.TABLE.find(
                {
                    "$and": [
                        {"disabled": False},
                        {"published": published},
                        {
                            "$or": [
                                {
                                    "description": {
                                        "$regex": q,
                                        "$options": "i",
                                    }
                                },
                                {"name": {"$regex": q, "$options": "i"}},
                            ]
                        },
                    ]
                }
            )
            .skip(((page_number - 1) * n_per_page) if page_number > 0 else 0)
            .limit(n_per_page)
        )
        items = []
        for find in search:
            items.append(Recipe(**find))
        return items

    @classmethod
    def count(cls, q: str = "") -> int:
        if q == "":
            count = cls.TABLE.count_documents({"disabled": False})
        else:
            count = cls.TABLE.count_documents(
                {
                    "$and": [
                        {"disabled": False},
                        {
                            "$or": [
                                {
                                    "description": {
                                        "$regex": q,
                                        "$options": "i",
                                    }
                                },
                                {"name": {"$regex": q, "$options": "i"}},
                            ]
                        },
                    ]
                }
            )
        return count
    
    @classmethod
    def count_public(cls, q: str = "", published: bool = True ) -> int:
        if q == "":
            count = cls.TABLE.count_documents({"disabled": False, "published": published})
        else:
            count = cls.TABLE.count_documents(
                {
                    "$and": [
                        {"disabled": False},
                        {"published": published},
                        {
                            "$or": [
                                {
                                    "description": {
                                        "$regex": q,
                                        "$options": "i",
                                    }
                                },
                                {"name": {"$regex": q, "$options": "i"}},
                            ]
                        },
                    ]
                }
            )
        return count

    @classmethod
    def search_by_name(
        cls, q: str, page_number: int = 0, n_per_page: int = 100, published: bool = True
    ) -> List[Recipe]:
        search = (
            cls.TABLE.find(
                {
                    "$and": [
                        {"disabled": False},
                        {"published": published},
                        {"name": {"$regex": q, "$options": "i"}},
                    ]
                }
            )
            .skip(((page_number - 1) * n_per_page) if page_number > 0 else 0)
            .limit(n_per_page)
        )
        items = []
        for find in search:
            items.append(Recipe(**find))
        return items

    @classmethod
    def list_random(
        cls, page_number: int = 0, n_per_page: int = 100, published: bool = True
    ) -> List[Recipe]:
        print (published)
        search = (
            cls.TABLE.aggregate(
                [
                    {
                        "$match": {
                            "$and": [
                                {"disabled": False},
                                {"published": published},
                            ]
                        }
                    },
                    {"$sample": {"size": n_per_page}},
                    {"$skip": ((page_number - 1) * n_per_page) if page_number > 0 else 0},
                    {"$limit": n_per_page},
                ]
            )
        )
        items = []
        for find in search:
            items.append(Recipe(**find))
        return items
