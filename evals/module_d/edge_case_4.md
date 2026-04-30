# Edge Case 4 — Violent or Threatening Symbols

## Case Description
A child's drawing contains explicit violent content: weapons, figures being harmed, blood, death imagery (e.g., gravestones, coffins), or threatening symbols that fall outside the typical HTP interpretive framework.

## What Goes Wrong
1. **Tone collapse under pressure:** The current prompt says to avoid the word "trauma" unless "the imagery is explicit and unmistakable" — but gives no specific instruction on what to do when it IS explicit. The model must improvise, which leads to inconsistent responses: some models dramatically over-alarm ("This drawing strongly indicates emotional distress and possible exposure to violence") while others under-flag ("The child shows creative expression through energetic mark-making").
2. **Parent-safe vs. honest tension:** The prompt's primary directive is "never alarming" — but genuine violent imagery may warrant more than gentle concern. The current instruction creates a conflict without a resolution path.
3. **Missing escalation guidance:** For concerning content in a child welfare context, there should be a clearly different response mode that recommends professional consultation — but the current prompt has no conditional logic for this.

## Proposed Prompt-Level Fix
Add an explicit escalation clause to the OVERALL MOOD section:

```
Exception — explicit violence or self-harm imagery:
If the drawing contains unambiguous depictions of violence, self-harm, death, weapons directed at
figures, or highly distressing symbols (not abstract or playful):
- Set overallMood to "concerning"
- Include in concerns: "This drawing contains imagery that may be worth a gentle, open-ended
  conversation with your child — something like 'Tell me about this part of your drawing.' If
  the theme continues across multiple drawings, speaking with a school counselor or
  child psychologist could be valuable."
- Do NOT use clinical language or alarm. Frame as an invitation to connect, not a diagnosis.
```
