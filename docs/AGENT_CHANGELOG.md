# Agent Changelog

## [2026-11-15] Codex — Initial handoff bootstrap
- **Phase:** 0
- **Did:** Created handoff and append-only changelog with full phase checklist.
- **Verified:** NOT verified yet.
- **Decisions:** Use the empty designated workspace as project root.
- **Open issues:** Environment and network availability not yet checked.
- **Next:** Verify bootstrap files, then start Phase 1.

## [2026-11-15] Codex — Scaffold and dependency install preparation
- **Phase:** 1
- **Did:** Created required scaffold, central thresholds, configuration example, pinned candidate dependency list, and preserved the supplied brief as prompt.md. Implementation files are stubs.
- **Verified:** Host python3 is 3.9.6, below requirement; bundled Python is 3.12.14. Phase 0 file/checklist assertion passed.
- **Decisions:** Use bundled Python 3.12 for the clean venv; dependency pins are candidates until installation succeeds.
- **Open issues:** Dependency installation and network availability unverified.
- **Next:** Create a clean venv and attempt dependency installation.

## [2026-11-15] Codex — Clean install attempt
- **Phase:** 1
- **Did:** Created .venv using bundled Python 3.12.14; started installation of pinned requirements.
- **Verified:** Sandboxed `.venv/bin/python -m pip install -r requirements.txt` failed because DNS could not reach PyPI; network-enabled retry is running and downloading packages.
- **Decisions:** Do not mark the dependency gate passed until retry and import checks finish.
- **Open issues:** Installation result pending.
- **Next:** Wait for installation; run import and dependency checks.

## [2026-11-15] Codex — HANDOFF FLUSH
- **Phase:** 1
- **Did:** Network-enabled initial requirements installation completed; added `httpx==0.27.2` after discovering OpenAI constructor incompatibility with resolved 0.28.1. Rewrote handoff with current exact state.
- **Verified:** Initial install succeeded; `pip check`, `import src`, and OpenAI constructor passed after downgrade. Combined import was interrupted while BERTopic/numba was compiling; no result. Final requirements have not been tested in a fresh venv.
- **Decisions:** Keep Phase 1 in progress; later phases remain untouched.
- **Open issues:** Clean final install and BERTopic import pending; all application modules are stubs.
- **Next:** Run Phase 1 verification in a fresh venv, then proceed through remaining phases.

## [2026-11-15] Codex Astra — New specification and initial ingestion
- **Did:** Preserved new master prompt, created PROGRESS_STATE.md, defined four engineering responsibilities, implemented canonical validator and synthetic benchmark (organic records + exactly 35 bots), added tests.
- **Verified:** pip check and OpenAI constructor passed; 2 ingestion tests passed in 0.78s.
- **Limitations:** Repeated synthetic templates are not independent accuracy evidence. Live connectors, corpus loader, all analytics and UI remain pending. No benchmark targets claimed.
- **Next:** Finish Phase 2 ingestion, then preprocessing.

## [2026-11-15] Codex Astra — Full offline application integration
- Implemented corpus/live adapters, preprocessing, inference/cache/weights, semantic and lexical topic paths, dashboard, CLI evaluation, documentation and tests.
- Verified: 5 pytest tests passed; 335 and 10,035-row evaluations exited zero; Streamlit AppTest analysis and bot toggle passed with four KPIs; 50,035-row preprocessing took 6.700575 seconds and flagged 35 bots.
- Benchmark targets not all achieved: initial smoke macro-F1 .78296, baseline .70369; alignment zero in lexical fallback. Independent held-out benchmarks remain pending.
- Network corpus verification ongoing; integrations requiring credentials/models are not claimed verified.

## [2026-11-15] Codex Astra — Real data and semantic model verification
- Corrected Hinglish tweet/sentiment mapping after inspecting the actual public dataset. Verified 3,830 HF rows plus 1,170 labelled synthetic replacements for the 5k request.
- Downloaded multilingual MiniLM and verified actual BERTopic/UMAP/HDBSCAN on 100 organic posts.
- Fixed Hindi combining-mark tokenization; six tests pass. Added real HF accuracy measurement (300 rows, heuristic accuracy .4467/macro-F1 .3876). Synthetic baseline now matches synthetic heuristic at 1.0, so improvement target is missed.
- All live fallback adapters verified. Authenticated provider quality and independently authored sarcasm test set remain pending.

## [2026-11-15] Codex Astra — Dashboard launched
- Real semantic evaluation completed, with alignment 0 and ARI .24695; target not claimed passed.
- Started Streamlit successfully at 127.0.0.1:8501 after sandbox bind restriction. Session 49523.
- Functional application delivered; outstanding acceptance gaps explicitly retained in PROGRESS_STATE.md and report.

## [2026-11-15] Codex Astra — React/Node and locally trained model migration
- User replaced Streamlit/synthetic/API-only architecture. Built React/Vite UI, Node/Express service and persistent Python model worker.
- Downloaded pinned Cardiff and SentiMix published splits. 26,054 deduplicated rows, with 17,670 train / 3,647 validation / 4,737 test. No generated replacements.
- Trained unigram baseline, three word/character candidates, 49,667-parameter PyTorch head on frozen multilingual MiniLM features, and five validation-selected ensemble candidates. Selected neural weight .25.
- Actual held-out F1 .651486 vs baseline .600733; accuracy .648301. Training 216.96 sec. No encoder fine-tuning or 82% target claim.
- Verified: four ML tests, production React build, Node API health/model/explore/predict/400 validation; browser dashboard, Model lab and inference interactions.
- Upstream SentiMix encoding artifacts verified against original download bytes, not introduced locally. Documented.
- Archived old Streamlit implementation under legacy/; current pytest targets tests_ml only. Current application lives at localhost:3001.
