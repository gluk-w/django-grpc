from functools import wraps
import grpc
from grpc._utilities import RpcMethodHandler

from django_grpc.signals import grpc_request_started, grpc_got_request_exception, grpc_request_finished


class SignalWrapper:
    """
    Wraps all RPC handlers to emit signal before and after each RPC
    """
    # Names of properties that can hold RPC callback
    METHOD_PROPERTIES = ('unary_unary', 'unary_stream', 'stream_unary', 'stream_stream')

    def __init__(self, server: 'grpc.Server'):
        self.server = server

    def add_generic_rpc_handlers(self, generic_rpc_handlers: tuple):
        """
        This method does the magic. It must have same interface as `grpc.Server.add_generic_rpc_handlers`
        """
        generic_rpc_handlers[0]._method_handlers = {
            key: self._replace_method_handler(method_handler)
            for key, method_handler in generic_rpc_handlers[0]._method_handlers.items()
        }
        self.server.add_generic_rpc_handlers(generic_rpc_handlers)

    def _replace_method_handler(self, method_handler: 'RpcMethodHandler') -> 'RpcMethodHandler':
        """
        Creates identical instance of RpcMethodHandler() with wrapped method handler.
        """
        kwargs = {
            prop: getattr(method_handler, prop)
            for prop in method_handler._fields
        }
        kwargs['unary_unary'] = _unary_unary(kwargs['unary_unary'])
        kwargs['unary_stream'] = _unary_stream(kwargs['unary_stream'])
        # @TODO add support for stream-unary and stream-stream methods
        # kwargs['stream_unary'] = _unary_stream(kwargs['stream_unary'])
        # kwargs['stream_stream'] = _unary_stream(kwargs['stream_stream'])

        return RpcMethodHandler(**kwargs)


def _unary_unary(func):
    if func is None:
        return

    @wraps(func)
    def inner(*args, **kwargs):
        grpc_request_started.send(None, request=args[0], context=args[1])
        try:
            response = func(*args, **kwargs)
        except Exception as exc:
            grpc_got_request_exception.send(None, request=args[0], context=args[1], exception=exc)
            raise
        else:
            grpc_request_finished.send(None, request=args[0], context=args[1])
        return response

    return inner


def _unary_stream(func):
    if func is None:
        return

    @wraps(func)
    def inner(*args, **kwargs):
        grpc_request_started.send(None, request=args[0], context=args[1])
        try:
            for it in func(*args, **kwargs):
                yield it
        except Exception as exc:
            grpc_got_request_exception.send(None, request=args[0], context=args[1], exception=exc)
            raise
        else:
            grpc_request_finished.send(None, request=args[0], context=args[1])

    return inner
