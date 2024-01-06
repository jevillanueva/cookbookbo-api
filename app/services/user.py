from datetime import datetime
import random
import re
import string

from pymongo.collection import ReturnDocument

from app.core.database import db
from app.models.user import UserInDB


class UserService:
    @staticmethod
    def insert_or_update_user(user: UserInDB) -> UserInDB:
        if hasattr(user, "id"):
            delattr(user, "id")
        find = UserService.get_user(user)
        if find is None:
            exists_username = True
            pattern = re.compile("[^%s]" % string.printable)
            while exists_username:
                username_generated = f"{user.given_name}.{user.family_name}".lower()
                username_generated = pattern.sub("", username_generated)
                username_generated = re.sub(" +", " ", username_generated)
                username_generated = username_generated.strip()
                username_generated = username_generated.replace(" ", ".")
                username_generated = f"{username_generated}#{random.randint(1, 9999):04}"
                exists_username = UserService.exists_username(username_generated)
            user.username = username_generated
            user.date_insert = datetime.utcnow()
            ret = db.user.insert_one(user.model_dump(by_alias=True))
            ret = db.user.find_one({"_id": ret.inserted_id})
        else:
            if hasattr(user, "date_insert"):
                delattr(user, "date_insert")
            if hasattr(user, "admin"):
                delattr(user, "admin")
            if hasattr(user, "username"):
                delattr(user, "username")
            user.date_update = datetime.utcnow()
            user.disabled = find.disabled
            ret = db.user.find_one_and_update(
                {"email": user.email},
                {"$set": user.model_dump(by_alias=True)},
                return_document=ReturnDocument.AFTER,
            )
        return UserInDB(**ret)

    @staticmethod
    def get_user(user: UserInDB) -> UserInDB | None:
        ret = db.user.find_one({"email": user.email})
        if ret is not None:
            return UserInDB(**ret)
        else:
            return None

    @staticmethod
    def get_user_public(username: str) -> UserInDB | None:
        ret = db.user.find_one({"username": username, "disabled": False})
        if ret is not None:
            return UserInDB(**ret)
        else:
            return None

    @staticmethod
    def exists_username(username: str) -> bool:
        ret = db.user.find_one({"username": username})
        return ret is not None
