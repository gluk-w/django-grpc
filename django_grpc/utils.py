from concurrent import futures

import grpc
from django.utils.module_loading import import_string


def create_server(max_workers, port):
    # create a gRPC server
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=max_workers))

    add_servicers(server)
    server.add_insecure_port('[::]:%s' % port)
    return server


def add_servicers(server):
    """
    Add servicers to the server
    """
    from django.conf import settings
    for path in settings.GRPC_SERVICERS:
        callback = import_string(path)
        callback(server)


def extract_handlers(server):
    for it in server._state.generic_handlers[0]._method_handlers.values():
        yield it.unary_unary.__qualname__
