"""Default backend for admin tasks. Required for monitoring lynx"""

from lynxfall.rabbit.core import *

# Some functions

def _handle_await(code):
    if "await " not in code:
        return code.replace("return ", "ret = ")
    code = "".join(["    " + txt + "\n" for txt in code.lstrip().split('\n')])
    return f"""
async def task_runner():
{code}
ret = asyncio.run(task_runner())
"""

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
    name = "Admin Task"
    description = "Perform/Evaluate commands in Lynxfall worker for debugging."
    ackall = True

async def backend(state, json, **kwargs):
    if json["meta"].get("op"):
        # Handle admin operations
        op = json["meta"]["op"]
        _ret, _err = _exec_op(op)
        return _ret, _err
    return None
