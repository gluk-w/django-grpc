# django-grpc

[![CircleCI](https://circleci.com/gh/gluk-w/django-grpc.svg?style=svg)](https://circleci.com/gh/gluk-w/django-grpc)


Easy way to launch gRPC server with access to Django ORM and other handy stuff.
gRPC calls are much faster that traditional HTTP requests because communicate over
persistent connection and are compressed. Underlying gRPC library is written in C which
makes it work faster than any RESTful framework where a lot of time is spent on serialization/deserialization.

Note that you need this project only if you want to use Django functionality in gRPC service. 
For pure python implementation [read this](https://grpc.io/docs/languages/python/quickstart/)

* Supported Python: 3.4+
* Supported Django: 2.X and 3.X

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
    'options': [("grpc.max_receive_message_length", 1024 * 1024 * 100)],  # optional, list of key-value pairs to configure the channel. The full list of available channel arguments: https://grpc.github.io/grpc/core/group__grpc__arg__keys.html
    'credentials': [{
        'private_key': 'private_key.pem',
        'certificate_chain': 'certificate_chain.pem'
    }],    # required only if SSL/TLS support is required to be enabled
    'async': False  # Default: False, if True then gRPC server will start in ASYNC mode
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

## Helpers

### Ratelimits

You can limit number of requests to your procedures by using decorator `django_grpc.helpers.ratelimit.ratelimit`.

```python
from tests.sampleapp import helloworld_pb2_grpc, helloworld_pb2
from django_grpc.helpers import ratelimit


class Greeter(helloworld_pb2_grpc.GreeterServicer):
    
    @ratelimit(max_calls=10, time_period=60)
    def SayHello(self, request, context):
        return helloworld_pb2.HelloReply(message='Hello, %s!' % request.name)
```
> When limit is reached for given time period decorator will abort with status `grpc.StatusCode.RESOURCE_EXHAUSTED`

As storage for state of calls [Django's cache framework](https://docs.djangoproject.com/en/4.0/topics/cache/#django-s-cache-framework)
is used. By default `"default"` cache system is used but you can specify any other in settings `RATELIMIT_USE_CACHE`

#### Advanced usage

Using groups
```python
@ratelimit(max_calls=10, time_period=60, group="main")
def foo(request, context):
    ...

@ratelimit(max_calls=5, time_period=60, group="main")
def bar(request, context):
    ...
```
`foo` and `bar` will share the same counter because they are in the same group

Using keys
```python
@ratelimit(max_calls=5, time_period=10, keys=["request:dot.path.to.field"])
@ratelimit(max_calls=5, time_period=10, keys=["metadata:user-agent"])
@ratelimit(max_calls=5, time_period=10, keys=[lambda request, context: context.peer()])
```
Right now 3 type of keys are supported with prefixes `"request:"`, `"metadata:"` and as callable.

- `"request:"` allows to extract request's field value by doted path
- `"metadata:"` allows to extract metadata from `context.invocation_metadata()`
- callable function that takes request and context and returns string

> NOTE: if value of key is empty string it still will be considered a valid value
> and can cause sharing of ratelimits between different RPCs in the same group

> TIP: To use the same configuration for different RPCs use dict variable
> ```python
> MAIN_GROUP = {"max_calls": 5, "time_period": 60, "group": "main"}
> 
> @ratelimit(**MAIN_GROUP)
> def foo(request, context):
>    ...
>
> @ratelimit(**MAIN_GROUP)
> def bar(request, context):
>    ...
> ```


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
