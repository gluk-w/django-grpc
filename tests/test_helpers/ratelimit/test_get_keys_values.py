from django_grpc.helpers.ratelimit import get_keys_values
from tests.sampleapp import helloworld_pb2

from django_grpc_testtools.context import FakeServicerContext


def test_no_keys():
    request = helloworld_pb2.HelloRequest()
    context = FakeServicerContext()

    values = get_keys_values(request, context, [])

    assert values == []


def test_key_is_function():
    request = helloworld_pb2.HelloRequest(name="Aleksandr")
    context = FakeServicerContext()

    values = get_keys_values(request, context, [lambda request, context: request.name])

    assert values == ["Aleksandr"]


def test_get_request_field():
    request = helloworld_pb2.HelloRequest(name="Aleksandr")
    context = FakeServicerContext()

    values = get_keys_values(request, context, ["request:name"])

    assert values == ["Aleksandr"]


def test_get_metadata_value():
    request = helloworld_pb2.HelloRequest()
    context = FakeServicerContext()
    context.set_invocation_metadata((("user-agent", "Python 3.7 client"),))

    values = get_keys_values(request, context, ["metadata:user-agent"])

    assert values == ["Python 3.7 client"]
