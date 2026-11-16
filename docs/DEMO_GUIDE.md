# Demo — React and locally trained ML

1. Start `npm start`, open http://127.0.0.1:3001. Explain the React → Node → Python architecture.
2. Overview: inspect real test posts, language filters, low-confidence flags, sentiment bars and lexical topic projection. Explain the 90-post sample.
3. Model lab: compare baseline with the validation-selected hybrid, inspect neural learning curves, regularization experiments, language-level F1 and confusion matrix.
4. Inference studio: paste actual posts, one per line, and run local inference. Predictions are from saved weights, not an API provider. Some predictions are wrong and uncertainty is visible.
5. Data sources: inspect original split sizes, download URLs, and SHA256 checksums. Explain why no synthetic timeline or engagement chart is present.
6. Show ml/train.py and artifacts/training.log to demonstrate training, validation refinement and restored best neural weights. The encoder is frozen; the classifier/head is locally trained.

The achieved test macro-F1 is 65.15%; do not present the old synthetic scores or claim the earlier 82% target is met.
