from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, Request, Response, UploadFile, status
from fastapi.responses import JSONResponse

from app.auth.access import get_actual_user, get_api_key, get_api_key_public
from app.models.recipe import (
    FileBlob,
    Recipe,
    RecipeInDB,
    RecipePublic,
)
from app.models.result import Result
from app.models.token import Token
from app.models.user import UserInDB
from app.services.recipe import RecipeService
from app.utils.content_types import CONTENT_TYPES_IMAGE, CONTENT_TYPES_VALID
from app.utils.exclusion_fields import RESULT_FORMAT
from app.utils.mongo_validator import PyObjectId
from app.utils import google_cloud_storage
from app.utils.review_state import ReviewState

from app.core.configuration import MAX_SIZE_IMAGE_MB

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
    itemDB = RecipeInDB(**item.model_dump(by_alias=True))
    itemDB.username_insert = user.username
    inserted = RecipeService.insert(item=itemDB)
    return inserted


@router.patch(
    "/image",
    response_model=Recipe,
    responses={
        status.HTTP_200_OK: {"model": Recipe},
        status.HTTP_404_NOT_FOUND: {"model": Result},
        status.HTTP_400_BAD_REQUEST: {"model": Result},
    },
)
async def update_image_recipe(
    id: PyObjectId,
    file: UploadFile,
    user: UserInDB = Depends(get_actual_user),
):
    if not file.content_type in CONTENT_TYPES_IMAGE:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=Result(
                message=f"File not is a image, please use this formats: {','.join(CONTENT_TYPES_VALID)}"
            ).model_dump(),
        )
    inserted = RecipeService.get(id)
    if inserted is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=Result(message="Recipe Not Found").model_dump(),
        )

    result, filename, url, content_type = google_cloud_storage.upload_file(
        inserted.id, file.filename, file.content_type, file.file
    )
    # delete old image if exists after  upload new image
    if inserted.image is not None and result:
        deleted = google_cloud_storage.delete_file(inserted.image.name)
    if result:
        blob = FileBlob(name=filename, url=url, content_type=content_type)
        inserted = RecipeService.update_image(inserted.id, blob)
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
            content=Result(message="Id Field Not Found").model_dump(),
        )
    itemDB = RecipeInDB(**item.model_dump(by_alias=True))
    itemDB.username_update = user.username
    updated = RecipeService.update(itemDB)
    if updated is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=Result(message="Recipe Not Found").model_dump(),
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
    itemDB = RecipeInDB(tags=[], steps=[], preparation=[])
    itemDB.id = id
    itemDB.username_update = user.username
    deleted = RecipeService.delete(item=itemDB)
    if deleted is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=Result(message="Recipe Not Found").model_dump(),
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch(
    "/publish",
    responses={
        status.HTTP_404_NOT_FOUND: {"model": Result},
        status.HTTP_200_OK: {"model": Recipe},
    },
)
async def publish_recipe(id: PyObjectId, user: UserInDB = Depends(get_actual_user)):
    itemDB = RecipeInDB(tags=[], steps=[], preparation=[])
    itemDB.id = id
    itemDB.username_update = user.username
    publish = RecipeService.publish(item=itemDB, published=True)
    if publish is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=Result(message="Recipe Not Found").model_dump(),
        )
    return publish


@router.patch(
    "/unpublish",
    responses={
        status.HTTP_404_NOT_FOUND: {"model": Result},
        status.HTTP_200_OK: {"model": Recipe},
    },
)
async def unpublish_recipe(id: PyObjectId, user: UserInDB = Depends(get_actual_user)):
    itemDB = RecipeInDB(tags=[], steps=[], preparation=[])
    itemDB.id = id
    itemDB.username_update = user.username
    publish = RecipeService.publish(item=itemDB, published=False)
    if publish is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=Result(message="Recipe Not Found").model_dump(),
        )
    return publish


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
        search = RecipeService.list_random(
            page_number=page_number, n_per_page=n_per_page, published=True
        )
    return search


@router.get("/public", response_model=RecipePublic, status_code=status.HTTP_200_OK)
async def get_recipe_public(
    search: Optional[str] = None,
    page: int = 0,
    size: int = 10,
):
    if search is not None:
        search_recipes = RecipeService.search_public(
            q=search,
            page_number=page,
            n_per_page=size,
            published=True,
            exclude_fields=RESULT_FORMAT.RECIPE_PUBLIC_SEARCH,
        )
        count_recipes = RecipeService.count_public(q=search, published=True)
    else:
        search_recipes = RecipeService.list_public(
            page_number=page,
            n_per_page=size,
            published=True,
            exclude_fields=RESULT_FORMAT.RECIPE_PUBLIC_SEARCH,
        )
        count_recipes = RecipeService.count_public(published=True)
    return RecipePublic(content=search_recipes, total=count_recipes)


@router.get(
    "/public/{id}",
    responses={
        status.HTTP_404_NOT_FOUND: {"model": Result},
        status.HTTP_200_OK: {"model": Recipe},
    },
)
async def get_recipe_id(id: PyObjectId):
    recipe = RecipeService.get_public(id=id, exclude_fields={"reviewed": 0})
    if recipe is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=Result(message="Recipe Not Found").model_dump(),
        )
    return recipe


@router.get(
    "/public/{id}/meta",
    responses={
        status.HTTP_404_NOT_FOUND: {"model": Result},
        status.HTTP_200_OK: {"model": Recipe},
    },
)
async def get_recipe_id_meta(id: PyObjectId):
    recipe = RecipeService.get_public(id=id, exclude_fields=RESULT_FORMAT.RECIPE_META)
    if recipe is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=Result(message="Recipe Not Found").model_dump(),
        )
    return recipe


# states:
# published = true -> published
# published = false and reviewed = true  -> rejected
# published = false and reviewed = false -> not_reviewed
# published = false and reviewed = null -> not_requested
@router.get("/user/public", response_model=RecipePublic, status_code=status.HTTP_200_OK)
async def get_recipe_user(
    search: Optional[str] = None,
    page: int = 0,
    size: int = 100,
    state: Literal[
        "published", "rejected", "not_reviewed", "not_requested"
    ] = "not_requested",
    user: Token = Depends(get_api_key_public),
):
    if search is not None:
        if state == "published":
            result = RecipeService.search_public(
                q=search,
                page_number=page,
                n_per_page=size,
                published=True,
                publisher=user.username,
                exclude_fields=RESULT_FORMAT.RECIPE_USER_PUBLIC_SEARCH,
            )
            count = RecipeService.count_public(
                q=search, published=True, publisher=user.username
            )
        elif state == "rejected":
            result = RecipeService.search_public(
                q=search,
                page_number=page,
                n_per_page=size,
                published=False,
                reviewed=ReviewState.REVIEWED,
                publisher=user.username,
                exclude_fields=RESULT_FORMAT.RECIPE_USER_PUBLIC_SEARCH,
            )
            count = RecipeService.count_public(
                q=search,
                published=False,
                reviewed=ReviewState.REVIEWED,
                publisher=user.username,
            )
        elif state == "not_reviewed":
            result = RecipeService.search_public(
                q=search,
                page_number=page,
                n_per_page=size,
                published=False,
                reviewed=ReviewState.NOT_REVIEWED,
                publisher=user.username,
                exclude_fields=RESULT_FORMAT.RECIPE_USER_PUBLIC_SEARCH,
            )
            count = RecipeService.count_public(
                q=search,
                published=False,
                reviewed=ReviewState.NOT_REVIEWED,
                publisher=user.username,
            )
        elif state == "not_requested":
            result = RecipeService.search_public(
                q=search,
                page_number=page,
                n_per_page=size,
                published=False,
                reviewed=ReviewState.NOT_REQUESTED,
                publisher=user.username,
                exclude_fields=RESULT_FORMAT.RECIPE_USER_PUBLIC_SEARCH,
            )
            count = RecipeService.count_public(
                q=search,
                published=False,
                reviewed=ReviewState.NOT_REQUESTED,
                publisher=user.username,
            )
        return RecipePublic(content=result, total=count)
    else:
        if state == "published":
            result = RecipeService.list_public(
                page_number=page,
                n_per_page=size,
                published=True,
                publisher=user.username,
                exclude_fields=RESULT_FORMAT.RECIPE_USER_PUBLIC_SEARCH,
            )
            count = RecipeService.count_public(published=True, publisher=user.username)
        elif state == "rejected":
            result = RecipeService.list_public(
                page_number=page,
                n_per_page=size,
                published=False,
                reviewed=ReviewState.REVIEWED,
                publisher=user.username,
                exclude_fields=RESULT_FORMAT.RECIPE_USER_PUBLIC_SEARCH,
            )
            count = RecipeService.count_public(
                published=False, reviewed=ReviewState.REVIEWED, publisher=user.username
            )
        elif state == "not_reviewed":
            result = RecipeService.list_public(
                page_number=page,
                n_per_page=size,
                published=False,
                reviewed=ReviewState.NOT_REVIEWED,
                publisher=user.username,
                exclude_fields=RESULT_FORMAT.RECIPE_USER_PUBLIC_SEARCH,
            )
            count = RecipeService.count_public(
                published=False,
                reviewed=ReviewState.NOT_REVIEWED,
                publisher=user.username,
            )
        elif state == "not_requested":
            result = RecipeService.list_public(
                page_number=page,
                n_per_page=size,
                published=False,
                reviewed=ReviewState.NOT_REQUESTED,
                publisher=user.username,
                exclude_fields=RESULT_FORMAT.RECIPE_USER_PUBLIC_SEARCH,
            )
            count = RecipeService.count_public(
                published=False,
                reviewed=ReviewState.NOT_REQUESTED,
                publisher=user.username,
            )
        return RecipePublic(content=result, total=count)


@router.delete(
    "/user/public/{id}",
    responses={
        status.HTTP_404_NOT_FOUND: {"model": Result},
        status.HTTP_409_CONFLICT: {"model": Result},
        status.HTTP_204_NO_CONTENT: {"model": None},
    },
)
async def delete_recipe_user(id: PyObjectId, user: Token = Depends(get_api_key_public)):
    itemDB = RecipeInDB()
    itemDB.id = id
    itemDB.publisher = user.username
    itemDB.username_update = user.username
    find = RecipeService.get_id_and_user(id=id, publisher=user.username)
    if find is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=Result(message="Receta no encontrada").model_dump(),
        )
    if find.published is True:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=Result(
                message="No se puede eliminar, elimine el estado público primero"
            ).model_dump(),
        )
    deleted = RecipeService.delete_id_and_user(item=itemDB)
    if deleted is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=Result(message="Receta no encontrada").model_dump(),
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch(
    "/user/public/{id}/review",
    responses={
        status.HTTP_404_NOT_FOUND: {"model": Result},
        status.HTTP_409_CONFLICT: {"model": Result},
        status.HTTP_200_OK: {"model": Recipe},
    },
)
async def to_review_recipe_user(
    id: PyObjectId, user: Token = Depends(get_api_key_public)
):
    itemDB = RecipeInDB()
    itemDB.id = id
    itemDB.publisher = user.username
    itemDB.username_update = user.username
    find = RecipeService.get_id_and_user(id=id, publisher=user.username)
    if find is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=Result(message="Receta no encontrada").model_dump(),
        )
    if find.published is True:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=Result(message="La receta ya se encuentra publicada").model_dump(),
        )
    itemDB.reviewed = False
    reviewed = RecipeService.to_review_id_and_user(item=itemDB)
    if reviewed is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=Result(message="Receta no encontrada").model_dump(),
        )
    return reviewed


@router.patch(
    "/user/public/{id}/unreview",
    responses={
        status.HTTP_404_NOT_FOUND: {"model": Result},
        status.HTTP_409_CONFLICT: {"model": Result},
        status.HTTP_200_OK: {"model": Recipe},
    },
)
async def delete_review_recipe_user(
    id: PyObjectId, user: Token = Depends(get_api_key_public)
):
    itemDB = RecipeInDB()
    itemDB.id = id
    itemDB.publisher = user.username
    itemDB.username_update = user.username
    find = RecipeService.get_id_and_user(id=id, publisher=user.username)
    if find is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=Result(message="Receta no encontrada").model_dump(),
        )
    if find.published is True:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=Result(message="La receta ya se encuentra publicada").model_dump(),
        )
    itemDB.reviewed = None
    reviewed = RecipeService.to_review_id_and_user(item=itemDB)
    if reviewed is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=Result(message="Receta no encontrada").model_dump(),
        )
    return reviewed


@router.patch(
    "/user/public/{id}/unpublish",
    responses={
        status.HTTP_404_NOT_FOUND: {"model": Result},
        status.HTTP_409_CONFLICT: {"model": Result},
        status.HTTP_200_OK: {"model": Recipe},
    },
)
async def delete_publish_recipe_user(
    id: PyObjectId, user: Token = Depends(get_api_key_public)
):
    itemDB = RecipeInDB()
    itemDB.id = id
    itemDB.publisher = user.username
    itemDB.username_update = user.username
    find = RecipeService.get_id_and_user(id=id, publisher=user.username)
    if find is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=Result(message="Receta no encontrada").model_dump(),
        )
    if find.published is True:
        itemDB.reviewed = None
        itemDB.published = False
        reviewed = RecipeService.unpublish_id_and_user(item=itemDB)
        if reviewed is None:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=Result(message="Receta no encontrada").model_dump(),
            )
        return reviewed
    else:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=Result(message="La receta ya se encuentra publicada").model_dump(),
        )


@router.patch(
    "/user/public/{id}/image",
    response_model=Recipe,
    responses={
        status.HTTP_200_OK: {"model": Recipe},
        status.HTTP_404_NOT_FOUND: {"model": Result},
        status.HTTP_400_BAD_REQUEST: {"model": Result},
        status.HTTP_409_CONFLICT: {"model": Result},
        status.HTTP_413_REQUEST_ENTITY_TOO_LARGE: {"model": Result},
    },
)
async def update_image_recipe_user(
    request: Request,
    id: PyObjectId,
    file: UploadFile,
    user: Token = Depends(get_api_key_public),
):
    if not file.content_type in CONTENT_TYPES_IMAGE:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=Result(
                message=f"Formato no válido, únicos formatos permitidos: {','.join(CONTENT_TYPES_VALID)}"
            ).model_dump(),
        )
    try:
        size_image = request.headers.get("content-length")
        size_image = int(size_image)
    except:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=Result(message="Tamaño de imagen no válido").model_dump(),
        )
    if size_image > MAX_SIZE_IMAGE_MB * 1024 * 1024:
        return JSONResponse(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            content=Result(
                message=f"Tamaño de imagen no válido, máximo permitido: {MAX_SIZE_IMAGE_MB} MB"
            ).model_dump(),
        )
    find = RecipeService.get_id_and_user(id=id, publisher=user.username)
    if find is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=Result(message="Receta no encontrada").model_dump(),
        )
    if find.published is True:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=Result(
                message="La receta ya se encuentra publicada, no se puede cambiar la imagen"
            ).model_dump(),
        )
    result, filename, url, content_type = google_cloud_storage.upload_file(
        find.id, file.filename, file.content_type, file.file
    )
    # delete old image if exists after  upload new image
    if find.image is not None and result:
        deleted = google_cloud_storage.delete_file(find.image.name)
    if result:
        blob = FileBlob(name=filename, url=url, content_type=content_type)
        find = RecipeService.update_image(find.id, blob)
    return find


@router.post(
    "/user/public",
    response_model=Recipe,
    status_code=status.HTTP_201_CREATED,
)
async def insert_recipe_user(
    item: Recipe,
    user: Token = Depends(get_api_key_public),
):
    item.id = None
    itemDB = RecipeInDB(**item.model_dump(by_alias=True))
    itemDB.username_insert = user.username
    itemDB.publisher = user.username
    itemDB.published = False
    itemDB.reviewed = None
    inserted = RecipeService.insert(item=itemDB)
    return inserted


@router.get(
    "/user/public/{id}",
    responses={
        status.HTTP_404_NOT_FOUND: {"model": Result},
        status.HTTP_200_OK: {"model": Recipe},
    },
)
async def get_recipe_user_id(id: PyObjectId, user: Token = Depends(get_api_key_public)):
    find = RecipeService.get_id_and_user(id=id, publisher=user.username)
    if find is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=Result(message="Recipe Not Found").model_dump(),
        )
    return find


@router.put(
    "/user/public",
    responses={
        status.HTTP_200_OK: {"model": Recipe},
        status.HTTP_400_BAD_REQUEST: {"model": Result},
        status.HTTP_404_NOT_FOUND: {"model": Result},
    },
)
async def update_recipe_user(item: Recipe, user: Token = Depends(get_api_key_public)):
    if item.id is None:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=Result(message="ID es necesario").model_dump(),
        )
    find = RecipeService.get_id_and_user(id=item.id, publisher=user.username)
    if find is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=Result(
                message="Recipe no encontrada, no se puede editar"
            ).model_dump(),
        )
    if find.published is True:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=Result(
                message="La receta ya se encuentra publicada, no se puede editar"
            ).model_dump(),
        )
    if find.published is False and find.reviewed is False:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=Result(
                message="La receta ya se encuentra en revisión, no se puede editar"
            ).model_dump(),
        )
    itemDB = RecipeInDB()
    itemDB.id = item.id
    itemDB.name = item.name
    itemDB.description = item.description
    itemDB.lang = item.lang
    itemDB.owner = item.owner
    itemDB.tags = item.tags
    itemDB.year = item.year
    itemDB.location = item.location
    itemDB.category = item.category
    itemDB.portion = item.portion
    itemDB.preparation_time_minutes = item.preparation_time_minutes
    itemDB.preparation = item.preparation
    itemDB.username_update = user.username
    itemDB.lat = item.lat
    itemDB.lng = item.lng
    itemDB.elevation = item.elevation
    # New draft
    itemDB.published = False
    itemDB.reviewed = None

    updated = RecipeService.update_user(itemDB)
    if updated is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=Result(message="Recipe Not Found").model_dump(),
        )
    else:
        return updated
