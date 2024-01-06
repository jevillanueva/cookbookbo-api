from fastapi import FastAPI, Request, status
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse, HTMLResponse
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
from app.core import configuration
from app.routers import oauth_google, recipe, token, users, page, page_render
from app.services.page import PageService

TITLE = configuration.APP_TITLE
VERSION = configuration.APP_VERSION
app = FastAPI(
    title=TITLE,
    version=VERSION,
    openapi_url=None,
    docs_url=None,
    redoc_url=None,
)

app.add_middleware(
    SessionMiddleware, secret_key=configuration.APP_SECRET_KEY_MIDDLEWARE
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Index"])
def read_root():
    search = PageService.get_by_slug(slug="index")
    if search is not None:
        return HTMLResponse(content=search.html, status_code=status.HTTP_200_OK)
    else:
        return {"title": TITLE, "version": VERSION}


@app.get("/api/docs", tags=["Documentation"])  # Tag it as "documentation" for our docs
async def get_documentation(request: Request):
    response = get_swagger_ui_html(
        openapi_url="/api/openapi.json",
        title="Documentation",
    )
    return response


@app.get("/api/openapi.json", tags=["Documentation"])
async def get_open_api_endpoint(request: Request):
    response = JSONResponse(
        get_openapi(title=TITLE, version=VERSION, routes=app.routes)
    )
    return response


@app.get("/api/redoc", tags=["Documentation"])  # Tag it as "documentation" for our docs
async def redoc_html(request: Request):
    response = get_redoc_html(openapi_url="/api/openapi.json", title="Documentation")
    return response


app.include_router(
    oauth_google.router,
    prefix="/api/google",
    tags=["Security Google"],
    include_in_schema=False,
)
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(token.router, prefix="/api/token", tags=["Token"])
app.include_router(recipe.router, prefix="/api/recipe", tags=["Recipes"])
app.include_router(page.router, prefix="/api/pages", tags=["Pages"])
app.include_router(page_render.router, prefix="/pages", tags=["Pages"])
