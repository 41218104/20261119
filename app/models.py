from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator


class Vector3(BaseModel):
    model_config = ConfigDict(extra="forbid")

    x: float = Field(allow_inf_nan=False)
    y: float = Field(allow_inf_nan=False)
    z: float = Field(allow_inf_nan=False)


class ScaleVector(BaseModel):
    model_config = ConfigDict(extra="forbid")

    x: float = Field(gt=0, allow_inf_nan=False)
    y: float = Field(gt=0, allow_inf_nan=False)
    z: float = Field(gt=0, allow_inf_nan=False)


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

    @model_validator(mode="before")
    @classmethod
    def reject_explicit_none(cls, values):
        """明確傳 null 視為無效更新，避免把 None 寫進 NOT NULL 欄位。"""
        if isinstance(values, dict):
            for key, value in values.items():
                if value is None:
                    raise ValueError(f"{key} 不可為 null")
        return values


class ObjectOut(ObjectBase):
    id: int
    scale: ScaleVector
    created_at: datetime
    updated_at: datetime
