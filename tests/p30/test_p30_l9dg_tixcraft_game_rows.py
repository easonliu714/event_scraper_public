"""P30-L9-DG exact public game role negatives, no network."""
import importlib.util,pathlib,unittest
p=pathlib.Path(__file__).resolve().parents[2]/"scripts/p30_l9dg_tixcraft_game_rows.py"
s=importlib.util.spec_from_file_location("l9dg",p); m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
NOW="2026-11-02T09:16:00Z"
def sample():
    return {"detail_url":m.DETAIL,"game_url":m.GAME,"detail_title":m.TITLE,"game_title":m.TITLE,
      "rows":[{"show":show,"priority":priority,"venue":"臺北大巨蛋","button":"Find tickets"}
      for show in m.SHOWS for priority in (True,False)]}
class Gate(unittest.TestCase):
    def test_exact_four_row_source_receipts(self):
        x=m.inspect(sample(),NOW)
        self.assertEqual(x["decision"],"REVIEW_GAME_FOUR_ROWS_NO_SESSION_ID_OR_STOCK")
        self.assertEqual(len(x["candidateFields"]),3)
        self.assertEqual({f["source"] for f in x["candidateFields"]},{m.GAME,m.DETAIL})
        self.assertEqual({f["decision"] for f in x["candidateFields"]},{"REVIEW"})
        self.assertEqual((x["acceptedFields"],x["ticketSessionIdsVerified"],x["goldenAccepted"],x["published"]),(0,0,0,False))
    def test_url_title_identity(self):
        for key,value in (("game_url",m.DETAIL),("game_url",m.GAME+"?session=1"),
                          ("game_url",m.GAME+"#checkout"),("game_url","https://tixcraft.com.evil.example/activity/game/26_forever"),
                          ("detail_title","F✦FOREVER"),("game_title","F✦FOREVER")):
            with self.subTest(key=key):
                a=sample();a[key]=value;self.assertEqual(m.inspect(a,NOW)["candidateFields"],[])
    def test_four_distinct_row_roles(self):
        for mutate in ("drop","swap","bool","date","venue","button","extra"):
            a=sample()
            if mutate=="drop":a["rows"].pop()
            if mutate=="swap":a["rows"][0],a["rows"][1]=a["rows"][1],a["rows"][0]
            if mutate=="bool":a["rows"][0]["priority"]=1
            if mutate=="date":a["rows"][0]["show"]="2026-10-04T14:00:00+08:00"
            if mutate=="venue":a["rows"][0]["venue"]="臺北小巨蛋"
            if mutate=="button":a["rows"][0]["button"]="Sold out"
            if mutate=="extra":a["rows"][0]["session_id"]="123"
            with self.subTest(mutate=mutate):self.assertEqual(m.inspect(a,NOW)["candidateFields"],[])
    def test_unverified_checkout_claims(self):
        for key,value in (("ticket_session_id","1"),("session_ids",[]),("checkout_url",m.GAME),
                          ("inventory",0),("sold_out",False),("seat_status","available"),("golden_accepted",False)):
            a=sample();a[key]=value;self.assertEqual(m.inspect(a,NOW)["decision"],"HOLD_UNVERIFIED_GAME_CLAIM")
    def test_timestamp(self):
        for t in ("bad","2026-11-02T17:16:00",None):
            self.assertEqual(m.inspect(sample(),t)["decision"],"HOLD_OBSERVATION")
if __name__=="__main__":unittest.main()
