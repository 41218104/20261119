from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Response, status

from . import storage
from .models import ObjectCreate, ObjectUpdate


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


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/objects", tags=["objects"])
def list_objects():
    return storage.list_objects()


@app.post("/objects", status_code=status.HTTP_201_CREATED, tags=["objects"])
def create_object(payload: ObjectCreate):
    return storage.create_object(payload)


@app.get("/objects/{object_id}", tags=["objects"])
def get_object(object_id: int):
    item = storage.get_object(object_id)
    if item is None:
        raise HTTPException(status_code=404, detail=f"Object {object_id} not found")
    return item


@app.put("/objects/{object_id}", tags=["objects"])
def update_object(object_id: int, payload: ObjectUpdate):
    item = storage.update_object(object_id, payload)
    if item is None:
        raise HTTPException(status_code=404, detail=f"Object {object_id} not found")
    return item


@app.delete(
    "/objects/{object_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["objects"],
)
def delete_object(object_id: int):
    if not storage.delete_object(object_id):
        raise HTTPException(status_code=404, detail=f"Object {object_id} not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
