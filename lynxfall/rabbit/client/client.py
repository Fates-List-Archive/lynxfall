import asyncio

# Needed for it to actually work
import uuid
from copy import deepcopy

import aio_pika
import orjson

RMQ_META = {
    "pv": 1, # Protocol Version
    "dbg": True, # Debug Mode
    "worker": None, # For when we do multi server rabbit
    "op": None, # Any operations that we should run as a string
    "ret": None # The UUID to save returned values to on Redis if wanted
}

async def add_rmq_task(queue_name: str, data: dict, **meta):
    """Adds a RabbitMQ Task using the Fates List Worker Protocol"""
    if not Client.worker_key or not Client.redis:
        raise Exception("You must set worker key and redis using set before using this!")
    if meta:
        meta = deepcopy(RMQ_META) | meta
    else:
        meta = RMQ_META
    channel = await rabbitmq_db.channel()
    await channel.set_qos(prefetch_count=1)
    await channel.default_exchange.publish(
        aio_pika.Message(orjson.dumps({"ctx": data, "meta": meta}), delivery_mode=aio_pika.DeliveryMode.PERSISTENT, headers = {"auth": Client.worker_key}),
        routing_key=queue_name
    )

async def add_rmq_task_with_ret(queue_name, data: dict, **meta):
    """Add RabbitMQ Task, wait for it to complete, then get return code from Redis and return it"""
    if "ret" in meta.keys():
        _ret = meta["ret"]
    else:
        _ret = str(uuid.uuid4())
        meta["ret"] = _ret
    await add_rmq_task(queue_name, data, **meta)
    return await rmq_get_ret(_ret)

async def rmq_get_ret(id):
    tries = 0
    while tries < 100:
        ret = await Client.redis.get(f"rabbit-{id}")
        if not ret:
            await asyncio.sleep(0.5) # Wait for half second before retrying
            tries += 1
            continue
        await Client,redis.delete(f"rabbit-{id}")
        return orjson.loads(ret), True
    return id, False # We didnt get anything
