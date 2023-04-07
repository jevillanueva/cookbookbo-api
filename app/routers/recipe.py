from typing import List, Optional

from fastapi import APIRouter, Depends, Response, status
from fastapi.responses import JSONResponse

from app.auth.access import get_actual_user, get_api_key
from app.models.recipe import Recipe, RecipeInDB, RecipePublic
from app.models.result import Result
from app.models.user import User, UserInDB
from app.services.recipe import RecipeService
from app.utils.mongo_validator import PyObjectId

router = APIRouter()


@router.get("", response_model=List[Recipe], status_code=status.HTTP_200_OK)
async def get_recipe(
    user: UserInDB = Depends(get_actual_user),
    q: Optional[str] = None,
    page_number: int = 0,
    n_per_page: int = 100,
):
    if q is not None:
        search = RecipeService.search(
            q=q, page_number=page_number, n_per_page=n_per_page
        )
    else:
        search = RecipeService.list(page_number=page_number, n_per_page=n_per_page)
    return search


@router.post(
    "",
    response_model=Recipe,
    status_code=status.HTTP_201_CREATED,
)
async def insert_recipe(
    item: Recipe,
    user: UserInDB = Depends(get_actual_user),
):
    item.id = None
    itemDB = RecipeInDB(**item.dict(by_alias=True))
    itemDB.username_insert = user.username
    inserted = RecipeService.insert(item=itemDB)
    return inserted


@router.put(
    "",
    responses={
        status.HTTP_200_OK: {"model": Recipe},
        status.HTTP_400_BAD_REQUEST: {"model": Result},
        status.HTTP_404_NOT_FOUND: {"model": Result},
    },
)
async def update_recipe(item: Recipe, user: UserInDB = Depends(get_actual_user)):
    if item.id is None:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=Result(message="Id Field Not Found").dict(),
        )
    itemDB = RecipeInDB(**item.dict(by_alias=True))
    itemDB.username_update = user.username
    updated = RecipeService.update(itemDB)
    if updated is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=Result(message="Recipe Not Found").dict(),
        )
    else:
        return updated


@router.delete(
    "",
    responses={
        status.HTTP_404_NOT_FOUND: {"model": Result},
        status.HTTP_204_NO_CONTENT: {"model": None},
    },
)
async def delete_recipe(id: PyObjectId, user: UserInDB = Depends(get_actual_user)):
    itemDB = RecipeInDB(tags=[], steps=[], ingredients=[])
    itemDB.id = id
    itemDB.username_update = user.username
    deleted = RecipeService.delete(item=itemDB)
    if deleted is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=Result(message="Recipe Not Found").dict(),
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/skill", response_model=List[Recipe], status_code=status.HTTP_200_OK)
async def get_recipe_skill(
    user: UserInDB = Depends(get_api_key),
    q: Optional[str] = None,
    page_number: int = 0,
    n_per_page: int = 5,
):
    if q is not None:
        search = RecipeService.search_by_name(
            q=q, page_number=page_number, n_per_page=n_per_page, published=True
        )
    else:
        search = RecipeService.list_random(page_number=page_number, n_per_page=n_per_page, published=True)
    return search

@router.get("/public", response_model=RecipePublic, status_code=status.HTTP_200_OK)
async def get_recipe(
    search: Optional[str] = None,
    page: int = 0,
    size: int = 10,
):
    if search is not None:
        search_recipes = RecipeService.search_public(
            q=search, page_number=page, n_per_page=size, published=True
        )
        count_recipes = RecipeService.count_public(q=search, published=True)
        print ("count_recipes", count_recipes, search)
    else:
        search_recipes = RecipeService.list_public(page_number=page, n_per_page=size, published=True)
        count_recipes = RecipeService.count_public(published=True)
        print ("count_recipes", count_recipes)
    return RecipePublic(content=search_recipes, total=count_recipes)