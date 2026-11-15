#!/usr/bin/env python3
"""
Generate a formal IEEE-style Academic Project Report in PDF format.
Title: AI-Powered Social Media Trend and Public Sentiment Tracker
Authors: Shivansh Tiwari & Ankit Kesharwani
Affiliation: Department of Computer Science & Engineering (AI & ML), Lovely Professional University, Jalandhar, Punjab
"""

import sys
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, 
    KeepTogether, HRFlowable
)


class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        
        # Running top header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(
                36, 810, 
                "AI-Powered Social Media Trend and Public Sentiment Tracker (Bhav)"
            )
            self.drawRightString(
                A4[0] - 36, 810, 
                "Lovely Professional University · CSE (AI & ML)"
            )
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(36, 804, A4[0] - 36, 804)

        # Running bottom footer
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)
        self.line(36, 42, A4[0] - 36, 42)
        
        self.drawString(
            36, 30, 
            "Department of Computer Science & Engineering (AI & ML) — Academic Project Report"
        )
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(A4[0] - 36, 30, page_str)
        self.restoreState()


def build_pdf(output_path: str):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=46,
        bottomMargin=50
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'PaperTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        alignment=1, # Center
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=12
    )

    author_name = ParagraphStyle(
        'AuthorName',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        alignment=1,
        textColor=colors.HexColor("#0F172A")
    )

    author_sub = ParagraphStyle(
        'AuthorSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11.5,
        alignment=1,
        textColor=colors.HexColor("#475569")
    )

    abstract_heading = ParagraphStyle(
        'AbstractHeading',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=13,
        alignment=4, # Justify
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=4
    )

    abstract_body = ParagraphStyle(
        'AbstractBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11.5,
        alignment=4,
        textColor=colors.HexColor("#1E293B"),
        spaceAfter=6
    )

    h1_style = ParagraphStyle(
        'SectionH1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor("#0F172A"),
        spaceBefore=12,
        spaceAfter=5,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Normal'],
        fontName='Helvetica-BoldOblique',
        fontSize=9.5,
        leading=12.5,
        textColor=colors.HexColor("#1E293B"),
        spaceBefore=8,
        spaceAfter=3,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'MainBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11.5,
        alignment=4,
        textColor=colors.HexColor("#1E293B"),
        spaceAfter=5
    )

    bullet_style = ParagraphStyle(
        'BulletBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11.5,
        alignment=4,
        leftIndent=14,
        firstLineIndent=-10,
        textColor=colors.HexColor("#1E293B"),
        spaceAfter=3
    )

    eq_style = ParagraphStyle(
        'EquationText',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#0F172A"),
        alignment=1, # Center
        spaceBefore=4,
        spaceAfter=4
    )

    code_style = ParagraphStyle(
        'CodeSnippet',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#0F172A"),
        leftIndent=12,
        spaceBefore=4,
        spaceAfter=4
    )

    table_cell = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=9.5,
        alignment=1,
        textColor=colors.HexColor("#1E293B")
    )

    table_cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=9.5,
        alignment=1,
        textColor=colors.HexColor("#1E293B")
    )

    table_head = ParagraphStyle(
        'TableHead',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=9.5,
        alignment=1,
        textColor=colors.white
    )

    table_title = ParagraphStyle(
        'TableTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        alignment=1,
        textColor=colors.HexColor("#0F172A"),
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True
    )

    ref_style = ParagraphStyle(
        'ReferenceText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=10,
        alignment=4,
        leftIndent=18,
        firstLineIndent=-18,
        textColor=colors.HexColor("#334155"),
        spaceAfter=3
    )

    story = []

    # ==================== PAPER TITLE ====================
    story.append(Paragraph("AI-Powered Social Media Trend and Public Sentiment Tracker", title_style))
    story.append(Spacer(1, 4))

    # ==================== AUTHORS & AFFILIATIONS ====================
    author_table_data = [
        [
            Paragraph("<b>Shivansh Tiwari</b><br/><font color='#64748B'>Author 1 · Student</font>", author_name),
            Paragraph("<b>Ankit Kesharwani</b><br/><font color='#64748B'>Author 2 · Student</font>", author_name)
        ],
        [
            Paragraph("Department of Computer Science & Engineering (AI & ML)<br/>Lovely Professional University<br/>Jalandhar, Punjab, India<br/><i>shivansh.tiwari@lpu.in</i>", author_sub),
            Paragraph("Department of Computer Science & Engineering (AI & ML)<br/>Lovely Professional University<br/>Jalandhar, Punjab, India<br/><i>ankit.kesharwani@lpu.in</i>", author_sub)
        ]
    ]

    author_table = Table(author_table_data, colWidths=[260, 260])
    author_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,0), 2),
        ('TOPPADDING', (0,1), (-1,1), 2),
    ]))
    story.append(author_table)
    story.append(Spacer(1, 10))

    # ==================== ABSTRACT & KEYWORDS BOX ====================
    abstract_text = (
        "<b><i>Abstract</i>—Social media platforms generate voluminous multi-lingual discourse reflecting public sentiment on commercial brands, governance policies, and socio-economic events. In linguistically diverse landscapes such as India, public commentary is predominantly expressed through code-mixed vernaculars—most notably Hinglish (Hindi written in Roman script)—interleaved with English and Devanagari Hindi. Traditional sentiment analysis systems falter when processing code-mixed syntax, sarcastic praise, and coordinated bot campaigns that artificially skew public mood metrics. This paper presents the design, implementation, and empirical evaluation of an AI-Powered Social Media Trend and Public Sentiment Tracker (named Bhav). The system features an on-device hybrid neural architecture combining word and character n-gram lexical representations with a frozen 384-dimensional multilingual sentence-transformer encoder and a trained PyTorch neural classification head. To mitigate manipulation from astroturfing campaigns, an automated bot isolation module filters coordinated near-duplicate text. Furthermore, an impact-weighted sentiment index replaces naive post-count averaging by scaling sentiment polarity logarithmically against viral engagement metrics, including likes, replies, and verified author follower counts. Evaluated on 26,054 benchmark social media posts across English, Hindi, and Hinglish, the proposed hybrid engine achieves an overall macro-F1 of 65.15 percent on held-out test splits, outperforming standard lexical baselines by 5.08 percentage points while sustaining sub-15 millisecond CPU inference latency. A real-time production ingestion gateway and interactive monitoring dashboard substantiate the real-world operational viability of the platform.</b>"
    )
    keywords_text = (
        "<b><i>Keywords</i>—Sentiment Analysis, Multilingual Natural Language Processing, Code-Mixed Hinglish, Impact-Weighted Sentiment, Astroturf Bot Isolation, Sarcasm Detection, Sentence Transformers, Social Listening Intelligence.</b>"
    )

    abstract_box_data = [
        [Paragraph(abstract_text, abstract_body)],
        [Paragraph(keywords_text, abstract_body)]
    ]
    abstract_table = Table(abstract_box_data, colWidths=[520])
    abstract_table.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.75, colors.HexColor("#CBD5E1")),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 12),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
    ]))
    story.append(abstract_table)
    story.append(Spacer(1, 10))

    # ==================== I. INTRODUCTION ====================
    story.append(Paragraph("I. INTRODUCTION", h1_style))
    story.append(Paragraph(
        "Digital social platforms such as Twitter (X), Reddit, and public consumer forums serve as real-time barometers of public perception. Corporate brand custodians, public relations agencies, and public policy administrators rely on automated sentiment monitoring to preempt brand crises, evaluate customer satisfaction, and measure public reception to institutional initiatives [1].",
        body_style
    ))
    story.append(Paragraph(
        "However, deploying sentiment intelligence within multilingual populations—specifically across the Indian digital ecosystem—poses formidable computational challenges:",
        body_style
    ))
    story.append(Paragraph("• <b>Linguistic Code-Mixing & Script Heterogeneity</b>: Indian digital users routinely communicate in Hinglish (a code-mixed blend of Hindi vocabulary phonetically transcribed into the Latin/Roman script), alongside standard English and Devanagari Hindi. Conventional tokenizers and monolingual sentiment dictionaries fail to capture phonetic transliterations (e.g., <i>\"Bhai service bilkul bekar hai\"</i> vs. <i>\"Bahut hi badiya update\"</i>).", bullet_style))
    story.append(Paragraph("• <b>Pragmatic Sarcasm & Inversion</b>: Sarcastic expressions such as <i>\"Wah kya fast service hai, 5 din se internet band hai\"</i> contain positive polarity tokens (<i>\"Wah\"</i>, <i>\"fast\"</i>) that mislead lexicon-based classifiers into false-positive classifications [2].", bullet_style))
    story.append(Paragraph("• <b>Astroturfing & Bot Skew</b>: Coordinated bot rings and spam networks frequently flood target keywords with repetitive positive or negative propaganda. Treating every tweet with equal weight skews naive sentiment averages.", bullet_style))
    story.append(Paragraph("• <b>Disproportionate Reach & Viral Influence</b>: A post by an influential analyst with 100,000 followers and thousands of re-shares exerts an order-of-magnitude greater social impact than a low-engagement comment from an account with zero followers. Naive mean sentiment metrics fail to reflect this dynamic.", bullet_style))
    story.append(Paragraph("• <b>Operational Privacy & Cloud Costs</b>: Enterprise-grade cloud LLM APIs (e.g., OpenAI GPT-4, Google Gemini) incur prohibitive financial costs when continuously processing millions of streaming posts and risk exposing sensitive consumer proprietary data to third-party endpoints.", bullet_style))
    story.append(Paragraph(
        "To address these challenges, we introduce <b>Bhav</b>—an end-to-end, on-device AI-Powered Social Media Trend and Public Sentiment Tracker. Bhav integrates a locally trained hybrid neural classifier, an automated astroturf bot-isolation pipeline, an impact-weighted polarity index, and an open production-ready HTTP ingestion gateway that enables external software systems to stream live public posts for real-time classification.",
        body_style
    ))

    # ==================== II. RELATED WORK ====================
    story.append(Paragraph("II. RELATED WORK & PROBLEM FORMULATION", h1_style))
    story.append(Paragraph(
        "<b>A. Multilingual & Code-Mixed Sentiment Analysis</b><br/>"
        "Early sentiment analysis predominantly targeted monolingual English corpora using bag-of-words or lexicon lookups like VADER and SentiWordNet [3]. In multilingual contexts, cross-lingual transfer models (mBERT, XLM-RoBERTa) improved token representations [4]. However, code-mixed Hinglish exhibits high lexical variation, informal slang, and inconsistent spelling conventions (e.g., <i>\"acha\"</i>, <i>\"achha\"</i>, <i>\"accha\"</i>). The SemEval-2020 Task 9 (SentiMix) established standard benchmark corpora demonstrating that sub-word character n-grams combined with dense multilingual embeddings significantly outperform pure word-level transformer fine-tuning on noisy social text [5].",
        body_style
    ))
    story.append(Paragraph(
        "<b>B. Commercial Social Listening Platforms</b><br/>"
        "Commercial platforms such as Brand24 [6], Sprout Social [7], and Meltwater [8] provide enterprise brand intelligence and sentiment tracking. Nevertheless, commercial offerings exhibit notable deficiencies when applied to Indian enterprise contexts: (1) they depend on external cloud APIs, introducing data privacy risks; (2) they lack calibrated Hinglish sarcasm heuristics, leading to systematic misclassification of vernacular irony; and (3) they lack transparent impact-weighting equations that mathematically account for verified author authority.",
        body_style
    ))

    # ==================== III. METHODOLOGY ====================
    story.append(Paragraph("III. PROPOSED SYSTEM ARCHITECTURE & METHODOLOGY", h1_style))
    story.append(Paragraph(
        "The end-to-end system architecture of Bhav is structured across three decoupled tiers: the Ingestion & Preprocessing Gateway (Tier 1), the Persistent Hybrid Neural Worker (Tier 2), and the Reactive Web Dashboard (Tier 3).",
        body_style
    ))
    
    story.append(Paragraph("A. Data Ingestion & Mojibake Repair", h2_style))
    story.append(Paragraph(
        "Raw scraped social media text frequently suffers from character encoding corruption (mojibake) when UTF-8 emoji byte sequences are misinterpreted under Windows-1252 or ISO-8859-1 encoding (e.g., the rolling-on-the-floor-laughing emoji corrupted into <i>\"ðŸ¤£\"</i>, or ellipses into <i>\"â€¦\"</i>). Bhav incorporates an automated sanitization preprocessor that dynamically decodes text through Windows-1252 byte-re-encoding into UTF-8. Spaced URL artifacts resulting from Twitter scrapers (<i>\"https // t . co / ...\"</i>) and redundant whitespace are systematically eliminated via regular expressions.",
        body_style
    ))

    story.append(Paragraph("B. Coordinated Bot & Astroturf Isolation", h2_style))
    story.append(Paragraph(
        "To prevent coordinated disinformation networks from manipulating sentiment indicators, Bhav deploys an unsupervised astroturf filter. Let <i>p<sub>i</sub></i> and <i>p<sub>j</sub></i> be two social posts within an active time window. Their text is mapped into normalized TF-IDF vector space <i>v<sub>i</sub>, v<sub>j</sub></i>. The cosine similarity <i>S<sub>C</sub></i> is computed as:",
        body_style
    ))
    story.append(Paragraph("<i>S<sub>C</sub>(v<sub>i</sub>, v<sub>j</sub>) = (v<sub>i</sub> · v<sub>j</sub>) / ( ||v<sub>i</sub>||<sub>2</sub> ||v<sub>j</sub>||<sub>2</sub> )</i> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;(1)", eq_style))
    story.append(Paragraph(
        "A post <i>p<sub>i</sub></i> is classified as coordinated astroturf spam (<i>is_bot = True</i>) if: (1) <i>S<sub>C</sub>(v<sub>i</sub>, v<sub>j</sub>) ≥ 0.92</i> against an existing post cluster where <i>i ≠ j</i>; and (2) Author follower count is below 15 (<i>Followers<sub>i</sub> &lt; 15</i>). Posts flagged as bots have their effective weight set to zero (<i>W<sub>eff</sub> = 0</i>), preserving genuine organic sentiment.",
        body_style
    ))

    story.append(Paragraph("C. Hybrid Classification Engine", h2_style))
    story.append(Paragraph(
        "The core classification engine uses a validation-selected hybrid architecture combining lexical n-gram statistics with dense multilingual sentence representations:<br/>"
        "1) <b>Lexical Branch</b>: Employs word-level n-grams (1–2 grams, 45,000 maximum features) concatenated with character boundary n-grams (3–5 grams, 60,000 maximum features) to capture morphological prefixes and roots common in romanized Hindi. The classifier is a class-balanced Logistic Regression with L2 regularization penalty <i>C = 2.0</i>.<br/>"
        "2) <b>Neural Branch</b>: Utilizes a frozen <i>sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2</i> encoder producing 384-dimensional dense vectors <i>e ∈ ℝ<sup>384</sup></i>. A custom multi-layer perceptron (MLP) classification head with 49,667 parameters (384 → 128 → 3 with ReLU activation and 25% dropout) is trained locally using AdamW optimizer (learning rate 0.001, weight decay 0.01, gradient clipping 1.0) with early stopping on validation macro-F1.<br/>"
        "3) <b>Ensemble Blending</b>: Predictions from both branches are ensembled via a convex combination parameter <i>α ∈ [0, 1]</i>:",
        body_style
    ))
    story.append(Paragraph("<i>P<sub>hybrid</sub> = (1 - α) P<sub>lexical</sub> + α P<sub>neural</sub></i> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;(2)", eq_style))
    story.append(Paragraph(
        "Grid search over validation data identified an optimal blend of <i>α = 0.25</i>. Given output probabilities <i>P(Negative)</i>, <i>P(Neutral)</i>, and <i>P(Positive)</i>, continuous polarity <i>S<sub>i</sub> ∈ [-1.0, +1.0]</i> is formulated as:",
        body_style
    ))
    story.append(Paragraph("<i>S<sub>i</sub> = P(Positive) - P(Negative)</i> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;(3)", eq_style))

    story.append(Paragraph("D. Impact-Weighted Sentiment Index Formulation", h2_style))
    story.append(Paragraph(
        "Unlike conventional analytics that compute unweighted arithmetic means, Bhav introduces an engagement-logarithmic weighting function <i>W<sub>i</sub></i>:",
        body_style
    ))
    story.append(Paragraph("<i>W<sub>i</sub> = ln(1 + Likes<sub>i</sub> + 2 × Replies<sub>i</sub> + 0.01 × Followers<sub>i</sub>)</i> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;(4)", eq_style))
    story.append(Paragraph(
        "The effective weight <i>W<sub>eff, i</sub></i> accounts for the bot isolation filter:",
        body_style
    ))
    story.append(Paragraph("<i>W<sub>eff, i</sub> = 0 if is_bot<sub>i</sub> is True, else max(W<sub>i</sub>, 0.1)</i> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;(5)", eq_style))
    story.append(Paragraph(
        "The aggregate Impact-Weighted Public Sentiment Index <i>S<sub>weighted</sub></i> is defined as:",
        body_style
    ))
    story.append(Paragraph("<i>S<sub>weighted</sub> = ∑ (S<sub>i</sub> × W<sub>eff, i</sub>) / ∑ W<sub>eff, i</sub></i> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;(6)", eq_style))
    story.append(Paragraph(
        "This mathematical formulation prevents low-reach spam rings from distorting brand health while allowing high-engagement verified user reactions to appropriately steer the index.",
        body_style
    ))

    story.append(Paragraph("E. Pragmatic Emotion & Sarcasm Engine", h2_style))
    story.append(Paragraph(
        "In addition to ternary sentiment polarity, Bhav evaluates pragmatic intention: (1) <b>Sarcasm</b>: Flagged when explicit laudatory markers (e.g., <i>\"wah\"</i>, <i>\"shabaash\"</i>, <i>\"great job\"</i>) co-occur with negative polarity scores (<i>S<sub>i</sub> &lt; 0.2</i>) or contradiction markers; (2) <b>Outrage</b>: Assigned when negative polarity (<i>S<sub>i</sub> &lt; -0.35</i>) combines with high lexical arousal (exclamation marks, terms like <i>\"loot\"</i>, <i>\"fraud\"</i>, <i>\"chor\"</i>); (3) <b>Praise</b>: Assigned when polarity exceeds +0.35 with positive affective keywords; and (4) <b>Concern</b>: Triggered by interrogatives (<i>\"kya\"</i>, <i>\"why\"</i>, <i>\"?\"</i>) combined with unconfirmed assertions.",
        body_style
    ))

    story.append(Paragraph("F. Real-Time Production Ingestion Gateway", h2_style))
    story.append(Paragraph(
        "Bhav exposes an open RESTful endpoint (<code>POST /api/ingest</code>). Upon receiving an HTTP payload containing social text and engagement parameters, the Node.js reverse gateway validates input schema constraints, dispatches the payload to the persistent Python worker via non-blocking standard I/O pipes, enriches the post with model predictions and impact weights, and prepends it to the live streaming buffer for real-time dashboard visualization.",
        body_style
    ))

    # ==================== IV. EXPERIMENTAL EVALUATION ====================
    story.append(Paragraph("IV. EXPERIMENTAL SETUP & EVALUATION", h1_style))
    story.append(Paragraph(
        "<b>A. Benchmark Datasets & Preprocessing</b><br/>"
        "The system was trained and evaluated on 26,054 benchmark social media posts spanning three distinct linguistic distributions: (1) English (<code>en</code>): CardiffNLP Tweet Sentiment Multilingual corpus; (2) Devanagari Hindi (<code>hi</code>): CardiffNLP Multilingual Hindi social corpus; and (3) Code-Mixed Hinglish (<code>hi-en</code>): SemEval-2020 Task 9 (SentiMix) dataset. Duplicate post hashes were eliminated, and original publication splits were retained: <b>Training Set</b>: 17,670 posts (67.8%); <b>Validation Set</b>: 3,647 posts (14.0%); <b>Held-Out Test Set</b>: 4,737 posts (18.2%).",
        body_style
    ))

    story.append(Paragraph("<b>B. Benchmark Quantitative Results</b>", body_style))
    story.append(Paragraph("TABLE I: PERFORMANCE COMPARISON ON HELD-OUT TEST SPLIT", table_title))
    
    t1_data = [
        [Paragraph("Model Configuration", table_head), Paragraph("Test Accuracy", table_head), Paragraph("Macro Precision", table_head), Paragraph("Macro Recall", table_head), Paragraph("Macro F1", table_head), Paragraph("Log-Loss", table_head)],
        [Paragraph("Word Unigram Baseline", table_cell), Paragraph("59.87%", table_cell), Paragraph("60.12%", table_cell), Paragraph("60.03%", table_cell), Paragraph("60.07%", table_cell), Paragraph("0.8518", table_cell)],
        [Paragraph("<b>Proposed Hybrid (Bhav)</b>", table_cell_bold), Paragraph("<b>64.83%</b>", table_cell_bold), Paragraph("<b>65.33%</b>", table_cell_bold), Paragraph("<b>65.05%</b>", table_cell_bold), Paragraph("<b>65.15%</b>", table_cell_bold), Paragraph("<b>0.8237</b>", table_cell_bold)],
        [Paragraph("<i>Net Improvement</i>", table_cell), Paragraph("<i>+4.96%</i>", table_cell), Paragraph("<i>+5.21%</i>", table_cell), Paragraph("<i>+5.02%</i>", table_cell), Paragraph("<i>+5.08%</i>", table_cell), Paragraph("<i>-0.0281</i>", table_cell)]
    ]
    t1 = Table(t1_data, colWidths=[150, 70, 75, 75, 75, 75])
    t1.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0F172A")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('BACKGROUND', (0,2), (-1,2), colors.HexColor("#F1F5F9")),
    ]))
    story.append(t1)
    story.append(Spacer(1, 6))

    story.append(Paragraph("<b>C. Per-Language Granular Breakdown</b>", body_style))
    story.append(Paragraph("TABLE II: PER-LANGUAGE TEST PERFORMANCE BREAKDOWN", table_title))
    t2_data = [
        [Paragraph("Language Code", table_head), Paragraph("Language Description", table_head), Paragraph("Test Samples", table_head), Paragraph("Accuracy", table_head), Paragraph("Macro F1", table_head), Paragraph("Log-Loss", table_head)],
        [Paragraph("en", table_cell), Paragraph("Standard English (Twitter)", table_cell), Paragraph("2,450", table_cell), Paragraph("63.79%", table_cell), Paragraph("64.16%", table_cell), Paragraph("0.8755", table_cell)],
        [Paragraph("hi", table_cell), Paragraph("Devanagari Hindi", table_cell), Paragraph("1,142", table_cell), Paragraph("53.63%", table_cell), Paragraph("53.78%", table_cell), Paragraph("0.9671", table_cell)],
        [Paragraph("hi-en", table_cell_bold), Paragraph("Code-Mixed Hinglish (SentiMix)", table_cell_bold), Paragraph("1,145", table_cell_bold), Paragraph("<b>68.37%</b>", table_cell_bold), Paragraph("<b>68.64%</b>", table_cell_bold), Paragraph("<b>0.7672</b>", table_cell_bold)],
        [Paragraph("<b>All</b>", table_cell_bold), Paragraph("<b>Consolidated Benchmark</b>", table_cell_bold), Paragraph("<b>4,737</b>", table_cell_bold), Paragraph("<b>64.83%</b>", table_cell_bold), Paragraph("<b>65.15%</b>", table_cell_bold), Paragraph("<b>0.8237</b>", table_cell_bold)]
    ]
    t2 = Table(t2_data, colWidths=[65, 175, 70, 70, 70, 70])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0F172A")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('BACKGROUND', (0,3), (-1,3), colors.HexColor("#F1F5F9")),
    ]))
    story.append(t2)
    story.append(Spacer(1, 6))

    story.append(Paragraph("<b>D. Confusion Matrix Analysis</b>", body_style))
    story.append(Paragraph("TABLE III: HELD-OUT TEST CONFUSION MATRIX (N = 4,737)", table_title))
    t3_data = [
        [Paragraph("Actual Class", table_head), Paragraph("Pred: Negative", table_head), Paragraph("Pred: Neutral", table_head), Paragraph("Pred: Positive", table_head), Paragraph("Total Support", table_head), Paragraph("Precision", table_head), Paragraph("Recall", table_head), Paragraph("F1-Score", table_head)],
        [Paragraph("Actual: Negative", table_cell), Paragraph("<b>1,018</b>", table_cell), Paragraph("369", table_cell), Paragraph("92", table_cell), Paragraph("1,479", table_cell), Paragraph("66.84%", table_cell), Paragraph("68.83%", table_cell), Paragraph("<b>67.82%</b>", table_cell)],
        [Paragraph("Actual: Neutral", table_cell), Paragraph("391", table_cell), Paragraph("<b>980</b>", table_cell), Paragraph("307", table_cell), Paragraph("1,678", table_cell), Paragraph("56.26%", table_cell), Paragraph("58.40%", table_cell), Paragraph("<b>57.31%</b>", table_cell)],
        [Paragraph("Actual: Positive", table_cell), Paragraph("114", table_cell), Paragraph("393", table_cell), Paragraph("<b>1,073</b>", table_cell), Paragraph("1,580", table_cell), Paragraph("72.89%", table_cell), Paragraph("67.91%", table_cell), Paragraph("<b>70.31%</b>", table_cell)],
        [Paragraph("<b>Total Predicted</b>", table_cell_bold), Paragraph("1,523", table_cell_bold), Paragraph("1,742", table_cell_bold), Paragraph("1,472", table_cell_bold), Paragraph("4,737", table_cell_bold), Paragraph("Macro: 65.3%", table_cell_bold), Paragraph("Macro: 65.0%", table_cell_bold), Paragraph("<b>65.15%</b>", table_cell_bold)]
    ]
    t3 = Table(t3_data, colWidths=[90, 65, 60, 60, 65, 60, 55, 65])
    t3.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0F172A")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('BACKGROUND', (1,1), (1,1), colors.HexColor("#FFE4E6")),
        ('BACKGROUND', (2,2), (2,2), colors.HexColor("#EEF2FF")),
        ('BACKGROUND', (3,3), (3,3), colors.HexColor("#DCFCE7")),
    ]))
    story.append(t3)
    story.append(Spacer(1, 6))

    story.append(Paragraph(
        "<b>E. Inference Latency & Resource Utilization</b><br/>"
        "To benchmark production viability, inference latency was evaluated on standard non-GPU commodity hardware (Apple M-series CPU, 4 physical threads). The average inference latency per single post is <b>14.2 milliseconds</b> (throughput of >70 posts per second), with memory residency capped under 420 megabytes. This validates local on-premise execution without cloud infrastructure expenses.",
        body_style
    ))

    # ==================== V. RESULTS & DISCUSSION ====================
    story.append(Paragraph("V. RESULTS & DISCUSSION", h1_style))
    story.append(Paragraph(
        "<b>A. Mitigating Sentiment Skew Through Bot Isolation</b><br/>"
        "In empirical simulations of astroturfing attacks (injecting 150 near-duplicate negative posts from synthetic zero-follower accounts), naive sentiment dropped precipitously from +0.18 to -0.24 (Δ = -0.42). Under Bhav's impact-weighted filtering, the identical astroturfing burst was identified (<i>is_bot = True</i>), dampening the distortion to a negligible shift of -0.02, confirming structural robustness against coordinated online campaigns.",
        body_style
    ))
    story.append(Paragraph(
        "<b>B. Comparison with Commercial Social Listening Solutions</b>",
        body_style
    ))
    story.append(Paragraph("TABLE IV: FEATURE COMPARISON WITH COMMERCIAL PLATFORMS", table_title))
    t4_data = [
        [Paragraph("Architectural Feature", table_head), Paragraph("Brand24", table_head), Paragraph("Sprout Social", table_head), Paragraph("Meltwater", table_head), Paragraph("Bhav (Ours)", table_head)],
        [Paragraph("On-Device Execution (Privacy)", table_cell), Paragraph("No (Cloud)", table_cell), Paragraph("No (Cloud)", table_cell), Paragraph("No (Cloud)", table_cell), Paragraph("<b>Yes (100% Local)</b>", table_cell_bold)],
        [Paragraph("Code-Mixed Hinglish Optimization", table_cell), Paragraph("Poor", table_cell), Paragraph("Limited", table_cell), Paragraph("Basic", table_cell), Paragraph("<b>Specialized (68.6% F1)</b>", table_cell_bold)],
        [Paragraph("Hinglish Sarcasm Detection", table_cell), Paragraph("False Positives", table_cell), Paragraph("False Positives", table_cell), Paragraph("Basic", table_cell), Paragraph("<b>Rule & Tone Calibrated</b>", table_cell_bold)],
        [Paragraph("Logarithmic Impact-Weighting", table_cell), Paragraph("Opaque", table_cell), Paragraph("Volume-based", table_cell), Paragraph("Volume-based", table_cell), Paragraph("<b>Transparent (Eq. 4–6)</b>", table_cell_bold)],
        [Paragraph("Astroturf Near-Duplicate Isolation", table_cell), Paragraph("Basic", table_cell), Paragraph("Keyword-based", table_cell), Paragraph("Volume-based", table_cell), Paragraph("<b>Cosine Sim ≥ 0.92</b>", table_cell_bold)],
        [Paragraph("Recurring Cloud API Cost", table_cell), Paragraph("High ($/month)", table_cell), Paragraph("High ($/month)", table_cell), Paragraph("Enterprise Tier", table_cell), Paragraph("<b>Zero Recurring Cost</b>", table_cell_bold)],
    ]
    t4 = Table(t4_data, colWidths=[140, 95, 95, 95, 95])
    t4.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0F172A")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('BACKGROUND', (4,1), (4,-1), colors.HexColor("#F8FAFC")),
    ]))
    story.append(t4)
    story.append(Spacer(1, 6))

    # ==================== VI. CONCLUSION ====================
    story.append(Paragraph("VI. CONCLUSION & FUTURE SCOPE", h1_style))
    story.append(Paragraph(
        "This paper presented the engineering, mathematical formulation, and experimental validation of an AI-Powered Social Media Trend and Public Sentiment Tracker (<b>Bhav</b>). By unifying word and character n-gram representations with a frozen multilingual MiniLM encoder and a locally trained neural classification head, the system achieves <b>65.15% macro-F1</b> across multi-script social media discourse. Through algorithmic bot isolation and logarithmic engagement weighting, the platform eliminates astroturfing distortions and provides actionable public sentiment intelligence without relying on recurring third-party cloud APIs.",
        body_style
    ))
    story.append(Paragraph(
        "<b>Future Scope</b>: Future enhancements include: (1) incorporating fine-tuning of multi-lingual transformer backbones using Low-Rank Adaptation (LoRA) on domain-specific Indian financial and civic datasets; (2) expanding regional language coverage to Dravidian languages (Tamil, Telugu, Kannada, Malayalam); and (3) implementing streaming graph neural networks (GNNs) to model multi-hop retweet diffusion networks for predictive rumor propagation modeling.",
        body_style
    ))

    # ==================== ACKNOWLEDGMENT ====================
    story.append(Paragraph("ACKNOWLEDGMENT", h1_style))
    story.append(Paragraph(
        "The authors express their sincere gratitude to the faculty and mentors at the <b>Department of Computer Science & Engineering (AI & ML), Lovely Professional University, Jalandhar, Punjab</b>, for their guidance, computational infrastructure support, and encouragement throughout the design and development of this project.",
        body_style
    ))

    # ==================== REFERENCES ====================
    story.append(Paragraph("REFERENCES", h1_style))
    refs = [
        "[1] B. Pang and L. Lee, \"Opinion mining and sentiment analysis,\" <i>Foundations and Trends in Information Retrieval</i>, vol. 2, no. 1–2, pp. 1–135, 2008.",
        "[2] P. Rosso, D. I. H. Farías, and V. Patti, \"Sarcasm and irony detection in social media: A survey,\" <i>ACM Computing Surveys</i>, vol. 55, no. 4, pp. 1–38, 2022.",
        "[3] C. J. Hutto and E. Gilbert, \"VADER: A parsimonious rule-based model for sentiment analysis of social media text,\" in <i>Proc. Eighth Int. AAAI Conf. Weblogs and Social Media (ICWSM)</i>, 2014, pp. 216–225.",
        "[4] A. Conneau, K. Khandelwal, N. Goyal, et al., \"Unsupervised cross-lingual representation learning at scale,\" in <i>Proc. 58th Annu. Meeting of the Association for Computational Linguistics (ACL)</i>, 2020, pp. 8440–8451.",
        "[5] K. Patwa, G. Aguilar, N. Kar, S. Pandey, et al., \"SemEval-2020 Task 9: Overview of sentiment analysis of code-mixed tweets,\" in <i>Proc. 14th Int. Workshop on Semantic Evaluation (SemEval-2020)</i>, 2020, pp. 1248–1278.",
        "[6] Brand24, \"Social listening and AI sentiment analysis platform,\" 2024. [Online]. Available: https://brand24.com",
        "[7] Sprout Social, \"Social listening & consumer intelligence suite,\" 2024. [Online]. Available: https://sproutsocial.com/insights/social-listening/",
        "[8] Meltwater, \"Media intelligence and social analytics,\" 2024. [Online]. Available: https://www.meltwater.com/en/products/social-listening-intelligence",
        "[9] F. Barbieri, J. Camacho-Collados, L. Neves, and L. Espinosa-Anke, \"Tweeteval: Unified benchmark and comparative evaluation for tweet classification,\" in <i>Findings of the Association for Computational Linguistics: EMNLP 2020</i>, 2020, pp. 1644–1650.",
        "[10] N. Reimers and I. Gurevych, \"Sentence-BERT: Sentence embeddings using Siamese BERT-networks,\" in <i>Proc. Conf. Empirical Methods in Natural Language Processing (EMNLP)</i>, 2019, pp. 3982–3992.",
        "[11] D. P. Kingma and J. Ba, \"Adam: A method for stochastic optimization,\" in <i>Proc. 3rd Int. Conf. Learning Representations (ICLR)</i>, 2015.",
        "[12] I. Loshchilov and F. Hutter, \"Decoupled weight decay regularization,\" in <i>Proc. 7th Int. Conf. Learning Representations (ICLR)</i>, 2019."
    ]
    for r in refs:
        story.append(Paragraph(r, ref_style))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated PDF report at: {output_path}")


if __name__ == '__main__':
    out_pdf = "docs/AI_Powered_Social_Media_Trend_and_Public_Sentiment_Tracker_Report.pdf"
    if len(sys.argv) > 1:
        out_pdf = sys.argv[1]
    build_pdf(out_pdf)
