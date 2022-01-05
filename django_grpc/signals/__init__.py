from django.db import reset_queries, close_old_connections
from django.dispatch import Signal


# Triggered before each RPC
# Args provided by signal: request, context
grpc_request_started = Signal()

# Triggered after each RPC
# Args provided by signal: request, context
grpc_request_finished = Signal()

# Triggered if there was an error during RPC execution
# Args provided by signal: request, context, exception
grpc_got_request_exception = Signal()

# Reset database connections between requests
grpc_request_started.connect(reset_queries)
grpc_request_started.connect(close_old_connections)
grpc_request_finished.connect(close_old_connections)
