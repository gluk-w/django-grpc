from django_grpc.utils import create_server


def test_reflection(settings):
    settings.GRPCSERVER['reflection'] = True
    server = create_server(1, 50080)
    server.start()

    assert len(server._state.generic_handlers) == 2, "Reflection handler must be appended"
    assert (
        '/grpc.reflection.v1alpha.ServerReflection/ServerReflectionInfo'
        in server._state.generic_handlers[1]._method_handlers
    )

    server.stop(True)
