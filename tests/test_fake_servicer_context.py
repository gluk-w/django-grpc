from grpc import RpcError, StatusCode
import pytest

from django_grpc_testtools.context import FakeServicerContext


def test_fake_servicer_context():
    context = FakeServicerContext()
    with pytest.raises(RpcError):
        context.abort(StatusCode.UNAVAILABLE, 'test')
