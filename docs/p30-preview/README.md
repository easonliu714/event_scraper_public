# SRC-P30-G1 candidate: isolated PWA (NOT PUBLISHED)

Original Preview: `easonliu714/eventradar-pwa-preview@03e515d65e827d5ed67fe341d079907a96bf784a`.
Proposed isolated Pages path (only after separately authorized Merge): `/event_scraper_public/p30-preview/`.

- Main Source `docs/index.html`, `docs/data.json`, and `docs/manifest.json` are untouched.
- The original Preview main `index.html` is adapted only to load frozen data as 13 same-origin chunks and to display the P30 candidate warning.
- `data-parts/part_00.txt` … `part_12.txt` are ordered UTF-8 fragments of the **exact** Preview main `data.json` bytes. This transport workaround is required because the connected GitHub create-blob endpoint rejected the 5.16 MB single-file upload.
- The browser reconstructs the original file, verifies byte count and SHA-256 using WebCrypto before parsing and displaying it. If a chunk or verification is invalid, it fails closed.
- CI also checks Git Blob identity of the reassembled original, exact Source main-data identity, 9,850 / 8,436 rows, and 7,914 shared URLs.
- `preview_status.json`, `manifest.json` and the two G5C/G5D JavaScript files are verbatim Git Blob copies.
- Preview historical snapshot is **NOT** Golden. Notification, scraping, scheduler, publishing and writer code are not imported.
- To roll back: leave Draft PR unmerged; if separately merged, revert only the isolated P30 paths. No force push.
- P20 Source PR #2 and Preview PR #1 retain their fixed heads and acceptance evidence. Their unmerged functional changes are not copied here.

**P30-G1 integration is candidate only.** Android UAT requires separately approved Pages publication of this isolated path. `R3C-O3`, `G5J`, `G5K` and main-data publication remain HOLD.
