#cython: language_level=3

# Cython is dumb and doesn't handle coroutines correctly, lets fix this by using a stub (depends.py) which uses the core stuff here
from typing import Callable, Optional, List

from starlette.requests import Request
from starlette.responses import Response

import random
from math import ceil
import asyncio

class Limit:
    def __init__(
        self,
        int times = 1,
        int milliseconds = 0,
        int seconds = 0,
        int minutes = 0,
        int hours = 0,
    ):
        self.times: int = times
        self.milliseconds: int = milliseconds + 1000 * seconds + 60000 * minutes + 3600000 * hours   

async def _handle_rl(
    *,
    request: Request, 
    response: Response, 
    limits: List[Limit], 
    gstrategy: Limit,
    prefix,
    identifier, 
    callback,
    redis,
    operation_bucket = None
):
    if not redis:
        raise Exception("You must call LynxfallLimiter.init in the startup event of FastAPI!")
        
    cdef int index = 0
    
    # Strategy for RL is picked randomly and applied
    if limits:
        index = random.randint(0, len(limits) - 1)
        strategy = limits[index]
        
    # moved here because constructor run before app startup
    rate_key = await identifier(request) 
        
    # No ratelimit
    if not rate_key:
        return
        
    # Key format for per route sublimits is lynxfall_limiter.sub-METHOD@URL:KEY#index - These are specific to a single route and keep rotating
    # Key format for global ratelimits is lynxfall_limiter.global-METHOD@URL:KEY - These are global to a API endpoint and blocks you from the whole API for 3 minutes + milliseconds if you hit it
    # Key format for API wide (ceiling) ratelimit if needed is lynxfall_limiter.apiwide:KEY
    # Key format for API block limit (global and API wide trigger this) is lynxfall_limiter.block:KEY. It may or may not have a expiry
    if not operation_bucket:
        method = request.method if request.method not in ("HEAD", "OPTIONS", "CONNECT", "TRACE") else "GET"
        path = request.url.path
    else:
        method = "OP"
        path = operation_bucket
        
    sub_key = f"{prefix}.sub-{method}@{request.url.path}:{rate_key}#{index}" if limits else ""
    global_key = f"{prefix}.global-{method}@{request.url.path}:{rate_key}"
    api_block_key = f"{prefix}.block:{rate_key}"
        
    async def rl_update(key):
        tr = redis.pipeline()
        tr.incrby(key, 1)
        tr.pttl(key)
        return await tr.execute()
        
    # Get rl for sub and global ratelimit
    cdef int nums = 0
    cdef int pexpires = 0
    cdef int numg = 0
    cdef int pexpireg = 0
        
    sub_key_rl = await rl_update(sub_key)
        
    if limits:
        nums: int = sub_key_rl[0]
        pexpires: int = sub_key_rl[1]
 
    numg, pexpireg = await rl_update(global_key)
        
    # Expire ratelimits
    if limits and nums == 1:
        await redis.pexpire(sub_key, strategy.milliseconds)
        
    if numg == 1 and gstrategy:
        await redis.pexpire(global_key, gstrategy.milliseconds)
            
    # Set ratelimit headers
    def _set_headers(response, strategy, pexpire, num, *, ext: str):
        response.headers[f"Requests-{ext}-Total"] = str(strategy.times)
        response.headers[f"Requests-{ext}-Used"] = str(num)
        response.headers[f"Requests-{ext}-Remaining"] = str(strategy.times - num) if num <= strategy.times else "-1" # Requests remaining in time window
        response.headers[f"Requests-{ext}-Window"] = str(strategy.milliseconds/1000)
        response.headers[f"Requests-{ext}-Expiry-Time"] = str(pexpire)
        response.headers["Request-Bucket"] = path
        return response
        
    response = _set_headers(response, strategy, pexpires, nums, ext = "Sub") if limits else response
    response = _set_headers(response, gstrategy, pexpireg, numg, ext = "Global")   
        
    if limits:
        response.headers["Ratelimit-Sub-Index"] = str(index)
        
    cdef int expire = 0
        
    # Handle ratelimits
    if gstrategy and numg > gstrategy.times:
        tr = redis.pipeline()
        tr.incrby(api_block_key, 1)
        tr.pexpire(api_block_key, gstrategy.milliseconds + 1000*60*3)
        await tr.execute()
        expire = ceil(pexpireg / 1000)
        return await callback(request, response, pexpireg, expire)
        
    elif limits and nums > strategy.times:
        expire = ceil(pexpires / 1000)
        return await callback(request, response, pexpires, expire)
        
    # Handle API blocks
    tr = redis.pipeline()
    tr.get(api_block_key)
    tr.pttl(api_block_key)
    blocked, pexpireb = await tr.execute()
    if blocked:
        expire = ceil(pexpireb / 1000)
        return await callback(request, response, pexpireb, expire)
        
    return None
