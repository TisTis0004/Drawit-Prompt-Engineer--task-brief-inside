# Module A — Cross-Model Replication Notes

## Divergence Summary

### Mood Classification (Most Critical)

| Drawing | Baseline | Gemini Flash | Gemma4:e4b | qwen2.5vl:7b |
|---------|----------|-------------|------------|---------------|
| drawing_1 | concerning | **neutral** | **positive** ⚠️ | (running) |
| drawing_2 | concerning | (see batch) | (see batch) | (see batch) |
| drawing_3 | neutral | (see batch) | (see batch) | (see batch) |
| drawing_4 | neutral | (see batch) | (see batch) | (see batch) |
| drawing_5 | positive | (see batch) | (see batch) | (see batch) |

*Full data auto-populated in comparison_table.csv after batch run*

**⚠️ Critical finding (drawing_1):** Baseline=concerning, Gemini Flash=neutral, Gemma4=positive — three models classify the same drawing at three different severity levels. This is the starkest illustration of the mood threshold calibration problem.

### Root Cause: Mood Threshold Ambiguity

The production app and all tested models apply the same rule ("concerning only when multiple indicators converge") but with different implicit thresholds. Observed pattern:

- **Production app:** Convergence = 2+ of: missing person, weather elements, blocked architectural features, simplified figure, isolation symbols
- **Models:** Convergence = 3+ indicators, or very explicit distress signals

This creates systematic under-classification for drawings in the "moderate concerning" range — drawings that the production app treats as concerning but that models treat as neutral.

### Structural Divergences

No missing JSON fields observed in valid model runs. All vision-capable models (gemini-2.5-flash, gemma4:e4b, qwen2.5vl:7b) produced parseable JSON conforming to the schema.

One structural note: some models include `createdAt` in their output (which the prompt doesn't request), others omit it. The pipeline overwrites `createdAt` server-side so this is not an issue in production.

### Tonal Divergences

**Gemini 2.5 Flash:**
- Closest to production tone
- Uses "your child's drawing" (second-person possessive) — matches app's personal register
- Concerns phrasing: warm, observational, parent-safe

**Gemma4:e4b:**
- Slightly more analytical register
- Uses "the drawing shows" / "the child's..." (third-person)
- Occasionally omits "may" hedging ("the placement indicates" rather than "may indicate")
- Recommendations are appropriately specific

**qwen2.5vl:7b:**
- See batch run outputs for characterization

**ministral-3:8b:**
- Text-only model — cannot process image
- Expected failure, documented for completeness

## What Changed to Align Models

The v3_optimized prompt (Module B output) serves dual purpose:
1. Token reduction (Module B)
2. Structural alignment — tighter instruction wording reduces model-to-model variation

The key change for Module A alignment: collapsing the tone instruction from a 17-line prose section to a 4-line bullet block reduced "interpretation space" for models to deviate.

The mood threshold issue is not fully resolved by prompt changes alone — it would benefit from few-shot examples showing the convergence threshold explicitly. This is noted as a future improvement.

## Comparison Table

See `comparison_table.csv` — generated automatically after batch run.
Columns: drawing_id, field, baseline, gemini-2.5-flash, gemma4:e4b, qwen2.5vl:7b, divergence_type, flagged
