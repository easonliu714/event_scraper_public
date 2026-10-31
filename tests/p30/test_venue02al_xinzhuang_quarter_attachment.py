"""Offline refusal tests for Xinzhuang quarterly bulletin."""
import importlib.util
import pathlib
import unittest

path = pathlib.Path(__file__).resolve().parents[2] / "scripts/p30_venue02al_xinzhuang_quarter_attachment.py"
spec = importlib.util.spec_from_file_location("quarter", path)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

def fixture():
    listing = {"url": gate.INDEX, "detail_url": gate.DETAIL, "title": gate.TITLE}
    detail = {"url": gate.DETAIL, "sid": gate.SID, "title": gate.TITLE,
              "updated_at": gate.UPDATED, "attachment_label": gate.TITLE,
              "attachment_type": "PDF_LINK_UNPARSED", "event_ids": [],
              "event_dates": [], "ticket_event_ids": []}
    return listing, detail

class Gate(unittest.TestCase):
    def test_source_boundary(self):
        a, b = fixture()
        result = gate.inspect(a, b, "2026-10-31")
        self.assertEqual(result["decision"], "HOLD_PDF_ATTACHMENT_NO_EVENT_LEVEL_IDENTITY")
        self.assertEqual(len(result["candidateProvenance"]), 3)
        self.assertEqual(result["acceptedFields"], 0)
        self.assertFalse(result["published"])

    def test_sid_refusal(self):
        a, b = fixture()
        b["sid"] = "unverified"
        self.assertEqual(gate.inspect(a, b, "2026-10-31")["decision"], "HOLD_QUARTER_SID_TITLE_PARITY")

    def test_date_role_refusal(self):
        a, b = fixture()
        b["event_dates"] = [gate.UPDATED]
        self.assertEqual(gate.inspect(a, b, "2026-10-31")["decision"], "HOLD_UNVERIFIED_EVENT_FIELDS")

    def test_attachment_unparsed(self):
        a, b = fixture()
        b["attachment_type"] = "PARSED"
        self.assertEqual(gate.inspect(a, b, "2026-10-31")["decision"], "HOLD_ATTACHMENT_NOT_INDEPENDENTLY_PARSED")

    def test_title_parity(self):
        a, b = fixture()
        a["title"] = "other"
        self.assertEqual(gate.inspect(a, b, "2026-10-31")["decision"], "HOLD_QUARTER_SID_TITLE_PARITY")

    def test_observation_date(self):
        a, b = fixture()
        self.assertEqual(gate.inspect(a, b, "today")["decision"], "HOLD_OBSERVED_AT")

if __name__ == "__main__":
    unittest.main()
