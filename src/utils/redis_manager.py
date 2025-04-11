from redis import Redis


class RedisManager(Redis):
    def __init__(self, **kwargs):
        test_connection = kwargs.get("test_connection", False)
        del kwargs["test_connection"]
        super().__init__(**kwargs)
        if test_connection:
            self.set("testconnection", "testconnection", ex=3)
