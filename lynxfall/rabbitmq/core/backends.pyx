# Import all needed backends
import importlib
import os
from loguru import logger

class Backends():
    def __init__(self, backend_folder = "rabbitmq/backend"):
        self.rmq_backends = {}
        self.backend_folder = backend_folder

    async def add(self, path, config, backend, reload, state):
        if not reload and config.queue in self.rmq_backends.keys():
            raise ValueError("Queue already exists and not in reload mode!")
        self.rmq_backends |= {config.queue: {"backend": backend, "config": config()}}
        pre = self.getpre(config.queue)
        logger.debug(f"Got prehook {pre}")
        if pre:
            self.rmq_backends[config.queue]["pre_ret"] = await pre(state)
        else:
            self.rmq_backends[config.queue]["pre_ret"] = None

    def ackall(self, queue):
        try:
            return self.rmq_backends[queue]["config"].ackall
        except:
            return False

    def getpre(self, queue):
        try:
            return self.rmq_backends[queue]["config"].pre
        except:
            return None

    def get(self, queue):
        return self.rmq_backends[queue]["backend"]

    def getname(self, queue):
        return self.rmq_backends[queue]["config"].name

    def getdesc(self, queue):
        return self.rmq_backends[queue]["config"].description

    def getall(self):
        return self.rmq_backends.keys()

    async def load(self, state, path, reload = False):
        logger.debug(f"Worker: Loading {path}")
        _backend = importlib.import_module(path)
        if reload:
            importlib.reload(_backend)
        config = _backend.Config
        await self.add(path = path, config = config, backend = _backend.backend, reload = reload, state = state)

    async def loadall(self, state):
        """Load all backends"""
        for f in os.listdir(self.backend_folder):
            if not f.startswith("_") and not f.startswith("."):
                await self.load(state, self.getpath(f))

    async def reload(self, state, backend):
        path = self.getpath(backend)
        logger.debug(f"Worker: Reloading {path}")
        try:
            await self.load(state, path, reload = True) 
        except Exception as exc:
            logger.warning(f"Reloading failed | {type(exc).__name__}: {exc}")
            raise exc

    def getpath(self, f):
        """Utility function to get the path given a .py file (or backend name)"""
        return self.backend_folder.replace("/", ".") + f.replace(".py", "")
