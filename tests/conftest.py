import os
import pytest

from django_grpc_testtools.executor import TestGRPCServer


@pytest.fixture
def grpc_server():
    manage_py = os.path.join(os.path.dirname(os.path.abspath(__file__)), "manage.py")
    server = TestGRPCServer(manage_py)
    server.start()
    yield server.addr()
    server.stop()
