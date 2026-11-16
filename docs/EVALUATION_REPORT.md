# Local model evaluation

Train: 17,670; validation: 3,647; test: 4,737.

| Model | Test accuracy | Test macro F1 |
|---|---:|---:|
| Word unigram baseline | 59.87% | 60.07% |
| Validation-selected hybrid | 64.83% | 65.15% |

Macro-F1 improvement: 5.08 percentage points.
Selected neural blend weight: 0.25. Training elapsed: 217.0 seconds.

## Per-language test results

| Language | Accuracy | Macro F1 |
|---|---:|---:|
| en | 63.79% | 64.16% |
| hi | 53.63% | 53.78% |
| hi-en | 68.37% | 68.64% |

## Method
Frozen pretrained encoder; 49,667-parameter neural head trained locally with AdamW and early stopping. Encoder weights are NOT fine-tuned.

Training uses class-balanced logistic regression, word/character features, three regularization candidates, and a PyTorch head trained with AdamW, dropout, gradient clipping and validation early stopping. Five ensemble blend weights are selected on validation macro-F1. Test labels are not used to fit/select models. Saved artifacts and source files have SHA256 checksums.

The old 82% accuracy/F1 target is not met; this report does not claim it is.

## Limitations
- No sarcasm/emotion labels; these capabilities are not claimed.
- Dataset cards and upstream rights govern reuse; downloaded social text may contain offensive content.
- No post timestamps or engagement available: no invented trend timeline or reach weighting.
- Frozen encoder pretraining overlap is unknown; exact normalized duplicates removed, near-duplicates not fully audited.
- Probabilities are uncalibrated estimates; review threshold is a fixed heuristic, not a guaranteed error bound.
- Original SentiMix test files contain some encoding artifacts; downloads were verified byte-for-byte against the upstream files.
- Cardiff Hindi includes Romanized examples; language tags are dataset configuration labels, not guaranteed script labels.
- Sources: https://huggingface.co/datasets/cardiffnlp/tweet_sentiment_multilingual and https://huggingface.co/datasets/RTT1/SentiMix . Original SentiMix paper: https://aclanthology.org/2020.semeval-1.100/ .
