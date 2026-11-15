"""Render the actual training artifact as a readable evaluation report."""
import json
from ml.data import ROOT

def main():
    m=json.loads((ROOT/'artifacts/metrics.json').read_text())
    lines=['# Local model evaluation','',f"Train: {m['training_rows']:,}; validation: {m['validation_rows']:,}; test: {m['test_rows']:,}.",'','| Model | Test accuracy | Test macro F1 |','|---|---:|---:|']
    for name,key in [('Word unigram baseline','baseline_test'),('Validation-selected hybrid','test')]:
        lines.append(f"| {name} | {m[key]['accuracy']:.2%} | {m[key]['macro_f1']:.2%} |")
    lines+=['',f"Macro-F1 improvement: {(m['test']['macro_f1']-m['baseline_test']['macro_f1'])*100:.2f} percentage points.",f"Selected neural blend weight: {m['selected_neural_weight']}. Training elapsed: {m['seconds']:.1f} seconds.",'','## Per-language test results','', '| Language | Accuracy | Macro F1 |','|---|---:|---:|']
    for lang,result in m['per_language'].items():lines.append(f"| {lang} | {result['accuracy']:.2%} | {result['macro_f1']:.2%} |")
    lines+=['','## Method',m['encoder_training'],'','Training uses class-balanced logistic regression, word/character features, three regularization candidates, and a PyTorch head trained with AdamW, dropout, gradient clipping and validation early stopping. Five ensemble blend weights are selected on validation macro-F1. Test labels are not used to fit/select models. Saved artifacts and source files have SHA256 checksums.','', 'The old 82% accuracy/F1 target is not met; this report does not claim it is.','', '## Limitations']
    lines += ['- '+s for s in m['limitations']]
    lines += ['- Original SentiMix test files contain some encoding artifacts; downloads were verified byte-for-byte against the upstream files.','- Cardiff Hindi includes Romanized examples; language tags are dataset configuration labels, not guaranteed script labels.','- Sources: https://huggingface.co/datasets/cardiffnlp/tweet_sentiment_multilingual and https://huggingface.co/datasets/RTT1/SentiMix . Original SentiMix paper: https://aclanthology.org/2020.semeval-1.100/ .']
    (ROOT/'docs/EVALUATION_REPORT.md').write_text('\n'.join(lines)+'\n')
if __name__=='__main__':main()
