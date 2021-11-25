import time
import uuid
from typing import Any

from aiohttp import web
from pydantic import BaseModel, ValidationError

from service.middleware.logger import ELKAsync
from service.middleware.data_classes import ErrorResult, ResponseFailure
from service.middleware.exceptions import BadRequestError
from service.middleware.utils import (
    log_error,
    log_request,
    log_response,
)


class MiddlewareMain:
    @staticmethod
    @web.middleware
    async def server_error_handler(request, handler, logger: ELKAsync = None):
        """
        Catch and log errors.
        Requires ELKAsync logger object in request.app["ELKAsync"],
        else doesn't log.

        :param request: request object.
        :param handler: handler function.
        :param logger: ELKAsync logger.
        :return: response object or an aiohttp exception.
        """

        req_id = uuid.uuid4()

        # Get logger object
        if (
            isinstance(request.app, web.Application)
            and "ELKAsync" in request.app
            and request.app["ELKAsync"]
        ):
            logger = request.app["ELKAsync"]

        try:
            await log_request(request, req_id, logger=logger)
            time_begin = time.time()

            response = await handler(request)

            time_end = time.time() - time_begin
            await log_response(request, req_id, response, time_end, logger=logger)

            return response
        # 401: Unauthorized
        except web.HTTPUnauthorized as e:
            response = ResponseFailure(
                result=ErrorResult(
                    error_type=type(e).__name__,
                    error_message=str(e),
                ),
            )

            await log_error(request, req_id, response, 401, exception=e, logger=logger)

            raise web.HTTPUnauthorized(
                text=response.json(), content_type="application/json"
            )
        # 400: BadRequest
        except BadRequestError as e:
            response = ResponseFailure(
                result=ErrorResult(
                    error_type=type(e).__name__,
                    error_message=str(e),
                ),
            )

            await log_error(request, req_id, response, 400, exception=e, logger=logger)

            raise web.HTTPBadRequest(
                text=response.json(), content_type="application/json"
            )
        # 200: User Exceptions
        except UserWarning as e:
            response = ResponseFailure(
                result=ErrorResult(
                    error_type=type(e).__name__,
                    error_message=str(e),
                ),
            )

            await log_error(request, req_id, response, 200, exception=e, logger=logger)

            raise web.HTTPOk(text=response.json(), content_type="application/json")
        # 500: InternalServerError
        except Exception as e:
            response = ResponseFailure(
                result=ErrorResult(
                    error_type=type(e).__name__,
                    error_message=str(e),
                ),
            )

            await log_error(request, req_id, response, 500, exception=e, logger=logger)

            raise web.HTTPInternalServerError(
                text=response.json(), content_type="application/json"
            )

    @staticmethod
    @web.middleware
    async def prepare_data(request: web.Request, handler: Any) -> web.Response:
        """
        Middleware that takes json payload from incoming requests,
         validates it and sends back data received from handlers.
        This middleware expects all responses to be pydantic dataclasses
         or data structures implementing .json() method.
        Removal of this middleware removes validation of data
         and breaks logic of handlers.

        :param request: web.Request object.
        :param handler: handler function.
        :return: results of calling handler.
        """

        # If handler has data parameter and defines its type
        if "data" in handler.__annotations__:
            try:
                annotation = handler.__annotations__["data"]
                request_json = await request.json()

                try:
                    # Usually handlers should use pydantic class as an annotation
                    if issubclass(annotation, BaseModel):
                        request["data"] = annotation(**request_json)
                    else:
                        raise BadRequestError(
                            "Handler data annotation is not a subclass of pydantic.BaseModel."
                        )
                # issubclass(..., Union[...]) throws TypeError
                except TypeError:
                    # Getting classes from Union
                    classes: tuple = annotation.__args__
                    matched_classes_number: int = 0
                    validation_error: str = ""

                    # Attempt to put incoming data in all classes in the union
                    for single_class in classes:
                        try:
                            request["data"] = single_class(**request_json)
                            matched_classes_number += 1
                        except ValidationError as e:
                            validation_error = str(e)

                    # If failed to match any of the classes, raise the last validation error
                    if matched_classes_number == 0:
                        raise BadRequestError(validation_error)
                    # Everything is fine
                    elif matched_classes_number == 1:
                        pass
                    # If matched several classes
                    else:
                        raise BadRequestError(
                            "Request matches several of the classes in the union."
                        )
            except ValidationError as e:
                raise BadRequestError(
                    e.json(indent=0).replace("\n", "").replace('"', "'")
                )
            except Exception as e:
                raise BadRequestError(str(e))

        # Call the handler or the next middleware
        # Data parameter is not passed to avoid breaking middleware chaining logic
        response = await handler(request)

        if isinstance(response, BaseModel):
            return web.json_response(text=response.json())

        # No need to wrap response
        return response
