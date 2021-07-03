class Client:
    worker_key: str = None
    redis = None

def setup(worker_key: str, redis):
    Client.worker_key = worker_key
    Client.redis = redis
