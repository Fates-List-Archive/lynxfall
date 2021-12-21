#cython: language_level=3

# Cython is dumb and doesn't handle coroutines correctly, lets fix this by using a stub (depends.py) which uses the core stuff here
from typing import Callable, Optional, List

from starlette.requests import Request
from starlette.responses import Response
from fastapi.exceptions import HTTPException

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
    identifier, 
    callback,
    redis,
    global_limit: List[Limit] = None,
    operation_bucket = None,
    applied_global: bool = False,
    **kwargs
):
    f_args = locals()
    if not redis:
        raise Exception("You must call LynxfallLimiter.init in the startup event of FastAPI!")
    
    prefix = "cad-rl:" # Cats and dragons RL (because it tends to be random on how it ratelimits)
    
    cdef int index = 0
    
    # Strategy for RL is picked randomly and applied
    index = random.randint(0, len(limits) - 1)
    strategy = limits[index]
    
    if applied_global: 
        meta = "global"
    else:
        meta = "sub"
    
    if global_limit and not applied_global:
        f_args |= {"applied_global": True, "limits": global_limit}
        await _handle_rl(**f_args)
    
    # No other limit, quit
    if not applied_global and len(limits) <= 1:
        return None
        
    # moved here because constructor run before app startup
    rate_key = await identifier(request)
        
    # No ratelimit
    if not rate_key:
        return
        
    # Key format for per route sublimits is lynxfall_limiter.sub-METHOD@URL:KEY#index - These are specific to a single route and keep rotating
    # Key format for global ratelimits is lynxfall_limiter.global-METHOD@URL:KEY - These are global to a API endpoint and blocks you from the whole API for 3 minutes + milliseconds if you hit it
    # Key format for API wide (ceiling) ratelimit if needed is lynxfall_limiter.apiwide:KEY
    # Key format for API block limit (global and API wide trigger this) is lynxfall_limiter.block:KEY. It may or may not have a expiry
    method = request.method if request.method not in ("HEAD", "OPTIONS", "CONNECT", "TRACE") else "GET"
    if operation_bucket:
        path = operation_bucket
    else:
        path = request.url.path
        
    key = f"{prefix}{method}@{path}:{rate_key}#{index}::{meta}"
        
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
        
    key_rl = await rl_update(key)
        
    nums: int = key_rl[0]
    pexpires: int = key_rl[1]
        
    # Expire ratelimits
    if nums == 1:
        await redis.pexpire(key, strategy.milliseconds)
            
    # Set ratelimit headers
    def _set_headers(response, strategy, pexpire, num, *, ext: str):
        response.headers[f"Requests-{ext}-Total"] = str(strategy.times)
        response.headers[f"Requests-{ext}-Used"] = str(num)
        response.headers[f"Requests-{ext}-Remaining"] = str(strategy.times - num) if num <= strategy.times else "-1" # Requests remaining in time window
        response.headers[f"Requests-{ext}-Window"] = str(strategy.milliseconds/1000)
        response.headers[f"Requests-{ext}-Expiry-Time"] = str(pexpire)
        response.headers[f"Requests-{ext}-Key"] = key
        response.headers["Request-Bucket"] = path
        return response
        
    response = _set_headers(response, strategy, pexpires, nums, ext = "Sub" if not applied_global else "Global")
    
    if not applied_global:
        response.headers["Ratelimit-Sub-Index"] = str(index)
        
    cdef int expire = 0
    
    # Handle limits
    if nums > strategy.times:
        expire = ceil(pexpires / 1000)
        return await callback(request, response, pexpires, expire)
        
    # Handle API blocks
    api_block_key = f"{prefix}api-block:{rate_key}"
      
    blocked = await redis.get(api_block_key)
    if blocked:
        raise HTTPException(detail="Due to API abuse, you have been temporarily blocked from using our APIs!", status_code=400)
        
    return None
