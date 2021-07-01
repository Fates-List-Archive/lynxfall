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
