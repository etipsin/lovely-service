import json
import traceback
from typing import Any
from uuid import UUID

import orjson
from aiohttp import web

from service.middleware.logger import ELKAsync
from service.middleware.data_classes import (
    ResponseFailure,
    ELKErrorLog,
    ELKRequestLog,
    ELKResponseLog,
)


async def get_request_body(request: Any, max_length: int = 0):
    """Get decoded json or body from the request."""

    body = ""

    # Aiohttp
    if hasattr(request, "text"):
        body = await request.text()

    try:
        body = orjson.loads(body)
    except Exception:
        pass

    if 0 < max_length < len(str(body)):
        body = str(body)[:max_length] + "..."

    return body


async def get_response_body(response: Any, max_length: int = 0):
    """Get decoded json or body from the response."""

    body = ""

    # Aiohttp
    if hasattr(response, "text"):
        try:
            body = json.loads(response.text)
        except json.JSONDecodeError:
            body = response.text
        except Exception:
            body = ""

    if 0 < max_length < len(str(body)):
        body = str(body)[:max_length] + "..."

    return body


async def get_response_status_code(response: Any):
    """Get status code from the response."""
    status_code = None

    # Aiohttp response
    if hasattr(response, "status"):
        status_code = response.status

    return status_code


async def log_request(
    request: web.Request, req_id: UUID, logger: ELKAsync = None
) -> None:
    """
    Log request in ELK.

    :param request: request object.
    :param req_id: request uuid.
    :param logger: ELKAsync logger.
    """

    if logger:
        # Remove Authorization header from logs
        headers = dict(request.headers)
        headers.pop("Authorization", None)

        await logger.info(
            msg=f"Request #{req_id}",
            extra=ELKRequestLog(
                **{
                    "type": "Request",
                    "request_uuid": str(req_id),
                    "url": str(request.url),
                    "method": request.method,
                    "body": await get_request_body(request),
                    "headers": headers,
                    "cookies": dict(request.cookies),
                },
            ).dict(),
        )


async def log_response(
    request: web.Request,
    req_id: UUID,
    response: web.Response,
    execution_time: float,
    logger: ELKAsync = None,
) -> None:
    """
    Log response in ELK.

    :param request: request object.
    :param req_id: request uuid.
    :param response: response object.
    :param execution_time: time elapsed since handler was called.
    :param logger: ELKAsync logger.
    """

    if logger:
        await logger.info(
            msg=f"Response #{req_id}",
            extra=ELKResponseLog(
                **{
                    "type": "Response",
                    "request_uuid": str(req_id),
                    "url": str(request.url),
                    "method": request.method,
                    "body": await get_response_body(response),
                    "status_code": await get_response_status_code(response),
                    "execution_time": execution_time,
                },
            ).dict(),
        )


async def log_error(
    request: web.Request,
    req_id: UUID,
    response: ResponseFailure,
    status_code: int,
    exception: Exception = None,
    logger: ELKAsync = None,
) -> None:
    """
    Log error in ELK.

    :param request: request object.
    :param req_id: request uuid.
    :param response: response object.
    :param status_code: response status code.
    :param exception: caught exception.
    :param logger: ELKAsync logger.
    """

    if logger:
        tb = None
        if exception:
            tb = "".join(traceback.format_tb(exception.__traceback__))

        await logger.error(
            msg=f"Error #{req_id}",
            extra=ELKErrorLog(
                **{
                    "type": "Error",
                    "request_uuid": str(req_id),
                    "url": str(request.url),
                    "method": request.method,
                    "body": await get_request_body(request),
                    "status_code": status_code,
                    "error_info": response.dict(),
                    "traceback": tb,
                },
            ).dict(),
        )
