from abc import ABCMeta
import logging
from concurrent import futures

import grpc
from django.utils.module_loading import import_string


logger = logging.getLogger(__name__)


def create_server(max_workers, port, interceptors=None):
    from django.conf import settings
    config = getattr(settings, 'GRPCSERVER', dict())
    servicers_list = config.get('servicers', [])  # callbacks to add servicers to the server
    interceptors = load_interceptors(config.get('interceptors', []))
    maximum_concurrent_rpcs = config.get('maximum_concurrent_rpcs', None)

    # create a gRPC server
    server = grpc.server(
        thread_pool=futures.ThreadPoolExecutor(max_workers=max_workers),
        interceptors=interceptors,
        maximum_concurrent_rpcs=maximum_concurrent_rpcs
    )

    add_servicers(server, servicers_list)
    server.add_insecure_port('[::]:%s' % port)
    return server


def add_servicers(server, servicers_list):
    """
    Add servicers to the server
    """
    for path in servicers_list:
        logger.debug("Adding servicers from %s", path)
        callback = import_string(path)
        callback(server)


def load_interceptors(strings):
    if not strings:
        return None
    result = []
    for path in strings:
        logger.debug("Initializing interceptor from %s", path)
        result.append(import_string(path)())
    return result

def extract_handlers(server):
    for path, it in server._state.generic_handlers[0]._method_handlers.items():
        unary = it.unary_unary
        if unary is None:
            name = "???"
            params = "???"
            abstract = 'DOES NOT EXIST'
        else:
            code = it.unary_unary.__code__
            name = code.co_name
            params = ", ".join(code.co_varnames)
            abstract = ''
            if isinstance(it.__class__, ABCMeta):
                abstract = 'NOT IMPLEMENTED'

        yield "{path}: {name}({params}) {abstract}".format(
            path=path,
            name=name,
            params=params,
            abstract=abstract
        )
