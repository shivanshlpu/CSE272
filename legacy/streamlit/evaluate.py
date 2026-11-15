"""Headless, honest evaluation: synthetic smoke metrics are not held-out evidence."""
import argparse
import json
import time
from pathlib import Path
import pandas as pd
from sklearn.metrics import f1_score, accuracy_score, adjusted_rand_score
from src.ingestion import generate_synthetic_benchmark
from src.preprocessing import preprocess
from src.llm_engine import analyze, lexicon_baseline
from src.llm_bertopic import fit_topics


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--n-samples',type=int,default=300)
    parser.add_argument('--provider',choices=['auto','groq','ollama'],default='auto')
    parser.add_argument('--quick',action='store_true')
    parser.add_argument('--semantic',action='store_true')
    args = parser.parse_args()
    raw = generate_synthetic_benchmark(args.n_samples,seed=91)
    started = time.perf_counter()
    cleaned = preprocess(raw)
    bot_seconds = time.perf_counter()-started
    predicted = analyze(cleaned,args.provider,use_cache=False)
    topics = fit_topics(predicted,args.semantic,args.provider)
    organic = topics[~raw.true_is_bot]
    f1 = f1_score(organic.ground_truth,organic.label,average='macro',zero_division=0)
    baseline = f1_score(organic.ground_truth,organic.text.map(lexicon_baseline),average='macro',zero_division=0)
    recall = float(cleaned.loc[raw.true_is_bot,'is_bot'].mean())
    fpr = float(cleaned.loc[~raw.true_is_bot,'is_bot'].mean())
    alignments = []
    for _, group in organic.groupby('true_theme'):
        modes = [g.topic_id.mode().iloc[0] for _,g in group.groupby('lang')]
        alignments.append(len(modes)==3 and len(set(modes))==1 and modes[0]>=0)
    throughput = {}
    for workers in [1,8]:
        measured = analyze(cleaned.head(100),args.provider,workers,use_cache=False)
        throughput[str(workers)] = measured.attrs['telemetry']
    results = dict(dataset='Repeated-template synthetic smoke set; NOT independent held-out validation', n_posts=len(raw), sentiment_macro_f1=float(f1), sentiment_accuracy=float(accuracy_score(organic.ground_truth,organic.label)), baseline_macro_f1=float(baseline), improvement_percentage_points=float(100*(f1-baseline)), per_language_f1={lang:float(f1_score(g.ground_truth,g.label,average='macro',zero_division=0)) for lang,g in organic.groupby('lang')}, bot_recall=recall, bot_false_positive_rate=fpr, bot_detection_seconds=bot_seconds, theme_alignment_rate=sum(alignments)/max(1,len(alignments)), adjusted_rand_index=float(adjusted_rand_score(organic.true_theme,organic.topic_id)), topic_mode=topics.attrs['topic_mode'], throughput=throughput, gates=dict(sentiment_f1=bool(f1>=.82), improvement=bool(f1-baseline>=.18), bot_recall=recall>=.95, bot_fpr=fpr<.02), held_out_sarcasm_benchmark='NOT VERIFIED: independent 150-case handwritten set not available', hf_accuracy='NOT VERIFIED: separate HF evaluation not run')
    root = Path(__file__).parent
    corpus_path = root/'data/corpus_v2_5000_42.parquet'
    if corpus_path.exists():
        corpus = pd.read_parquet(corpus_path)
        real = corpus[corpus.source == 'HuggingFace'].groupby('lang', group_keys=False).head(100)
        hf = analyze(preprocess(real), args.provider, use_cache=False)
        results['hf_accuracy'] = {'n':len(hf), 'accuracy':float(accuracy_score(hf.ground_truth,hf.label)), 'macro_f1':float(f1_score(hf.ground_truth,hf.label,average='macro',zero_division=0)), 'note':'First 100 rows per language of cached real HF records; not randomized held-out sampling'}
    (root/'data').mkdir(exist_ok=True)
    for name in ['evaluation_report.json','eval_results.json']:
        (root/'data'/name).write_text(json.dumps(results,indent=2))
    report = '# Evaluation report\n\nActual execution results; synthetic engagement and repeated templates limit generalization. No claim of independent accuracy is made.\n\n'
    report += '\n'.join(f'- **{key}:** {value}' for key,value in results.items())
    report += '\n\n## Limitations and next validation\nHeuristic fallback and lexical clustering do not guarantee sarcasm or cross-language alignment targets. Targets marked false are missed. Evaluate a real configured LLM and cached multilingual embeddings against an independently authored held-out set; do not tune the test set to force a pass. Live provider throughput is unverified in auto mode.\n'
    (root/'data/evaluation_report.md').write_text(report)
    (root/'docs/EVALUATION_REPORT.md').write_text(report)
    print(report)

if __name__ == '__main__':
    main()
