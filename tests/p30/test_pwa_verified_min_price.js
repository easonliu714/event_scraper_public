"use strict";
// Field-level, source-SHA-anchored price display; never infer from plain text.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const html = fs.readFileSync("docs/index.html","utf8");
const scripts = [...html.matchAll(/<script>([^]*?)<\/script>/g)];
assert.equal(scripts.length,1);
const script=scripts[0][1];
new vm.Script(script,{filename:"docs/index.html"});
const start=script.indexOf("    function formalCardPriceSummary(");
const end=script.indexOf("    function renderList(",start);
assert.ok(start>=0 && end>start, "existing price/helper section missing");
const context={
    URL,
    isCandidateOfficialUrl(value){
        try {
            const u=new URL(value);
            return u.protocol==="https:" && Boolean(u.hostname) && !u.username && !u.password;
        } catch {return false;}
    }
};
vm.createContext(context);
vm.runInContext(script.slice(start,end)+"\nthis.priceSummary=formalCardPriceSummary;",context);
const summary=context.priceSummary;
const rows=JSON.parse(fs.readFileSync("docs/data.json","utf8"));
assert.equal(rows.length,1,"formal source-qualified TPAC record preserved");
const source=rows[0];
assert.equal(source.source_event_id,"2040");
assert.equal(source.price,"","current formal feed is unchanged by UI-only PR");
assert.equal(summary(source),"票價詳官方資訊","old unaccepted price remains unknown");

const verified={...source,
    price:"NT$1,500 起", golden_accepted:false,
    _formal_field_evidence:{...source._formal_field_evidence,price:{
        value:"NT$1,500 起",
        role:"EVENT_GENERAL_ADMISSION_MIN_PRICE",
        price_kind:"GENERAL_NON_DISCOUNTED",
        event_id:"2040", source:source.url, source_url:source.url,
        observed_at:"2026-11-08T13:15:54Z",
        source_body_sha256:source._publication.source_body_sha256.detail,
        min_price_ntd:1500,max_price_ntd:3500,
        decision:"FIELD_ACCEPTED",accepted:true
    }}
};
const positive=summary(verified);
assert.equal(positive,"NT$1,500 起（詳官方）",
    "strictly accepted minimum may display without changing regression Golden");
assert.equal(summary({...verified,_candidate:{decision:"REVIEW"}}),"票價詳官方資訊");
assert.equal(summary({...verified,published:false}),"票價詳官方資訊");
assert.equal(summary({...verified,formal_field_pass:false}),"票價詳官方資訊");

function badReceipt(change){
    return {...verified,_formal_field_evidence:{...verified._formal_field_evidence,
        price:{...verified._formal_field_evidence.price,...change}}};
}
for(const [key,value] of [
    ["accepted",false],["decision","REVIEW"],
    ["role","DISCOUNTED_TICKET_PRICE"],["price_kind","MEMBER_PROMOTION"],
    ["event_id","2041"],["source","https://tpac.org.taipei/program/9999"],
    ["source_url","https://tpac.org.taipei/program/9999"],
    ["value","NT$100 起"],["min_price_ntd",100],
    ["max_price_ntd",900],["source_body_sha256","0".repeat(64)],
    ["observed_at","2026-11-08T13:15:54"]
]) {
    assert.equal(summary(badReceipt({[key]:value})),"票價詳官方資訊",
                 "reject unsupported or conflicting price receipt: "+key);
}
for(const changedPrice of ["NT$0 起","NT$1000000 起",
                           "會員早鳥 NT$1,500 起","NT$1,500–3,500",
                           "NT$1,500 起+手續費","NT$2,000 起"]) {
    assert.equal(summary({...verified,price:changedPrice}),"票價詳官方資訊",
                 "no promo or malformed minimum: "+changedPrice);
}
const spoof={...verified,url:"https://tpac.org.taipei.evil.org/program/2040"};
assert.equal(summary(spoof),"票價詳官方資訊");
assert.equal(summary({...verified,_publication:{...verified._publication,
    source_body_sha256:{...verified._publication.source_body_sha256,detail:"a".repeat(64)}}}),
    "票價詳官方資訊","publisher source SHA must match accepted price receipt");
assert.match(script,/formalCardPriceSummary\(e\)/);
console.log("PASS_TPAC_PRICE_1500_NEW_STRICT_FIELD_RECEIPT_NO_GOLDEN_CHANGE");
console.log("PASS_PRICE_DISCOUNTS_FEES_WRONG_SOURCE_ID_HASH_AND_REVIEW_ALL_HOLD");
