import asyncio
from lynxfall.rabbit.client import RabbitClient

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
}

async def add_rmq_task(queue_name: str, data: dict, *, headers: dict = None, **meta):
    """Adds a RabbitMQ Task using the Fates List Worker Protocol"""
    if not RabbitClient.worker_key or not RabbitClient.redis or not RabbitClient.rabbit:
        raise Exception("You must set worker key, redis and redis using set before using this!")
    if meta:
        _meta = deepcopy(RMQ_META)
        _meta.update(meta)
        meta = _meta
    else:
        meta = RMQ_META
    meta["id"] = str(uuid.uuid4())
    base_headers = {"auth": RabbitClient.worker_key}
    if headers:
        headers = base_headers.update(headers)
    else:
        headers = base_headers
    channel = await RabbitClient.rabbit.channel()
    await channel.set_qos(prefetch_count=1)
    await channel.default_exchange.publish(
        aio_pika.Message(orjson.dumps({"ctx": data, "meta": meta}), delivery_mode=aio_pika.DeliveryMode.PERSISTENT, headers = headers),
        routing_key=queue_name
    )
