# Module C — Arabic Localization

## Approach

Produced `prompts/v4_arabic/system.txt` — a prompt variant that instructs the model to output all string values in Modern Standard Arabic (فصحى معاصرة) while keeping all JSON keys in English.

The localization is implemented entirely at the prompt level: no separate schema, no code changes to the API layer. The model sees English instructions and produces Arabic-valued JSON.

## Key Decisions

**Register:** Modern Standard Arabic, not Gulf or Levantine dialect. The app targets both Qatari and Jordanian mothers — MSA is the only register that works for both and is appropriate for written, health-adjacent communication.

**overallMood enum:** Changed from `"positive" | "neutral" | "concerning"` to `"ايجابي" | "طبيعي" | "يستدعي الانتباه"`. If the app is deploying an Arabic-facing UI, the rendered mood label should be Arabic. "يستدعي الانتباه" (requires attention) is softer than "مقلق" (worrying) while still communicating elevated status. The Pydantic schema validator was updated to accept both English and Arabic mood values.

**Framing "concerning" findings:** The biggest localization challenge. Mental health stigma in MENA contexts means that clinical-sounding phrasing in the concerns array would drive users away. Added an explicit Arabic softening template to the prompt:
- "يستحق هذا الجانب من الرسمة اهتماماً لطيفاً ومتابعة دافئة ولطيفة مع طفلك."
- "قد يعكس هذا شيئاً يحتاج طفلك للتعبير عنه — فتح حوار هادئ قد يُفيد."

**Banned clinical vocabulary:** "تشخيص," "اضطراب," "صدمة," "مرض" — equivalent to the English ban on "diagnosis," "disorder," "trauma," "pathology."

**Tone addition:** Added "ولطيف" (gentle/kind) to several tone phrases. "لطيف" carries strong resonance in Arabic parenting discourse that has no single-word English equivalent — it combines gentleness and kindness in a way that consistently produced softer concerns phrasing in outputs.

## What Stayed the Same as v1

- All JSON keys (schema is unchanged)
- All scoring dimensions and field names
- The HTP methodology steps (language stays English as instructions)
- The mood convergence rule (only threshold changed to Arabic values)
- Schema adherence instruction

## Trade-offs Noted

- Arabic titles run slightly longer than English equivalents due to grammatical construction — acceptable
- MSA register may feel slightly formal to some Gulf users; dialect would be warmer but non-portable
- The English system prompt instructing Arabic output adds ~100 tokens vs. a fully Arabic prompt — accepted for maintainability and debuggability

See `evals/module_c/arabic_notes.md` for full cultural/linguistic decision log.
