"""P30-L9-DF role and identity regression, no network or publication."""
import importlib.util,pathlib,unittest
p=pathlib.Path(__file__).resolve().parents[2]/"scripts/p30_l9df_tixcraft_forever_shuttle.py"
spec=importlib.util.spec_from_file_location("l9df",p)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
NOW="2026-11-02T08:05:00Z"
def sample():
    return dict(concert_url=m.CONCERT,shuttle_url=m.SHUTTLE,
        concert_title="F✦FOREVER恆星之城 光年赴約・臺北・限定場演唱會",
        shuttle_type="返鄉專車",shuttle_routes=["A","B","K"],
        show_times=list(m.SHOWS),venue="臺北大巨蛋",
        general_prices=list(m.GENERAL),accessible_prices=list(m.ACCESSIBLE),
        general_sale="2026-10-04T14:00:00+08:00",
        ticket_release="2026-10-13T18:00:00+08:00",
        shuttle_sale="2026-10-11T12:00:00+08:00")
class Gate(unittest.TestCase):
    def test_eight_source_bound_review_receipts(self):
        r=m.inspect(sample(),NOW)
        self.assertEqual(r["decision"],"REVIEW_TWO_DISTINCT_ACTIVITY_PATHS_NO_TICKET_SESSION")
        self.assertEqual(len(r["candidateFields"]),8)
        self.assertEqual({x["source"] for x in r["candidateFields"]},{m.CONCERT,m.SHUTTLE})
        self.assertEqual({x["decision"] for x in r["candidateFields"]},{"REVIEW"})
        self.assertEqual((r["acceptedFields"],r["ticketSessionIdsVerified"],r["goldenAccepted"],r["published"]),(0,0,0,False))
        self.assertEqual(r["releaseState"],"HARD_HOLD_NO_PUBLICATION")
    def test_distinct_transport_identity_fail_closed(self):
        for key,val in [("concert_url",m.SHUTTLE),("shuttle_url",m.CONCERT),
                        ("concert_url",m.CONCERT+"#buy"),
                        ("concert_url","https://tixcraft.com.evil.example/activity/detail/26_forever"),
                        ("shuttle_routes",["A","B"]),("shuttle_type","演唱會")]:
            with self.subTest(key=key,val=val):
                x=sample();x[key]=val
                self.assertEqual(m.inspect(x,NOW)["candidateFields"],[])
    def test_price_and_date_role_fail_closed(self):
        for key,val in [("show_times",[m.SHOWS[0]]),("general_prices",[1840]),
                        ("general_prices",[True]+list(m.GENERAL[1:])),
                        ("accessible_prices",[1680,1840]),
                        ("general_sale","2026-11-28T19:00:00+08:00"),
                        ("ticket_release","2026-11-28T19:00:00+08:00"),
                        ("shuttle_sale","2026-10-04T14:00:00+08:00")]:
            with self.subTest(key=key):
                x=sample();x[key]=val
                self.assertEqual(m.inspect(x,NOW)["candidateFields"],[])
    def test_unverified_claims_fail_closed(self):
        for key,val in [("ticket_session_id",0),("checkout_url",m.CONCERT),
                        ("inventory",False),("formal_accepted",False),
                        ("golden_accepted",True),("shuttle_is_concert_admission",False)]:
            x=sample();x[key]=val
            self.assertEqual(m.inspect(x,NOW)["decision"],"HOLD_UNVERIFIED_CLAIM")
    def test_time_fail_closed(self):
        for t in [None,"invalid","2026-11-02T16:05:00"]:
            self.assertEqual(m.inspect(sample(),t)["decision"],"HOLD_OBSERVATION")
if __name__=="__main__":unittest.main()
