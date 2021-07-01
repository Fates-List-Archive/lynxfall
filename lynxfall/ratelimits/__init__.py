from math import ceil
from typing import Callable

import aioredis
from fastapi import HTTPException
from starlette.requests import Request
from starlette.responses import Response
from starlette.status import HTTP_429_TOO_MANY_REQUESTS

async def default_identifier(request: Request):
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0]
    return request.client.host


async def default_callback(request: Request, response: Response, pexpire: int, expire: int):
    """
    default callback when too many requests
    :param request:
    :param pexpire: The remaining milliseconds
    :param response:
    :return:
    """

    raise HTTPException(
        HTTP_429_TOO_MANY_REQUESTS, 
        detail = f"You are being ratelimited. Try again in {expire} seconds", 
        headers={"Retry-After": str(expire)} | dict(response.headers)
    )


class LynxfallLimiter:
    redis: aioredis.Redis = None
    prefix: str = None
    identifier: Callable = None
    callback: Callable = None

    @classmethod
    def init(
        cls,
        redis: aioredis.Redis,
        prefix: str = "lynxfall_limiter",
        identifier: Callable = default_identifier,
        callback: Callable = default_callback,
    ):
        cls.redis = redis
        cls.prefix = prefix
        cls.identifier = identifier
        cls.callback = callback
