#cython: language_level=3
"""Lynxfall Task Handling using rabbitmq (simple rabbitmq workers)"""
import asyncio
import importlib
from loguru import logger
from lynxfall.rabbit.core.process import run_worker, disconnect_worker

def run(**run_worker_args):
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.create_task(run_worker(**run_worker_args))

        # we have now entered a never-ending loop that waits for data and runs
        # callbacks whenever necessary. 
        loop.run_forever()
    except KeyboardInterrupt:
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(disconnect_worker())
        except Exception:
            pass
    except Exception:
        logger.exception("Something happened and the worker was forced to shut down!")
