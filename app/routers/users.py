from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2AuthorizationCodeBearer
from google.oauth2 import id_token
from google.auth.transport import requests
from app.auth.access import get_actual_user, get_api_key_public
from app.core import configuration
from app.models.result import Result
from app.models.token import Token
from app.models.user import User, UserInDB
from app.services.user import UserService

CLIENT_ID = configuration.APP_GOOGLE_CLIENT_ID
router = APIRouter()


@router.get("/me", response_model=User)
async def get_me(user: Optional[dict] = Depends(get_actual_user)):
    return user



@router.get("/me/public", responses={
        status.HTTP_404_NOT_FOUND: {"model": Result},
        status.HTTP_200_OK: {"model": User},
        status.HTTP_400_BAD_REQUEST: {"model": Result},
    },)
async def get_data(user: Token = Depends(get_api_key_public)):
    try:
        finded = UserService.get_user_public(user.username)
        if finded is None:
            return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=Result(message="Usuario no encontrado").dict(),
        )
        return finded
    except ValueError as e:
        print(e)
        raise HTTPException(status_code=401, detail="Token de acceso no válido")
    return user
