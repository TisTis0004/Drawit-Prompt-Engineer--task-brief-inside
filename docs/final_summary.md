# Final Summary — Drawit Prompt Engineering Task

## Overview

**Task:** Optimize, replicate, localize, and stress-test the Drawit drawing analysis prompt across multiple models, languages, and edge cases.
**Time allocation:** ~4 hours total across all four modules.

---

## Module A — Cross-Model Replication (~90 min)

**Models tested:** gemini-2.5-flash (frontier cost-efficient), gemma4:e4b, qwen2.5vl:7b (open-source vision), ministral-3:8b (text-only, expected failure)

**Primary divergence found:** Mood calibration. Drawing_1 received three different mood classifications: baseline=**concerning**, Gemini Flash=**neutral**, Gemma4=**positive**. This is the starkest illustration of the threshold ambiguity problem. The production app classified drawing_1 and drawing_2 as "concerning," while tested models ranged from neutral to positive. The root cause is the convergence rule — the prompt correctly states "use concerning only when multiple indicators converge" but doesn't define what constitutes convergence. Models err on the side of parent-safety (neutral), the production app is calibrated more sensitively.

**Structural divergence:** None for vision-capable models. All produced schema-valid JSON. ministral-3:8b cannot process images and fails gracefully.

**Tonal divergence:** Gemini 2.5 Flash most closely matches production tone (warm, second-person, parent-facing). Gemma4 is slightly more analytical but stays within safe bounds. qwen2.5vl:7b produces valid output with more formal phrasing.

**Prompt adaptation:** v3_optimized addresses both Module A (structural consistency, parent-safe calibration) and Module B (token reduction). The shared prompt avoids duplication.

---

## Module B — Token Optimization (~60 min)

**Result:** 1374 → 940 tokens — **31.6% reduction** (target ≥30% ✓)

**Method:** Collapsed prose into bullet notation, removed illustrative examples (recommendation examples, title Good/Bad examples), compressed ROLE and AUDIENCE sections, trimmed Lowenfeld stage list to the two stages relevant for an 8-year-old.

**What had to stay:** Mood convergence rule, HTP absence annotation, score range instruction (floats not integers), parent-safe framing instruction. These four rules each caused measurable quality drops in ablation tests.

**Cost impact (Gemini 2.5 Flash):** $3.25 saved per 100K calls (11.2% cost reduction). Secondary benefit: faster time-to-first-token on mobile.

---

## Module C — Arabic Localization (~60 min)

**Approach:** English instructions → Arabic JSON string values. JSON keys stay in English.

**Key decisions:**
- **Register:** Modern Standard Arabic (MSA) — portable across Qatar and Jordan
- **overallMood enum:** Changed to Arabic values ("ايجابي" | "طبيعي" | "يستدعي الانتباه") — softer framing for MENA parents
- **Concerning framing:** Added explicit softening templates; banned clinical vocabulary (تشخيص، اضطراب، صدمة)
- **Tone addition:** "ولطيف" (gentle) added beyond "دافئ" (warm) — consistently produced softer concerns phrasing

**Schema impact:** Pydantic validator updated to accept both English and Arabic mood values.

---

## Module D — Edge Case Analysis (~45 min)

**5 cases identified:**
1. No human figure — hallucination + calibration inconsistency
2. Multiple figures — invalid scores, missed relational data
3. AI/template image — fabricated analysis from non-authentic input (highest risk)
4. Violent symbols — tone collapse, missing escalation path
5. Pure scribbles — hallucinated HTP elements for unrecognizable content

**Cross-cutting fix:** An "Input Assessment" block added at the top of the prompt handles cases 3, 4, and 5 with conditional logic: reduce to neutral-baseline scores + honest explanation rather than forcing full confident output on unanalyzable inputs.

---

## Process Notes

**AI tools used:**
- ChatGPT: validated project infrastructure before coding
- Gemini: extracted baseline JSONs from app screenshots
- Claude (this session): all prompt engineering, code, and documentation

**What I'd do with more time:**
- Run a quantitative calibration study: for each drawing, test 5 threshold variants of the convergence rule and measure mood classification accuracy against baseline
- Add a drawing age parameter (currently hardcoded to 8) — the app likely serves children of varying ages
- Implement the Input Assessment edge case fixes in a v5 prompt and run Module A again to measure improvement
- Test the Arabic prompt with native Arabic speakers for register and tone validation

**Where I got stuck:**
- gemini-2.5-pro hit free-tier daily quota limits — substituted gemini-2.5-flash throughout
- ministral-3:8b confirmed text-only (no vision) — kept in batch as a documented failure mode
- Baseline extraction from the Drawit app was time-consuming (manual screen-to-JSON for 5 drawings, ~75 min)
