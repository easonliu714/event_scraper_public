#!/usr/bin/env python3
"""L9-BE: scope provenance is bounded; zero exact labels is a rotation HOLD."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))
from p30_l9be_tixfun_scope_root import inspect_scopes
class Cases(unittest.TestCase):
    def test_no_heading(self): self.assertEqual(inspect_scopes("<p>演出時間</p>")["decision"],"HOLD_TITLE_HEADING_NOT_UNIQUE")
    def test_duplicate_heading(self): self.assertEqual(inspect_scopes("<h1>灣聲映像館VIII</h1><h2>灣聲映像館VIII</h2>")["decision"],"HOLD_TITLE_HEADING_NOT_UNIQUE")
    def test_exact_local(self):
        x=inspect_scopes("<main><section><h1>灣聲映像館VIII</h1><p>演出時間</p><p>售票時間</p></section></main>")
        self.assertEqual(x["decision"],"REVIEW_EXACT_SCOPE_LABELS_NO_VALUES")
        self.assertEqual(x["acceptedFields"],0)
    def test_only_embedded_hint_hold(self):
        x=inspect_scopes("<main><section><h1>灣聲映像館VIII</h1><p>演出時間請見官方公告</p></section></main>")
        self.assertEqual(x["decision"],"HOLD_NO_EXACT_SCOPE_LABELS_ROTATE_SOURCE")
        self.assertTrue(x["scopes"][0]["nonExactRoleHints"])
    def test_unrelated_outside_scope(self):
        x=inspect_scopes("<main><section><h1>灣聲映像館VIII</h1><p>尚未公告</p></section></main><footer><p>票價</p></footer>")
        self.assertEqual(x["decision"],"HOLD_NO_EXACT_SCOPE_LABELS_ROTATE_SOURCE")
    def test_no_field_values(self):
        x=inspect_scopes("<section><h1>灣聲映像館VIII</h1><p>票價</p><p>1000</p></section>")
        self.assertEqual(x["acceptedFields"],0)
if __name__=="__main__": unittest.main()
