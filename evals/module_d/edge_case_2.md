# Edge Case 2 — Multiple Figures (Family Scene)

## Case Description
A child draws a family group: multiple people, a house, and a tree. The HTP method is designed for a single "Person" element. When multiple figures appear, the model must decide which person to analyze.

## What Goes Wrong
1. **Ambiguous subject:** Without instruction, models pick a figure arbitrarily (usually largest/most central), which may represent the father or another family member rather than the child's self-portrait.
2. **Invalid scores:** emotionalIndicators and personalityTraits are designed for self-portrait analysis. Applied to an arbitrarily chosen figure from a family scene, the scores lose psychological validity entirely.
3. **Missed relational data:** Figure proximity, relative sizes, and spatial isolation are rich HTP signals in family drawings — but the current prompt has no instruction to capture relational dynamics between figures.

## Proposed Prompt-Level Fix
Add to the METHODOLOGY section:

```
When multiple human figures appear:
- Identify the likely self-representation (typically the most elaborated figure, or the one closest
  in apparent age to the child)
- Note explicitly in keyInsights which figure is being analyzed and that multiple figures are present
- Use relative sizes and spatial relationships as input for socialBonds and agreeableness scores
- Flag any figure that is significantly smaller, faceless, or spatially isolated from others
- Framing: "The drawing includes multiple figures — the relationships between them may offer
  insight into how your child experiences family or social dynamics."
```
