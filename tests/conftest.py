import os
import pytest
from django.core.cache import cache

from django_grpc.utils import create_server
from django_grpc_testtools.executor import TestGRPCServer


@pytest.fixture
def grpc_server():
    """
    gRPC server running as a separate process
    """
    manage_py = os.path.join(os.path.dirname(os.path.abspath(__file__)), "manage.py")
    server = TestGRPCServer(manage_py)
    server.start()
    yield server.addr()
    server.stop()


@pytest.fixture
def local_grpc_server():
    """
    gRPC server running in the same process, so mocks are accessible
    :return:
    """
    server = create_server(1, 50080)
    server.start()

    yield "localhost:50080"

    server.stop(True)


@pytest.fixture(autouse=True)
def clear_cache():
    """Clears django cache before and after test."""
    cache.clear()
    yield
    cache.clear()
