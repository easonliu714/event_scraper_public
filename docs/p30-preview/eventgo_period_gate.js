/* EventRadar G5D V1.0.0: Preview-only Event Go title PERIOD evidence.
   Do NOT use short dates, plain year, sales windows, or single HTTP failures.
   Runs AFTER G5C; raw data.json remains untouched. */
(function(root){
'use strict';
const sourceOrigin='https://eventgo.bnextmedia.com.tw';
const rangeRE=/(?<!\d)(20\d\d-\d\d-\d\d)\s*[～~〜－–—]\s*(20\d\d-\d\d-\d\d)(?!\d)/g;
const allIso=/20\d\d-\d\d-\d\d/g;
const saleContext=/(報名期間|售票期間|購票期間|預購期間|早鳥期間|報名截止|售票截止|售票開始|開賣時間)\s*[:：]?\s*$/;
function validDate(s) {
  if(typeof s!=='string'||!/^(20\d\d)-(\d\d)-(\d\d)$/.test(s))return false;
  const y=Number(s.slice(0,4)),m=Number(s.slice(5,7)),d=Number(s.slice(8,10));
  if(y<2024||y>2040)return false;
  const q=new Date(Date.UTC(y,m-1,d));
  return q.getUTCFullYear()===y&&q.getUTCMonth()===m-1&&q.getUTCDate()===d;
}
function period(e){
  if(!e||e.platform!=='Event Go'||typeof e.title!=='string')return null;
  if(e.title.length>700)return null;
  if(e.date!=null&&e.date!==''&&e.date!=='詳內文')return null;
  try {
    const u=new URL(String(e.url||''));
    if(u.protocol!=='https:'||u.origin!==sourceOrigin||!/^\/event\/detail\/[A-Za-z0-9]+\/?$/.test(u.pathname)||u.search||u.hash)return null;
  } catch (_) {return null;}
  const ranges=[...e.title.matchAll(rangeRE)],isos=e.title.match(allIso)||[];
  if(ranges.length!==1||isos.length!==2)return null;
  const m=ranges[0],start=m[1],end=m[2];
  if(!validDate(start)||!validDate(end)||start>end)return null;
  // Long campaign/sale ranges are not reliable proof of the event's last session.
  const days=(Date.parse(end+'T00:00:00Z')-Date.parse(start+'T00:00:00Z'))/86400000;
  if(days>400)return null;
  if(saleContext.test(e.title.slice(Math.max(0,m.index-20),m.index)))return null;
  return Object.freeze({start,end,source:'EVENTGO_TITLE_EXACT_PERIOD'});
}
function filter(records, day){
  if(!Array.isArray(records)||!validDate(day))throw new TypeError('HOLD_G5D_BAD_RECORDS_OR_DAY');
  const visible=[],hidden=[],by_platform={};
  for(const r of records){
    if(!r||typeof r!=='object'||Array.isArray(r))throw new TypeError('HOLD_G5D_INVALID_RECORD');
    const p=String(r.platform||'UNKNOWN'),st=by_platform[p]??(by_platform[p]={input:0,visible:0,expired_eventgo_period:0});st.input++;
    const x=period(r);
    if(x&&x.end<day){
      st.expired_eventgo_period++;
      hidden.push({url:r.url,platform:p,reason:'expired_eventgo_title_period',start:x.start,end:x.end});
    } else {visible.push(r);st.visible++;}
  }
  if(visible.length+hidden.length!==records.length)throw new Error('HOLD_G5D_COUNT_CLOSURE');
  return {visible,hidden,report:{day,total:records.length,visible:visible.length,hidden:hidden.length,
    expired_eventgo_period:hidden.length,by_platform}};
}
const api=Object.freeze({validDate,period,filter});
if(typeof module!=='undefined'&&module.exports)module.exports=api;
root.EventRadarTitlePeriodGate=api;
})(typeof window!=='undefined'?window:globalThis);
