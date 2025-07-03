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
        # Graceful shutdown을 위한 상태 관리
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
        """시그널 핸들러를 설정합니다 (Gunicorn arbiter.py 참고)"""
        # SIGTERM 핸들러 저장
        self._original_sigterm_handler = signal.signal(signal.SIGTERM, self._handle_sigterm)
        
        # SIGINT 핸들러도 설정 (Ctrl+C)
        signal.signal(signal.SIGINT, self._handle_sigterm)
        
        self.stdout.write("Signal handlers registered for graceful shutdown")

    def _handle_sigterm(self, signum, frame):
        """SIGTERM 시그널을 처리하여 graceful shutdown을 시작합니다"""
        self.stdout.write(f"Received signal {signum}. Starting graceful shutdown...")
        self._shutdown_event.set()

    def _graceful_shutdown(self, server):
        """서버를 gracefully하게 종료합니다"""
        try:
            # 새로운 연결 수락을 중지
            self.stdout.write("Stopping server from accepting new connections...")
            
            # gRPC 서버 종료 (graceful=True로 설정하여 진행 중인 요청 완료 대기)
            if hasattr(server, 'stop'):
                # 동기 서버의 경우
                server.stop(grace=True)
            else:
                # 비동기 서버의 경우
                asyncio.create_task(server.stop(grace=True))
            
            # Django 시그널 전송
            grpc_shutdown.send(None)
            
            self.stdout.write("Graceful shutdown completed")
            
        except Exception as e:
            self.stderr.write(f"Error during graceful shutdown: {e}")

    async def _graceful_shutdown_async(self, server):
        """비동기 서버를 gracefully하게 종료합니다"""
        try:
            # 새로운 연결 수락을 중지
            self.stdout.write("Stopping async server from accepting new connections...")
            
            # gRPC 비동기 서버 종료
            await server.stop(grace=True)
            
            # Django 시그널 전송
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

        # autoreload 모드가 아닐 때만 시그널 핸들러 설정
        # autoreload는 별도 스레드에서 실행되므로 메인 스레드가 아니어서 시그널 핸들러를 등록할 수 없음
        if not kwargs.get("autoreload", False):
            self._setup_signal_handlers()

        server = create_server(max_workers, port)
        self._server = server

        server.start()

        self.stdout.write("gRPC server is listening port %s" % port)

        # list_handlers 옵션이 있으면 핸들러 목록 출력 (기본값 False)
        if kwargs.get("list_handlers", False):
            self.stdout.write("Registered handlers:")
            for handler in extract_handlers(server):
                self.stdout.write("* %s" % handler)

        # autoreload 모드가 아닐 때만 graceful shutdown 로직 실행
        if not kwargs.get("autoreload", False):
            # Graceful shutdown을 위한 대기 루프
            try:
                while not self._shutdown_event.is_set():
                    time.sleep(0.1)
            except KeyboardInterrupt:
                self.stdout.write("Received keyboard interrupt, starting graceful shutdown...")
                self._shutdown_event.set()

            # Graceful shutdown 수행
            self._graceful_shutdown(server)
        else:
            # autoreload 모드에서는 기존 방식대로 wait_for_termination 사용
            server.wait_for_termination()
            # Send shutdown signal to all connected receivers
            grpc_shutdown.send(None)

    def _serve_async(self, max_workers, port, *args, **kwargs):
        """
        Run gRPC server in async mode
        """
        self.stdout.write("gRPC async server starting  at %s" % datetime.datetime.now())

        # autoreload 모드가 아닐 때만 시그널 핸들러 설정
        # autoreload는 별도 스레드에서 실행되므로 메인 스레드가 아니어서 시그널 핸들러를 등록할 수 없음
        if not kwargs.get("autoreload", False):
            self._setup_signal_handlers()

        # Coroutines to be invoked when the event loop is shutting down.
        _cleanup_coroutines = []

        server = create_server(max_workers, port)
        self._server = server

        async def _main_routine():
            await server.start()
            self.stdout.write("gRPC async server is listening port %s" % port)

            # list_handlers 옵션이 있으면 핸들러 목록 출력 (기본값 False)
            if kwargs.get("list_handlers", False):
                self.stdout.write("Registered handlers:")
                for handler in extract_handlers(server):
                    self.stdout.write("* %s" % handler)

            # autoreload 모드가 아닐 때만 graceful shutdown 로직 실행
            if not kwargs.get("autoreload", False):
                # Graceful shutdown을 위한 대기
                while not self._shutdown_event.is_set():
                    await asyncio.sleep(0.1)

                # Graceful shutdown 수행
                await self._graceful_shutdown_async(server)
            else:
                # autoreload 모드에서는 기존 방식대로 wait_for_termination 사용
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
                # autoreload 모드에서는 KeyboardInterrupt를 무시하고 정상 종료
                pass
        finally:
            loop.run_until_complete(*_cleanup_coroutines)
            loop.close()
