# Module D — Edge Case & Failure Mode Analysis

## Methodology

Five failure modes were identified through analysis of the current prompt, the five baseline outputs, and the two initial model test runs. Each case represents a class of input where the current prompt structure produces unreliable, misleading, or schema-breaking output.

The cases were selected to cover distinct failure categories:
1. Missing HTP element (person absent)
2. Multiple HTP subjects (family scene)
3. Non-authentic input (template/AI-generated)
4. Extreme content (violent symbols)
5. Insufficient content (pure scribbles)

## Summary Table

| # | Case | Failure Type | Severity |
|---|------|--------------|----------|
| 1 | No human figure | Semantic + calibration | Medium |
| 2 | Multiple figures | Invalid scores + missed data | Medium |
| 3 | AI/template image | Hallucinated analysis | High |
| 4 | Violent symbols | Tone collapse + missing escalation | High |
| 5 | Pure scribbles | Hallucinated HTP elements | High |

## Cross-Cutting Observation

Three of the five cases (3, 4, 5) share a root cause: the model is instructed to always produce a full, confident JSON output — but no instruction exists for what to do when the input is fundamentally unanalyzable or requires a different response mode. The fix pattern is consistent: add conditional logic that produces a reduced-confidence output with an honest parent-facing explanation, rather than forcing confident scores where none are warranted.

## Proposed Global Addition to Prompt

The individual fixes in edge_case_3.md, edge_case_4.md, and edge_case_5.md could be consolidated into a single "Input Assessment" section added before the HTP analysis steps:

```
# INPUT ASSESSMENT (run before HTP analysis)

Before analysis, assess three conditions:
1. AUTHENTICITY: Are there signs of a template, coloring page, or AI-generated image?
   → If yes: set all trait scores to 0.5, note in concerns, continue with reduced confidence
2. CONTENT THRESHOLD: Is there sufficient recognizable content for HTP analysis?
   → If primarily scribbles/abstract: note the limitation, set trait scores to 0.5
3. EXPLICIT DISTRESS: Does the drawing contain unambiguous violent or self-harm imagery?
   → If yes: set overallMood to "concerning", include a gentle conversation prompt in concerns
```

See `evals/module_d/edge_case_{1-5}.md` for individual case details and proposed fixes.
