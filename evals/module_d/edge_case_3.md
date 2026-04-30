# Edge Case 3 — AI-Generated or Traced Template Image

## Case Description
A parent uploads a coloring-book page, AI-generated illustration, or printed template that a child has colored in. The prompt assumes the input is a spontaneous hand-drawn child's drawing.

## What Goes Wrong
1. **False developmental assessment:** Template images bypass Lowenfeld stage calibration entirely — the structural quality belongs to the template artist, not the child. A coloring page would score artificially high on conscientiousness and confidence due to perfect line quality.
2. **Hallucinated authenticity:** The model has no instruction to detect non-spontaneous origin. It treats all visual inputs as authentic child drawings.
3. **Invalid psychological scores:** All scores derived from line quality, figure proportions, and placement (nearly all scores) are meaningless for drawings the child did not construct.

## Proposed Prompt-Level Fix
Add an authenticity check to the METHODOLOGY section (before HTP analysis):

```
First, assess drawing authenticity:
- Signs of non-spontaneous origin: perfectly uniform line weights, printed-quality linework,
  symmetric proportions inconsistent with age, pre-drawn outlines being colored in
- If the drawing appears to be a template or AI-generated image:
  - Set overallMood to "neutral"
  - Set all emotionalIndicators and personalityTraits to 0.5 (neutral baseline)
  - Include in concerns: "This drawing may include pre-drawn elements (template, coloring page,
    or printed image). Psychological scores reflect limited confidence — upload a fully
    hand-drawn original for the most meaningful analysis."
```
