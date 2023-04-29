from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Depends, HTTPException, status
import requests
from starlette.requests import Request
from app.auth.access import get_api_key_public

from app.core import configuration
from app.models.result import Result
from app.models.token import Token
from app.models.user import UserInDB
from app.services.token_public import TokenPublicService
from app.services.user import UserService
from app.utils import validate_forwarded_proto

router = APIRouter()

oauth = OAuth()
CONF_URL = "https://accounts.google.com/.well-known/openid-configuration"
oauth.register(
    name="google",
    server_metadata_url=CONF_URL,
    client_kwargs={"scope": "openid email profile"},
    client_id=configuration.APP_GOOGLE_CLIENT_ID,
    client_secret=configuration.APP_GOOGLE_CLIENT_SECRET,
)


@router.get("/login")
async def login(request: Request):
    redirect_uri = request.url_for("auth_server_side")
    redirect_uri = validate_forwarded_proto.validateHTTPS(
        url=redirect_uri, schema=request.headers.get("x-forwarded-proto")
    )
    google = oauth.create_client("google")
    return await google.authorize_redirect(request, redirect_uri)


@router.get("/auth", response_model=Result)
async def auth_server_side(request: Request):
    google = oauth.create_client("google")
    token = await google.authorize_access_token(request)
    user = token.get("userinfo")
    request.session["user"] = dict(user)
    userDB = UserInDB(
        username=user.get("email"),
        email=user.get("email"),
        picture=user.get("picture"),
        given_name=user.get("given_name"),
        family_name=user.get("family_name"),
        disabled=False,
    )
    ret = UserService.insert_or_update_user(userDB)

    
    return Result(message="Login Success")


@router.get("/logout", response_model=Result)  # Tag it as "authentication" for our docs
async def logout(request: Request):
    # Remove the user
    request.session.pop("user", None)
    return Result(message="Logout Success")


@router.get("/login/public")
async def login_public(request: Request):
    token = request.headers.get("Authorization")
    if token is not None:
        result = requests.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": token},
        )
        if result.status_code == 200:
            data = result.json()
            userDB = UserInDB(
                username=data.get("email"),
                email=data.get("email"),
                picture=data.get("picture"),
                given_name=data.get("given_name"),
                family_name=data.get("family_name"),
                disabled=False,
            )
            ret = UserService.insert_or_update_user(userDB)

            generated, token = TokenPublicService.create(Token(username=ret.username, token=""))
            return {"token": token}
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials.",
        )

@router.get("/logout/public", response_model=Result)
async def logout_public(user: Token = Depends(get_api_key_public)):
    TokenPublicService.delete_by_jti(jti=user.jti)
    return Result(message="Logout Success")