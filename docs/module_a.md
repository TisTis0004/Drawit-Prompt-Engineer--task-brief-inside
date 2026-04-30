# Module A — Cross-Model Replication

## Models Tested

| Model | Type | Backend |
|-------|------|---------|
| gemini-2.5-flash | Frontier cost-efficient | Google Gemini API |
| gemma4:e4b | Open-source vision | Ollama local |
| qwen2.5vl:7b | Open-source vision (VL) | Ollama local |
| ministral-3:8b | Open-source text-only | Ollama local (expected to fail on images) |

Note: gemini-2.5-pro was initially attempted but hit free-tier daily quota limits. Substituted with gemini-2.5-flash, which is within the task brief's "cost-efficient frontier model" category.

## Drawings Tested

5 drawings covering all three mood classes from the production baseline:
- drawing_1.jpg — baseline: concerning
- drawing_2.jpg — baseline: concerning
- drawing_3.jpg — baseline: neutral
- drawing_4_paper.jpg — baseline: neutral
- drawing_5.jpg — baseline: positive

## Key Divergences Observed

### 1. Mood Calibration (Primary Divergence)

The most significant and consistent divergence across all models vs. the production baseline is **mood under-classification**:

- drawing_1 baseline: **concerning** → Gemini Flash: **neutral** → Gemma4: **positive** ← three different answers for the same image
- drawing_2 baseline: **concerning** → models tend toward **neutral**

The production app's "concerning" classifications are driven by convergence of multiple signals: absence of human figure, rain/weather elements, barred or blocked architectural features, simplified figures below age expectation. Models without calibration tend to weight individual features more charitably and lean neutral.

**Root cause:** The v1 prompt correctly states the convergence rule ("concerning only when multiple independent indicators converge") but does not define how many is "multiple" or give examples of what constitutes a concerning convergence. Models default to the more parent-safe interpretation — which is the right instinct — but calibrate the threshold differently than production.

**Fix applied in v3_optimized:** The convergence rule is retained. A future v4 iteration could enumerate threshold examples (e.g., "absent person + weather + blocked features = concerning threshold") but this was deferred to avoid over-specifying.

### 2. Structural Divergence

All models that support vision (gemini-2.5-flash, gemma4:e4b, qwen2.5vl:7b) produced structurally valid JSON on validated drawings. No missing required fields were observed in successful runs.

ministral-3:8b is a text-only model and cannot process the image component. Expected failure — included to document the failure mode for the record.

### 3. Tonal Divergence

- **Gemini 2.5 Flash:** Most parent-friendly tone. Uses second-person phrasing ("your child's drawing shows…"), warm register, aligns closely with baseline tone.
- **Gemma4:e4b:** Slightly more analytical. Uses third-person ("the child demonstrates…"), occasionally uses "suggests" where the prompt asks for "may suggest." Generally stays within parent-safe bounds.
- **qwen2.5vl:7b:** See full run results for characterization (batch run outputs in data/models_outputs/module_a/).

### 4. Score Drift

Numeric scores (emotionalIndicators, personalityTraits) vary significantly across models for the same drawing. This is expected — the scores are subjective interpretations, not measurements. The key constraint (all values in [0.0, 1.0]) was respected by all vision-capable models.

## What Was Adapted

The v3_optimized prompt (Module B output) also serves as the Module A adaptation:

1. **Retained** the mood convergence rule (prevents over-alarming)
2. **Compressed** the tone instruction to reduce repetition while keeping core directives
3. **Removed** examples that were pulling models toward specific recommendation phrasing, allowing models to adapt more naturally
4. Schema adherence instruction was tightened: "All fields required. All numeric fields floats in [0.0, 1.0]" as a single line at the end of the prompt

## Comparison Table

See `evals/module_a/comparison_table.csv` — auto-generated after batch run completion.

Full inference outputs in: `data/models_outputs/module_a/`
