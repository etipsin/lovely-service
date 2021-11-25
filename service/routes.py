from aiohttp import web
from service.swagger.swagger import update_function_docstring_with_swagger

from service.routing import health_check
from service.routing.v1 import project


def get_routes_v1():
    """
    Create aiohttp routes definitions.

    :return: aiohttp routes definitions.
    """

    functions = [
        # Project
        ("/create", project.create),
        ("/read", project.read),
        ("/update", project.update),
        ("/delete", project.delete),
        ("/list", project.lst),
    ]

    routes = []
    for path, func in functions:
        func = update_function_docstring_with_swagger(func)

        # web.post(...) is a frozen structure,
        # so we need to modify functions before its creation
        routes.append(web.post(path, func))

    return routes


def get_routes_misc():
    """
    Create aiohttp routes definitions.

    :return: aiohttp routes definitions.
    """

    functions = [("/health_check", health_check.health_check)]

    routes = []
    for path, func in functions:
        func = update_function_docstring_with_swagger(func)

        # web.post(...) is a frozen structure,
        # so we need to modify functions before its creation
        routes.append(web.get(path, func))

    return routes
