import subprocess
from random import randint
import tempfile
from mirakuru import TCPExecutor


class TestGRPCServer:
    def __init__(self, manage_py, params=None, stdout_file: str = None):
        if params is None:
            params = {}
        params.setdefault('--port', 50000 + randint(0, 10000))
        self.port = params.get('--port')
        self.manage_py = manage_py
        stdout = open(stdout_file, "wb") if stdout_file is not None else subprocess.DEVNULL
        self.process = TCPExecutor(
            ['python', self.manage_py, 'grpcserver'] + list(self.flat_params(params)),
            host='localhost', port=self.port,
            stdout=stdout,
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

    def _clear_process(self) -> None:
        if self.process:
            self.process.__exit__(None, None, None)

        self._endtime = None
