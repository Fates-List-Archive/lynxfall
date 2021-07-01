#cython: language_level=3

# Stub to bypass Cython async limitations with regards to coroutines
from typing import Optional, List

from starlette.requests import Request
from starlette.responses import Response

from lynxfall.ratelimits import LynxfallLimiter
from lynxfall.ratelimits.core import Limit, _handle_rl

class Ratelimiter:
    def __init__(
        self,
        *,
        global_limit: Limit,
        sub_limits: Optional[List[Limit]] = [],
    ):
        self.sub_limits = sub_limits
        self.global_limit = global_limit
    
    async def __call__(self, request: Request, response: Response):          
        return await _handle_rl(
            request = request, 
            response = response,
            limits = self.sub_limits,
            gstrategy = self.global_limit,
            prefix = LynxfallLimiter.prefix,
            identifier = LynxfallLimiter.identifier or self.identifier,
            callback = LynxfallLimiter.callback or self.callback,
            redis = LynxfallLimiter.redis
        )
