from django.db import reset_queries, close_old_connections
from django.dispatch import Signal


# Triggered before each RPC
grpc_request_started = Signal(providing_args=["request", "context"])

# Triggered after each RPC
grpc_request_finished = Signal(providing_args=["request", "context"])

# Triggered if there was an error during RPC execution
grpc_got_request_exception = Signal(providing_args=["request", "context", "exception"])

# Reset database connections between requests
grpc_request_started.connect(reset_queries)
grpc_request_started.connect(close_old_connections)
grpc_request_finished.connect(close_old_connections)
