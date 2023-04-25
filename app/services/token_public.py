from datetime import datetime, timedelta

from jose import jwt, JWTError
from pymongo.collection import ReturnDocument
import uuid
from app.core import configuration
from app.core.database import db
from app.models.token import Token
from app.utils.currentmillis import current

SECRET = configuration.APP_SECRET_TOKENS
TIME_EXPIRES = configuration.APP_TOKEN_EXPIRES


class TokenPublicService:
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
        jti = str(uuid.uuid4())
        expires = datetime.utcnow() + timedelta(minutes=TIME_EXPIRES)
        payload = {"sub": item.username, "exp": expires, "jti": jti}
        token = jwt.encode(payload, SECRET, algorithm=configuration.APP_TOKEN_ALGORITHM)
        item.jti = jti
        item.expires = expires
        ret = db.token_public.insert_one(item.dict(by_alias=True))
        return ret, token

    @staticmethod
    def delete_by_jti(jti: str):
        ret = db.token_public.find_one_and_update(
            {"jti": jti, "disabled": False},
            {"$set": {"disabled": True, "date_update": datetime.utcnow()}},
            return_document=ReturnDocument.AFTER,
        )
        return ret
    
    @staticmethod
    def validate_token(token: str):
        try:
            payload = jwt.decode(token, SECRET, algorithms=[configuration.APP_TOKEN_ALGORITHM])
            ret = TokenPublicService.get_by_jti(payload.get("jti"))
            if (ret is None):
                return False, None
            return True, Token(username=payload.get("sub"), jti=payload.get("jti"), token="")
        except JWTError:
            return None, None

    @staticmethod
    def get_by_jti(jti: str):
        ret = db.token_public.find_one({"jti": jti, "disabled": False})
        return ret
