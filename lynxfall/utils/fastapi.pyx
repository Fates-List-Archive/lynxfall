#cython: language_level=3
import secrets
import string

from fastapi import Request
from fastapi.responses import HTMLResponse, ORJSONResponse, RedirectResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.status import HTTP_302_FOUND, HTTP_303_SEE_OTHER
from pydantic import BaseModel
import importlib
import os
from loguru import logger


# Some basic utility functions for Fates List (and other fastapi users as well)
def redirect(path: str) -> RedirectResponse:
    return RedirectResponse(path, status_code=HTTP_303_SEE_OTHER)


def abort(code: int) -> StarletteHTTPException:
    raise StarletteHTTPException(status_code=code)

    
# API returners
def api_return(done: bool, reason: str, status_code: int, headers: dict = None, **kwargs): 
    serialized: dict = {}
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


# Simple API versioning for APIs
def api_versioner(request, def_version):
    path = str(request.url.path)
    new_scope = request.scope
    if path.startswith("/api/") and not path.startswith(("/api/v", "/api/ws")):
        if request.headers.get("API-Version"):
            api_ver = request.headers.get("API-Version")
        else:
            api_ver = str(def_version)
        new_scope["path"] = path.replace("/api", f"/api/v{api_ver}")
    else:
        if path.startswith("/api/v"):
            api_ver = path.split("/")[2][1:] # Split by / and get 2nd (vX part and then get just X)
        else:
            api_ver = str(def_version)
    api_ver = "0" if not api_ver
    if request.headers.get("Method") and str(request.headers.get("Method")).upper() in ("GET", "POST", "PUT", "PATCH", "DELETE"):
        new_scope["method"] = str(request.headers.get("Method")).upper()
    return new_scope, api_ver


# A simple routing system for those who don't want to worry about the nuances of imcluding routers
def include_routers(
    app, 
    service_name, 
    service_dir, 
    ignore_starts: tuple = ("_", ".", "models", "base")
):
    logger.info(f"Loading routes for service {service_name}")
    
    for root, dirs, files in os.walk(service_dir):
        if not root.startswith(ignore_starts):
            rrep = root.replace("/", ".")
            for f in files:
                if not f.startswith(ignore_starts):
                    
                    try:
                        end = f[-3:]
                    except IndexError:
                        continue
                    
                    if end == ".py":
                        path = f"{rrep}.{f.replace('.py', '')}"
                        logger.info(
                            f"Loading route {f} with path {path} and root dir {root}"
                        )
                        route = importlib.import_module(path)
                        app.include_router(route.router)

    logger.info(f"Done init of {service_name}")
