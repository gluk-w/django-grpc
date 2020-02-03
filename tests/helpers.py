import grpc

from tests.sampleapp import helloworld_pb2_grpc, helloworld_pb2


def call_hello_method(addr, name):
    with grpc.insecure_channel(addr) as channel:
        stub = helloworld_pb2_grpc.GreeterStub(channel)
        response, call = stub.SayHello.with_call(helloworld_pb2.HelloRequest(name=name))
        return response.message
