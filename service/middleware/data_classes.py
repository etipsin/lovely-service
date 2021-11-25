import orjson
from typing import Union, Optional
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


class ErrorResult(BaseClass):
    error_type: str = Field("", description="Error Type.")
    error_message: str = Field("", description="Error Message.")


class ResponseFailure(BaseClass):
    success: bool = Field(False, description="Success.")
    result: Optional[ErrorResult] = Field(title="Result.")


class ELKLog(BaseClass):
    type: str = Field(description="Request Type.")
    request_uuid: str = Field(description="UUID Request.")
    url: str = Field(description="URL Request.")
    method: str = Field(description="Request Method.")
    body: Union[str, dict, list] = Field(description="Request Body.")


class ELKRequestLog(ELKLog):
    headers: dict = Field(description="Request Headers.")
    cookies: dict = Field(description="Request Cookies.")


class ELKResponseLog(ELKLog):
    status_code: int = Field(description="Status Code.")
    execution_time: float = Field(description="Execution Time.")


class ELKErrorLog(ELKLog):
    status_code: int = Field(description="Response status.")
    error_info: ResponseFailure = Field(description="Error Information.")
    traceback: str = Field(description="Traceback.")
