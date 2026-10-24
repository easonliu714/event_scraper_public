# -*- coding: utf-8 -*-
"""Read-only version gate and cloud-mode regression tests."""
import ast
import os
import pathlib
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]

class VersionGateTests(unittest.TestCase):
    def test_no_trailing_whitespace_in_python(self):
        lines = (ROOT/'show_news.py').read_text(encoding='utf-8').splitlines()
        self.assertEqual([i for i, line in enumerate(lines, 1) if line.rstrip(' \t') != line], [])

    def test_runtime_constant_exact(self):
        tree = ast.parse((ROOT/'show_news.py').read_text(encoding='utf-8'))
        versions = [ast.literal_eval(node.value) for node in tree.body
                    if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'VERSION'
                        for t in node.targets)]
        self.assertEqual(versions, ['V44.2-CLOUD-GATE3'])

    def test_version_from_launcher_is_readonly(self):
        # No third-party dependencies, logs, network, or notifications are required.
        p = subprocess.run(['bash', 'scripts/run_show_news.sh', '--version'], cwd=ROOT,
                           capture_output=True, text=True, timeout=15, check=True,
                           env={**os.environ, 'EVENT_RADAR_TELEGRAM':'0', 'EVENT_RADAR_TERMUX':'0'})
        self.assertIn('EVENT_RADAR_VERSION=V44.2-CLOUD-GATE3', p.stdout)
        self.assertIn('PASS EVENT_RADAR_VERSION_READONLY', p.stdout)

    def test_actions_calls_version_and_defaults_notifications_off(self):
        wf = (ROOT/'.github/workflows/event_radar.yml').read_text(encoding='utf-8')
        self.assertIn('bash scripts/run_show_news.sh --version', wf)
        self.assertIn("EVENT_RADAR_TELEGRAM: '0'", wf)
        self.assertIn("EVENT_RADAR_TERMUX: '0'", wf)
        self.assertIn("timezone: 'Asia/Taipei'", wf)
        self.assertIn("runs-on: ubuntu-latest", wf)

    def test_launcher_rejects_unknown_mode_and_has_opt_in_only(self):
        p = subprocess.run(['bash','scripts/run_show_news.sh','--invalid'], cwd=ROOT,
                           capture_output=True, text=True, timeout=15, check=False)
        self.assertNotEqual(p.returncode, 0)
        self.assertIn('HOLD INVALID_OPTION', p.stderr)

if __name__ == '__main__':
    unittest.main()
