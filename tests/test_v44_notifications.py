import ast, asyncio, os, subprocess, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
R=Path(__file__).resolve().parents[1]
src=(R/'show_news.py').read_text(encoding='utf8')
module=ast.parse(src)

def load(*names):
    selected=[node for node in module.body if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name in names]
    ns={'ENABLE_TELEGRAM':False,'ENABLE_TERMUX':False,'subprocess':subprocess,'append_log_run':lambda _:None}
    exec(compile(ast.Module(body=selected,type_ignores=[]),'<test>','exec'),ns)
    return ns

class NotificationsAndWorkflow(unittest.TestCase):
    def test_default_shell_both_off(self):
        sh=(R/'scripts/run_show_news.sh').read_text()
        self.assertIn('export EVENT_RADAR_TELEGRAM=0',sh)
        self.assertIn('export EVENT_RADAR_TERMUX=0',sh)
    def test_false_termux_never_launches(self):
        fn=load('send_termux_notification')['send_termux_notification']
        with patch('subprocess.run',side_effect=AssertionError('should not call subprocess')):
            self.assertFalse(fn('a','b'))
    def test_false_telegram_never_uses_bot(self):
        fn=load('send_telegram_message_with_retry')['send_telegram_message_with_retry']
        self.assertEqual(asyncio.run(fn({'title':'test'})),(False,'TELEGRAM_DISABLED'))
    def test_cloud_requires_opt_in_config(self):
        yml=(R/'.github/workflows/event_radar.yml').read_text()
        self.assertIn("EVENT_RADAR_TELEGRAM: '0'",yml)
        self.assertIn("EVENT_RADAR_TERMUX: '0'",yml)
        self.assertIn("timezone: 'Asia/Taipei'",yml)
    def test_ci_no_force_push(self):
        sh=(R/'scripts/commit_data.sh').read_text()
        self.assertNotIn(' --force',sh)
        self.assertNotIn('pull --no-rebase',sh)
        self.assertIn('REMOTE_MAIN_DRIFT',sh)
    def test_termux_only_path(self):
        self.assertIn('ENABLE_TERMUX and not ENABLE_TELEGRAM',src)
        self.assertIn("send_termux_notification('🔥 發現關注活動'",src)
    def test_optional_notifications_need_explicit_flags(self):
        sh=(R/'scripts/run_show_news.sh').read_text()
        self.assertIn('--telegram)',sh)
        self.assertIn('--termux)',sh)
    def test_cloud_owned_push_never_inner_push(self):
        self.assertIn('if PUBLISH_VIA_ACTIONS:',src)
        self.assertIn('PASS ACTIONS_WRITER:',src)
    def test_bounded_details(self):
        self.assertIn("DETAIL_NEW_LIMIT', '24'",src)
        self.assertIn("DETAIL_REPAIR_LIMIT', '16'",src)
    def test_launcher_has_no_git_write_actions(self):
        # The cloud checkout has no prepare_pr.sh: verify the actual launched shell.
        script=(R/'scripts/run_show_news.sh').read_text()
        self.assertNotIn('git push ',script)
        self.assertNotIn('git commit ',script)
    def test_once_mode(self):
        self.assertIn("'once': (lambda: check_and_notify",src)
if __name__=='__main__': unittest.main()
