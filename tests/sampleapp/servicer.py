from tests.sampleapp import helloworld_pb2_grpc, helloworld_pb2


class Greeter(helloworld_pb2_grpc.GreeterServicer):
    def SayHello(self, request, context):
        if request.name == 'ValueError':
            raise ValueError("Emulated error")

        return helloworld_pb2.HelloReply(message='Hello, %s!' % request.name)
