import logging
import math
from contextlib import asynccontextmanager
from typing import Annotated, Any

from fastapi import FastAPI, HTTPException, Path, Query, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from . import storage
from .models import ObjectCreate, ObjectOut, ObjectUpdate

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("xr_api")

ObjectId = Annotated[int, Path(ge=1, le=2**63 - 1)]


def _sanitize(value: Any) -> Any:
    """把 422 錯誤詳情轉成可安全序列化的資料（含 NaN、例外物件）。"""
    if isinstance(value, float):
        return str(value) if not math.isfinite(value) else value
    if isinstance(value, dict):
        return {str(key): _sanitize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_sanitize(item) for item in value]
    if value is None or isinstance(value, (str, int, bool)):
        return value
    return str(value)


@asynccontextmanager
async def lifespan(app: FastAPI):
    storage.init_db()
    yield


app = FastAPI(
    title="XR 場景物件管理 API",
    description="管理 XR 場景中的 3D 物件：名稱、模型網址、位置、旋轉、縮放。",
    version="1.0.0",
    lifespan=lifespan,
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": _sanitize(exc.errors())},
    )


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/objects", response_model=list[ObjectOut], tags=["objects"])
def list_objects(
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
):
    return storage.list_objects(skip, limit)


@app.post(
    "/objects",
    response_model=ObjectOut,
    status_code=status.HTTP_201_CREATED,
    tags=["objects"],
)
def create_object(payload: ObjectCreate):
    item = storage.create_object(payload)
    logger.info("object created: id=%s name=%s", item["id"], item["name"])
    return item


@app.get("/objects/{object_id}", response_model=ObjectOut, tags=["objects"])
def get_object(object_id: ObjectId):
    item = storage.get_object(object_id)
    if item is None:
        logger.warning("object not found: id=%s", object_id)
        raise HTTPException(status_code=404, detail=f"Object {object_id} not found")
    return item


@app.put("/objects/{object_id}", response_model=ObjectOut, tags=["objects"])
def update_object(object_id: ObjectId, payload: ObjectUpdate):
    item = storage.update_object(object_id, payload)
    if item is None:
        logger.warning("object not found for update: id=%s", object_id)
        raise HTTPException(status_code=404, detail=f"Object {object_id} not found")
    logger.info("object updated: id=%s name=%s", item["id"], item["name"])
    return item


@app.delete(
    "/objects/{object_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["objects"],
)
def delete_object(object_id: ObjectId):
    if not storage.delete_object(object_id):
        logger.warning("object not found for delete: id=%s", object_id)
        raise HTTPException(status_code=404, detail=f"Object {object_id} not found")
    logger.info("object deleted: id=%s", object_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
