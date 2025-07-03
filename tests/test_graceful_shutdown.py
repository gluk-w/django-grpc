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
    """Test class for graceful shutdown functionality"""

    def setUp(self):
        """Test setup"""
        super().setUp()
        self.port = 50052  # Test port

    def test_signal_handler_registration(self):
        """Test that signal handlers are properly registered"""
        from django_grpc.management.commands.grpcserver import Command
        
        command = Command()
        
        # Check state before signal handler setup
        self.assertIsNone(command._original_sigterm_handler)
        
        # Setup signal handlers
        with patch('signal.signal') as mock_signal:
            command._setup_signal_handlers()
            
            # Verify signal.signal was called twice (SIGTERM, SIGINT)
            self.assertEqual(mock_signal.call_count, 2)
            
            # Verify SIGTERM handler was saved
            self.assertIsNotNone(command._original_sigterm_handler)

    def test_sigterm_handler(self):
        """Test that SIGTERM handler works correctly"""
        from django_grpc.management.commands.grpcserver import Command
        
        command = Command()
        
        # Check initial state
        self.assertFalse(command._shutdown_event.is_set())
        
        # Call SIGTERM handler
        command._handle_sigterm(signal.SIGTERM, None)
        
        # Verify shutdown event was set
        self.assertTrue(command._shutdown_event.is_set())

    @patch('django_grpc.management.commands.grpcserver.create_server')
    def test_graceful_shutdown_sync_server(self, mock_create_server):
        """Test graceful shutdown for synchronous server"""
        from django_grpc.management.commands.grpcserver import Command
        
        # Create mock server
        mock_server = MagicMock()
        mock_create_server.return_value = mock_server
        
        command = Command()
        
        # Call graceful shutdown
        command._graceful_shutdown(mock_server)
        
        # Verify server's stop method was called with grace=True
        mock_server.stop.assert_called_once_with(grace=True)

    @patch('django_grpc.management.commands.grpcserver.create_server')
    def test_graceful_shutdown_async_server(self, mock_create_server):
        """Test graceful shutdown for asynchronous server"""
        from django_grpc.management.commands.grpcserver import Command
        
        # Create mock server (without stop method)
        mock_server = MagicMock()
        del mock_server.stop
        mock_create_server.return_value = mock_server
        
        command = Command()
        
        # Call graceful shutdown
        command._graceful_shutdown(mock_server)
        
        # Verify asyncio.create_task was called
        # (Actually difficult to verify through mock, so only check exception handling)

    def test_command_initialization(self):
        """Test that Command initialization is correct"""
        from django_grpc.management.commands.grpcserver import Command
        
        command = Command()
        
        # Check initial state
        self.assertIsNotNone(command._shutdown_event)
        self.assertIsNone(command._server)
        self.assertIsNone(command._original_sigterm_handler)

    @patch('django_grpc.management.commands.grpcserver.create_server')
    @patch('django_grpc.management.commands.grpcserver.signal.signal')
    def test_serve_method_signal_setup(self, mock_signal, mock_create_server):
        """Test that signal handlers are set up in _serve method"""
        from django_grpc.management.commands.grpcserver import Command
        
        # Create mock server
        mock_server = MagicMock()
        mock_create_server.return_value = mock_server
        
        command = Command()
        
        # Call _serve method (actually infinite loop, so test partially)
        with patch.object(command, '_setup_signal_handlers') as mock_setup:
            with patch.object(command, '_graceful_shutdown'):
                # Set shutdown event in advance to exit loop
                command._shutdown_event.set()
                command._serve(max_workers=1, port=self.port)
                
                # Verify signal handler setup was called
                mock_setup.assert_called_once()


class GracefulShutdownIntegrationTestCase(TestCase):
    """Integration test: graceful shutdown test with actual process"""

    def setUp(self):
        """Test setup"""
        super().setUp()
        self.port = 50053  # Integration test port

    @pytest.mark.skipif(
        os.name == 'nt',  # Skip on Windows due to different signal handling
        reason="Skip on Windows due to different signal handling"
    )
    def test_sigterm_integration(self):
        """Test graceful shutdown by sending actual SIGTERM signal"""
        # This test is an integration test that starts an actual process and sends SIGTERM.
        # Should only run in actual environment.
        
        # Django settings for testing
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tests.settings')
        
        # Start process
        process = subprocess.Popen([
            'python', 'manage.py', 'grpcserver',
            '--port', str(self.port),
            '--max_workers', '1'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        try:
            # Wait for server to start
            time.sleep(2)
            
            # Send SIGTERM signal
            process.send_signal(signal.SIGTERM)
            
            # Wait for graceful shutdown
            process.wait(timeout=10)
            
            # Verify process terminated normally
            self.assertEqual(process.returncode, 0)
            
        except subprocess.TimeoutExpired:
            # Force kill process if timeout occurs
            process.kill()
            process.wait()
            self.fail("Graceful shutdown timed out")
        
        finally:
            # Force kill if process is still running
            if process.poll() is None:
                process.kill()
                process.wait() 