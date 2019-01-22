from tests.sampleapp import helloworld_pb2_grpc
from tests.sampleapp.servicer import Greeter


def register_servicer(server):
    """ Callback for django_grpc """
    helloworld_pb2_grpc.add_GreeterServicer_to_server(Greeter(), server)

