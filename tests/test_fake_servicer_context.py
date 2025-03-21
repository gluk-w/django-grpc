from grpc import RpcError, StatusCode, ServicerContext
import pytest

from django_grpc_testtools.context import FakeServicerContext


def test_fake_servicer_context():
    context = FakeServicerContext()
    assert isinstance(context, ServicerContext)
    with pytest.raises(RpcError):
        context.abort(StatusCode.UNAVAILABLE, 'test')
