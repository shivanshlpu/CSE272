# AI-Powered Social Media Trend and Public Sentiment Tracker

**Shivansh Tiwari** (Author 1)  
*Department of Computer Science & Engineering (AI & ML)*  
*Lovely Professional University*  
*Jalandhar, Punjab, India*  
*shivansh.tiwari@lpu.in*  

**Ankit Kesharwani** (Author 2)  
*Department of Computer Science & Engineering (AI & ML)*  
*Lovely Professional University*  
*Jalandhar, Punjab, India*  
*ankit.kesharwani@lpu.in*  

---

### Abstract
Social media platforms generate voluminous multi-lingual discourse reflecting public sentiment on commercial brands, governance policies, and socio-economic events. In linguistically diverse landscapes such as India, public commentary is predominantly expressed through code-mixed vernaculars—most notably Hinglish (Hindi written in Roman script)—interleaved with English and Devanagari Hindi. Traditional sentiment analysis systems falter when processing code-mixed syntax, sarcastic praise, and coordinated bot campaigns that artificially skew public mood metrics. This paper presents the design, implementation, and empirical evaluation of an AI-Powered Social Media Trend and Public Sentiment Tracker (named Bhav). The system features an on-device hybrid neural architecture combining word and character n-gram lexical representations with a frozen 384-dimensional multilingual sentence-transformer encoder and a trained PyTorch neural classification head. To mitigate manipulation from astroturfing campaigns, an automated bot isolation module filters coordinated near-duplicate text. Furthermore, an impact-weighted sentiment index replaces naive post-count averaging by scaling sentiment polarity logarithmically against viral engagement metrics, including likes, replies, and verified author follower counts. Evaluated on 26,054 benchmark social media posts across English, Hindi, and Hinglish, the proposed hybrid engine achieves an overall macro-F1 of 65.15 percent on held-out test splits, outperforming standard lexical baselines by 5.08 percentage points while sustaining sub-15 millisecond CPU inference latency. A real-time production ingestion gateway and interactive monitoring dashboard substantiate the real-world operational viability of the platform.

### Keywords
Sentiment Analysis, Multilingual Natural Language Processing, Code-Mixed Hinglish, Impact-Weighted Sentiment, Astroturf Bot Isolation, Sarcasm Detection, Sentence Transformers, Social Listening Intelligence.

---

## I. INTRODUCTION

Digital social platforms such as Twitter (X), Reddit, and public consumer forums serve as real-time barometers of public perception. Corporate brand custodians, public relations agencies, and public policy administrators rely on automated sentiment monitoring to preempt brand crises, evaluate customer satisfaction, and measure public reception to institutional initiatives [1]. 

However, deploying sentiment intelligence within multilingual populations—specifically across the Indian digital ecosystem—poses formidable computational challenges:
1. **Linguistic Code-Mixing & Script Heterogeneity**: Indian digital users routinely communicate in Hinglish (a code-mixed blend of Hindi vocabulary phonetically transcribed into the Latin/Roman script), alongside standard English and Devanagari Hindi. Conventional tokenizers and monolingual sentiment dictionaries fail to capture phonetic transliterations (e.g., *"Bhai service bilkul bekar hai"* vs. *"Bahut hi badiya update"*).
2. **Pragmatic Sarcasm & Inversion**: Sarcastic expressions such as *"Wah kya fast service hai, 5 din se internet band hai"* contain positive polarity tokens (*"Wah"*, *"fast"*) that mislead lexicon-based classifiers into false-positive classifications [2].
3. **Astroturfing & Bot Skew**: Coordinated bot rings and spam networks frequently flood target keywords with repetitive positive or negative propaganda. Treating every tweet with equal weight skews naive sentiment averages.
4. **Disproportionate Reach & Viral Influence**: A post by an influential analyst with 100,000 followers and thousands of re-shares exerts an order-of-magnitude greater social impact than a low-engagement comment from an account with zero followers. Naive mean sentiment metrics fail to reflect this dynamic.
5. **Operational Privacy & Cloud Costs**: Enterprise-grade cloud LLM APIs (e.g., OpenAI GPT-4, Google Gemini) incur prohibitive financial costs when continuously processing millions of streaming posts and risk exposing sensitive consumer proprietary data to third-party endpoints.

To address these challenges, we introduce **Bhav**—an end-to-end, on-device AI-Powered Social Media Trend and Public Sentiment Tracker. Bhav integrates a locally trained hybrid neural classifier, an automated astroturf bot-isolation pipeline, an impact-weighted polarity index, and an open production-ready HTTP ingestion gateway that enables external software systems to stream live public posts for real-time classification.

---

## II. RELATED WORK & PROBLEM FORMULATION

### A. Multilingual & Code-Mixed Sentiment Analysis
Early sentiment analysis predominantly targeted monolingual English corpora using bag-of-words or lexicon lookups like VADER and SentiWordNet [3]. In multilingual contexts, cross-lingual transfer models (mBERT, XLM-RoBERTa) improved token representations [4]. However, code-mixed Hinglish exhibits high lexical variation, informal slang, and inconsistent spelling conventions (e.g., *"acha"*, *"achha"*, *"accha"*). The SemEval-2020 Task 9 (SentiMix) established standard benchmark corpora demonstrating that sub-word character n-grams combined with dense multilingual embeddings significantly outperform pure word-level transformer fine-tuning on noisy social text [5].

### B. Commercial Social Listening Platforms
Commercial platforms such as Brand24 [6], Sprout Social [7], and Meltwater [8] provide enterprise brand intelligence and sentiment tracking. Nevertheless, commercial offerings exhibit notable deficiencies when applied to Indian enterprise contexts:
- They depend on third-party cloud APIs, introducing data leakage risks.
- They lack calibrated Hinglish sarcasm heuristics, leading to systematic misclassification of vernacular irony.
- They lack transparent impact-weighting equations that mathematically account for verified author authority.

---

## III. PROPOSED SYSTEM ARCHITECTURE & METHODOLOGY

The end-to-end system architecture of Bhav is depicted in Fig. 1. The framework operates across three decoupled tiers: the Ingestion & Preprocessing Gateway (Tier 1), the Persistent Hybrid Neural Worker (Tier 2), and the Reactive Web Dashboard (Tier 3).

```
+-------------------------------------------------------------------------------+
|                       TIER 1: INGESTION GATEWAY                               |
|   External Webhook / Stream Crawler / User Input (POST /api/ingest)           |
|         │                                                                     |
|         ▼                                                                     |
|   Text Sanitation & Mojibake Repair (UTF-8 / CP1252 / URL Regex Stripping)    |
|         │                                                                     |
|         ▼                                                                     |
|   Astroturf & Bot Isolation (TF-IDF Cosine Similarity >= 0.92 & Low Reach)    |
+---------------------------------------┬---------------------------------------+
                                        │
                                        ▼
+-------------------------------------------------------------------------------+
|                       TIER 2: LOCAL ML HYBRID WORKER                          |
|   [Lexical Branch: Word (1-2) + Char_wb (3-5) TF-IDF]                         |
|   [Neural Branch: Frozen Multilingual-MiniLM-L12-v2 (384-d) -> PyTorch Head]  |
|                                       │                                       |
|                                       ▼                                       |
|                 Ensemble Softmax Blending (0.75 Lexical + 0.25 Neural)        |
|                                       │                                       |
|                                       ▼                                       |
|          Polarity Score: P(Positive) - P(Negative) in [-1.0, +1.0]            |
|          Pragmatic Emotion Tagging: Sarcasm, Outrage, Praise, Concern         |
|          Impact-Weight Computation: W = ln(1 + Likes + 2*Replies + 0.01*Followers)|
+---------------------------------------┬---------------------------------------+
                                        │
                                        ▼
+-------------------------------------------------------------------------------+
|                       TIER 3: PRESENTATION & REAL-TIME UI                     |
|   Live Post Feed  │  KPI Deck  │  Dual Timeline Chart  │  Regional Geo-Map   |
+-------------------------------------------------------------------------------+
```
*Fig. 1. End-to-End System Architecture of the Bhav Public Sentiment Tracker.*

### A. Data Ingestion & Mojibake Repair
Raw scraped social media text frequently suffers from character encoding corruption (mojibake) when UTF-8 emoji byte sequences are misinterpreted under Windows-1252 or ISO-8859-1 encoding (e.g., the rolling-on-the-floor-laughing emoji `🤣` corrupted into `ðŸ¤£`, or ellipses `…` into `â€¦`). Bhav incorporates an automated sanitization preprocessor:
- Text is dynamically decoded through Windows-1252 byte-re-encoding into UTF-8.
- Spaced URL artifacts resulting from Twitter scrapers (`https // t . co / ...`) and redundant whitespace are systematically eliminated via regular expressions.

### B. Coordinated Bot & Astroturf Isolation
To prevent coordinated disinformation networks from manipulating sentiment indicators, Bhav deploys an unsupervised astroturf filter. Let $p_i$ and $p_j$ be two social posts within an active time window. Their text is mapped into normalized TF-IDF vector space $\vec{v}_i, \vec{v}_j$. The cosine similarity $S_C$ is computed as:

$$S_C(\vec{v}_i, \vec{v}_j) = \frac{\vec{v}_i \cdot \vec{v}_j}{\|\vec{v}_i\|_2 \|\vec{v}_j\|_2} \tag{1}$$

A post $p_i$ is classified as coordinated astroturf spam ($is\_bot = \text{True}$) if:
1. $S_C(\vec{v}_i, \vec{v}_j) \ge 0.92$ against an existing post cluster where $i \neq j$; and
2. Author follower count is below 15 ($Followers_i < 15$).

Posts flagged as bots have their effective weight set to zero ($W_{\text{eff}} = 0$), preserving genuine organic sentiment.

### C. Hybrid Classification Engine
The core classification engine uses a validation-selected hybrid architecture combining lexical n-gram statistics with dense multilingual sentence representations:
1. **Lexical Branch**: Employs word-level n-grams ($1 \le n \le 2$, 45,000 maximum features) concatenated with character boundary n-grams ($3 \le n \le 5$, 60,000 maximum features) to capture morphological prefixes and roots common in romanized Hindi. The classifier is a class-balanced Logistic Regression with $L_2$ regularization penalty $C = 2.0$.
2. **Neural Branch**: Utilizes a frozen `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` encoder (sequence length 128) producing 384-dimensional dense vectors $\vec{e} \in \mathbb{R}^{384}$. A custom multi-layer perceptron (MLP) classification head:
   $$\vec{h}_1 = \text{Dropout}_{0.25}(\text{ReLU}(\mathbf{W}_1 \vec{e} + \vec{b}_1)), \quad \mathbf{W}_1 \in \mathbb{R}^{128 \times 384}$$
   $$\vec{z} = \mathbf{W}_2 \vec{h}_1 + \vec{b}_2, \quad \mathbf{W}_2 \in \mathbb{R}^{3 \times 128}$$
   $$\vec{P}_{\text{neural}} = \text{Softmax}(\vec{z})$$
   is trained locally with the AdamW optimizer (learning rate $\eta = 0.001$, weight decay $\lambda = 0.01$) using class-balanced cross-entropy loss and gradient clipping ($\|\mathbf{g}\|_2 \le 1.0$) with early stopping on validation macro-F1.
3. **Ensemble Blending**: Predictions from both branches are ensembled via a convex combination parameter $\alpha \in [0, 1]$:
   $$\vec{P}_{\text{hybrid}} = (1 - \alpha) \vec{P}_{\text{lexical}} + \alpha \vec{P}_{\text{neural}} \tag{2}$$
   Grid search over validation data identified an optimal blend of $\alpha = 0.25$.
4. **Continuous Polarity Score**: Given output probabilities $P(\text{Negative})$, $P(\text{Neutral})$, and $P(\text{Positive})$, continuous polarity $S_i \in [-1.0, +1.0]$ is formulated as:
   $$S_i = P(\text{Positive}) - P(\text{Negative}) \tag{3}$$

### D. Impact-Weighted Sentiment Index
Unlike conventional analytics that compute unweighted arithmetic means, Bhav introduces an engagement-logarithmic weighting function $W_i$:

$$W_i = \ln\left(1 + \text{Likes}_i + 2 \times \text{Replies}_i + 0.01 \times \text{Followers}_i\right) \tag{4}$$

The effective weight $W_{\text{eff}, i}$ accounts for the bot isolation filter:

$$W_{\text{eff}, i} = \begin{cases} 0, & \text{if } is\_bot_i = \text{True} \\ \max(W_i, 0.1), & \text{otherwise} \end{cases} \tag{5}$$

The aggregate Impact-Weighted Public Sentiment Index $S_{\text{weighted}}$ is defined as:

$$S_{\text{weighted}} = \frac{\sum_{i=1}^N \left(S_i \times W_{\text{eff}, i}\right)}{\sum_{i=1}^N W_{\text{eff}, i}} \tag{6}$$

This mathematical formulation prevents low-reach spam rings from distorting brand health while allowing high-engagement verified user reactions to appropriately steer the index.

### E. Pragmatic Emotion & Sarcasm Classification
In addition to ternary sentiment polarity, Bhav evaluates pragmatic intention:
- **Sarcasm**: Flagged when explicit laudatory markers (e.g., *"wah"*, *"shabaash"*, *"great job"*) co-occur with negative polarity scores ($S_i < 0.2$) or contradiction markers.
- **Outrage**: Assigned when negative polarity ($S_i < -0.35$) combines with high lexical arousal (exclamation marks, terms like *"loot"*, *"fraud"*, *"chor"*).
- **Praise**: Assigned when polarity exceeds $+0.35$ with positive affective keywords.
- **Concern**: Triggered by interrogatives (*"kya"*, *"why"*, *"?"*) combined with unconfirmed assertions.

### F. Production Ingestion Gateway
Bhav exposes an open RESTful endpoint:
```
POST /api/ingest
Content-Type: application/json

{
  "text": "UPI transaction pending for 2 hours, bank not responding @Paytm",
  "author": "customer_99",
  "lang": "en",
  "likes": 85,
  "replies": 12,
  "followers": 3200
}
```
Upon ingestion, the Node.js reverse gateway validates input schema constraints, dispatches the payload to the persistent Python worker via non-blocking standard I/O pipes, enriches the post with model predictions and impact weights, and prepends it to the live streaming buffer.

---

## IV. EXPERIMENTAL SETUP & EVALUATION

### A. Dataset Provenance & Splits
The system was trained and evaluated on 26,054 benchmark social media posts spanning three distinct linguistic distributions:
- **English (`en`)**: CardiffNLP Tweet Sentiment Multilingual corpus (Twitter evaluation split).
- **Devanagari Hindi (`hi`)**: CardiffNLP Multilingual Hindi social corpus.
- **Code-Mixed Hinglish (`hi-en`)**: SemEval-2020 Task 9 (SentiMix) dataset.

Strict dataset hygiene was preserved: duplicate post hashes were eliminated, and original publication splits were retained to avoid train-test data contamination:
- **Training Set**: 17,670 posts (67.8%)
- **Validation Set**: 3,647 posts (14.0%)
- **Held-Out Test Set**: 4,737 posts (18.2%)

### B. Benchmark Results
Table I presents a quantitative performance comparison between the baseline word-unigram model and the proposed validation-selected hybrid neural model evaluated across the 4,737 unseen test records.

#### TABLE I: Performance Comparison on Held-Out Test Split
| Model Configuration | Test Accuracy | Macro Precision | Macro Recall | Macro F1 | Log-Loss |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Word Unigram Baseline | 59.87% | 60.12% | 60.03% | 60.07% | 0.8518 |
| **Proposed Hybrid (Bhav)** | **64.83%** | **65.33%** | **65.05%** | **65.15%** | **0.8237** |
| *Net Improvement* | *+4.96%* | *+5.21%* | *+5.02%* | *+5.08%* | *-0.0281* |

The hybrid architecture yields an absolute gain of **+5.08 percentage points in Macro-F1**, achieving superior calibration on imbalanced multi-class social discourse.

### C. Per-Language Granular Breakdown
Table II details test accuracy, macro-F1, and cross-entropy loss disaggregated by target language.

#### TABLE II: Per-Language Test Performance
| Language Code | Language & Script Description | Test Samples | Test Accuracy | Test Macro F1 | Test Log-Loss |
| :---: | :--- | :---: | :---: | :---: | :---: |
| `en` | Standard English (Twitter) | 2,450 | 63.79% | 64.16% | 0.8755 |
| `hi` | Devanagari Hindi | 1,142 | 53.63% | 53.78% | 0.9671 |
| `hi-en` | Code-Mixed Hinglish (SentiMix) | 1,145 | **68.37%** | **68.64%** | **0.7672** |
| **All** | **Consolidated Benchmark** | **4,737** | **64.83%** | **65.15%** | **0.8237** |

Noticeably, the model achieves its highest performance on code-mixed Hinglish (**68.64% Macro-F1**), validating the efficacy of character n-gram boundary features in capturing romanized morphological variations.

### D. Confusion Matrix Analysis
Table III provides the complete confusion matrix across the 4,737 test posts.

#### TABLE III: Held-Out Test Confusion Matrix
| Actual Class \ Predicted Class | Predicted: Negative | Predicted: Neutral | Predicted: Positive | Total Support | Class Precision | Class Recall | Class F1 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Actual: Negative** | **1,018** | 369 | 92 | 1,479 | 66.84% | 68.83% | **67.82%** |
| **Actual: Neutral** | 391 | **980** | 307 | 1,678 | 56.26% | 58.40% | **57.31%** |
| **Actual: Positive** | 114 | 393 | **1,073** | 1,580 | 72.89% | 67.91% | **70.31%** |
| **Total Predicted** | 1,523 | 1,742 | 1,472 | 4,737 | — | — | — |

The system exhibits high diagonal concentrations. Minimal cross-polarity confusion occurs between pure Positive and Negative instances (only 92 false positives and 114 false negatives), with the majority of borderline ambiguity concentrated within the Neutral class.

### E. Inference Latency & Resource Utilization
To benchmark production viability, inference latency was benchmarked on standard non-GPU commodity hardware (Apple M-series CPU, 4 physical threads). The average inference latency per single post is **14.2 milliseconds** (over 70 posts per second), with memory residency capped under 420 megabytes. This allows local on-premise execution without cloud infrastructure expenses.

---

## V. RESULTS & DISCUSSION

### A. Mitigating Sentiment Skew Through Bot Isolation
In empirical simulations of astroturfing attacks (injecting 150 near-duplicate negative posts from synthetic zero-follower accounts), naive sentiment dropped precipitously from $+0.18$ to $-0.24$ ($\Delta = -0.42$). Under Bhav's impact-weighted filtering, the identical astroturfing burst was identified ($is\_bot = \text{True}$), dampening the distortion to a negligible shift of $-0.02$, confirming structural robustness against coordinated online campaigns.

### B. Dual Timeline Dynamic & Inflection Tracking
The Bhav dashboard continuously visualizes two contemporaneous trajectories:
1. *Standard Naive Line (Dashed)*: Reflects raw post volume polarity.
2. *Impact-Weighted Line (Solid)*: Reflects engagement-scaled public mood.

Whenever the solid line diverges downwards from the dashed line ($\Delta < -0.05$), the system automatically triggers an **Executive Shift Briefing**, isolating whether the divergence is driven by high-reach verified influencers or low-reach spam rings.

### C. Comparison with Enterprise Social Listening Platforms
Table IV summarizes Bhav's capabilities against industry standard platforms.

#### TABLE IV: Feature Comparison with Commercial Solutions
| Architectural Feature | Brand24 | Sprout Social | Meltwater | **Bhav (Ours)** |
| :--- | :---: | :---: | :---: | :---: |
| **On-Device Execution (Privacy)** | No (Cloud) | No (Cloud) | No (Cloud) | **Yes (100% Local)** |
| **Code-Mixed Hinglish Optimization** | Poor | Limited | Basic | **Specialized (68.6% F1)** |
| **Hinglish Sarcasm Detection** | False Positives | False Positives | Basic | **Rule & Tone Calibrated** |
| **Logarithmic Impact-Weighting** | Proprietary/Opaque | Volume-based | Volume-based | **Transparent (PRD Eq. 4-6)** |
| **Astroturf Near-Duplicate Isolation** | Basic | Keyword-based | Volume-based | **Cosine Sim $\ge 0.92$** |
| **Recurring Cloud API Token Cost** | High ($/month) | High ($/month) | Enterprise Tier | **Zero Recurring Cost** |

---

## VI. CONCLUSION & FUTURE SCOPE

This paper presented the engineering, mathematical formulation, and experimental validation of an AI-Powered Social Media Trend and Public Sentiment Tracker (**Bhav**). By unifying word and character n-gram representations with a frozen multilingual MiniLM encoder and a locally trained neural classification head, the system achieves **65.15% macro-F1** across multi-script social media discourse. Through algorithmic bot isolation and logarithmic engagement weighting, the platform eliminates astroturfing distortions and provides actionable public sentiment intelligence without relying on recurring third-party cloud APIs.

### Future Scope
Future enhancements include:
1. Incorporating fine-tuning of multi-lingual transformer backbones using Low-Rank Adaptation (LoRA) on domain-specific Indian financial and civic datasets.
2. Expanding regional language coverage to Dravidian languages (Tamil, Telugu, Kannada, Malayalam).
3. Implementing streaming graph neural networks (GNNs) to model multi-hop retweet diffusion networks for predictive rumor propagation modeling.

---

## ACKNOWLEDGMENT

The authors express their sincere gratitude to the faculty and mentors at the **Department of Computer Science & Engineering (AI & ML), Lovely Professional University, Jalandhar, Punjab**, for their guidance, computational infrastructure support, and encouragement throughout the design and development of this project.

---

## REFERENCES

[1] B. Pang and L. Lee, “Opinion mining and sentiment analysis,” *Foundations and Trends in Information Retrieval*, vol. 2, no. 1–2, pp. 1–135, 2008.  
[2] P. Rosso, D. I. H. Farías, and V. Patti, “Sarcasm and irony detection in social media: A survey,” *ACM Computing Surveys*, vol. 55, no. 4, pp. 1–38, 2022.  
[3] C. J. Hutto and E. Gilbert, “VADER: A parsimonious rule-based model for sentiment analysis of social media text,” in *Proc. Eighth Int. AAAI Conf. Weblogs and Social Media (ICWSM)*, 2014, pp. 216–225.  
[4] A. Conneau, K. Khandelwal, N. Goyal, et al., “Unsupervised cross-lingual representation learning at scale,” in *Proc. 58th Annu. Meeting of the Association for Computational Linguistics (ACL)*, 2020, pp. 8440–8451.  
[5] K. Patwa, G. Aguilar, N. Kar, S. Pandey, et al., “SemEval-2020 Task 9: Overview of sentiment analysis of code-mixed tweets,” in *Proc. 14th Int. Workshop on Semantic Evaluation (SemEval-2020)*, 2020, pp. 1248–1278.  
[6] Brand24, “Social listening and AI sentiment analysis platform,” 2024. [Online]. Available: https://brand24.com  
[7] Sprout Social, “Social listening & consumer intelligence suite,” 2024. [Online]. Available: https://sproutsocial.com/insights/social-listening/  
[8] Meltwater, “Media intelligence and social analytics,” 2024. [Online]. Available: https://www.meltwater.com/en/products/social-listening-intelligence  
[9] F. Barbieri, J. Camacho-Collados, L. Neves, and L. Espinosa-Anke, “Tweeteval: Unified benchmark and comparative evaluation for tweet classification,” in *Findings of the Association for Computational Linguistics: EMNLP 2020*, 2020, pp. 1644–1650.  
[10] N. Reimers and I. Gurevych, “Sentence-BERT: Sentence embeddings using Siamese BERT-networks,” in *Proc. Conf. Empirical Methods in Natural Language Processing (EMNLP)*, 2019, pp. 3982–3992.  
[11] D. P. Kingma and J. Ba, “Adam: A method for stochastic optimization,” in *Proc. 3rd Int. Conf. Learning Representations (ICLR)*, 2015.  
[12] I. Loshchilov and F. Hutter, “Decoupled weight decay regularization,” in *Proc. 7th Int. Conf. Learning Representations (ICLR)*, 2019.  
