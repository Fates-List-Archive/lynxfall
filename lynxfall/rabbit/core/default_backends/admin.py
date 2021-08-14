"""Default backend for admin tasks. Required for monitoring lynx"""

from lynxfall.rabbit.core import *
import asyncio
import orjson

# Some functions

def _handle_await(code):
    if "await " not in code:
        return code.replace("return ", "ret = ")
    code = "".join(["    " + txt + "\n" for txt in code.lstrip().split('\n')])
    return f"""
async def task_runner():
{code}
ret = asyncio.get_event_loop().run_until_complete(task_runner())
"""

def serialize(data):
    try:
        return orjson.dumps(data)
    except Exception:
        return str(data)
    
def _exec_op(op):
    try:
        op = _handle_await(op)
        loc = {}
        exec(op.lstrip(), globals() | locals(), loc)
        _ret = loc["ret"] if loc.get("ret") is not None else loc # Get return stuff
        if not loc:
            _ret = None # No return or anything
        _err = False
    except Exception as exc:
        _ret, _err = exc, True
    return _ret, _err

# Actual Code Below

class Config:
    queue = "_admin"
    name = "Admin/Monitoring Backend"
    description = "Perform/Evaluate commands in Lynxfall worker for debugging."
    
async def backend(state, json, **kwargs):
    if json["meta"].get("op"):
        # Handle admin operations
        op = json["meta"]["op"]
        _ret, _err = _exec_op(op)
        return {"ret": _ret, "err": _err}
    return {"ret": None, "err": False}
