

## 2026-11-09 17:24 Asia/Taipei — TPAC-R4 Owner-approved bounded two-catalog source policy (engineering-only)
```text
Owner scoped authority: TPAC official /program + /event → isolated REVIEW/LKG ONLY
  min 6h per host-wide cycle, concurrency=1
  robots.txt <=1, /program LIST <=1, /event LIST <=1, DETAIL combined <=2
  403/429 => STOP immediately, no retries; redirects/bypass forbidden
  Independent cross-host IMMUTABLE Claim + prior timestamp MUST PASS before native GET
  CURRENT: /rulesets=[], branch protection 403 UNVERIFIED, Git tags deletable
           => HOLD_CROSS_HOST_IMMUTABLE_CLAIM_UNVERIFIED_NO_GET
Engineering Draft #243, head 2a7c8402b3e78ff0475853b99f003028dfc34430
  scripts/p30_tpac_r4_source_policy.py (NEW):
    RequestBudget.__post_init__          freeze 1+2+2/6h/concurrency1 bounds
    enforce_elapsed                     >=21600s cross-catalog fence (offline schema only)
    stop_on_response                     403/429 immediate fail-closed
    _verify_robots                       require both catalogs & selected details
    review_two_catalog_plan              2 distinct namespaced IDs, five max URLs, no GET
    assert_no_untrusted_live_authority   always HOLD without trusted WORM provider
  tests/p30/test_p30_tpac_r4_source_policy.py (NEW): 9 positive/negative tests
  .github/workflows/eventradar_tpac_multi_event_refresh.yml: exact-head read-only
    checks + synthetic-only Claim-HOLD manifest; latest HEAD CI UNVERIFIED
  Source Adapter consumes NO new native GET (0/2 independent R4 refresh)
  No formal activity JSON/Golden/platform status/Publisher/Scheduler changes
```
- **Safety boundary:** Owner approved source frequency and request count only, not actual claim-provider credentials or formal publication. GitHub lightweight refs and 30-day artifacts cannot be asserted WORM; no automatic native network authority from any boolean or fixture.
- **NEXT Gate:** real protected append-only CAS Claim proof or external WORM, independent no-delete/no-force-push/readback/race/6h checks, then newly timed legitimate TPAC LIST+DETAIL isolated cycles. Preserve Owner Android region PASS, original 1 published activity and UI-only #245 unmerged.
