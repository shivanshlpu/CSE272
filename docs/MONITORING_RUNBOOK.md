# Bhav monitoring service

## What runs
React dashboard → Express API and scheduler → one persistent Python analysis/storage worker → SQLite WAL database. This is a single-instance deployable service, not a horizontally scalable production cluster. Never run multiple scheduler processes against the same database. The original synthetic dashboard, hardcoded regional statistics, simulated feed and heuristic emotion/bot displays are no longer part of the active application.

## Reproduce
1. Use Python 3.12 and Node.js 20.20 or newer.
2. Create `.venv`, install `requirements-ml.txt`, run `npm run setup`.
3. Run `.venv/bin/python -m ml.data` and `.venv/bin/python -m ml.download_encoder` to download published sentiment data and the pinned multilingual encoder.
4. Run `npm run train` then `npm run train:stance`. Both commands fit local classifiers and persist measured validation/test results. The stance trainer downloads immutable TweetEval data; it never generates labelled training data.
5. Run `npm run seed` to add the user's selected video without adding any comments.
6. Copy `.env.example` to `.env`; set `YOUTUBE_API_KEY` for a Google Cloud project with YouTube Data API v3 enabled. Do not send the key to the frontend or commit it.
7. Run `npm run build` and `npm start`. Open http://127.0.0.1:3001.

The seed video is CswOUBuokjo, whose public oEmbed title was retrieved as “INDIA’S GOT LATENT S2 EP9 ft. Raftaar, Balraj Ghai, Sahil Kale.” Initial claim: “This episode of India’s Got Latent is entertaining and worth watching.” This is an analyst-chosen target, not a fact inferred from comments. Create another monitor to evaluate a different claim; stored stance labels belong to their original claim.

## Collection
Every enabled monitor is checked every 15 seconds and runs at its configured interval while the server is alive. Each run refreshes the newest 100 top-level comments per selected video and uses the remaining two pages to continue a persisted historical cursor. It upserts source IDs, timestamps and observed like counts. It does not collect replies, infer followers, or claim all comments have been collected. Existing comments not revisited may have stale edits, deletions or likes; a source-link check is required before citing a specific comment externally. Bounded storage and analysis are explicit: latest 10,000 records per monitor stored, latest 2,000 analyzed, latest 100 displayed.

YouTube requests time out after 20 seconds and transient failures retry at most twice with backoff. Disabled comments, invalid keys, unavailable videos and partial runs are visible. Local quota reservation persists across restarts and reserves every request attempt. Default local budget is 1,000 units/day, measured in UTC; YouTube's project-wide quota and reset schedule can differ. Search costs 100 units per request; commentThreads.list costs 1. API project usage from other applications is not included. A failed run waits at least five minutes before scheduled retry; an analyst can manually request another run.

A saved cursor can expire. An invalid-page-token response resets that cursor for the next run. Partial ingestion is idempotent by monitor and comment ID. A server or worker restart marks previously running jobs interrupted. Shutdown is bounded; unfinished work can be retried after restart. There is no exactly-once external collection guarantee.

## Model interpretation
Sentiment predicts positive, neutral, negative tone. Stance predicts agreement, disagreement or no clear stance about a supplied target. NONE in TweetEval includes off-topic and ambiguous material, so it is not proof of neutrality. The stance classifier combines separate text/target embeddings, their interaction and pair embeddings; regularization is selected on validation data. All encoder weights remain frozen.

Recorded stance experiment: 2,605 train, 294 validation, 1,248 test rows after normalized text deduplication. Test macro F1 62.56%, lexical baseline 53.24%. A separately fitted model withholding the Hillary Clinton target from training attains 38.12% F1 on 295 held-out-topic test posts. Hyperparameters were selected on the full target validation set, so this audit is not a fully nested zero-shot benchmark. Hindi/Hinglish stance is unvalidated. The UI marks machine labels as estimates requiring review. Review corrections persist; an edited comment invalidates its old review. Corrections do not silently retrain or alter the reported benchmark metrics.

Semantic themes are KMeans clusters over multilingual sentence embeddings with TF-IDF keyword labels; they are exploratory, not validated issue taxonomies. Themes are refit on the analysis sample, so cluster IDs are not stable across refreshes. Growth compares topic shares in two 24-hour windows using the same clustering in that analysis, minimum 10 comments per window and at least 5 current comments in an emerging cluster. A representative comment is closest to its cluster centroid. “Most liked” means maximum observed likes within collected comments, not demonstrated real-world influence. Volume counts comments, not unique people. Summaries are auditable aggregates, not generated political messaging or population opinion estimates.

## Operations
`GET /api/health` is process liveness. `GET /api/ready` requires model artifacts and a configured YouTube key, but does not validate that key with Google. `/api/status` reports local quota, worker/model status, active collection IDs and retention. All routes except liveness require `MONITOR_API_TOKEN` when set. A token of at least 24 characters is mandatory for non-loopback HOST bindings. Supply it through a secret manager and use HTTPS termination with a matching APP_ORIGIN. The dashboard token is kept only in memory. It is one shared service credential, not per-user identity or RBAC; use an authenticated gateway before a multi-user rollout.

Back up SQLite using SQLite's backup API rather than copying an active WAL file. Store `data/monitoring.sqlite`, model artifacts and the encoder cache on durable volumes. Protect backups and expire their source data too. SQLite files are owner-readable/writable. The service prunes records not refreshed in 29 days and old collection logs; source-policy reviews and deletion requests still need operational handling. No automatic external messaging is sent. The app does not infer individuals' political affiliation or track authors.

Before operational rollout: configure real credentials, verify collection against an accessible and a comments-disabled video, exercise quota/retention/restart recovery on the deployment host, test expected load, add organization identity and role permissions, and validate stance on reviewed domain/language-specific data. Platform-specific permitted-use and privacy requirements must be checked before external deployment. The connector was tested with isolated provider-response fixtures; no authenticated YouTube collection was run because the owner chose to finish without supplying a key. Dependencies were used in the existing environment; a clean-machine installation/container deployment is not yet verified.

## Tests
`npm run test:monitor` exercises provider pagination, deduplication, retries, missing credentials, cost accounting, storage/review persistence, expiry, timestamp windows and dataset provenance. `npm test` includes the existing sentiment tests. Fixture comments exist only inside tests and are never displayed as live data or used to train models.
