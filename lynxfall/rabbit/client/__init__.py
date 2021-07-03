class Client:
    worker_key: str = None
    redis = None
    rabbit = None

def setup(worker_key: str, redis, rabbit):
    Client.worker_key = worker_key
    Client.redis = redis
    Client.rabbit = rabbit
