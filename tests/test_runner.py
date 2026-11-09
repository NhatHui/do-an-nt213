import subprocess
import unittest
from unittest.mock import patch

import run_experiments as runner


class PreflightTests(unittest.TestCase):
    @patch.object(runner.subprocess, 'run', side_effect=FileNotFoundError)
    def test_missing_docker(self, run):
        self.assertFalse(runner.preflight()[0])

    @patch.object(runner.subprocess, 'run', side_effect=subprocess.TimeoutExpired('docker', 20))
    def test_docker_timeout(self, run):
        self.assertFalse(runner.preflight()[0])

    @patch.object(runner.subprocess, 'run', return_value=subprocess.CompletedProcess([], 1))
    @patch.object(runner, 'get')
    def test_unavailable_engine_does_not_probe_services(self, get, run):
        self.assertFalse(runner.preflight()[0])
        get.assert_not_called()

    @patch.object(runner.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0))
    @patch.object(runner, 'get', side_effect=[(200, ''), (0, 'offline')])
    def test_missing_service(self, get, run):
        ready, message = runner.preflight()
        self.assertFalse(ready)
        self.assertIn('18082', message)

    @patch.object(runner.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0))
    @patch.object(runner, 'get', return_value=(200, ''))
    def test_ready(self, get, run):
        self.assertTrue(runner.preflight()[0])
        self.assertEqual(get.call_count, 2)

    @patch.object(runner, 'preflight', return_value=(False, 'offline'))
    @patch.object(runner.Path, 'write_text')
    @patch.object(runner.subprocess, 'run')
    def test_blocked_run_preserves_reports(self, run, write_text, preflight):
        self.assertEqual(runner.main(), 2)
        write_text.assert_not_called()
        run.assert_not_called()


if __name__ == '__main__':
    unittest.main()