I'll look up the current Openverse and Wikimedia API docs (parameters, headers, rate limits) to ground a bulletproof plan, then present the full plan.

[1 tool called]

- Here’s a bulletproof, ruthless plan to make visuals work reliably with Openverse/Wikimedia and to eliminate blank/flicker output.

### 1) Openverse and Wikimedia: compliant, resilient fetchers
- Query hygiene
  - Build scene queries from key phrases + tags; enforce min length ≥ 3, alnum+space only; dedupe.
  - Cap total queries per video (e.g., 30) and per scene (≤2) to avoid rate limits.
- HTTP etiquette
  - Add a descriptive User-Agent with contact (env `APP_CONTACT_URL`).
  - Add Accept: application/json; for Commons media GETs add Referer: `https://commons.wikimedia.org/`.
- Rate-limit and retry
  - Treat 400/401/403/404 as non-retry; log and skip.
  - For 429, respect Retry-After; else back off 2–4s with jitter, one retry only.
  - Global per-host concurrency cap (e.g., 2) and min-delay (Openverse 600ms, Commons 300ms).
- Data selection
  - Wikimedia: use `thumburl` at `iiurlwidth=1920` for downloads; originals are frequently hotlink-blocked.
  - Openverse: use canonical `url` or `thumbnail` if `url` blocked; keep only licenses in commercial/mod.
- Download strategy
  - Prefer headered direct download; only attempt webhook if it sets a proper UA; fallback from original → thumbnail → generate fallback.
  - Validate downloads (non-zero size, image MIME); compute sha256 for cache.

### 2) Fallbacks that never fail
- Generation
  - Pre-generate N gradient-card fallbacks per video (e.g., 24) into `.cache/fallbacks/` with text overlays from scene key phrases.
- Timeline integration
  - If manifest empty or any scene lacks a valid asset, inject fallbacks immediately (do not wait).
  - Synthesize scenes from paragraphs when no markers; clamp durations; enforce monotonic timing.
- Assembly of stills
  - For images, after scale/pad, apply `fps=...` and `tpad=stop_mode=clone:stop_duration=<scene_len>` so each shot holds its duration.
  - Use only `xfade=fade/dissolve` with correct offsets; avoid incompatible transitions.

### 3) Minimal in-memory assembly if preprocessing fails
- If timeline.json is missing or invalid, construct a minimal timeline spanning narration duration (6–12s per shot) using pre-generated fallbacks, and assemble directly. Avoid path guesswork by using project-relative `.cache/fallbacks/*.png` with the assembler’s robust resolver.

### 4) Script-to-scenes: consistent segmentation
- Use markers if present; otherwise split by paragraphs with WPM estimate; enforce:
  - start_time ≥ previous end; end_time > start_time; durations clamped to 6–25s.
  - Split long sections into 8–15s chunks evenly with text slices.
- Compute Ken Burns parameters from scene duration and configured fps.

### 5) Logging and guardrails
- Add structured logs per scene: chosen asset, resolved path, duration, final labels.
- Record Openverse/Wikimedia responses (counts, time) and reasons for skips (license, 403/404).
- Write a `visuals_report.json` per slug: queries used, asset decisions, fallbacks injected, final timeline summary.

### 6) Tests and probes
- Connectivity tests (mockless) with sanitized queries to both sources; assert non-error behavior even if 0 results.
- Unit tests for scene segmentation monotonicity; for assembler ensure still images generate the correct tpad segment length.
- Golden run smoke test: build a 60–90s synthetic timeline from fallbacks and assemble; assert non-zero MP4, proper duration ±2s.

### 7) Command flow
- Keep `run_full_production_pipeline_v4.py` as-is for idea/script/tts.
- Enhancer auto-runs after audio and before upload:
  - plan assets → fetch (graceful on failures) → generate visual timeline (or minimal fallback) → assemble visual MP4.

### 8) Operational tips
- Set `APP_CONTACT_URL` env for polite UA; configure `N8N_*` webhooks only if they add UA/Referer; otherwise bypass.
- Cache results and thumbnails per slug to reduce external calls across retries.

This plan eliminates blank/flicker by: compliant API usage; strict backoff; thumbnail-first downloads; immediate, robust fallbacks; enforced scene timing; image hold with tpad; and a last-resort in-memory timeline. It adds visibility via logs/reports and guarantees a visual output even under total API failure.