# django-grpc

[![CircleCI](https://circleci.com/gh/gluk-w/django-grpc.svg?style=svg)](https://circleci.com/gh/gluk-w/django-grpc)


Easy way to launch gRPC server with access to Django ORM and other handy stuff.
gRPC calls are much faster that traditional HTTP requests because communicate over
persistent connection and are compressed. Underlying gRPC library is written in C which
makes it work faster than any RESTful framework where a lot of time is spent on serialization/deserialization.

Note that you need this project only if you want to use Django functionality in gRPC service. 
For pure python implementation [read this](https://grpc.io/docs/quickstart/python.html)

* Supported Python: 3.4+
* Supported Django: 2.X (let me know if you need Django 3 support)

## Installation

```bash
pip install django-grpc
``` 

Update settings.py
```python
INSTALLED_APPS = [
    # ...
    'django_grpc',
]

GRPCSERVER = {
    'servicers': ['dotted.path.to.callback.eg.grpc_hook'],  # see `grpc_hook()` below
    'interceptors': ['dotted.path.to.interceptor_class',],  # optional, interceprots are similar to middleware in Django
    'maximum_concurrent_rpcs': None,
}
```

The callback that initializes "servicer" must look like following:
```python
import my_pb2
import my_pb2_grpc

def grpc_hook(server):
    my_pb2_grpc.add_MYServicer_to_server(MYServicer(), server)

...
class MYServicer(my_pb2_grpc.MYServicer):

    def GetPage(self, request, context):
        response = my_pb2.PageResponse(title="Demo object")
        return response
```

## Usage
```bash
python manage.py grpcserver
```

For developer's convenience add `--autoreload` flag during development.


## Signals
The package uses Django signals to allow decoupled applications get notified when some actions occur:
* `django_grpc.signals.grpc_request_started` - sent before gRPC server begins processing a request
* `django_grpc.signals.grpc_request_finished` - sent when gRPC server finishes delivering response to the client
* `django_grpc.signals.grpc_got_request_exception` - this signal is sent whenever RPC encounters an exception while
processing an incoming request.

Note that signal names are similar to Django's built-in signals, but have "grpc_" prefix.


## Serializers
There is an easy way to serialize django model to gRPC message using `django_grpc.serializers.serialize_model`.


## Testing
Test your RPCs just like regular python methods which return some 
structure or generator. You need to provide them with only 2 parameters:
request (protobuf structure or generator) and context (use `FakeServicerContext` from the example below).

### Fake Context
You can pass instance of `django_grpc_testtools.context.FakeServicerContext` to your gRPC method
to verify how it works with context (aborts, metadata and etc.).
```python
import grpc
from django_grpc_testtools.context import FakeServicerContext
from tests.sampleapp.servicer import Greeter
from tests.sampleapp.helloworld_pb2 import HelloRequest

servicer = Greeter()
context = FakeServicerContext()
request = HelloRequest(name='Tester')

# To check metadata set by RPC 
response = servicer.SayHello(request, context)
assert context.get_trailing_metadata("Header1") == '...'

# To check status code
try:
    servicer.SayHello(request, context) 
except Exception:
    pass

assert context.abort_status == grpc.StatusCode.INVALID_ARGUMENT
assert context.abort_message == 'Cannot say hello to John'
```

In addition to standard gRPC context methods, FakeServicerContext provides:
 * `.set_invocation_metadata()` allows to simulate metadata from client to server.
 * `.get_trailing_metadata()` to get metadata set by your server
 * `.abort_status` and `.abort_message` to check if `.abort()` was called 
