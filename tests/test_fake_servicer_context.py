from importlib.resources import files

from grpc import RpcError, StatusCode, ServicerContext
import pytest

from django_grpc_testtools.context import DEFAULT_TIME_REMAINING, FakeServicerContext


def test_fake_servicer_context():
    context = FakeServicerContext()
    assert isinstance(context, ServicerContext)
    with pytest.raises(RpcError):
        context.abort(StatusCode.UNAVAILABLE, 'test')


def test_abort_records_status_message_and_the_fact_that_it_was_called():
    context = FakeServicerContext()
    assert context.abort_called is False

    with pytest.raises(RpcError):
        context.abort(StatusCode.INVALID_ARGUMENT, 'Cannot say hello to John')

    assert context.abort_called is True
    assert context.abort_status == StatusCode.INVALID_ARGUMENT
    assert context.abort_message == 'Cannot say hello to John'


def test_abort_called_distinguishes_unknown_abort_from_no_abort():
    """`abort_status` defaults to UNKNOWN, so it cannot answer "was abort called?" on its own."""
    context = FakeServicerContext()
    assert context.abort_status == StatusCode.UNKNOWN
    assert context.abort_called is False

    with pytest.raises(RpcError):
        context.abort(StatusCode.UNKNOWN, 'boom')

    assert context.abort_status == StatusCode.UNKNOWN
    assert context.abort_called is True


def test_abort_code_is_a_read_write_alias_of_abort_status():
    context = FakeServicerContext()
    assert context.abort_code == context.abort_status

    context.abort_code = StatusCode.NOT_FOUND
    assert context.abort_status == StatusCode.NOT_FOUND

    context.set_code(StatusCode.PERMISSION_DENIED)
    assert context.abort_code == StatusCode.PERMISSION_DENIED


def test_aborted_is_a_read_write_alias_of_abort_called():
    context = FakeServicerContext()
    assert context.aborted is False

    context.aborted = True
    assert context.abort_called is True

    context.abort_called = False
    assert context.aborted is False


def test_set_code_does_not_mark_the_context_as_aborted():
    context = FakeServicerContext()
    context.set_code(StatusCode.NOT_FOUND)
    assert context.abort_called is False


def test_clear_resets_the_outcome_but_keeps_the_inputs():
    context = FakeServicerContext()
    context.set_invocation_metadata((('key', 'value'),))
    context.set_time_remaining(5.0)
    context.set_trailing_metadata((('Header1', 'set-by-server'),))
    with pytest.raises(RpcError):
        context.abort(StatusCode.NOT_FOUND, 'nope')

    context.clear()

    # Outcome of the call is forgotten...
    assert context.abort_called is False
    assert context.abort_status == StatusCode.UNKNOWN
    assert context.abort_message == ''
    with pytest.raises(KeyError):
        context.get_trailing_metadata('Header1')

    # ...while what describes the call itself survives.
    assert context.invocation_metadata() == (('key', 'value'),)
    assert context.time_remaining() == 5.0


def test_time_remaining_reports_the_simulated_deadline():
    context = FakeServicerContext()
    assert context.time_remaining() == DEFAULT_TIME_REMAINING

    context.set_time_remaining(29.9)
    assert context.time_remaining() == 29.9


def test_invocation_metadata_round_trip():
    context = FakeServicerContext()
    assert context.invocation_metadata() == tuple()

    context.set_invocation_metadata((('idempotency-key', 'abc123'),))
    assert dict(context.invocation_metadata()) == {'idempotency-key': 'abc123'}


def test_trailing_metadata_round_trip():
    context = FakeServicerContext()
    context.set_trailing_metadata((('Header1', 'value1'), ('Header2', 'value2')))

    assert context.get_trailing_metadata('Header1') == 'value1'
    assert context.get_trailing_metadata('Header2') == 'value2'


def test_package_ships_py_typed_marker():
    """Guards the packaging: without this file type checkers fall back to Any."""
    assert files('django_grpc_testtools').joinpath('py.typed').is_file()
