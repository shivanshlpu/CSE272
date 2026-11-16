# Architecture — React / Node / local trained ML

## Runtime

React/Vite static assets → Express API → persistent Python JSON-lines worker → saved lexical/neural model.

Node owns request validation, 256KB body limit, batch limits (100 posts, 5k characters each), an eight-request queue cap, a 180-second timeout and worker restart after process failure. It launches Python directly without a shell or interpolating user input. The worker loads corpus and trained models once, then serves inference. Worker exceptions are returned as structured errors; no heuristic or generated-data fallback replaces failures.

The frontend shows immutable trained-model metrics separately from filtered exploration statistics. Exploration operates only on real test records, selecting a reproducible sample of up to 90 matches; it does not claim to analyze the entire corpus on each view. Search and language filters query Node. Inference results include probabilities, polarity P(positive)-P(negative), and a fixed review threshold.

## Training

Raw dataset downloads → provenance manifest → normalized hash deduplication → original train/validation/test splits → train-only feature fitting → validation model/epoch/blend selection → test evaluation → trusted local artifacts.

Lexical branch: word TF-IDF (1–2 grams, 45k features) plus char_wb TF-IDF (3–5 grams, 60k features), class-balanced logistic regression. C in {0.5,2,8} is validation-selected. Baseline uses word unigrams only.

Neural branch: frozen 384-d multilingual MiniLM with max sequence length 128; L2-normalized embeddings; 384→128→3 head with ReLU/dropout .25. AdamW lr .001, weight decay .01, class-balanced cross entropy, batch 128, gradient clip 1, maximum 25 epochs and five-epoch validation patience. Train shuffling and model initialization use seed 42. Early-stopping restores the best validation weights.

Ensemble: choose neural weight from {0,.25,.5,.75,1} on validation macro-F1. Selected .25. No test-based tuning. NumPy/sklearn/Torch artifacts preserve the selected model. The encoder is not fine-tuned; cached vectors accelerate repeat experiments.

## Honest boundaries

No synthetic dataset or metadata is consumed. No external LLM calls. No fabricated timeline/geography/reach. No trained sarcasm, emotion, bot or causal-shift claims. NMF themes and SVD projection are exploratory lexical views, not cross-lingual BERTopic evaluation. Existing source scripts under legacy/ are historical and excluded from pytest discovery.

Dataset URLs and revisions are pinned in the manifest. The pretrained encoder revision used for this run is pinned to e8f8c211226b894fcb81acc59f3b34ba3efd5f42 in the model and download helper. Frozen encoder pretraining overlap and near-duplicate leakage are not fully audited. Source social-language labels do not imply a specific writing script.
