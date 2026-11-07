"""Source-local exact identity and policy checks, no network."""
import unittest
from scripts import p30_ab_opentix_ticc_native_once as gate


class DualOfficialNativeTests(unittest.TestCase):
    def test_exact_urls(self):
        for line in ("A", "B"):
            src = gate.SOURCES[line]
            self.assertEqual(gate.exact_href(line, src["detail"]), src["detail"])
            self.assertIsNone(gate.exact_href(line, "https://evil.test/event/2070446724700692480"))
            self.assertIsNone(gate.exact_href(line, src["detail"] + "#checkout"))
        self.assertIsNone(gate.exact_href("B", gate.SOURCES["B"]["detail"] + "&bId=999"))
        self.assertIsNone(gate.exact_href("A", gate.SOURCES["A"]["detail"] + "?session=1"))

    def test_local_same_id_and_inert_rejection(self):
        for line in ("A", "B"):
            s = gate.SOURCES[line]
            listing = '<main><article><a href="' + s["detail"] + '">' + s["title"] + '</a></article></main>'
            detail = '<main><article><h1>' + s["title"] + '</h1></article></main>'
            yes = gate.inspect_pair(line, listing, detail)
            self.assertEqual(yes["same_id_review"], 1)
            self.assertEqual(yes["role_review"], 1)
            self.assertEqual(gate.inspect_pair(line, listing, '<h1>' + s["title"] + '</h1>')["same_id_review"], 0)
            self.assertEqual(gate.inspect_pair(line, '<script>' + listing + '</script>', detail)["same_id_review"], 0)
            self.assertEqual(gate.inspect_pair(line, listing + listing, detail)["same_id_review"], 0)

    def test_explicit_robots_policy(self):
        for line in ("A", "B"):
            gate.explicit_robots_allow(line, b"User-agent: *\nAllow: /\n")
            with self.assertRaisesRegex(ValueError, "PATH_DENIED"):
                gate.explicit_robots_allow(line, b"User-agent: *\nDisallow: /\n")
            with self.assertRaisesRegex(ValueError, "NO_APPLICABLE_GROUP"):
                gate.explicit_robots_allow(line, b"User-agent: unrelated\nAllow: /\n")

    def test_no_publication_defaults(self):
        self.assertEqual(gate.SOURCES["A"]["source_id"], "05")
        self.assertEqual(gate.SOURCES["B"]["event_id"], "7806")
        self.assertEqual(gate.CAP, 3 * 1024 * 1024)


if __name__ == "__main__":
    unittest.main()
