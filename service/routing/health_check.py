from aiohttp import web


async def health_check(request: web.Request) -> web.Response:
    """
    Check service state.

    ---
    security:
        - bearerAuth: []
    summary: Check service state.
    tags:
        - Misc
    description: Check service state.
    responses:
        '200':
            description: Success operation.
    """

    return web.Response(text="200")
