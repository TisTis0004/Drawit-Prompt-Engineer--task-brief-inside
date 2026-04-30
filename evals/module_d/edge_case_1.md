# Edge Case 1 — Drawing with No Human Figure

## Case Description
A child submits a drawing that contains only environmental elements (house, tree, landscape, weather) with no human figure present. The HTP method expects a Person element.

## Observed in Baseline
Drawing_1 baseline was classified "concerning" partly because no person appears. The concern reads: "The absence of a human figure, particularly for a child of 8, is atypical and is worth gentle attention as it may suggest avoidance of self-representation or relational themes."

## What Goes Wrong
1. **Hallucination risk:** Without explicit instruction, models sometimes invent person-related interpretations when no person exists, because the HTP framework assumes all three elements and the model fills the gap.
2. **Mood inconsistency:** Gemini 2.5 Flash classified drawing_1 as "neutral" while production classified it "concerning." The prompt gives no explicit rule for how much weight to assign person-absence, so calibration is non-deterministic across models.
3. **Clinical phrasing:** When the model does note the absence, it tends toward clinical language ("indicates avoidance of self-concept") rather than parent-safe framing.

## Proposed Prompt-Level Fix
Add to the METHODOLOGY section:

```
When the Person element is absent in a drawing by a child aged 7–9:
- Note this explicitly in keyInsights (e.g., title: "A World Without a Figure")
- Do NOT invent person-related scores — reflect the absence in lower socialBonds and extroversion
- Include as an observed concern ONLY if combined with at least one other convergent indicator
- Parent-safe framing: "The absence of a human figure may reflect a current focus on the
  environment over self-representation — common in children deeply engaged with their surroundings."
```
