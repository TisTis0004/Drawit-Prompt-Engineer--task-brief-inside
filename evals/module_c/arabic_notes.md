# Module C — Arabic Localization: Cultural & Linguistic Decision Notes

## Approach
The Arabic prompt variant (v4_arabic) keeps all JSON keys in English and instructs the model to output all string values in Modern Standard Arabic (فصحى معاصرة), calibrated for a Qatari or Jordanian mother reader.

---

## Decision Notes

### 1. Register: Modern Standard Arabic (MSA) vs. Dialect
**Decision:** MSA (فصحى معاصرة), not Gulf or Levantine dialect.
**Rationale:** The app targets both Qatari and Jordanian users. MSA is understood pan-regionally and is the expected register for written, professional, or health-adjacent communication. Dialect would alienate one target market and reads as informal in a sensitive context.

### 2. Framing "Concerning" Findings
**Decision:** Added a dedicated "CONCERNING FINDINGS — ARABIC FRAMING GUIDANCE" section with explicit softening templates.
**Rationale:** Arabic parenting culture in the Gulf and Levant tends to be protective of family image. A parent reading "يثير القلق" (raises concern) about their child's drawing is likely to distrust the app or disengage. We use "يستحق اهتماماً لطيفاً" (deserves gentle attention) — factually accurate but far softer in Arabic register.
**Templates provided:**
- "يستحق هذا الجانب من الرسمة اهتماماً لطيفاً ومتابعة دافئة ولطيفة مع طفلك."
- "قد يعكس هذا شيئاً يحتاج طفلك للتعبير عنه — فتح حوار هادئ قد يُفيد."

### 3. overallMood Enum Changed to Arabic
**Decision:** `"positive" | "neutral" | "concerning"` → `"ايجابي" | "طبيعي" | "يستدعي الانتباه"`
**Rationale:** The mood label is likely rendered in the UI. For an Arabic-localized deployment, the displayed value should be Arabic. "يستدعي الانتباه" (requires attention) is softer than "مقلق" (worrying) while conveying the same elevated status.
**Trade-off:** This creates a schema divergence vs. the English schema. Handled in the Pydantic validator by maintaining a `VALID_MOODS` set that accepts both English and Arabic mood values.

### 4. Banned Clinical Vocabulary
**Decision:** Explicitly banned: "تشخيص" (diagnosis), "اضطراب" (disorder), "صدمة" (trauma), "مرض" (illness/disease).
**Rationale:** Mental health stigma is higher in many MENA contexts than in Western ones. Clinical vocabulary about a child would trigger rejection of both the finding and the product. The instruction to use "قد يشير إلى," "يمكن أن يعكس" is the Arabic parallel to the English "may suggest," "could indicate."

### 5. Tone Descriptor: Added "ولطيف" (Gentle/Kind)
**Decision:** Added "ولطيف" to several tone phrases beyond "دافئ" (warm).
**Rationale:** "Gentle" carries distinct cultural resonance in Arabic parenting discourse. In tested outputs, adding "ولطيف" to the tone instruction produced softer phrasing in the concerns array without reducing substance.

### 6. Religious Sensitivity — Handled by Model Calibration
**Decision:** No explicit religious phrases inserted into the prompt.
**Rationale:** Inserting "بإذن الله" or similar in the prompt risks being patronizing. Models trained on Arabic data naturally adopt appropriate religious register when given an accurate audience description ("religious, family-oriented"). This approach was preferred to hard-coding phrases the model might apply incoherently.

### 7. Color Names in Arabic
**Decision:** All `dominantColors[].color` strings and `symbolism` strings must be in Arabic.
**Rationale:** Consistency — if all string values are in Arabic, mixed-language color display (some Arabic, some English) would be jarring in the UI. Color names are among the most visible strings.

### 8. Drawing Title Length
**Trade-off noted:** Arabic titles run structurally longer than English equivalents (definite articles, noun-adjective agreement). A "short" Arabic title may be 5–8 words where English would use 3–5. Accepted as a minor layout concern — semantic correctness takes priority.

### 9. Word-Count Guidance in Arabic
**Decision:** Insight title length framed as "3–6 كلمات" (3–6 words in Arabic).
**Rationale:** Providing the constraint in Arabic script makes it culturally native and avoids confusion with Arabic morphology (one Arabic word often carries multiple English words' meaning, making character-count guidance ambiguous).

### 10. JSON Key Preservation
**Decision:** All JSON keys remain in English exactly as defined in the schema.
**Rationale:** The app frontend consumes JSON by key name. Translating keys would break parsing. Keys-in-English / values-in-Arabic is the cleanest localization boundary and matches standard i18n practice.
