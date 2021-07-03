#cython: language_level=3
import aio_pika
import aioredis
from loguru import logger
import nest_asyncio
import builtins
import orjson
from lynxfall.rabbit.core.backends import Backends
from lynxfall.utils.string import secure_strcmp
import time
nest_asyncio.apply()

# Import all needed backends
backends = Backends()
builtins.backends = backends

def serialize(obj):
    try:
        orjson.dumps({"rc": obj})
        return obj
    except:
        try:
            return dict(obj)
        except:
            return str(obj)

async def _new_task(queue, state):
    friendly_name = state.backends.getname(queue)
    _channel = await state.rabbit.channel()
    _queue = await _channel.declare_queue(queue, durable = True) # Function to handle our queue
    async def _task(message: aio_pika.IncomingMessage):
        """RabbitMQ Queue Function"""
        curr = state.stats.on_message
        logger.opt(ansi = True).info(f"<m>{friendly_name} called (message {curr})</m>")
        state.stats.on_message += 1
        _json = orjson.loads(message.body)
        _headers = message.headers
        if not _headers:
            logger.error(f"Invalid auth for {friendly_name}")
            message.ack()
            return # No valid auth sent
        if not secure_strcmp(_headers.get("auth"), state.worker_key):
            logger.error(f"Invalid auth for {friendly_name} and JSON of {_json}")
            message.ack()
            return # No valid auth sent

        # Normally handle rabbitmq task
        _task_handler = TaskHandler(_json, queue)
        rc, err = await _task_handler.handle(state)
        if isinstance(rc, Exception):
            logger.warning(f"{type(rc).__name__}: {rc} (JSON of {_json})")
            rc = f"{type(rc).__name__}: {rc}"
            state.stats.err_msgs.append(message) # Mark the failed message so we can ack it later    
        _ret = {"ret": serialize(rc), "err": err}

        if _json["meta"].get("ret"):
            await state.redis.set(f"rabbit.{_json['meta'].get('ret')}", orjson.dumps(_ret)) # Save return code in redis

        if state.backends.ackall(queue) or not _ret["err"]: # If no errors recorded
            message.ack()
        logger.opt(ansi = True).info(f"<m>Message {curr} Handled</m>")
        logger.debug(f"Message JSON of {_json}")
        await state.redis.incr(f"rmq_total_msgs", 1)
        state.stats.total_msgs += 1
        state.stats.handled += 1

    await _queue.consume(_task)

class TaskHandler():
    def __init__(self, dict, queue):
        self.dict = dict
        self.ctx = dict["ctx"]
        self.meta = dict["meta"]
        self.queue = queue

    async def handle(self, state):
        try:
            handler = state.backends.get(self.queue)
            rc = await handler(state, self.dict, **self.ctx)
            if isinstance(rc, tuple):
                return rc[0], rc[1]
            elif isinstance(rc, Exception):
                return rc, True
            return rc, False
        except Exception as exc:
            state.stats.errors += 1 # Record new error
            state.stats.exc.append(exc)
            return exc, True

class Stats():
    def __init__(self):
        self.errors = 0 # Amount of errors
        self.exc = [] # Exceptions
        self.err_msgs = [] # All messages that failed
        self.on_message = 1 # The currwnt message we are on. Default is 1
        self.handled = 0 # Handled messages count
        self.load_time = None # Amount of time taken to load site
        self.total_msgs = 0 # Total messages

    async def cure(self, index):
        """'Cures a error that has been handled"""
        self.errors -= 1
        await self.err_msgs[index].ack()

    async def cureall(self):
        i = 0
        while i < len(self.err_msgs):
            await self.cure(i)
            i+=1
        self.err_msgs = []
        return "Be sure to reload rabbitmq after this to clear exceptions"

    def __str__(self):
        s = []
        for k in self.__dict__.keys():
            s.append(f"{k}: {self.__dict__[k]}")
        return "\n".join(s)

class WorkerState():
    """
    Stores worker state
    - worker_key (the worker key)
    """
    pass

async def run_worker(
    *, 
    worker_key,
    backend_folder,
    startup_func,
    prepare_func
):
    """Main worker function"""
    state = WorkerState()
    builtins.state = state
    state.worker_key = worker_key
    startup_func(state, logger)
    state.start_time = time.time()
    # Import all needed backends
    state.backends = Backends(backend_folder = backend_folder)
    logger.opt(ansi = True).info(f"<magenta>Starting Lynxfall RabbitMQ Worker (time: {state.start_time})...</magenta>")
    state.stats = Stats()
    await backends.loadall(state) # Load all the backends and run prehooks
    await backends.load(state, "lynxfall.rabbit.core.default_backends.admin") # Load admin
    # Get handled message count
    total_msgs = await state.redis.get(f"rmq_total_msgs")
    state.stats.total_msgs = int(total_msgs) if total_msgs and isinstance(total_msgs, int) else 0
    state.prepare_rc = await prepare_func(state) if prepare_func else None
    for backend in backends.getall():
        await _new_task(backend, state)
    state.end_time = time.time()
    state.load_time = state.end_time - state.start_time
    logger.opt(ansi = True).info(f"<magenta>Worker up in {state.end_time - state.start_time} seconds at time {state.end_time}!</magenta>")

async def disconnect_worker():
    logger.opt(ansi = True).info("<magenta>RabbitMQ worker down. Killing DB connections!</magenta>")
    await builtins.state.rabbit.disconnect()
    await builtins.state.redis.close()
