import os
import threading
from random import randint
from time import sleep

import grpc
from django.core.management import call_command

from django_grpc_testtools.executor import TestGRPCServer
from tests.sampleapp import helloworld_pb2_grpc, helloworld_pb2


def start_server(**params):
    """
    Starts gRPC server in a separate thread using "grpcserver" management command with given parameters
    :return: connection string
    """
    def _grpc_server_async(options):

        call_command("grpcserver", **options)

    port = 50000 + randint(0, 10000)
    params["port"] = port
    # Start grpc server
    srv = threading.Thread(
        target=_grpc_server_async, args=[params]
    )
    srv.start()
    sleep(5)
    return "localhost:%s" % port


def call_hello_method(addr, name):
    with grpc.insecure_channel(addr) as channel:
        stub = helloworld_pb2_grpc.GreeterStub(channel)
        response, call = stub.SayHello.with_call(helloworld_pb2.HelloRequest(name=name))
        return response.message


def test_management_command(grpc_server):
    """
    Start gRPC server using management command and make sure it works
    """
    assert call_hello_method(grpc_server, 'Django GRPC') == 'Hello, Django GRPC!'


def test_management_command_with_autoreload():
    manage_py = os.path.join(os.path.dirname(os.path.abspath(__file__)), "manage.py")
    server = TestGRPCServer(manage_py, {'--autoreload': ''})
    server.start()

    assert call_hello_method(server.addr(), 'Autoreload') == 'Hello, Autoreload!'

    server.stop()


