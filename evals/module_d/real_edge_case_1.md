# Edge Case 1 — Pure Scribbles / Unrecognizable Content

## Case Description

A child submits a drawing that contains no identifiable HTP elements at all — just scribbles, random marks, abstract shapes, or a drawing so developmentally early that no figure, tree, or house can be recognized. The HTP method requires recognizable objects to function.

## What Goes Wrong

1. **Hallucinated objects:** Without explicit instruction, models invent HTP elements that aren't present. A scribbled drawing receives confident analysis: "The house shows a need for security" — when no house exists. This is the most dangerous failure mode as it produces completely fabricated psychological insights.
2. **Age mismatch:** Pure scribbles are typical for children aged 2–4 (pre-schematic stage). For an 8-year-old, scribbles may indicate frustration, lack of engagement, or developmental concern — but the prompt doesn't distinguish between age-appropriate and age-atypical scribbling.
3. **Schema compliance at the cost of accuracy:** The model is instructed to always produce a full JSON. Faced with uninterpretable content, it fills all fields with fabricated content rather than flagging the absence of analyzable data.

## Proposed Prompt-Level Fix

Add a minimum-content threshold to the METHODOLOGY section:

```
Before HTP analysis, assess whether the drawing contains sufficient recognizable content:
- If the drawing consists primarily of scribbles, random marks, or has no identifiable figures,
  objects, or landscape elements:
  - Note in keyInsights: "This drawing is richly expressive but abstract — detailed HTP analysis
    requires more recognizable elements."
  - Set emotionalIndicators and personalityTraits to 0.5 (neutral — insufficient data)
  - Include in concerns: "The drawing's abstract style makes a detailed psychological reading
    difficult. Scribbling is very normal for young children, though for an 8-year-old it may
    simply reflect the mood of the moment — consider asking your child to 'tell you about the
    drawing' rather than interpreting it visually."
  - Do NOT invent HTP elements that are not present.
```
