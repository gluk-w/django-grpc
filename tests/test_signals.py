import pytest
from grpc import RpcError

from tests.helpers import call_hello_method


def test_signals_sent(mocker, local_grpc_server):
    grpc_request_started_signal = mocker.patch("django_grpc.signals.grpc_request_started.send")
    grpc_request_finished_signal = mocker.patch("django_grpc.signals.grpc_request_finished.send")

    call_hello_method(local_grpc_server, "MyName")

    assert grpc_request_started_signal.call_count == 1
    assert grpc_request_started_signal.call_args[1]['request'].name == 'MyName'
    assert grpc_request_finished_signal.call_count == 1
    assert grpc_request_finished_signal.call_args[1]['request'].name == 'MyName'


def test_exception_signal_sent(mocker, local_grpc_server):
    grpc_request_started_signal = mocker.patch("django_grpc.signals.grpc_request_started.send")
    grpc_request_finished_signal = mocker.patch("django_grpc.signals.grpc_request_finished.send")
    grpc_got_request_exception_signal = mocker.patch("django_grpc.signals.grpc_got_request_exception.send")

    with pytest.raises(RpcError):
        call_hello_method(local_grpc_server, "ValueError")

    assert grpc_request_started_signal.call_count == 1
    assert grpc_request_finished_signal.call_count == 0
    assert grpc_got_request_exception_signal.call_count == 1
