from abc import ABCMeta
import logging
from concurrent import futures

import grpc
from django.core.exceptions import ImproperlyConfigured

from django.utils.module_loading import import_string
from django_grpc.signals.wrapper import SignalWrapper
from django.conf import settings


logger = logging.getLogger(__name__)


def create_server(max_workers, port, interceptors=None):
    config = getattr(settings, 'GRPCSERVER', dict())
    servicers_list = config.get('servicers', [])  # callbacks to add servicers to the server
    interceptors = load_interceptors(config.get('interceptors', []))
    maximum_concurrent_rpcs = config.get('maximum_concurrent_rpcs', None)
    options = config.get('options', [])
    credentials = config.get('credentials', None)
    is_async = config.get('async', False)
    need_reflection = config.get('reflection', False)

    # create a gRPC server
    if is_async is True:
        server = grpc.aio.server(
            interceptors=interceptors,
            maximum_concurrent_rpcs=maximum_concurrent_rpcs,
            options=options
        )
    else:
        server = grpc.server(
            thread_pool=futures.ThreadPoolExecutor(max_workers=max_workers),
            interceptors=interceptors,
            maximum_concurrent_rpcs=maximum_concurrent_rpcs,
            options=options
        )

    add_servicers(server, servicers_list)

    if need_reflection:
        enable_reflection(server)

    if credentials is None:
        server.add_insecure_port('[::]:%s' % port)
    else:
        credential_data = list()
        for credential in credentials:
            # read in key and certificate
            with open(credential.get('private_key'), 'rb') as pp:
                private_key = pp.read()
            with open(credential.get('certificate_chain'), 'rb') as cp:
                certificate_chain = cp.read()

            credential_data.append((private_key, certificate_chain,))

        # create server credentials
        logger.debug("Adding server credentials...")
        server_credentials = grpc.ssl_server_credentials(credential_data)

        # add secure port with credentials
        server.add_secure_port('[::]:%s' % port, server_credentials)

    return server


def add_servicers(server, servicers_list: list[str]):
    """
    Add servicers to the server
    """
    ps = SignalWrapper(server)
    if len(servicers_list) == 0:
        logger.warning("No servicers configured. Did you add GRPSERVER['servicers'] list to settings?")

    for path in servicers_list:
        logger.debug("Adding servicers from %s", path)
        callback = import_string(path)
        callback(ps)


def load_interceptors(strings) -> list:
    # Default interceptors
    result = []
    # User defined interceptors
    for path in strings:
        logger.debug("Initializing interceptor from %s", path)
        result.append(import_string(path)())
    return result


def extract_handlers(server):
    for handler in server._state.generic_handlers:
        for path, it in handler._method_handlers.items():
            unary = it.unary_unary
            if unary is None:
                name = "???"
                params = "???"
                abstract = "DOES NOT EXIST"
            else:
                code = it.unary_unary.__code__
                name = code.co_name
                params = ", ".join(code.co_varnames)
                abstract = ''
                if isinstance(it.__class__, ABCMeta):
                    abstract = "NOT IMPLEMENTED"

            yield "{path}: {name}({params}) {abstract}".format(
                path=path,
                name=name,
                params=params,
                abstract=abstract
            )


def enable_reflection(server):
    """
    Enables gRPC reflection for the server so consumers can discover available services and methods.
    https://grpc.io/docs/guides/reflection/
    """
    try:
        from grpc_reflection.v1alpha import reflection
    except ImportError:
        raise ImproperlyConfigured(
            "Failed to enable gRPC reflection. "
            "Install `grpcio-reflection` package or disable \"reflection\" in settings."
        )

    service_names = [
        handler.service_name()
        for handler in server._state.generic_handlers
    ]

    service_names.append(reflection.SERVICE_NAME)
    reflection.enable_server_reflection(service_names, server)
