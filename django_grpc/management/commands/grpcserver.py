import datetime
import time
import grpc
import sys

from django.core.management.base import BaseCommand
from concurrent import futures
from django.utils import autoreload
from django.utils.module_loading import import_string


class Command(BaseCommand):
    help = 'Run gRPC server'

    def add_arguments(self, parser):
        parser.add_argument('--max_workers', type=int, help="Number of workers")
        parser.add_argument('--port', type=int, default=50051, help="Port number to listen")
        parser.add_argument('--autoreload', action='store_true', default=False)

    def handle(self, *args, **options):
        if options['autoreload'] is True:
            self.stdout.write("ATTENTION! Autoreload is enabled!")
            autoreload.main(self._serve, None, options)
        else:
            self._serve(**options)

    def _serve(self, max_workers, port, *args, **kwargs):
        autoreload.raise_last_exception()
        self.stdout.write("Starting server at %s" % datetime.datetime.now())
        # create a gRPC server
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=max_workers))

        self._add_servicers(server)
        server.add_insecure_port('[::]:%s' % port)

        server.start()
        self.stdout.write("Server is listening port %s" % port)

        # since server.start() will not block,
        # a sleep-loop is added to keep alive
        try:
            while True:
                time.sleep(86400)
        except KeyboardInterrupt:
            server.stop(0)
            sys.exit(0)

    def _add_servicers(self, server):
        """
        Add servicers to the server
        """
        from django.conf import settings
        for path in settings.GRPC_SERVICERS:
            callback = import_string(path)
            callback(server)

