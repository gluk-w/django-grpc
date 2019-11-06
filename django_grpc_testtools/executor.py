from random import randint

from mirakuru import TCPExecutor


class TestGRPCServer:
    def __init__(self, manage_py, params=None):
        if params is None:
            params = {}
        params.setdefault('--port', 50000 + randint(0, 10000))
        self.port = params.get('--port')
        self.manage_py = manage_py
        self.process = TCPExecutor(
            ['python', self.manage_py, 'grpcserver'] + list(self.flat_params(params)),
            host='localhost', port=self.port
        )

    @classmethod
    def flat_params(cls, dict_):
        for k, v in dict_.items():
            yield str(k)
            if str(v) != "":
                yield str(v)

    def addr(self):
        return "localhost:%s" % self.port

    def start(self):
        self.process.start()

    def stop(self):
        self.process.stop()

