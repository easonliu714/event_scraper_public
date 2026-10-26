"""P30-L7-C: postponed original/tentative/confirmed field role regression tests."""
import importlib.util
import unittest
from pathlib import Path

path = Path(__file__).resolve().parents[2]/"scripts"/"p30_l7c_postpone_roles.py"
spec = importlib.util.spec_from_file_location("l7c", path)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

DETAIL = """<h2>2026台北金融科技展〖展覽延期〗</h2>
<div>展出日期：2026/10/23 ~ 2026/10/24</div>""".encode("utf-8")
ANNOUNCE = """<h1>〖緊急通知〗FinTech Taipei 2026 原訂10/23-24 因應颱風延期</h1>
<p>台北金融科技展將延期辦理，預定延期至12/18-12/19，確切調整時間將於10月底前公告；造成不便。</p>""".encode("utf-8")
META_DETAIL = {"state": "HTTP_OK", "observed_url": m.TWTC_URL, "sha256": "a"*64}
META_NOTICE = {"state": "HTTP_OK", "observed_url": m.ANNOUNCEMENT_URL, "sha256": "b"*64}


def parent():
    items = [{"platform": "中正紀念堂", "id": f"ck{i}", "title": f"來源測試{i}"}
             for i in range(5)]
    for i in range(39):
        postponed = i == 10
        items.append({"id": f"tw{i}", "platform": "台北世貿",
                      "title": "2026台北金融科技展【展覽延期】" if postponed else f"2026年展覽測試{i}",
                      "officialUrl": m.TWTC_URL if postponed else "https://twtc.com.tw/exhibition_more.aspx?id="+str(10000+i)+"&p=home",
                      "rawPeriod": "延期未定" if postponed else "11/06 ~ 11/09",
                      "dateEvidenceStatus": "LIST_DETAIL_PERIOD_CONFLICT" if postponed else "DATE_VERIFIED_BY_OFFICIAL_DETAIL_CANDIDATE",
                      "dateStart": None if postponed else "2026-11-06",
                      "dateEnd": None if postponed else "2026-11-09"})
    return {"kind": m.PARENT_KIND, "count": 44, "items": items,
            "dateVerifiedCount": 38, "dateUnverifiedCount": 1,
            "published": False, "goldenAccepted": False, "autoHidden": 0,
            "sourceRuntime": "DORMANT", "writerExecuted": False,
            "notificationExecuted": False}


class Cases(unittest.TestCase):
    def test_exact_url_scope(self):
        self.assertTrue(m.allowed(m.TWTC_URL))
        self.assertTrue(m.allowed(m.ANNOUNCEMENT_URL))
        for bad in ("http://twtc.com.tw/exhibition_more.aspx?id=28255&p=home",
                    "https://evil.com/exhibition_more.aspx?id=28255",
                    "https://twtc.com.tw/exhibition_more.aspx?id=28256&p=home",
                    "https://www.fintechtaipei.tw/Announcement/18",
                    "https://www.fintechtaipei.tw/Announcement/19?token=xx",
                    "https://twtc.com.tw:444/exhibition_more.aspx?id=28255",
                    "file:///etc/passwd"):
            self.assertFalse(m.allowed(bad))

    def test_original_extraction_not_current(self):
        self.assertEqual(m.parse_original(DETAIL), ("2026-10-23", "2026-10-24"))

    def test_tentative_and_no_confirmation(self):
        self.assertEqual(m.parse_tentative(ANNOUNCE), ("2026-12-18", "2026-12-19"))

    def test_announcement_without_explicit_tentative_rejected(self):
        payload = ANNOUNCE.replace("預定延期至".encode(), "確定改至".encode())
        with self.assertRaisesRegex(ValueError, "TENTATIVE_DATE_NOT_CONFIRMED"):
            m.parse_tentative(payload)

    def test_announcement_without_confirmation_pending_rejected(self):
        payload = ANNOUNCE.replace("確切調整時間將於10月底前公告".encode(), "時間已確認".encode())
        with self.assertRaisesRegex(ValueError, "NOT_EXPLICITLY_TENTATIVE"):
            m.parse_tentative(payload)

    def test_original_missing_postpone_title_rejected(self):
        html = DETAIL.replace("展覽延期".encode(), "展覽如期".encode())
        with self.assertRaisesRegex(ValueError, "TITLE_OR_STATUS"):
            m.parse_original(html)

    def test_parent_frozen_identity_and_no_deployment(self):
        match = m.select_postponed(parent())
        self.assertEqual(match["officialUrl"], m.TWTC_URL)
        self.assertEqual(match["rawPeriod"], "延期未定")

    def test_parent_rejects_tamper_or_wrong_url(self):
        data = parent()
        data["published"] = True
        with self.assertRaisesRegex(ValueError, "PARENT_FLAG"):
            m.select_postponed(data)
        data = parent()
        data["items"][15]["officialUrl"] = "https://evil.com"
        with self.assertRaisesRegex(ValueError, "WRONG_DETAIL_BINDING"):
            m.select_postponed(data)

    def test_overlay_preserves_44_and_old_38(self):
        p = parent()
        original = [x.copy() for x in p["items"]]
        new, evidence = m.build(p, DETAIL, ANNOUNCE, META_DETAIL, META_NOTICE)
        self.assertEqual(len(new["items"]), 44)
        self.assertEqual(new["dateVerifiedCount"], 38)
        self.assertEqual(new["dateUnverifiedCount"], 1)
        self.assertFalse(new["published"])
        self.assertEqual(p["items"], original)
        event = m.select_postponed({**new, "items":[dict(x, dateEvidenceStatus="LIST_DETAIL_PERIOD_CONFLICT") if x["id"]=="tw10" else x for x in new["items"]]})
        self.assertEqual(event["originalDateStart"], "2026-10-23")
        self.assertEqual(event["tentativeDateStart"], "2026-12-18")
        self.assertIsNone(event["confirmedDateStart"])
        self.assertIsNone(event["dateStart"])
        self.assertEqual(evidence["noticeStatus"], "TENTATIVE_DATE_SUBJECT_TO_OFFICIAL_CONFIRMATION")

    def test_http_200_and_exact_source_sha_required(self):
        bad = dict(META_NOTICE, sha256="")
        with self.assertRaisesRegex(ValueError, "LIVE_HTTP_EVIDENCE"):
            m.build(parent(), DETAIL, ANNOUNCE, META_DETAIL, bad)

    def test_date_range_handles_year_boundary(self):
        self.assertEqual(m.date_range(2026, 12, 31, 1, 2), ("2026-12-31", "2027-01-02"))


if __name__ == "__main__":
    unittest.main()
