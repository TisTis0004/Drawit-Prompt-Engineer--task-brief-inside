# Module B — Token Optimization

## What I Changed and Why

The goal was to reduce the input prompt by at least 30% while preserving schema adherence, parent-safe tone, and psychological depth.

**Starting point:** v1_original — 1374 tokens (system.txt + schema.json)
**Result:** v3_optimized — 940 tokens (31.6% reduction)

The optimization strategy was to collapse instructional prose into dense bullet notation while keeping every rule that maps to observable model behavior. The sections I targeted fell into two categories: (1) verbose tone instructions that repeat the same guidance in different words, and (2) illustrative examples that help a human reader but are redundant for a capable LLM.

**What was removed:**
- The ROLE section's three-sentence biographical setup was compressed to one line — the model doesn't need a backstory to perform the task
- The AUDIENCE section's tone list had sub-bullets ("Warm, but never sycophantic") that were expanded into prose. Collapsed to 4 bullets with `·` separators
- Lowenfeld's full stage list with age ranges takes ~50 tokens but only 2 stages matter for an 8-year-old: schematic (current) and dawning realism (approaching). The others were removed
- Concrete recommendation examples ("Continue inviting open conversation…") were helpful in v1 but the model produces appropriate recommendations without them
- The Good/Bad title examples and the OUTPUT FORMAT multi-sentence paragraph were reduced to 1-line instructions

**What was kept:**
- The mood convergence rule: "Use 'concerning' only when multiple independent indicators converge" — removing this caused over-classification
- HTP absence annotation: "Note absences — they carry weight" — without this, models skip missing-element commentary
- Score range reminder: "floats in [0.0, 1.0] — never 1–10, never percentages" — without this, Gemma4 produced integer scores
- Parent-safe framing: "may suggest," "could indicate" — removing caused clinical language in concerns

## Token Counts

| Version | Tokens | Reduction |
|---------|--------|-----------|
| v1_original | 1374 | baseline |
| v3_optimized | 940 | 31.6% |

Counter: `tiktoken` cl100k_base

## Cost Impact at Gemini 2.5 Flash Pricing

- Cost reduction per call: $0.000033 (11.2%)
- At 100K calls/month: $3.25 saved
- At 1M calls/month: $32.50 saved
- Secondary benefit: lower input token count reduces time-to-first-token latency

See `evals/module_b/token_analysis.md` for full breakdown.
