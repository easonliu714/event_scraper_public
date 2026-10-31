"""P30-VENUE-02BA source-local screening collection conflict and admission role."""
import importlib.util
import pathlib
import unittest

p = pathlib.Path(__file__).resolve().parents[2] / "scripts/p30_venue02ba_fuzhong_date_conflict.py"
spec = importlib.util.spec_from_file_location("gate", p)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def fixture():
    return {"list_url": m.LIST, "detail_url": m.DETAIL, "announcement_url": m.ANNOUNCE,
            "list_rows": m.LIST_ROWS, "detail_rows": m.DETAIL_ROWS,
            "announcement_titles": m.ANNOUNCEMENT, "announcement_datetime": m.ANNOUNCEMENT_TIME,
            "list_role": "索_IS_TICKET_REQUEST_NOT_SALE",
            "detail_id_role": "COLLECTION_PAGE_NOT_INDIVIDUAL_FILM_ID",
            "ticket_session_id": None, "verified_ticket_url": None, "canonical_screening_id": None,
            "available_for_purchase": None, "published_event": None}

class Gate(unittest.TestCase):
    def check(self, key=None, value=None):
        x = fixture()
        if key is not None:
            x[key] = value
        return m.inspect(x, "2026-11-01")
    def reject(self, expected, key, value):
        result = self.check(key, value)
        self.assertEqual(result["decision"], expected)
        self.assertEqual(result["acceptedFields"], 0)
        self.assertFalse(result["published"])
    def test_conflict_quarantined(self):
        result = self.check()
        self.assertEqual(result["decision"], "HOLD_NOV29_ANNOUNCEMENT_VS_NOV22_FILM_DETAIL_CONFLICT")
        self.assertEqual(len(result["candidateFields"]), 3)
        self.assertEqual(result["candidateFields"][2]["value"], "2026-11-22T16:00")
        self.assertEqual(result["provenance"][1]["decision"], "HOLD_CONFLICT_WITH_FILM_INTRO_NOV22")
    def test_observed_at(self):
        self.assertEqual(m.inspect(fixture(), "invalid")["decision"], "HOLD_OBSERVATION")
    def test_list_host(self): self.reject("HOLD_FUZHONG_LIST_SOURCE", "list_url", "https://evil.example/xcmovie?xsmsid=0M361641875264878260")
    def test_list_duplicate(self): self.reject("HOLD_FUZHONG_LIST_SOURCE", "list_url", m.LIST + "&xsmsid=0M361641875264878260")
    def test_list_fragment(self): self.reject("HOLD_FUZHONG_LIST_SOURCE", "list_url", m.LIST + "#other")
    def test_detail_host(self): self.reject("HOLD_FUZHONG_COLLECTION_DETAIL", "detail_url", "https://evil.example/xcmovieintro?xsmsid=0Q292499123701779627")
    def test_detail_id(self): self.reject("HOLD_FUZHONG_COLLECTION_DETAIL", "detail_url", m.DETAIL.replace("0Q292499123701779627", "wrong"))
    def test_announcement_id(self): self.reject("HOLD_FUZHONG_ANNOUNCEMENT", "announcement_url", m.ANNOUNCE.replace("0Q292625317919000726", "wrong"))
    def test_announcement_redirect(self): self.reject("HOLD_FUZHONG_ANNOUNCEMENT", "announcement_url", "http:" + m.ANNOUNCE[6:])
    def test_list_rows(self): self.reject("HOLD_LIST_DETAIL_FILM_DATE_PARITY", "list_rows", m.LIST_ROWS[:2])
    def test_list_role_mismatch(self): self.reject("HOLD_LIST_DETAIL_FILM_DATE_PARITY", "list_rows", (("無塵之地", "2026-11-29T16:00", "售"),) + m.LIST_ROWS[1:])
    def test_detail_date(self): self.reject("HOLD_LIST_DETAIL_FILM_DATE_PARITY", "detail_rows", m.DETAIL_ROWS[:2] + (("五花肉", "2026-11-29T16:00"),))
    def test_announcement_titles(self): self.reject("HOLD_ANNOUNCEMENT_CONTENT", "announcement_titles", ("無塵之地", "抓耙仔"))
    def test_announcement_date(self): self.reject("HOLD_ANNOUNCEMENT_CONTENT", "announcement_datetime", "2026-11-22T16:00")
    def test_admission(self): self.reject("HOLD_ADMISSION_OR_COLLECTION_ROLE", "list_role", "售")
    def test_collection(self): self.reject("HOLD_ADMISSION_OR_COLLECTION_ROLE", "detail_id_role", "TICKET_SESSION_ID")
    def test_ticket_id(self): self.reject("HOLD_UNVERIFIED_PROMOTION", "ticket_session_id", "0Q292499123701779627")
    def test_ticket_url(self): self.reject("HOLD_UNVERIFIED_PROMOTION", "verified_ticket_url", "https://example.com")
    def test_screening_id(self): self.reject("HOLD_UNVERIFIED_PROMOTION", "canonical_screening_id", "fake")
    def test_inventory(self): self.reject("HOLD_UNVERIFIED_PROMOTION", "available_for_purchase", True)
    def test_publish(self): self.reject("HOLD_UNVERIFIED_PROMOTION", "published_event", True)

if __name__ == "__main__":
    unittest.main()
