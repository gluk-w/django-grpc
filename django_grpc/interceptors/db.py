import grpc
from django.db import close_old_connections, reset_queries


class DatabaseConnectionInterceptor(grpc.ServerInterceptor):
    """
    gRPC server need to do some cleanup on each RPC just like Django does that for HTTP requests
    """
    def intercept_service(self, continuation, handler_call_details):
        reset_queries()
        close_old_connections()
        return continuation(handler_call_details)
