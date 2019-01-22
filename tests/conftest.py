import threading
from time import sleep

import pytest
from django.core.management import call_command



@pytest.fixture
def grpc_server_async():
    srv = threading.Thread(target=call_grpc_server_command, args=[{"max_workers": 3, "port": 50080, "autoreload": False}])
    srv.start()
    sleep(5)

    yield

    srv.join()
