import test from "node:test";
import assert from "node:assert/strict";
import {allowedHost,canonicalDetail,candidateTitle,KIND} from "../../scripts/p30_l3bb_ibon_browser.mjs";
test("tool identity",()=>assert.match(KIND,/NOT_GOLDEN/));
test("HTTPS only",()=>{
  assert.equal(allowedHost("https://ticket.ibon.com.tw/Index/entertainment"),true);
  for(const s of ["http://ticket.ibon.com.tw/","https://evil.com/","https://ticket.ibon.com.tw.evil.com/","https://ticket.ibon.com.tw:8080/","https://token@ticket.ibon.com.tw/"])assert.equal(allowedHost(s),false,s);
});
test("identical detail id canonical with Web and WebV3",()=>{
  assert.equal(canonicalDetail("/ActivityInfo/Details/40010"),"https://ticket.ibon.com.tw/ActivityInfo/Details/40010");
  assert.equal(canonicalDetail("/Web/ActivityInfo/Details/40010"),"https://ticket.ibon.com.tw/ActivityInfo/Details/40010");
  assert.equal(canonicalDetail("/WebV3/ActivityInfo/Details/40010"),"https://ticket.ibon.com.tw/ActivityInfo/Details/40010");
});
test("deny extra query or fragment",()=>{
  for(const s of ["/ActivityInfo/Details/40010?token=x","/ActivityInfo/Details/40010#item","/ActivityInfo/Details/fake","/Checkout/40010"])
    assert.equal(canonicalDetail(s),null);
});
test("deny arbitrary or foreign hosts",()=>{
  for(const s of ["https://bad.com/ActivityInfo/Details/40010",
    "https://ticket.ibon.com.tw.evil.com/ActivityInfo/Details/40010"])
    assert.equal(canonicalDetail(s),null);
});
test("candidate label is not transaction status",()=>{
  assert.equal(candidateTitle("2026 OPEN! DREAM WORLD 夢想音樂節"),"2026 OPEN! DREAM WORLD 夢想音樂節");
  assert.equal(candidateTitle("  活動 甲       乙  "),"活動 甲 乙");
  for(const s of ["購票","即將開賣","已售完","詳情","登入","http://evil.com",""])assert.equal(candidateTitle(s),null);
});
test("no NaN undefined or empty candidate",()=>{
  for(const s of [null,undefined,{},5,"x"])assert.equal(candidateTitle(s),null);
});
