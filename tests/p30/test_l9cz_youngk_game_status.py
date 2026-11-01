"""Source-backed Young K public game table and status-role negative regressions."""
import importlib.util
import pathlib
import unittest
p=pathlib.Path(__file__).resolve().parents[2]/"scripts/p30_l9cz_youngk_game_status.py"
s=importlib.util.spec_from_file_location("l9cz",p)
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def fixture():
    return {"detail_url":m.DETAIL,"buy_tickets_href":m.GAME,"game_url":m.GAME,
            "detail_title":m.TITLE,"game_title":m.TITLE,"venue":"台北國際會議中心TICC",
            "game_rows":[list(x) for x in m.ROWS],"availability_scope":"PUBLIC_DISPLAY_ONLY",
            "ticket_session_id":None,"inventory_count":None,"checkout_url":None,"published_event":None}
class GameStatusGate(unittest.TestCase):
    def check(self,key=None,value=None):
        row=fixture()
        if key is not None: row[key]=value
        return m.inspect(row,"2026-11-02")
    def test_review_without_stock_claim(self):
        r=self.check()
        self.assertEqual(r["decision"],"REVIEW_GAME_STATUS_HOLD_SESSION_INVENTORY")
        self.assertEqual(len(r["candidateFields"]),3)
        self.assertEqual(r["acceptedFields"],0)
        self.assertFalse(r["inventoryVerified"])
        self.assertEqual(r["ticketSessionIdsVerified"],0)
        self.assertFalse(r["published"])
        self.assertTrue(all(f["decision"]=="REVIEW" and f["source_url"]==m.GAME for f in r["candidateFields"]))
    def test_exact_detail_to_game(self):
        for key,value,decision in [
            ("detail_url",m.GAME,"HOLD_DETAIL_SOURCE"),
            ("buy_tickets_href",m.GAME+"?session=1","HOLD_DETAIL_GAME_EDGE"),
            ("game_url",m.GAME+"#stock","HOLD_DETAIL_GAME_EDGE"),
            ("detail_title","unrelated","HOLD_EVENT_IDENTITY"),
            ("game_title","other","HOLD_EVENT_IDENTITY"),
            ("venue","Zepp New Taipei","HOLD_VENUE")]:
            with self.subTest(key=key): self.assertEqual(self.check(key,value)["decision"],decision)
    def test_promo_not_third_show_and_status_not_inventory(self):
        rows=[list(x) for x in m.ROWS];rows[2][0]="2026-11-30T18:00"
        self.assertEqual(self.check("game_rows",rows)["decision"],"HOLD_GAME_ROW_STATUS")
        rows=[list(x) for x in m.ROWS];rows[0][2]="IN_STOCK"
        self.assertEqual(self.check("game_rows",rows)["decision"],"HOLD_GAME_ROW_STATUS")
        self.assertEqual(self.check("availability_scope","INVENTORY_CONFIRMED")["decision"],"HOLD_DISPLAY_NOT_INVENTORY")
    def test_no_session_stock_checkout_or_publication(self):
        for key,value in [("ticket_session_id","26_youngk"),("inventory_count",2),
                          ("checkout_url",m.GAME),("published_event",True)]:
            with self.subTest(key=key): self.assertEqual(self.check(key,value)["decision"],"HOLD_UNVERIFIED_SESSION_OR_PUBLICATION")
    def test_observation_and_invalid_row(self):
        self.assertEqual(m.inspect(fixture(),"bad")["decision"],"HOLD_OBSERVATION")
        self.assertEqual(m.inspect(None,"2026-11-02")["decision"],"HOLD_DETAIL_SOURCE")
if __name__=="__main__": unittest.main()
