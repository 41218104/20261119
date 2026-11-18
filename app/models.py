from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class Vector3(BaseModel):
    x: float
    y: float
    z: float


class ScaleVector(BaseModel):
    x: float = Field(gt=0)
    y: float = Field(gt=0)
    z: float = Field(gt=0)


class ObjectBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=100)
    model_url: HttpUrl
    position: Vector3
    rotation: Vector3


class ObjectCreate(ObjectBase):
    scale: ScaleVector


class ObjectUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=100)
    model_url: HttpUrl | None = None
    position: Vector3 | None = None
    rotation: Vector3 | None = None
    scale: ScaleVector | None = None


class ObjectOut(ObjectBase):
    id: int
    scale: ScaleVector
    created_at: datetime
    updated_at: datetime
