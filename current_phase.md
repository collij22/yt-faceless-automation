```markdown
<!-- Implementable blueprint for Phases 6–7 aligned to README, reusing n8n + current Python modules, with precise contracts, CLI, tests, and acceptance criteria. -->

### Phase 6 — Upload & Publishing Automation

- **Objectives**
  - Automate upload and scheduling to YouTube via n8n workflows.
  - Ensure reliable, idempotent publishing with strict validation and observability.
  - Produce artifacts for traceability and seamless handoff to Phase 7 analytics.

- **Prerequisites (from Phases 3–5)**
  - `content/{slug}/final.mp4` produced by assembly.
  - `content/{slug}/metadata.json` (title, description, tags, chapters, category, audience flags).
  - Optional: `content/{slug}/thumbnail.jpg|.png`.

- **Environment variables (.env)**
  - `YOUTUBE_UPLOAD_WEBHOOK_URL` (required): n8n webhook for the YouTube upload workflow.
  - `DEFAULT_PRIVACY_STATUS` (optional): one of `public|unlisted|private` (default: `private`).
  - `DEFAULT_PUBLISH_TZ` (optional): IANA tz, e.g., `UTC`.
  - `DEFAULT_CATEGORY_ID` (optional): YouTube category ID (e.g., `27` for Education).
  - `PUBLISH_RETRY_MAX_ATTEMPTS` (default: `3`).
  - `PUBLISH_RETRY_BACKOFF_SEC` (default: `5`).

- **Data contracts**
  - Upload request payload (Python builds; n8n expects this JSON):
    - `video_path: str` (absolute or workspace-relative)
    - `thumbnail_path: Optional[str]`
    - `title: str` (≤ 100 chars; SEO target ≤ 60)
    - `description: str` (≤ 5000 chars; chapters embedded if provided)
    - `tags: List[str]` (combined length ≤ 500 chars)
    - `category_id: Optional[int]`
    - `privacy_status: Literal["public","unlisted","private"]`
    - `publish_at_iso: Optional[str]` (RFC3339; if set + `privacy_status=private|unlisted`, schedule)
    - `made_for_kids: bool`
    - `language: Optional[str]` (e.g., `en`)
    - `chapters: Optional[List[{"start": "00:00", "title": str}]]`
    - `slug: str` (idempotency key + trace)
    - `checksum_sha256: str` (file checksum for idempotency)
  - Upload response payload (from n8n):
    - `execution_id: str`
    - `video_id: str`
    - `status: Literal["uploaded","scheduled"]`
    - `publish_at_iso: Optional[str]`
    - `errors: Optional[List[str]]`

- **n8n workflow contract (workflows/youtube_upload.json)**
  - HTTP In: validate JSON, require `video_path`, `title`, `description`.
  - File handling: read video from path, upload via YouTube node.
  - Metadata: set title, description, tags, category, audience, language.
  - Thumbnail: if present, upload via YouTube node “Upload Thumbnail”.
  - Scheduling: if `publish_at_iso` present, set `status=private` + schedule at `publishAt`.
  - Response: 200 with `video_id`, `execution_id`, and status; 4xx/5xx with error details.
  - Idempotency: optional store by `slug+checksum_sha256`; if duplicate, return prior `video_id`.

- **Python changes**
  - Add types in `src/yt_faceless/core/schemas.py`:
    - `YouTubeUploadPayload` (TypedDict)
    - `YouTubeUploadResponse` (TypedDict)
  - Extend `src/yt_faceless/integrations/n8n_client.py`:
    - `def upload_video(payload: YouTubeUploadPayload) -> YouTubeUploadResponse: ...`
      - Validates, posts JSON to `YOUTUBE_UPLOAD_WEBHOOK_URL`, handles retries/backoff, maps errors.
  - Add orchestrator API in `src/yt_faceless/orchestrator.py`:
    - `def publish(slug: str, override_paths: Optional[dict] = None, schedule_iso: Optional[str] = None, privacy: Optional[str] = None, dry_run: bool = False) -> YouTubeUploadResponse: ...`
      - Loads `metadata.json`, composes payload, computes checksum of `final.mp4`, validates, calls `n8n_client.upload_video`, writes manifest.
  - CLI in `src/yt_faceless/cli.py`:
    - `ytfaceless publish --slug <slug> [--video <path>] [--thumbnail <path>] [--privacy <public|unlisted|private>] [--publish-at <RFC3339>] [--dry-run] [--force]`
      - `--force`: bypass idempotency.
      - Output: human-readable and `--json`.

- **Validation rules (pre-flight, fail-fast)**
  - Paths exist and are readable; video file non-empty; optional thumbnail valid image.
  - Title ≤ 100 chars; description ≤ 5000; `len(",".join(tags)) ≤ 500`.
  - Chapters: first chapter must start at `00:00`, strictly ascending timestamps.
  - `publish_at_iso`: must be future time; if set, privacy may be `private` or `unlisted`.
  - `made_for_kids`: boolean; if true, restrict features per policy (no personalized ads).
  - Sanitize description to avoid leading/trailing whitespace and unsupported characters.

- **Idempotency & artifacts**
  - Compute `checksum_sha256(final.mp4)`.
  - Write `output/{slug}/upload_manifest.json` with:
    - request payload, response payload, timestamps, checksum, env snapshot (privacy, tz).
  - On re-run, if manifest exists with same checksum and no `--force`, exit with success and echo prior `video_id`.

- **Observability**
  - Structured logging (info/debug/warning/error) around validation, request, response, retries.
  - Mask secrets in logs; include `execution_id` and `video_id` when available.

- **Testing plan (pytest)**
  - Unit: payload validation (parametrized), checksum computation, description builder (chapters), idempotency flow.
  - Unit: `n8n_client.upload_video` with HTTP mocked responses (200, 4xx, 5xx, timeouts, retries).
  - CLI: argument parsing, `--json` output shape, dry-run behavior.
  - Edge: overlong title/tags; missing video; past schedule time; duplicate upload.

- **Acceptance criteria (DoD)**
  - `ytfaceless publish` uploads or schedules video end-to-end via n8n.
  - Strict validation with actionable errors; no secrets in logs.
  - Manifest written; re-run with same checksum is idempotent.
  - Unit tests pass locally; documentation added to README Quickstart/CLI.

- **Conventional commits (suggested)**
  - `feat(cli): add publish command for YouTube uploads via n8n`
  - `feat(orchestrator): implement publish flow with idempotency and manifest`
  - `feat(integrations): add n8n upload_video client with retries`
  - `feat(schemas): add YouTube upload payload/response types`
  - `test(publish): add unit tests for validation and retries`
  - `docs(readme): document Phase 6 usage and env vars`


### Phase 7 — Optimization & Analytics Loop

- **Objectives**
  - Pull YouTube Analytics via n8n, produce actionable reports, and maintain an experiment pipeline (A/B titles/thumbnails/descriptions/chapters).
  - Establish weekly iteration cycles with measurable KPIs (CTR, AVD, APV, retention).

- **Environment variables (.env)**
  - `YOUTUBE_ANALYTICS_WEBHOOK_URL` (required): n8n webhook to fetch analytics.
  - `REPORTS_DIR` (default: `reports`).
  - `ANALYTICS_LOOKBACK_DAYS` (default: `28`).
  - `OPTIMIZER_BASELINES_JSON` (optional path): overrides KPI thresholds.

- **Data contracts**
  - Analytics request:
    - `video_id: str`
    - `lookback_days: int`
    - `granularity: Literal["daily","hourly","lifetime"]` (default `daily`)
  - Analytics response:
    - `video_id: str`
    - `time_window: {"start_iso": str, "end_iso": str}`
    - `kpis: { "impressions": int, "views": int, "ctr": float, "avg_view_duration_sec": float, "avg_percentage_viewed": float, "watch_time_hours": float }`
    - `retention_curve: List[{"second": int, "pct_viewing": float}]` (0–100)
    - `traffic_sources: List[{"source": str, "views": int, "ctr": Optional[float]}]`
    - `top_geographies: List[{"country": str, "views": int}]`
  - Experiment proposal:
    - `id: str` (slug + date + short uid)
    - `video_id: str`
    - `hypothesis: str`
    - `kpi: Literal["ctr","apv","avd","views"]`
    - `target_delta_pct: float`
    - `priority: int` (1 highest)
    - `variant_type: Literal["title","thumbnail","description","chapters"]`
    - `guardrails: {"min_runtime_hours": int, "min_impressions": int, "stop_if_ctr_drop_pct": float}`
    - `status: Literal["backlog","running","completed","aborted"]`

- **Python changes**
  - Types in `core/schemas.py`:
    - `AnalyticsRequest`, `AnalyticsSnapshot`, `ExperimentProposal`, `ExperimentResult`
  - `integrations/n8n_client.py`:
    - `def fetch_analytics(request: AnalyticsRequest) -> AnalyticsSnapshot: ...`
    - `def apply_metadata_update(video_id: str, fields: dict) -> dict: ...` (future Phase 7.2; n8n workflow to update metadata)
  - `orchestrator.py`:
    - `def analytics(slug_or_video_id: str, lookback_days: Optional[int] = None) -> AnalyticsSnapshot: ...`
    - `def propose_experiments(snapshot: AnalyticsSnapshot, baselines: dict | None = None) -> List[ExperimentProposal]: ...`
      - Heuristics:
        - If `ctr < baseline.ctr_low`: propose `thumbnail` test (priority 1); secondary `title` test (priority 2).
        - If `avg_percentage_viewed < baseline.apv_low`: propose `description` hook rework or `chapters` tweak (priority 2–3).
        - If `retention_curve` early drop (>40% loss by 30s): propose stronger hook (title/thumbnail pair).
        - If `traffic_sources` dominated by browse with low CTR: prioritize thumbnail.
      - Default baselines:
        - `ctr_low = 4.0`, `apv_low = 45.0`, `avd_low_sec = 120` (override via `OPTIMIZER_BASELINES_JSON`).
  - Reporting:
    - `def write_report(slug: str, snapshot: AnalyticsSnapshot, proposals: List[ExperimentProposal]) -> Path: ...`
      - Writes `reports/{YYYYMMDD}_{slug}.md` with KPIs table, retention chart (ASCII sparkline), prioritized proposals, and next actions.

- **CLI**
  - `ytfaceless analytics fetch --slug <slug> [--video-id <id>] [--lookback-days 28] [--json]`
  - `ytfaceless optimize propose --slug <slug> [--lookback-days 28] [--baselines <path>] [--json]`
  - Future: `ytfaceless optimize apply --video-id <id> --variant <title|thumbnail|description|chapters> --file <path>` (drives n8n update workflow)

- **n8n workflows**
  - `youtube_analytics.json` (to create):
    - HTTP In → YouTube Analytics node(s) → transform to `AnalyticsSnapshot` → HTTP Response.
    - Handle quota and partial data gracefully; include `execution_id`.
  - `youtube_update_metadata.json` (future-ready):
    - HTTP In → YouTube Update Video node (title/description/tags/thumbnail) → Response.

- **Observability**
  - Persist raw analytics JSON in `data/analytics/{video_id}/{YYYY-MM-DD}.json`.
  - Report files in `reports/` with stable naming; link to prior report if exists.
  - Logs include `execution_id` from n8n.

- **Testing plan (pytest)**
  - Unit: heuristic prioritization deterministic ordering; baseline overrides; edge cases (zero impressions, missing retention).
  - Unit: report writer produces expected sections and valid file path.
  - Unit: analytics client handles 200/4xx/5xx with retries/backoff.
  - Fixtures: synthetic `AnalyticsSnapshot` scenarios (low CTR, low APV, healthy video).

- **Acceptance criteria (DoD)**
  - `ytfaceless analytics fetch` returns structured KPIs and saves raw snapshot.
  - `ytfaceless optimize propose` produces prioritized, actionable experiments with guardrails.
  - Reports generated in `reports/` with clear next actions.
  - All unit tests pass; documentation updated.

- **Conventional commits (suggested)**
  - `feat(integrations): add analytics client for n8n webhook`
  - `feat(orchestrator): analytics fetch and experiment proposal heuristics`
  - `feat(reports): write Markdown analytics report with proposals`
  - `feat(cli): add analytics and optimize subcommands`
  - `test(optimizer): cover heuristics and reporting`
  - `docs(readme): add Phase 7 usage and workflows`


### Cross-phase guardrails and future-proofing

- **Security & compliance**
  - Keep secrets in `.env`; never log tokens or webhook URLs.
  - Validate and sanitize all external inputs; handle HTTP timeouts and 429 with backoff.

- **Quotas & retries**
  - Shared retry policy (exponential backoff, jitter) applied to all n8n calls.
  - Centralize constants in `core/config.py`.

- **Artifacts & traceability**
  - Upload manifests, analytics snapshots, and reports are immutable, timestamped, and linked by `slug` and `video_id`.

- **Extension to Phase 8**
  - Experiments backlog persisted at `data/experiments/backlog.json` for revenue analysis tie-in.
  - Add `sponsorship`/`affiliate` fields to proposals in future PRs.


### Proposed file changes/new files

- Update:
  - `src/yt_faceless/core/schemas.py`
  - `src/yt_faceless/integrations/n8n_client.py`
  - `src/yt_faceless/orchestrator.py`
  - `src/yt_faceless/cli.py`
  - `README.md` (CLI/Quickstart/env vars)
- Add:
  - `reports/.gitkeep`
  - `data/analytics/.gitkeep`
  - `workflows/youtube_analytics.json` (n8n)
  - `output/{slug}/upload_manifest.json` (runtime artifact)
  - Optional: `config/baselines.json` (optimizer thresholds)


### Example CLI flows

- Upload & schedule:
  - `ytfaceless publish --slug ai-trends-2025 --privacy private --publish-at 2025-09-20T15:00:00Z`
- Fetch analytics + propose:
  - `ytfaceless analytics fetch --slug ai-trends-2025 --lookback-days 28`
  - `ytfaceless optimize propose --slug ai-trends-2025 --lookback-days 28 --baselines config/baselines.json`


### Minimal directory tree impact

.
├─ src/yt_faceless/
│  ├─ cli.py                  # + publish, analytics, optimize
│  ├─ orchestrator.py         # + publish(), analytics(), propose_experiments(), write_report()
│  ├─ integrations/
│  │  └─ n8n_client.py        # + upload_video(), fetch_analytics(), apply_metadata_update()
│  └─ core/
│     └─ schemas.py           # + YouTubeUploadPayload, YouTubeUploadResponse, Analytics*, Experiment*
├─ workflows/
│  ├─ youtube_upload.json     # existing, aligned to contract
│  └─ youtube_analytics.json  # new
├─ data/
│  ├─ analytics/              # raw snapshots
│  └─ experiments/            # backlog (future)
├─ output/{slug}/upload_manifest.json
└─ reports/                   # generated Markdown reports
```