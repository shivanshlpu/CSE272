# Evaluation report

Actual execution results; synthetic engagement and repeated templates limit generalization. No claim of independent accuracy is made.

- **dataset:** Repeated-template synthetic smoke set; NOT independent held-out validation
- **n_posts:** 335
- **sentiment_macro_f1:** 1.0
- **sentiment_accuracy:** 1.0
- **baseline_macro_f1:** 1.0
- **improvement_percentage_points:** 0.0
- **per_language_f1:** {'en': 1.0, 'hi': 1.0, 'hi-en': 1.0}
- **bot_recall:** 1.0
- **bot_false_positive_rate:** 0.0
- **bot_detection_seconds:** 0.030417499991017394
- **theme_alignment_rate:** 0.0
- **adjusted_rand_index:** 0.24694986272097907
- **topic_mode:** Multilingual MiniLM + UMAP + HDBSCAN / BERTopic
- **throughput:** {'1': {'posts_per_second': 35338.28644053917, 'seconds': 0.0028297919925535098, 'p50_latency': 5.395995685830712e-06, 'p95_latency': 8.976749086286871e-06, 'failures': 0, 'cache_hit_rate': 0.0, 'provider': 'auto', 'model': 'heuristic'}, '8': {'posts_per_second': 39091.77284280461, 'seconds': 0.0025580830115359277, 'p50_latency': 5.541005521081388e-06, 'p95_latency': 9.88955216598697e-06, 'failures': 0, 'cache_hit_rate': 0.0, 'provider': 'auto', 'model': 'heuristic'}}
- **gates:** {'sentiment_f1': True, 'improvement': False, 'bot_recall': True, 'bot_fpr': True}
- **held_out_sarcasm_benchmark:** NOT VERIFIED: independent 150-case handwritten set not available
- **hf_accuracy:** {'n': 300, 'accuracy': 0.44666666666666666, 'macro_f1': 0.38757716792850766, 'note': 'First 100 rows per language of cached real HF records; not randomized held-out sampling'}

## Limitations and next validation
Heuristic fallback and lexical clustering do not guarantee sarcasm or cross-language alignment targets. Targets marked false are missed. Evaluate a real configured LLM and cached multilingual embeddings against an independently authored held-out set; do not tune the test set to force a pass. Live provider throughput is unverified in auto mode.
