from pathlib import Path

import aiojobs.aiohttp
import sentry_sdk
from aiohttp import web
from aiohttp_swagger import setup_swagger
from sentry_sdk.integrations.aiohttp import AioHttpIntegration

from alembic import command
from alembic.config import Config as AConfig

from service.middleware.logger import ELKAsync
from service.middleware.middleware import MiddlewareMain
from service.database.connector import AsyncpgsaStorage
from service.swagger.swagger import get_definitions

from service.config import Config
from service.data_classes import project
from service.routes import get_routes_misc, get_routes_v1


async def on_startup(app: web.Application) -> None:
    # Alembic
    alembic_config = AConfig(Path(__file__).parent.parent / "alembic.ini")
    alembic_config.set_main_option(
        "script_location", str(Path(__file__).parent.parent / "alembic")
    )
    alembic_config.set_main_option("sqlalchemy.url", Config.POSTGRES_DSN)
    command.upgrade(alembic_config, "head")


def get_app() -> web.Application:
    """
    Create aiohttp Application with
     routes, cleanup_ctx functions, and swagger docs.

    :return: configured aiohttp Application object.
    """
    api_v1 = web.Application()

    # Adding middlewares
    api_v1.middlewares.append(MiddlewareMain.server_error_handler)
    api_v1.middlewares.append(MiddlewareMain.prepare_data)

    # Adding routes
    api_v1.add_routes(get_routes_v1())

    # Adding on_startup and on_shutdown
    api_v1.on_startup.append(on_startup)

    # ELK
    api_v1["ELKAsync"] = ELKAsync(
        host=Config.ELK_HOST,
        port=Config.ELK_PORT,
        level=Config.ELK_LEVEL,
        service_name=Config.ELK_SERVICE_NAME,
        logger_name=Config.ELK_LOGGER_NAME,
        enable=Config.ELK_ENABLE,
    )
    api_v1.cleanup_ctx.append(api_v1["ELKAsync"].setup)

    # Storage
    api_v1["Storage"] = AsyncpgsaStorage(
        dsn=Config.POSTGRES_DSN,
        min_size=Config.POSTGRES_MIN_SIZE,
        max_size=Config.POSTGRES_MAX_SIZE,
        logger=api_v1["ELKAsync"],
    )
    api_v1.cleanup_ctx.append(api_v1["Storage"].setup)

    app = web.Application()
    app.add_subapp("/api/v1/", api_v1)
    app.add_routes(get_routes_misc())

    if Config.SWAGGER_ENABLE:
        setup_swagger(
            app,
            swagger_url="/doc",
            definitions=get_definitions(any_dataclass_module=project),
            title="Lovely Service Documentation.",
            description="Lovely Service Documentation.",
            api_version="1.0.0",
            ui_version=3,
        )

    aiojobs.aiohttp.setup(app)

    return app


def run_server():
    """Run server."""
    if Config.SENTRY_ENABLE and Config.SENTRY_DSN:
        sentry_sdk.init(dsn=Config.SENTRY_DSN, integrations=[AioHttpIntegration()])

    app = get_app()

    web.run_app(app, host=Config.HOST, port=Config.PORT)
