/* EventRadar G5C V1.0.0: evidence-scoped, reversible browser display filter.
   Source data.json is immutable. Source 404 alone does NOT hide records.
   DATE_CONFLICT_KEEP and DATE_MISMATCH_REVIEW are always preserved.
   TITLE_ONLY_EXPIRED_CANDIDATE is review-only, not evidence for removal. */
(function (root) {
  'use strict';
  const datePattern = /(^|[^0-9])(20[0-3][0-9]|1[1-3][0-9])\s*[\/.\-年]\s*(0?[1-9]|1[0-2])\s*[\/.\-月]\s*(0?[1-9]|[12][0-9]|3[01])\s*日?(?=$|[^0-9])/g;
  const unknown = /^(詳內文|詳情|未提供|待確認|null|none)$/i;
  const saleDate = /報名截止|早鳥截止|開賣時間|售票開始|購票截止|截止報名/;
  const exact = Object.freeze({
    'KKTIX': ['建立活動'],
    '台北世貿': ['經濟部商業發展署財團法人中國生產力中心'],
    '華山1914': ['文宣品放置', '團體特約導覽'],
    'StrollTimes': ['台北景點', '臺北景點', '桃園景點', '桃園活動', '台北活動', '臺北市立動物園', '台北景點推薦']
  });
  function taipeiDay(now) {
    const a = now instanceof Date ? now : new Date(now === undefined ? Date.now() : now);
    if (!Number.isFinite(a.getTime())) throw new Error('INVALID_CLOCK');
    const b = new Date(a.getTime() + 8 * 3600 * 1000);
    return `${b.getUTCFullYear()}-${String(b.getUTCMonth()+1).padStart(2,'0')}-${String(b.getUTCDate()).padStart(2,'0')}`;
  }
  function compact(s) {
    return String(s || '').normalize('NFKC').replace(/[\u200b-\u200d\ufeff]/g,'')
      .replace(/\s+/g,' ').trim().toLowerCase().replace(/[\s()（）【】\[\]・·-]/g,'');
  }
  function invalidReason(e) {
    const name=compact(e.title), platform=String(e.platform||'');
    if (!name) return 'non_event';
    if ((exact[platform]||[]).some(x=>name===compact(x))) return 'non_event';
    if (platform==='年代售票' && /測試節目.*(?:無效|請勿訂購)/.test(name)) return 'non_event';
    if (platform==='OPENTIX' && (/國家兩廳院.*紅玉.*雞蛋糕/.test(name)||/主辦節目免費身障票專區/.test(name))) return 'non_event';
    if (platform==='FamiTicket' && /全家帶你遊澎湖.*(?:交通券|住宿券)/.test(name)) return 'non_event';
    return '';
  }
  function parseDates(s) {
    if (typeof s!=='string' || s.length>260) return [];
    const out=[]; datePattern.lastIndex=0; let m;
    while ((m=datePattern.exec(s)) !== null) {
      let y=Number(m[2]); if (y<2000) y+=1911;
      const mo=Number(m[3]),day=Number(m[4]),dt=new Date(Date.UTC(y,mo-1,day));
      if (y<2020||y>2040||dt.getUTCFullYear()!==y||dt.getUTCMonth()!==mo-1||dt.getUTCDate()!==day) continue;
      out.push(`${y}-${String(mo).padStart(2,'0')}-${String(day).padStart(2,'0')}`);
      if (out.length>5) return [];
    }
    return out;
  }
  function diagnostic(e,day) {
    const title=String(e.title||''),raw=String(e.date||'');
    const tdArr=parseDates(title), ddArr=(raw.trim()&&!unknown.test(raw.trim()))?parseDates(raw):[];
    const td=tdArr.length?[...tdArr].sort().at(-1):null;
    const dd=ddArr.length?[...ddArr].sort().at(-1):null;
    if (dd&&td&&dd<day&&day<=td) return {code:'DATE_CONFLICT_KEEP',dd,td};
    if (dd&&td&&dd!==td) return {code:'DATE_MISMATCH_REVIEW',dd,td};
    if (dd) return {code:dd<day?'EXPIRED_CANDIDATE':'DATED_KEEP',dd,td};
    if (td) {
      if (tdArr.length===1&&saleDate.test(title)) return {code:'DATE_UNKNOWN_KEEP',dd:null,td};
      return {code:td<day?'TITLE_ONLY_EXPIRED_CANDIDATE':'TITLE_DATED_KEEP',dd:null,td};
    }
    return {code:'DATE_UNKNOWN_KEEP',dd:null,td:null};
  }
  const reasons=['non_event','expired_strict','date_conflict_keep','date_mismatch_review','title_expiry_review_keep','date_unknown_keep','dated_keep','title_dated_keep'];
  function filter(records,now) {
    if(!Array.isArray(records))throw new TypeError('INVALID_DATA_JSON');
    const day=taipeiDay(now),visible=[],counts=Object.fromEntries(reasons.map(x=>[x,0])),by_platform={};
    const hidden=[];
    for (const r of records) {
      if (!r || typeof r!=='object'||Array.isArray(r))throw new TypeError('INVALID_RECORD');
      const p=String(r.platform||'UNKNOWN');
      if (!Object.prototype.hasOwnProperty.call(by_platform,p))by_platform[p]={input:0,visible:0,expired_strict:0,non_event:0,date_conflict_keep:0,date_mismatch_review:0,title_expiry_review_keep:0,date_unknown_keep:0};
      const st=by_platform[p];st.input++;
      const bad=invalidReason(r),d=diagnostic(r,day);
      let reason;
      if(bad) reason='non_event';
      else reason=({EXPIRED_CANDIDATE:'expired_strict',DATE_CONFLICT_KEEP:'date_conflict_keep',DATE_MISMATCH_REVIEW:'date_mismatch_review',TITLE_ONLY_EXPIRED_CANDIDATE:'title_expiry_review_keep',DATE_UNKNOWN_KEEP:'date_unknown_keep',DATED_KEEP:'dated_keep',TITLE_DATED_KEEP:'title_dated_keep'})[d.code];
      if(!reason)throw new Error('HOLD_UNKNOWN_VALIDITY_STATUS');
      counts[reason]++;
      if(reason==='non_event'||reason==='expired_strict'){
        st[reason]++;
        hidden.push({url:r.url,platform:p,reason,dd:d.dd,td:d.td});
      }else{visible.push(r);st.visible++;
        if(Object.prototype.hasOwnProperty.call(st,reason))st[reason]++;
      }
    }
    const sum=Object.values(counts).reduce((a,b)=>a+b,0);
    if(sum!==records.length||visible.length+hidden.length!==records.length)throw new Error('HOLD_COUNT_CLOSURE');
    return {visible,hidden,report:{day,total:records.length,visible:visible.length,hidden:hidden.length,
      expired_strict:counts.expired_strict,non_event:counts.non_event,
      date_conflict_keep:counts.date_conflict_keep,date_mismatch_review:counts.date_mismatch_review,
      title_expiry_review_keep:counts.title_expiry_review_keep,date_unknown_keep:counts.date_unknown_keep,
      dated_keep:counts.dated_keep,title_dated_keep:counts.title_dated_keep,
      source_gone_auto_hidden:0,by_platform}};
  }
  const api=Object.freeze({taipeiDay,compact,invalidReason,parseDates,diagnostic,filter});
  if(typeof module!=='undefined'&&module.exports)module.exports=api;
  root.EventRadarValidity=api;
})(typeof window!=='undefined'?window:globalThis);
