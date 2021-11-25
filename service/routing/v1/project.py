import sqlalchemy as sa
from aiohttp import web
from aiojobs.aiohttp import atomic

from service.data_classes.project import *
from service.database.tables import project
from service.database.connector import AsyncpgsaStorage


@atomic
async def create(
    request: web.Request,
    data: RequestProjectCreate = None,
) -> ResponseProject:
    """Create Project."""

    data: RequestProjectCreate = data or request["data"]
    storage: AsyncpgsaStorage = request.app["Storage"]

    values = data.params.dict()

    query = project.insert().values(**values).returning(sa.literal_column("*"))
    result = await storage.fetchrow(query)

    response = ResponseProject(result=result)

    return response


async def read(
    request: web.Request, data: RequestProjectRead = None
) -> ResponseProjectSeveral:
    """Read Project."""

    data: RequestProjectRead = data or request["data"]
    storage: AsyncpgsaStorage = request.app["Storage"]

    query = project.select().where(project.c.id.in_(data.params))

    result = await storage.fetch(query)
    response = ResponseProjectSeveral(result=result)

    return response


@atomic
async def update(
    request: web.Request,
    data: RequestProjectUpdate = None,
) -> ResponseProject:
    """Update Project."""

    data: RequestProjectUpdate = data or request["data"]
    storage: AsyncpgsaStorage = request.app["Storage"]

    values = data.params.dict()
    values.pop("id")

    query = (
        project.update()
        .where(project.c.id == data.params.id)
        .values(**values)
        .returning(sa.literal_column("*"))
    )

    result = await storage.fetchrow(query)
    response = ResponseProject(result=result)

    return response


@atomic
async def delete(
    request: web.Request, data: RequestProjectDelete = None
) -> ResponseSuccess:
    """Delete Project."""

    data: RequestProjectDelete = data or request["data"]
    storage: AsyncpgsaStorage = request.app["Storage"]

    query = project.delete().where(project.c.id.in_(data.params))

    await storage.fetch(query)

    response = ResponseSuccess()

    return response


async def lst(
    request: web.Request, data: RequestProjectList = None
) -> ResponseProjectSeveral:
    """List of Projects."""

    data: RequestProjectList = data or request["data"]
    storage: AsyncpgsaStorage = request.app["Storage"]

    params = data.dict(exclude_unset=True)["params"]

    query = project.select()

    # Time
    if "created_gt" in params:
        query = query.where(
            project.c.created > params["created_gt"].replace(tzinfo=None)
        )

    if "created_lt" in params:
        query = query.where(
            project.c.created < params["created_lt"].replace(tzinfo=None)
        )

    if "updated_gt" in params:
        query = query.where(
            project.c.updated > params["updated_gt"].replace(tzinfo=None)
        )

    if "updated_lt" in params:
        query = query.where(
            project.c.updated < params["updated_lt"].replace(tzinfo=None)
        )

    query = query.order_by(project.c.created.desc())

    result = await storage.fetch(query)
    response = ResponseProjectSeveral(result=result)

    return response
