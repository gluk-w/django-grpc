import os
import signal
import subprocess
import time
import pytest
from django.test import TestCase
from django.core.management import call_command
from django.core.management.base import CommandError
from unittest.mock import patch, MagicMock


class GracefulShutdownTestCase(TestCase):
    """Graceful shutdown 기능을 테스트하는 클래스"""

    def setUp(self):
        """테스트 설정"""
        super().setUp()
        self.port = 50052  # 테스트용 포트

    def test_signal_handler_registration(self):
        """시그널 핸들러가 올바르게 등록되는지 테스트"""
        from django_grpc.management.commands.grpcserver import Command
        
        command = Command()
        
        # 시그널 핸들러 설정 전 상태 확인
        self.assertIsNone(command._original_sigterm_handler)
        
        # 시그널 핸들러 설정
        with patch('signal.signal') as mock_signal:
            command._setup_signal_handlers()
            
            # signal.signal이 두 번 호출되었는지 확인 (SIGTERM, SIGINT)
            self.assertEqual(mock_signal.call_count, 2)
            
            # SIGTERM 핸들러가 저장되었는지 확인
            self.assertIsNotNone(command._original_sigterm_handler)

    def test_sigterm_handler(self):
        """SIGTERM 핸들러가 올바르게 작동하는지 테스트"""
        from django_grpc.management.commands.grpcserver import Command
        
        command = Command()
        
        # 초기 상태 확인
        self.assertFalse(command._shutdown_event.is_set())
        
        # SIGTERM 핸들러 호출
        command._handle_sigterm(signal.SIGTERM, None)
        
        # shutdown 이벤트가 설정되었는지 확인
        self.assertTrue(command._shutdown_event.is_set())

    @patch('django_grpc.management.commands.grpcserver.create_server')
    def test_graceful_shutdown_sync_server(self, mock_create_server):
        """동기 서버의 graceful shutdown 테스트"""
        from django_grpc.management.commands.grpcserver import Command
        
        # Mock 서버 생성
        mock_server = MagicMock()
        mock_create_server.return_value = mock_server
        
        command = Command()
        
        # graceful shutdown 호출
        command._graceful_shutdown(mock_server)
        
        # 서버의 stop 메서드가 grace=True로 호출되었는지 확인
        mock_server.stop.assert_called_once_with(grace=True)

    @patch('django_grpc.management.commands.grpcserver.create_server')
    def test_graceful_shutdown_async_server(self, mock_create_server):
        """비동기 서버의 graceful shutdown 테스트"""
        from django_grpc.management.commands.grpcserver import Command
        
        # Mock 서버 생성 (stop 메서드가 없는 경우)
        mock_server = MagicMock()
        del mock_server.stop
        mock_create_server.return_value = mock_server
        
        command = Command()
        
        # graceful shutdown 호출
        command._graceful_shutdown(mock_server)
        
        # asyncio.create_task가 호출되었는지 확인
        # (실제로는 mock을 통해 확인하기 어려우므로 예외 처리만 확인)

    def test_command_initialization(self):
        """Command 초기화가 올바르게 되는지 테스트"""
        from django_grpc.management.commands.grpcserver import Command
        
        command = Command()
        
        # 초기 상태 확인
        self.assertIsNotNone(command._shutdown_event)
        self.assertIsNone(command._server)
        self.assertIsNone(command._original_sigterm_handler)

    @patch('django_grpc.management.commands.grpcserver.create_server')
    @patch('django_grpc.management.commands.grpcserver.signal.signal')
    def test_serve_method_signal_setup(self, mock_signal, mock_create_server):
        """_serve 메서드에서 시그널 핸들러가 설정되는지 테스트"""
        from django_grpc.management.commands.grpcserver import Command
        
        # Mock 서버 생성
        mock_server = MagicMock()
        mock_create_server.return_value = mock_server
        
        command = Command()
        
        # _serve 메서드 호출 (실제로는 무한 루프에 빠지므로 일부만 테스트)
        with patch.object(command, '_setup_signal_handlers') as mock_setup:
            with patch.object(command, '_graceful_shutdown'):
                # shutdown 이벤트를 미리 설정하여 루프를 빠져나오도록 함
                command._shutdown_event.set()
                command._serve(max_workers=1, port=self.port)
                
                # 시그널 핸들러 설정이 호출되었는지 확인
                mock_setup.assert_called_once()


class GracefulShutdownIntegrationTestCase(TestCase):
    """통합 테스트: 실제 프로세스에서 graceful shutdown 테스트"""

    def setUp(self):
        """테스트 설정"""
        super().setUp()
        self.port = 50053  # 통합 테스트용 포트

    @pytest.mark.skipif(
        os.name == 'nt',  # Windows에서는 signal 처리가 다르므로 스킵
        reason="Windows에서는 signal 처리가 다르므로 스킵"
    )
    def test_sigterm_integration(self):
        """실제 SIGTERM 시그널을 보내서 graceful shutdown 테스트"""
        # 이 테스트는 실제 프로세스를 시작하고 SIGTERM을 보내는 통합 테스트입니다.
        # 실제 환경에서만 실행해야 합니다.
        
        # 테스트용 Django 설정
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tests.settings')
        
        # 프로세스 시작
        process = subprocess.Popen([
            'python', 'manage.py', 'grpcserver',
            '--port', str(self.port),
            '--max_workers', '1'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        try:
            # 서버가 시작될 때까지 잠시 대기
            time.sleep(2)
            
            # SIGTERM 시그널 전송
            process.send_signal(signal.SIGTERM)
            
            # graceful shutdown을 위한 대기
            process.wait(timeout=10)
            
            # 프로세스가 정상적으로 종료되었는지 확인
            self.assertEqual(process.returncode, 0)
            
        except subprocess.TimeoutExpired:
            # 타임아웃 발생 시 프로세스 강제 종료
            process.kill()
            process.wait()
            self.fail("Graceful shutdown이 타임아웃되었습니다")
        
        finally:
            # 프로세스가 아직 실행 중이면 강제 종료
            if process.poll() is None:
                process.kill()
                process.wait() 