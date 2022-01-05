from datetime import datetime

from freezegun import freeze_time

from django_grpc.helpers.ratelimit import record_call
from django_grpc_testtools.context import FakeServicerContext
from tests.sampleapp import helloworld_pb2


class FakeGRPCServer:
    def Foo(self, request, context):
        pass

    def Bar(self, request, context):
        pass


def test_record_new_call(clear_cache):
    request = helloworld_pb2.HelloRequest()
    context = FakeServicerContext()
    with freeze_time(datetime.utcfromtimestamp(14)):
        count, time_left = record_call(FakeGRPCServer.Foo, request, context, time_period=10)

    assert count == 1
    assert time_left == 6


def test_record_two_calls(clear_cache):
    request = helloworld_pb2.HelloRequest()
    context = FakeServicerContext()
    with freeze_time(datetime.utcfromtimestamp(14)):
        count, time_left = record_call(FakeGRPCServer.Foo, request, context, time_period=10)

    assert count == 1
    assert time_left == 6

    with freeze_time(datetime.utcfromtimestamp(15)):
        count1, time_left1 = record_call(FakeGRPCServer.Foo, request, context, time_period=10)

    assert count1 == 2
    assert time_left1 == 5


def test_record_different_groups(clear_cache):
    request = helloworld_pb2.HelloRequest()
    context = FakeServicerContext()
    with freeze_time(datetime.utcfromtimestamp(14)):
        count, time_left = record_call(FakeGRPCServer.Foo, request, context, time_period=10)

    assert count == 1
    assert time_left == 6

    with freeze_time(datetime.utcfromtimestamp(16)):
        count, time_left = record_call(FakeGRPCServer.Bar, request, context, time_period=10)

    assert count == 1
    assert time_left == 4


def test_record_same_group(clear_cache):
    request = helloworld_pb2.HelloRequest()
    context = FakeServicerContext()
    with freeze_time(datetime.utcfromtimestamp(14)):
        count, time_left = record_call(FakeGRPCServer.Foo, request, context, time_period=10)

    assert count == 1
    assert time_left == 6

    with freeze_time(datetime.utcfromtimestamp(16)):
        count, time_left = record_call(
            FakeGRPCServer.Bar,
            request,
            context,
            time_period=10,
            group="FakeGRPCServer.Foo",
        )

    assert count == 2
    assert time_left == 4


def test_record_same_group_but_different_keys(clear_cache):
    request = helloworld_pb2.HelloRequest()
    context = FakeServicerContext()
    with freeze_time(datetime.utcfromtimestamp(14)):
        count, time_left = record_call(FakeGRPCServer.Foo, request, context, time_period=10)

    assert count == 1
    assert time_left == 6

    with freeze_time(datetime.utcfromtimestamp(16)):
        count, time_left = record_call(
            FakeGRPCServer.Bar,
            helloworld_pb2.HelloRequest(name="Aleksandr"),
            context,
            time_period=10,
            group="FakeGRPCServer.Foo",
            keys=["request:name"],
        )

    assert count == 1
    assert time_left == 4
