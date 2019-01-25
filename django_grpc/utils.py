from abc import ABCMeta
import logging
from concurrent import futures

import grpc
from django.utils.module_loading import import_string


logger = logging.getLogger(__name__)


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
        logger.debug("Adding servicers from %s", path)
        callback = import_string(path)
        callback(server)


def extract_handlers(server):
    for it in server._state.generic_handlers[0]._method_handlers.values():
        unary = it.unary_unary
        if unary is None:
            logger.warning("%s is invalid", it)
            continue
            
        code = it.unary_unary.__code__
        abstract = ''
        if isinstance(it.__class__, ABCMeta):
            abstract = 'NOT IMPLEMENTED'
        yield "{name}({params}) {abstract}".format(
            name=code.co_name,
            params=", ".join(code.co_varnames),
            abstract=abstract
        )
