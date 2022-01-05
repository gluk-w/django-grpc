from datetime import datetime

import grpc
import pytest
from freezegun import freeze_time

from django_grpc.helpers import ratelimit
from django_grpc_testtools.context import FakeServicerContext
from tests.sampleapp import helloworld_pb2


class FakeGRPCServer:
    @ratelimit(max_calls=3, time_period=10)
    def Foo(self, request, context):
        return True

    @ratelimit(max_calls=2, time_period=5)
    def Bar(self, request, context):
        return True

    @ratelimit(max_calls=3, time_period=10, group="FakeGRPCServer.Foo")
    @ratelimit(max_calls=2, time_period=10, keys=["metadata:user-agent"])
    def Baz(self, request, context):
        return True


def test_call_method_under_limit(clear_cache):
    request = helloworld_pb2.HelloRequest()
    context = FakeServicerContext()
    server = FakeGRPCServer()
    with freeze_time(datetime.utcfromtimestamp(14)):
        assert server.Foo(request, context)
        assert server.Foo(request, context)
        assert server.Foo(request, context)


def test_ratelimit_reached(clear_cache):
    request = helloworld_pb2.HelloRequest()
    context = FakeServicerContext()
    server = FakeGRPCServer()
    with freeze_time(datetime.utcfromtimestamp(14)):
        assert server.Foo(request, context)
        assert server.Foo(request, context)
        assert server.Foo(request, context)

        with pytest.raises(Exception):
            server.Foo(request, context)

        assert context.abort_status == grpc.StatusCode.RESOURCE_EXHAUSTED
        assert context.abort_message == ("Reached limit of 3 calls per 10 seconds. "
                                         "Resource will be available in 6 seconds.")


def test_ratelimit_reached_for_different_groups(clear_cache):
    request = helloworld_pb2.HelloRequest()
    context = FakeServicerContext()
    server = FakeGRPCServer()
    with freeze_time(datetime.utcfromtimestamp(14)):
        assert server.Foo(request, context)
        assert server.Foo(request, context)
        assert server.Foo(request, context)

        with pytest.raises(Exception):
            server.Foo(request, context)

        assert context.abort_status == grpc.StatusCode.RESOURCE_EXHAUSTED
        assert context.abort_message == ("Reached limit of 3 calls per 10 seconds. "
                                         "Resource will be available in 6 seconds.")

    with freeze_time(datetime.utcfromtimestamp(17)):
        assert server.Bar(request, context)
        assert server.Bar(request, context)

        with pytest.raises(Exception):
            server.Bar(request, context)

        assert context.abort_status == grpc.StatusCode.RESOURCE_EXHAUSTED
        assert context.abort_message == ("Reached limit of 2 calls per 5 seconds. "
                                         "Resource will be available in 3 seconds.")

def test_multiple_rpc_with_the_same_group(clear_cache):
    request = helloworld_pb2.HelloRequest()
    context = FakeServicerContext()
    server = FakeGRPCServer()
    with freeze_time(datetime.utcfromtimestamp(14)):
        assert server.Foo(request, context)
        assert server.Foo(request, context)
        assert server.Foo(request, context)

    with freeze_time(datetime.utcfromtimestamp(17)):
        assert server.Bar(request, context)
        assert server.Bar(request, context)

        with pytest.raises(Exception):
            server.Bar(request, context)

        assert context.abort_status == grpc.StatusCode.RESOURCE_EXHAUSTED
        assert context.abort_message == ("Reached limit of 2 calls per 5 seconds. "
                                         "Resource will be available in 3 seconds.")
