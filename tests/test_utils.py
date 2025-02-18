from django_grpc.utils import create_server, extract_handlers


def test_extract_handlers():
    server = create_server(1, 50080)
    handers =  set(extract_handlers(server))
    assert '/helloworld.Greeter/SayHello: inner(args, kwargs, response, exc) NOT IMPLEMENTED' in handers
    assert '/helloworld.Greeter/SayHelloStreamReply: ???(???) DOES NOT EXIST' in handers
    assert '/helloworld.Greeter/SayHelloBidiStream: ???(???) DOES NOT EXIST' in handers
