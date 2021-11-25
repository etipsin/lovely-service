import orjson
from typing import Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone


def orjson_dumps(v, *, default=None):
    # Add UTC timezone to datetime fields
    for key, value in v.items():
        # If it's a list of dicts
        if isinstance(value, list):
            for vv in value:
                if isinstance(vv, dict):
                    for kkey, vvalue in vv.items():
                        if isinstance(vvalue, datetime):
                            vv[kkey] = vvalue.replace(tzinfo=timezone.utc)
        if isinstance(value, datetime):
            v[key] = value.replace(tzinfo=timezone.utc)

    # orjson.dumps returns bytes, to match standard json.dumps we need to decode
    return orjson.dumps(
        v,
        default=default,
        option=orjson.OPT_OMIT_MICROSECONDS | orjson.OPT_UTC_Z,
    ).decode()


# Base class
class BaseClass(BaseModel):
    class Config:
        # Change default json encoders/decoders to orjson ones
        json_loads = orjson.loads
        json_dumps = orjson_dumps


# Requests
class Request(BaseClass):
    params: Any = Field(title="Data.")


# Responses
class ResponseSuccess(BaseClass):
    success: bool = Field(True, description="Success.")
    result: Any = Field({}, title="Result.")


class ErrorResult(BaseClass):
    error_type: str = Field("", description="Error Type.")
    error_message: str = Field("", description="Error Message.")


class ResponseFailure(BaseClass):
    success: bool = Field(False, description="Success.")
    result: Optional[ErrorResult] = Field(title="Result.")


# Swagger examples
class Examples(BaseClass):
    class Config:
        """Adds additional schema."""

        schema_extra = {
            "default": {
                "400": {
                    "description": "Bad Request.",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/ResponseFailure"},
                            "examples": {
                                "ResponseFailureDataFormat": {
                                    "summary": "Bad Request Error.",
                                    "value": {
                                        "success": False,
                                        "result": {
                                            "error_type": "BadRequestError",
                                            "error_message": "Bad Request Error.",
                                        },
                                    },
                                },
                            },
                        },
                    },
                },
                "500": {
                    "description": "Internal Server Error.",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/ResponseFailure"},
                            "examples": {
                                "ResponseInternalServerError": {
                                    "summary": "Internal Server Error.",
                                    "value": {
                                        "success": False,
                                        "result": {
                                            "error_type": "DatabaseError",
                                            "error_message": "Database Connection Error.",
                                        },
                                    },
                                },
                            },
                        },
                    },
                },
            },
        }
