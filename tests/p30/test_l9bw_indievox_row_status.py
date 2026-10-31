"""Offline negative regressions for P30-L9-BW; never fetch ticket inventory."""
import copy
import importlib.util
import pathlib
import unittest

p = pathlib.Path(__file__).resolve().parents[2] / "scripts/p30_l9bw_indievox_row_status.py"
spec = importlib.util.spec_from_file_location("l9bw", p)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def fixture():
    detail = {"url": m.DETAIL, "title": m.TITLE, "sessions": list(m.EXPECTED)}
    rows = [{"session": s, "status": ("NO_TICKETS_AVAILABLE_TEXT"
            if i in (2, 4) else "NO_EXPLICIT_STATUS")} for i, s in enumerate(m.EXPECTED)]
    game = {"url": m.GAME, "title": m.TITLE, "rows": rows,
            "per_session_price": None, "live_inventory_confirmed": False}
    return detail, game

class Gate(unittest.TestCase):
    def check(self, detail=None, game=None):
        a, b = fixture()
        return m.inspect(a if detail is None else detail, b if game is None else game, "2026-10-31")

    def test_source_snapshot_is_not_inventory(self):
        o = self.check()
        self.assertEqual(o["decision"], "HOLD_DYNAMIC_STATUS_AND_PER_SESSION_PRICE_NOT_VERIFIED")
        self.assertEqual(o["statusTextRows"], 2)
        self.assertEqual(len(o["candidateProvenance"]), 8)
        self.assertEqual((o["acceptedFields"], o["goldenAccepted"], o["published"]), (0, 0, False))
        self.assertFalse(o["inventoryVerified"])

    def test_detail_url_mismatch(self):
        a, b = fixture()
        a["url"] += "?other=1"
        self.assertEqual(self.check(detail=a)["decision"], "HOLD_SAME_EVENT_ID_URL")

    def test_game_url_mismatch(self):
        a, b = fixture()
        b["url"] = "https://evil.example/activity/game/" + m.EVENT_ID
        self.assertEqual(self.check(game=b)["decision"], "HOLD_SAME_EVENT_ID_URL")

    def test_title_mismatch(self):
        a, b = fixture()
        b["title"] += " other"
        self.assertEqual(self.check(game=b)["decision"], "HOLD_TITLE_PARITY")

    def test_missing_row(self):
        a, b = fixture()
        b["rows"].pop()
        self.assertEqual(self.check(game=b)["decision"], "HOLD_GAME_ROW_COUNT")

    def test_cross_row_swap(self):
        a, b = fixture()
        b["rows"][0], b["rows"][1] = b["rows"][1], b["rows"][0]
        self.assertEqual(self.check(game=b)["decision"], "HOLD_GAME_ROW_IDENTITY")

    def test_unrecognized_status(self):
        a, b = fixture()
        b["rows"][0]["status"] = "AVAILABLE"
        self.assertEqual(self.check(game=b)["decision"], "HOLD_DYNAMIC_STATUS_UNRECOGNIZED")

    def test_false_inventory_claim(self):
        a, b = fixture()
        b["live_inventory_confirmed"] = True
        self.assertEqual(self.check(game=b)["decision"], "HOLD_PRICE_OR_LIVE_INVENTORY_ASSERTION")

    def test_price_mapping_claim(self):
        a, b = fixture()
        b["per_session_price"] = [1500] * 6
        self.assertEqual(self.check(game=b)["decision"], "HOLD_PRICE_OR_LIVE_INVENTORY_ASSERTION")

    def test_missing_observation_date(self):
        a, b = fixture()
        self.assertEqual(m.inspect(a, b, "today")["decision"], "HOLD_OBSERVATION_DATE")

if __name__ == "__main__":
    unittest.main()
