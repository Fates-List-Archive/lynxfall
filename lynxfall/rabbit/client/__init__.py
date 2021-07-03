class Client:
    worker_key: str = None
    redis = None
    rabbit = None

    @classmethod
    def setup(clx, worker_key: str, redis, rabbit):
        cls.worker_key = worker_key
        cls.redis = redis
        cls.rabbit = rabbit
