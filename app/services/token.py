from datetime import datetime

from jose import jws
from pymongo.collection import ReturnDocument

from app.core import configuration
from app.core.database import db
from app.models.token import Token
from app.utils.currentmillis import current

SECRET = configuration.APP_SECRET_TOKENS


class TokenService:
    @staticmethod
    def create(item: Token):
        item.date_insert = datetime.utcnow()
        item.disabled = False
        if hasattr(item, "date_update"):
            delattr(item, "date_update")
        if hasattr(item, "id"):
            delattr(item, "id")
        if hasattr(item, "username_update"):
            delattr(item, "username_update")
        payload = {"username": item.username, "current": current()}
        item.token = jws.sign(
            payload, SECRET, algorithm=configuration.APP_TOKEN_ALGORITHM
        )
        ret = db.token.insert_one(item.model_dump(by_alias=True))
        return ret

    @staticmethod
    def get_by_id_and_user(item: Token):
        find = db.token.find_one(
            {"_id": item.id, "username": item.username, "disabled": False}
        )
        if find is not None:
            return Token(**find)
        else:
            return None

    @staticmethod
    def get_token(item: Token):
        find = db.token.find_one({"disabled": False, "token": item.token})
        if find is None:
            return None
        else:
            return find

    @staticmethod
    def get(username: str):
        finds = db.token.find({"disabled": False, "username": username})
        items = []
        for find in finds:
            items.append(Token(**find))
        return items

    @staticmethod
    def search(item: Token):
        finds = db.token.find(
            {
                "$and": [
                    {"disabled": False},
                    {"username": item.username},
                    {"token": {"$regex": item.token}},
                ]
            }
        )
        tokens = []
        for find in finds:
            tokens.append(Token(**find))
        return tokens

    @staticmethod
    def delete(item: Token):
        item.date_update = datetime.utcnow()
        ret = db.token.find_one_and_update(
            {"_id": item.id, "username": item.username, "disabled": False},
            {
                "$set": {
                    "disabled": True,
                    "date_update": item.date_update,
                    "username_update": item.username_update,
                }
            },
            return_document=ReturnDocument.AFTER,
        )
        return ret
