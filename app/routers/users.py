from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2AuthorizationCodeBearer
from google.oauth2 import id_token
from google.auth.transport import requests
from app.auth.access import get_actual_user, get_api_key_public
from app.core import configuration
from app.models.token import Token
from app.models.user import User, UserInDB
from app.services.user import UserService

CLIENT_ID = configuration.APP_GOOGLE_CLIENT_ID
router = APIRouter()


@router.get("/me", response_model=User)
async def get_me(user: Optional[dict] = Depends(get_actual_user)):
    return user



@router.get("/me/public", response_model=User)
async def get_data(user: Token = Depends(get_api_key_public)):
    try:
        userDB = UserInDB(username=user.username, email=user.username)
        finded = UserService.get_user(userDB)
        return finded
    except ValueError as e:
        print(e)
        raise HTTPException(status_code=401, detail="Token de acceso no válido")
    return user
