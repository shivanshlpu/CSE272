# Signal — trained multilingual sentiment intelligence

**Current stack: React 19 + Node.js/Express + locally trained Python ML.** The old Streamlit/API/synthetic prototype is archived under `legacy/` and is not used by this application.

## Start the built application

```sh
npm start
```

Open http://127.0.0.1:3001 . Node serves the built React frontend and runs a persistent Python inference worker. No Groq, OpenAI, Ollama or other inference API is used. Model weights are already trained in `artifacts/` in this workspace.

## Reproduce from source

Requires Python 3.12 and Node 20+. The current environment uses `.venv`.

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-ml.txt
npm run setup
python -m ml.data
python -m ml.download_encoder
python -m ml.train
python -m ml.report
npm run build
npm start
```

Downloads require internet; subsequent training and inference use cached local data/model files. A failed dataset download fails explicitly. No generated samples, synthetic fillers, fabricated engagement or invented dates enter the current pipeline. `requirements-ml.txt` lists the installed direct dependency versions used for this run; a separate clean environment reproduction has not been verified. Existing original `requirements.txt` is retained only for the archived prototype.

For frontend development, run `npm start` and `npm run dev` in separate terminals. Vite proxies `/api` to Node. `PORT` changes the Node port; `PYTHON_BIN` optionally overrides `.venv/bin/python`.

## Real training and refinement

Downloaded Cardiff multilingual sentiment (English/Hindi) and SemEval 2020 SentiMix (Hinglish) corpora supply **26,054** deduplicated examples: **17,670 training**, **3,647 validation**, **4,737 test**. Published splits are preserved; exact normalized-text overlaps are removed from training/validation, reserving test first. Raw download URLs, immutable dataset revisions and SHA256 checksums are in `data/downloaded/manifest.json`.

1. Train a word-unigram TF-IDF/logistic-regression baseline.
2. Train word-bigram + character 3–5-gram classifiers; compare three regularization settings on validation macro-F1.
3. Extract cached multilingual MiniLM embeddings. Train a **49,667-parameter PyTorch neural head** using AdamW, weighted cross entropy, dropout, gradient clipping and early stopping.
4. Select the lexical/neural ensemble weight from five candidates using validation data.
5. Evaluate the fixed model on the published test splits and save weights, predictions metrics, per-language results, confusion matrix and training history.

**The pretrained MiniLM encoder is frozen, not fine-tuned.** The classifier and neural head are trained locally. This is transfer learning with a trained hybrid classifier, not a pretrained model API wrapper.

Actual test macro-F1: **65.15%**, versus **60.07%** for the baseline (+5.08 percentage points). Test accuracy: **64.83%**. The earlier 82% research target is not met. Full metrics are in `artifacts/metrics.json` and `docs/EVALUATION_REPORT.md`.

## Interface

- **Overview:** filter real held-out posts, inspect sentiment distribution, uncertain predictions, lexical topic clusters and projection.
- **Model lab:** training history, all refinement experiments, per-language metrics and confusion matrix.
- **Inference studio:** run up to 100 actual posts per request through local weights; class probabilities and low-confidence review flags.
- **Data sources:** published split counts, immutable download links and checksums.

The downloaded corpora lack reliable post dates, reach and geography. Those fields are not invented: this version does not claim a live temporal trend tracker, influence weighting or geographic sentiment. Topic discovery is exploratory NMF, and the scatter is explicitly TF-IDF/SVD. Sarcasm/emotion labels are not trained or claimed.

## Tests

```sh
HF_HUB_OFFLINE=1 .venv/bin/python -m pytest -q
```

Four tests verify data provenance/split separation, artifact/source checksums, deterministic real-row inference and Unicode-preserving normalization. Node API health, model metadata, language-filtered exploration, inference and invalid-input rejection were checked against the running server. React production build and browser interactions were verified.

## Files

- `ml/data.py`: reproducible download, CoNLL parsing, normalization, exact deduplication.
- `ml/train.py`: actual training, hyperparameter selection, early stopping and test evaluation.
- `ml/model.py`: trained classifier loading and local inference.
- `ml/worker.py`: persistent JSON-lines inference process and exploratory topics.
- `server/index.mjs`: validated Express API, bounded request queue, timeout and worker lifecycle.
- `frontend/src/`: React application and responsive styling.
- `artifacts/`: trained weights, cached embeddings, training log and metrics.

Only load trusted local joblib artifacts. Raw social datasets may contain offensive text and personal handles. Follow source terms and licenses; downloading a mirror does not grant unrestricted redistribution. The app binds to localhost and is a research application, not a hardened public multi-user deployment. Source-language imbalance, upstream text corruption, unknown encoder pretraining overlap and uncalibrated probabilities limit performance. Do not interpret a 60% review threshold as a calibrated confidence guarantee.
