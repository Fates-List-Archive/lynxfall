import secrets
import string

from fastapi import Request
from fastapi.responses import HTMLResponse, ORJSONResponse, RedirectResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.status import HTTP_302_FOUND, HTTP_303_SEE_OTHER

# Some basic utility functions for Fates List (and other users as well)
def redirect(path: str) -> RedirectResponse:
    return RedirectResponse(path, status_code=HTTP_303_SEE_OTHER)

def abort(code: str) -> StarletteHTTPException:
    raise StarletteHTTPException(status_code=code)
    
# API returners
def api_return(done: bool, reason: str, status_code: int, headers: dict = None, **kwargs): 
    serialized = {}
    for kwarg in kwargs.keys():
        if isinstance(kwargs[kwarg], BaseModel):
            serialized = serialized | {kwarg: kwargs[kwarg].dict()}
        else:
            serialized = serialized | {kwarg: kwargs[kwarg]}
    return ORJSONResponse({"done": done, "reason": reason} | serialized, status_code = status_code, headers = headers)

def api_error(reason: str, code: int = None, status_code: int = 400, **kwargs):
    return api_return(done = False, reason = reason, status_code = status_code, **kwargs)

def api_no_perm(permlevel: int = None):
    base = "You do not have permission to perform this action!"
    if permlevel:
        base += f" You need permlevel {permlevel}"
    return api_error(
        base,
        status_code = 403
    )

def api_success(reason: str = None, status_code: int = 200, **kwargs):
    if kwargs and status_code == 200:
        status_code = 206
    return api_return(done = True, reason = reason, status_code = status_code, **kwargs)
