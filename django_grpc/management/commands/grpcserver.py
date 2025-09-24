import datetime
import asyncio
import signal
import threading
import time

from django.core.management.base import BaseCommand
from django.utils import autoreload
from django.conf import settings

from django_grpc.signals import grpc_shutdown
from django_grpc.utils import create_server, extract_handlers


class Command(BaseCommand):
    help = "Run gRPC server"
    config = getattr(settings, "GRPCSERVER", dict())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # State management for graceful shutdown
        self._shutdown_event = threading.Event()
        self._server = None
        self._original_sigterm_handler = None

    def add_arguments(self, parser):
        parser.add_argument("--max_workers", type=int, help="Number of workers")
        parser.add_argument("--port", type=int, default=50051, help="Port number to listen")
        parser.add_argument("--autoreload", action="store_true", default=False)
        parser.add_argument(
            "--list-handlers",
            action="store_true",
            default=False,
            help="Print all registered endpoints",
        )

    def handle(self, *args, **options):
        is_async = self.config.get("async", False)
        if is_async is True:
            self._serve_async(**options)
        else:
            if options["autoreload"] is True:
                self.stdout.write("ATTENTION! Autoreload is enabled!")
                if hasattr(autoreload, "run_with_reloader"):
                    # Django 2.2. and above
                    autoreload.run_with_reloader(self._serve, **options)
                else:
                    # Before Django 2.2.
                    autoreload.main(self._serve, None, options)
            else:
                self._serve(**options)

    def _setup_signal_handlers(self):
        """Setup signal handlers (inspired by Gunicorn arbiter.py)"""
        # Store SIGTERM handler
        self._original_sigterm_handler = signal.signal(signal.SIGTERM, self._handle_sigterm)
        
        # Also set SIGINT handler (Ctrl+C)
        signal.signal(signal.SIGINT, self._handle_sigterm)
        
        self.stdout.write("Signal handlers registered for graceful shutdown")

    def _handle_sigterm(self, signum, frame):
        """Handle SIGTERM signal to start graceful shutdown"""
        self.stdout.write(f"Received signal {signum}. Starting graceful shutdown...")
        self._shutdown_event.set()

    def _graceful_shutdown(self, server):
        """Gracefully shutdown the server"""
        try:
            # Stop accepting new connections
            self.stdout.write("Stopping server from accepting new connections...")
            
            # Stop gRPC server (with grace=True to wait for ongoing requests to complete)
            if hasattr(server, 'stop'):
                # For synchronous server
                server.stop(grace=True)
            else:
                # For asynchronous server
                asyncio.create_task(server.stop(grace=True))
            
            # Send Django signal
            grpc_shutdown.send(None)
            
            self.stdout.write("Graceful shutdown completed")
            
        except Exception as e:
            self.stderr.write(f"Error during graceful shutdown: {e}")

    async def _graceful_shutdown_async(self, server):
        """Gracefully shutdown the async server"""
        try:
            # Stop accepting new connections
            self.stdout.write("Stopping async server from accepting new connections...")
            
            # Stop gRPC async server
            await server.stop(grace=True)
            
            # Send Django signal
            grpc_shutdown.send(None)
            
            self.stdout.write("Async graceful shutdown completed")
            
        except Exception as e:
            self.stderr.write(f"Error during async graceful shutdown: {e}")

    def _serve(self, max_workers, port, *args, **kwargs):
        """
        Run gRPC server
        """
        autoreload.raise_last_exception()
        self.stdout.write("gRPC server starting at %s" % datetime.datetime.now())

        # Only setup signal handlers when not in autoreload mode
        # autoreload runs in a separate thread, not the main thread, so signal handlers cannot be registered
        if not kwargs.get("autoreload", False):
            self._setup_signal_handlers()

        server = create_server(max_workers, port)
        self._server = server

        server.start()

        self.stdout.write("gRPC server is listening port %s" % port)

        # Print handler list if list_handlers option is enabled (default: False)
        if kwargs.get("list_handlers", False):
            self.stdout.write("Registered handlers:")
            for handler in extract_handlers(server):
                self.stdout.write("* %s" % handler)

        # Only execute graceful shutdown logic when not in autoreload mode
        if not kwargs.get("autoreload", False):
            # Wait loop for graceful shutdown
            try:
                while not self._shutdown_event.is_set():
                    time.sleep(0.1)
            except KeyboardInterrupt:
                self.stdout.write("Received keyboard interrupt, starting graceful shutdown...")
                self._shutdown_event.set()

            # Perform graceful shutdown
            self._graceful_shutdown(server)
        else:
            # Use original wait_for_termination for autoreload mode
            server.wait_for_termination()
            # Send shutdown signal to all connected receivers
            grpc_shutdown.send(None)

    def _serve_async(self, max_workers, port, *args, **kwargs):
        """
        Run gRPC server in async mode
        """
        self.stdout.write("gRPC async server starting  at %s" % datetime.datetime.now())

        # Only setup signal handlers when not in autoreload mode
        # autoreload runs in a separate thread, not the main thread, so signal handlers cannot be registered
        if not kwargs.get("autoreload", False):
            self._setup_signal_handlers()

        # Coroutines to be invoked when the event loop is shutting down.
        _cleanup_coroutines = []

        server = create_server(max_workers, port)
        self._server = server

        async def _main_routine():
            await server.start()
            self.stdout.write("gRPC async server is listening port %s" % port)

            # Print handler list if list_handlers option is enabled (default: False)
            if kwargs.get("list_handlers", False):
                self.stdout.write("Registered handlers:")
                for handler in extract_handlers(server):
                    self.stdout.write("* %s" % handler)

            # Only execute graceful shutdown logic when not in autoreload mode
            if not kwargs.get("autoreload", False):
                # Wait for graceful shutdown
                while not self._shutdown_event.is_set():
                    await asyncio.sleep(0.1)

                # Perform graceful shutdown
                await self._graceful_shutdown_async(server)
            else:
                # Use original wait_for_termination for autoreload mode
                await server.wait_for_termination()

        async def _graceful_shutdown():
            # Send the signal to all connected receivers on server shutdown.
            # https://github.com/gluk-w/django-grpc/issues/31
            grpc_shutdown.send(None)

        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(_main_routine())
        except KeyboardInterrupt:
            if not kwargs.get("autoreload", False):
                self.stdout.write("Received keyboard interrupt, starting graceful shutdown...")
                self._shutdown_event.set()
                loop.run_until_complete(_main_routine())
            else:
                # Ignore KeyboardInterrupt in autoreload mode and exit normally
                pass
        finally:
            loop.run_until_complete(*_cleanup_coroutines)
            loop.close()
