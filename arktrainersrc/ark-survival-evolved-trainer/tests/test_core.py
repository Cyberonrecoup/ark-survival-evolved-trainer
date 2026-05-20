"""
Unit tests for the core module of ARK Trainer.
Uses mock processes to verify memory operations.
"""

import unittest
from unittest.mock import patch, MagicMock
from trainer.core import ArkProcess, get_process_id_by_name, modify_stat


class TestGetProcessIdByName(unittest.TestCase):
    """Tests for process ID retrieval."""

    @patch('trainer.core.kernel32')
    def test_found(self, mock_kernel32):
        """Test when process is found."""
        mock_snapshot = MagicMock()
        mock_kernel32.CreateToolhelp32Snapshot.return_value = 12345
        mock_kernel32.Process32First.return_value = True
        mock_kernel32.Process32Next.side_effect = [True, False]

        # Mock process entry
        class MockEntry:
            def __init__(self):
                self.th32ProcessID = 6789
                self.szExeFile = 'ShooterGame.exe'

        mock_kernel32.Process32First = MagicMock(return_value=True)
        mock_kernel32.Process32Next = MagicMock(return_value=True)

        pid = get_process_id_by_name('ShooterGame.exe')
        self.assertIsNotNone(pid)

    @patch('trainer.core.kernel32')
    def test_not_found(self, mock_kernel32):
        """Test when process is not found."""
        mock_kernel32.CreateToolhelp32Snapshot.return_value = 12345
        mock_kernel32.Process32First.return_value = True
        mock_kernel32.Process32Next.return_value = False
        pid = get_process_id_by_name('Nonexistent.exe')
        self.assertIsNone(pid)


class TestArkProcess(unittest.TestCase):
    """Tests for ArkProcess class."""

    @patch('trainer.core.get_process_id_by_name')
    @patch('trainer.core.kernel32.OpenProcess')
    def test_attach_success(self, mock_open, mock_get_pid):
        """Test successful attachment."""
        mock_get_pid.return_value = 1234
        mock_open.return_value = 5678
        proc = ArkProcess()
        result = proc.attach()
        self.assertTrue(result)
        self.assertEqual(proc.pid, 1234)
        self.assertEqual(proc.handle, 5678)

    @patch('trainer.core.get_process_id_by_name')
    def test_attach_failure(self, mock_get_pid):
        """Test attachment failure when process not found."""
        mock_get_pid.return_value = None
        proc = ArkProcess()
        result = proc.attach()
        self.assertFalse(result)
        self.assertIsNone(proc.pid)

    @patch('trainer.core.kernel32')
    def test_read_memory(self, mock_kernel32):
        """Test memory reading."""
        proc = ArkProcess()
        proc.handle = 999
        mock_kernel32.ReadProcessMemory.return_value = True
        mock_kernel32.ReadProcessMemory.side_effect = lambda h, addr, buf, size, br: (
            buf.raw.__setitem__(slice(0, 4), b'\x00\x00\x80\x3f') or True
        )
        data = proc.read_memory(0x1000, 4)
        self.assertIsNotNone(data)

    @patch('trainer.core.kernel32')
    def test_write_memory(self, mock_kernel32):
        """Test memory writing."""
        proc = ArkProcess()
        proc.handle = 999
        mock_kernel32.WriteProcessMemory.return_value = True
        result = proc.write_memory(0x1000, b'\x00\x00\x80\x3f')
        self.assertTrue(result)


class TestModifyStat(unittest.TestCase):
    """Tests for stat modification."""

    @patch('trainer.core.ArkProcess.write_memory')
    def test_modify_float(self, mock_write):
        """Test modifying a float stat."""
        mock_write.return_value = True
        proc = ArkProcess()
        proc.handle = 1
        result = modify_stat(0x1000, 100.0, proc)
        self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()
