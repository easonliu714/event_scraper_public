"""Offline P0 New Taipei monthly bulletin group and weekday refusal tests."""
import copy
import importlib.util
import pathlib
import unittest

p = pathlib.Path(__file__).resolve().parents[2] / "scripts/p30_venue02ak_ntpc_bulletin_roles.py"
spec = importlib.util.spec_from_file_location("venue02ak", p)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def fixture():
    # Group-level source observations from one official monthly bulletin, not eight event IDs.
    titles = ("秋意濃", "屁屁偵探", "詩劇迴影", "海象莫雷的漂流日誌",
              "阿甯咕的爸鼻不見了", "光仁高中年度音樂會",
              "琉光彩影", "樂舞共鳴")
    shows = (
        [("2026-11-01", "14:30", "日")],
        [("2026-11-07", "14:30", "六"), ("2026-11-08", "10:30", "日"),
         ("2026-11-08", "14:30", "日")],
        [("2026-11-10", "19:30", "日")],  # official says 日, actual 2026-11-10 is Tue
        [("2026-11-14", "15:00", "六"), ("2026-11-14", "19:30", "六"),
         ("2026-11-15", "11:00", "日"), ("2026-11-15", "15:00", "日")],
        [("2026-11-21", "14:30", "六"), ("2026-11-22", "10:30", "日"),
         ("2026-11-22", "14:30", "日")],
        [("2026-11-25", "19:00", "三")],
        [("2026-11-27", "19:30", "五")],
        [("2026-11-29", "14:00", "日")],
    )
    roles = ("ERA_CLAIM", "OPENTIX_CLAIM", "OPENTIX_CLAIM", "OPENTIX_CLAIM",
             "OPENTIX_CLAIM", "NO_TICKET", "SELF_SALE", "OPENTIX_CLAIM")
    index = {"url": m.INDEX, "bulletin_sid": m.SID, "heading": m.HEADING}
    detail = {"url": m.DETAIL, "sid": m.SID, "heading": m.HEADING,
              "performances": [{"title": title, "shows": rows, "ticket_role": role,
                                "ticket_event_id": None, "price": None}
                               for title, rows, role in zip(titles, shows, roles)]}
    return index, detail

class Gate(unittest.TestCase):
    def check(self, index=None, detail=None):
        a, b = fixture()
        return m.inspect(a if index is None else index, b if detail is None else detail, "2026-10-31")

    def test_bulletin_conflict_and_zero_accepted(self):
        o = self.check()
        self.assertEqual(o["decision"], "HOLD_BULLETIN_NOT_EVENT_ID_AND_WEEKDAY_CONFLICT")
        self.assertEqual(o["groupCount"], 8)
        self.assertEqual(len(o["calendarConflicts"]), 1)
        self.assertEqual(o["calendarConflicts"][0]["date"], "2026-11-10")
        self.assertEqual((o["acceptedFields"], o["goldenAccepted"], o["published"]), (0, 0, False))
        self.assertTrue(o["bulletinSidNotEventId"])

    def test_wrong_origin(self):
        a, b = fixture()
        b["url"] = "https://other.example/" + m.SID
        self.assertEqual(self.check(detail=b)["decision"], "HOLD_FIRST_PARTY_BULLETIN_LINK")

    def test_cross_sid(self):
        a, b = fixture()
        b["sid"] = "other"
        self.assertEqual(self.check(detail=b)["decision"], "HOLD_BULLETIN_SID")

    def test_bulletin_title_not_event_title(self):
        a, b = fixture()
        a["heading"] = b["performances"][0]["title"]
        self.assertEqual(self.check(index=a)["decision"], "HOLD_BULLETIN_TITLE_PARITY")

    def test_missing_group(self):
        a, b = fixture()
        b["performances"].pop()
        self.assertEqual(self.check(detail=b)["decision"], "HOLD_BULLETIN_GROUP_COUNT")

    def test_duplicate_group(self):
        a, b = fixture()
        b["performances"][1]["title"] = b["performances"][0]["title"]
        self.assertEqual(self.check(detail=b)["decision"], "HOLD_DUPLICATE_GROUP_TITLE")

    def test_ticket_event_id_is_unverified(self):
        a, b = fixture()
        b["performances"][1]["ticket_event_id"] = "12345"
        self.assertEqual(self.check(detail=b)["decision"], "HOLD_UNVERIFIED_TICKET_ID_OR_PRICE")

    def test_price_not_verified(self):
        a, b = fixture()
        b["performances"][0]["price"] = 1000
        self.assertEqual(self.check(detail=b)["decision"], "HOLD_UNVERIFIED_TICKET_ID_OR_PRICE")

    def test_bad_ticket_role(self):
        a, b = fixture()
        b["performances"][0]["ticket_role"] = "SOLD_OUT"
        self.assertEqual(self.check(detail=b)["decision"], "HOLD_TICKET_ROLE")

    def test_bad_calendar_date(self):
        a, b = fixture()
        b["performances"][0]["shows"] = [("2026-11-31", "14:30", "日")]
        self.assertEqual(self.check(detail=b)["decision"], "HOLD_INVALID_DATE")

    def test_conflict_resolved_still_no_event_id(self):
        a, b = fixture()
        b["performances"][2]["shows"] = [("2026-11-10", "19:30", "二")]
        self.assertEqual(self.check(detail=b)["decision"], "HOLD_BULLETIN_NOT_EVENT_ID_NO_TICKET_PARITY")

if __name__ == "__main__":
    unittest.main()
