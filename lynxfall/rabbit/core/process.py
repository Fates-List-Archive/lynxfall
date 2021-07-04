#cython: language_level=3
import aio_pika
import aioredis
from loguru import logger
import nest_asyncio
import orjson
from lynxfall.rabbit.core.backends import Backends
from lynxfall.utils.string import secure_strcmp
from lynxfall.core.classes import Singleton
from lynxfall.rabbit.client import RabbitClient # Patch for rabbitmq
import time
import sys
import uuid
nest_asyncio.apply()
    
class WorkerState(Singleton):
    """
    Stores worker state
    - worker_key (the worker key)
    - rabbit (rabbit)
    - redis (redis)
    """
    pass

state = WorkerState()

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
    ackall = state.backends.ackall(queue)
    async def _task(message: aio_pika.IncomingMessage):
        """RabbitMQ Queue Function"""
        ran = True
        
        try:
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
            id = uuid.uuid4()
            _json["task_id"] = id
            state.tasks_running[id] = (_json, _headers, queue)
            _task_handler = TaskHandler(_json, queue)
            rc, err = await _task_handler.handle(state)
            del state.tasks_running[id]
        
            if isinstance(rc, Exception):
                await state.on_error(state, logger, message, rc, "task_error", "th_ret_exc")
                
                if not ackall: # If not a ackall task, then we raise the exception
                    raise rc
                    
                else:
                    rc = f"{type(rc).__name__}: {rc}"
            
            _ret = {"ret": serialize(rc), "err": err}

            if _json["meta"].get("ret"):
                key = f"lynxrabbit:{_json['meta'].get('ret')}"
                logger.debug(f"Saving to {key}")
                
                try:
                    await state.redis.set(key, orjson.dumps(_ret), ex = 60*2) # Save return code in redis
                    
                except Exception as exc:
                    await state.on_error(state, logger, message, exc, "serialize_error", "json_error")
                    
                    try:
                        extra = str(_ret["ret"])
                    
                    except Exception:
                        extra = "No extra info available"
                    
                    _ret["ret"] = f"Could not save return in json: {extra}"
                    _ret["err"] = True
                    
                    try:
                        await state.redis.set(key, orjson.dumps(_ret), ex = 60*2) # Save error code in redis
                    
                    except Exception:
                        extra = "No extra info available"
                        
                        _ret["ret"] = f"Could not save return in json: {extra}"
                        _ret["err"] = True
                        
                        await state.redis.set(key, orjson.dumps(_ret), ex = 60*2) # Save error code in redis
               
        except Exception as exc:
            logger.exception()
            await state.on_error(state, logger, message, exc, "runtime_error", "unknown")
            state.stats.err_msgs.append(message) # Mark the failed message so we can ack it later
            ran = False
            
        if ran: # If no errors recorded
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
                await state.on_error(state, logger, None, rc, "task_error", "ret_exc")
                raise rc
            
            return rc
        
        except Exception as exc:
            await state.on_error(state, logger, None, exc, "task_error", "failed_with_exc")
            state.stats.errors += 1 # Record new error
            state.stats.exc.append(exc)
            raise exc

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

async def run_worker(
    *, 
    worker_key,
    backend_folder,
    on_startup,
    on_prepare,
    on_stop,
    on_error,
    monitor = True
):
    """Main worker function"""
    state.worker_key = worker_key
    state.on_startup = on_startup
    state.on_prepare = on_prepare
    state.on_stop = on_stop
    state.on_error = on_error
    
    await state.on_startup(state, logger)
    
    if not getattr(state, "rabbit"):
        print("on_startup must initialize rabbit as state.rabbit")
        sys.exit(-1)
        
    if not getattr(state, "redis"):
        print("on_startup must initialize redis as state.redis")
        sys.exit(-1)
    
    state.start_time = time.time()
    state.tasks_running = {}
    
    RabbitClient.setup(worker_key, state.redis, state.rabbit) # Some workers may want to make a new task. Allow this
    
    # Import all needed backends
    state.backends = Backends(backend_folder = backend_folder)
    logger.opt(ansi = True).info(f"<magenta>Starting Lynxfall RabbitMQ Worker (time: {state.start_time})...</magenta>")
    
    state.stats = Stats()
    await state.backends.loadall(state) # Load all the backends and run prehooks
    
    if monitor:
        await state.backends.load(state, "lynxfall.rabbit.core.default_backends.admin") # Load admin
    
    # Get handled message count
    total_msgs = await state.redis.get(f"rmq_total_msgs")
    state.stats.total_msgs = int(total_msgs) if total_msgs and isinstance(total_msgs, int) else 0
    state.preparations = await state.on_prepare(state, logger) if state.on_prepare else None
    
    logger.opt(ansi = True).debug("Stats setup is done")
    for backend in state.backends.getall():
        await _new_task(backend, state)
        
    state.end_time = time.time()
    state.load_time = state.end_time - state.start_time
    logger.opt(ansi = True).info(f"<magenta>Worker up in {state.end_time - state.start_time} seconds at time {state.end_time}!</magenta>")
    return state

async def disconnect_worker():
    logger.opt(ansi = True).info("<magenta>RabbitMQ worker down. Killing DB connections!</magenta>")
    await state.on_stop(state, logger)
    await state.rabbit.disconnect()
    await state.redis.close()
