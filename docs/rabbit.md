## Lynxfall RabbitMQ Worker documentation

Lynxfall RabbitMQ workers are a easy and robust way of handling messages/background tasks/queues. 
It uses RabbitMQ for the actual queue system, Redis for returning data from the worker and some custom code to make everything work.

### Creating a worker

Creating a worker requires you to do three things:

1) A launcher file to run your worker
2) Actual tasks (called backends on Lynxfall) for your worker to run
3) Add tasks to it using add_rmq_task

The below sections will deal with creating these two things.

#### The Launcher File

For extra security, you will need to first make a random secret called the worker key. You can use any random string generator to do this. Note that if this key is ever cracked or leaked, attackers may be able to gain arbitary code execution on your worker, so keep the worker key safe, preferrably in a .env file

Next, create a file called rabbitmq_worker.py and put the following code in it:

```py

from lynxfall.rabbit.launcher import run
import aioredis
import aio_pika

async def on_startup(state, logger):
    state.redis = aioredis.from_url(...)
    state.rabbit = aio_pika.connect_robust(...)

async def on_prepare(state, logger):
    """Do any custom preparations here"""
    pass

async def on_stop(state, logger):
    """Do on stop stuff here"""
    pass

run(
    worker_key = worker_key, 
    backend_folder = "my backend/tasks folder",
    on_startup = on_startup, 
    on_prepare = on_prepare, 
    on_stop = on_stop
)
```

Update the ...'s in the aioredis and aio_pika connection lines with your database details. Example below:

```py

redis = await aioredis.from_url('redis://localhost:12348', db = 1)
rabbit = await aio_pika.connect_robust(
    "amqp://meow:RABBITMQ_PWD@127.0.0.1/"
)
```
