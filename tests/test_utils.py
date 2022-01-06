from django_grpc.utils import create_server, extract_handlers


def test_extract_handlers():
    server = create_server(1, 50080)
    assert list(extract_handlers(server)) == [
        '/helloworld.Greeter/SayHello: inner(args, kwargs, response, exc) NOT IMPLEMENTED',
    ]
