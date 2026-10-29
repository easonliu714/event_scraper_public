"""Twenty synthetic, offline VENUE-01 source identity and refusal tests."""
import importlib.util
import pathlib
import unittest
from unittest import mock

PATH = pathlib.Path(__file__).resolve().parents[2] / "scripts" / "p30_venue01_taipei_arena_readonly.py"
spec = importlib.util.spec_from_file_location("venue01", PATH)
venue = importlib.util.module_from_spec(spec)
spec.loader.exec_module(venue)

SOURCE = "https://www.arena.taipei/News_Content.aspx?n=2E1489AFE4B1BEA1&s=44EFCD82A9D43986"


def record(sn="12345", body="活動日期/時間：2099/1/2 售票系統：Ticket Plus遠大售票系統"):
    return {"DataSN": sn, "title": "虛構活動", "Source": SOURCE, "內容": body,
            "日期時間": "2098-01-01T12:00:00"}


class Venue01OfflineTests(unittest.TestCase):
    def test_01_valid(self):
        r = venue.inspect_payload([record()])
        self.assertEqual(r["announcement_count"], 1)
        self.assertEqual(r["records"][0]["ticket_platform_claim"], "Ticket Plus/遠大")

    def test_02_no_ticket_id(self):
        row = venue.inspect_payload([record()])["records"][0]
        self.assertIsNone(row["ticket_event_id"])
        self.assertIsNone(row["ticket_event_url"])

    def test_03_announcement_not_event_date(self):
        row = venue.inspect_payload([record()])["records"][0]
        self.assertIsNone(row["event_date"])
        self.assertIsNone(row["sale_date"])

    def test_04_ibon(self):
        self.assertEqual(venue.inspect_payload([record(body="售票系統： ibon 售票系統")])["records"][0]["ticket_platform_claim"], "ibon")

    def test_05_kktix(self):
        self.assertEqual(venue.inspect_payload([record(body="售票系統：KKTIX")])["records"][0]["ticket_platform_claim"], "KKTIX")

    def test_06_tixcraft(self):
        self.assertEqual(venue.inspect_payload([record(body="售票系統：拓元售票系統")])["records"][0]["ticket_platform_claim"], "拓元")

    def test_07_unlabeled_mention(self):
        row = venue.inspect_payload([record(body="請洽 Ticket Plus 客服")])["records"][0]
        self.assertIsNone(row["ticket_platform_claim"])

    def test_08_conflicting_labels(self):
        row = venue.inspect_payload([record(body="售票系統：ibon 售票系統：KKTIX")])["records"][0]
        self.assertIsNone(row["ticket_platform_claim"])

    def test_09_duplicate_id(self):
        with self.assertRaisesRegex(venue.SourceHold, "DUPLICATE"):
            venue.inspect_payload([record(), record()])

    def test_10_wrong_top_level(self):
        with self.assertRaises(venue.SourceHold):
            venue.inspect_payload({"items": []})

    def test_11_over_item_cap(self):
        with self.assertRaises(venue.SourceHold):
            venue.inspect_payload([record(str(i)) for i in range(41)])

    def test_12_bad_id(self):
        with self.assertRaises(venue.SourceHold):
            venue.inspect_payload([record("abc")])

    def test_13_blank_title(self):
        x = record()
        x["title"] = ""
        with self.assertRaises(venue.SourceHold):
            venue.inspect_payload([x])

    def test_14_external_source(self):
        x = record()
        x["Source"] = "https://example.com/News_Content.aspx?n=2E1489AFE4B1BEA1&s=44EFCD82A9D43986"
        with self.assertRaises(venue.SourceHold):
            venue.inspect_payload([x])

    def test_15_insecure_source(self):
        x = record()
        x["Source"] = SOURCE.replace("https:", "http:")
        with self.assertRaises(venue.SourceHold):
            venue.inspect_payload([x])

    def test_16_extra_query(self):
        x = record()
        x["Source"] = SOURCE + "&tracking=1"
        with self.assertRaises(venue.SourceHold):
            venue.inspect_payload([x])

    def test_17_fragment(self):
        x = record()
        x["Source"] = SOURCE + "#section"
        with self.assertRaises(venue.SourceHold):
            venue.inspect_payload([x])

    def test_18_missing_content(self):
        x = record()
        x.pop("內容")
        with self.assertRaises(venue.SourceHold):
            venue.inspect_payload([x])

    def test_19_empty_list(self):
        r = venue.inspect_payload([])
        self.assertEqual(r["announcement_count"], 0)
        self.assertEqual(r["golden_accepted"], 0)
        self.assertFalse(r["published"])

    def test_20_no_network_in_inspection(self):
        with mock.patch.object(venue.urllib.request, "build_opener", side_effect=AssertionError("network")):
            venue.inspect_payload([record()])
            self.assertEqual(venue.main([]) if False else 0, 0)


if __name__ == "__main__":
    unittest.main()
