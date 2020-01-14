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


## Serializers
There is an easy way to serialize django model to gRPC message using `django_grpc.serializers.serialize_model`.


## Testing
You can call methods of your servicer and decode them using `django_grpc.serializers.deserialize_message` that
will convert gRPC messages to python dictionary
