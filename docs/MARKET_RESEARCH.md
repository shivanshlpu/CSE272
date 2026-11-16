# Public feedback monitoring research

Research date: 16 November 2026. Vendor pages describe advertised capabilities, not independently measured quality. No pricing or accuracy superiority is inferred.

| Existing solution | Evidence from vendor | Consequence for Bhav |
| --- | --- | --- |
| Brandwatch Consumer Research | Sentiment and key topics in 44 languages; customizable dashboards, categories, mention tagging and threshold alerts. https://www.brandwatch.com/products/consumer-research/features/ | Multilingual sentiment, dashboards, alerts and human tagging are established features, not a novel contribution. |
| Sprout Social Listening | Topic and sentiment monitoring, trend analysis, conversation insights and relevant creator discovery. https://sproutsocial.com/insights/social-media-listening/ | A generic social listening dashboard is insufficient differentiation. |
| Sprout sentiment guidance | Lists sarcasm, negation, industry jargon, multilingual slang and bot-driven spikes as analysis challenges. https://sproutsocial.com/insights/social-media-sentiment-analysis/ | Validate domain/language behavior; do not claim sarcasm or bot detection without labelled evaluation. |

## Specialization hypotheses
1. **Claim-relative feedback for public communications.** Define an explicit initiative or claim and separately measure emotional tone and stance. An angry complaint about rollout may still support the initiative. This workflow is useful for policy feedback and public-event analysis, but competitors may support similar customization; absence is not established by their public pages.
2. **Hindi/Hinglish quality that can be inspected.** Publish per-language results, benchmark a held-out target, and retain analyst corrections. The current sentiment model supports these languages, but the new stance model has only English evaluation. A claimed multilingual stance advantage is not yet supported.
3. **Traceable findings with coverage context.** Each theme links a representative comment and a most-liked comment, discloses sampled videos/time windows, and separates observations from population-level conclusions. Evidence quality is the product focus, rather than maximizing unsupported counts or geographic displays.
4. **Operational transparency for small specialist teams.** Durable collection jobs, explicit API quotas, source errors, backfill state, sample limits and deletion retention are visible. This is a narrower deployable foundation, not a replacement for established platforms' licensed cross-network coverage.

## Intended users and decisions
- PR teams: review recurring service complaints, verify a change in negative share and prioritize issues supported by representative comments.
- Government communication offices: distinguish approval of a defined initiative from complaints about execution; use findings to improve public explanations or services, not infer personal political affiliation.
- Market researchers: compare observed themes and language-specific model errors across selected sources; record sampling limitations before interpreting a brand response.

## Implemented versus unproven
Implemented: persistent video monitors; official YouTube comment and search connector; source timestamps/likes/links; trained sentiment plus separately trained target-conditioned stance; semantic theme clustering; publication-date timeline; observed two-window change; analyst stance corrections; run/error/quota visibility; token protection for remote binding; retention and bounded processing.
Not demonstrated: authenticated live ingestion (no API key supplied); comprehensive platform coverage/replies; robust unseen-topic or Hindi/Hinglish stance; calibrated confidence; population representativeness; validated causal influence; crisis alert delivery; organizational SSO/RBAC; high-availability/multi-instance deployment or load/security certification.

## Prioritized validation
Obtain a consented or otherwise appropriately sourced, independently annotated target-specific test set across English, Hindi and Hinglish. Use two annotators, an adjudication process and target-held-out evaluation. Keep uncertain/off-topic labels distinct from explicit neutrality. Compare a fine-tuned multilingual cross-encoder against the current learned interaction model using unchanged held-out data. Accept improvements only when evaluation supports them. Do not generate a dataset to make reported performance look stronger.

## Primary technical sources
- YouTube commentThreads.list: pagination, 1–100 results, plain text, commentsDisabled, 1-unit request cost. https://developers.google.com/youtube/v3/docs/commentThreads/list
- YouTube search.list: search endpoints and quota. https://developers.google.com/youtube/v3/docs/search/list
- YouTube developer policies: storage freshness, privacy and permitted uses. https://developers.google.com/youtube/terms/developer-policies
- YouTube compliance guidance: derived data and user-sensitive inference restrictions; public deployment requires platform-specific review. https://developers.google.com/youtube/terms/developer-policies-guide
- TweetEval official repository: stance task, five targets and published partitions, upstream usage conditions. https://github.com/cardiffnlp/tweeteval

The public YouTube oEmbed response for the user's selected video identified an entertainment episode, not a government initiative. The first monitor therefore uses an entertainment-evaluation claim. Other use cases can be configured through the same monitor form.
