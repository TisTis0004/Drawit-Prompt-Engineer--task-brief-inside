# Drawit — Prompt Engineering Task

4-module prompt engineering interview task for the Drawit AI drawing analysis platform.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env  # add GEMINI_API_KEY
```

## Running Inference

```bash
# Single drawing, specific module and model
python src/run_inference.py --module a --model gemini-2.5-flash --drawing drawing_1

# All drawings for a module
python src/run_inference.py --module a --model gemma4:e4b --drawing all

# Generate comparison table (Module A)
python src/run_inference.py --module a --model gemini-2.5-flash --drawing all --compare-table

# Full batch — all modules × all models × all drawings
python src/run_batch.py

# Resume batch, skip already-run combinations
python src/run_batch.py --skip-existing
```

## Models

| Model | Type | Requires |
|-------|------|---------|
| `gemini-2.5-flash` | Gemini API | `GEMINI_API_KEY` in .env |
| `gemma4:e4b` | Ollama (vision) | Ollama running locally |
| `qwen2.5vl:7b` | Ollama (vision) | Ollama running locally |
| `ministral-3:8b` | Ollama (text-only) | Ollama — will fail on images gracefully |

## Modules

| Module | Prompt | Task |
|--------|--------|------|
| `a` | v1_original | Cross-model replication vs. production baseline |
| `b` | v3_optimized | Token-optimized prompt (31.6% reduction) |
| `c` | v4_arabic | Arabic localization for MENA mothers |
| `d` | v1_original | Edge case analysis (see evals/module_d/) |

## Outputs

- Inference results: `data/models_outputs/module_{a,b,c}/`
- Comparison tables: `evals/module_a/comparison_table.csv`
- Logs: `logs/{date}.log`
- Final deliverables: `outputs/module_{a,b,c,d}/`

## Project Structure

```
prompts/           Prompt versions (v1_original, v3_optimized, v4_arabic)
data/
  drawings/        5 test images
  baseline_outputs/ Production app baseline JSONs (5 drawings)
  models_outputs/  All inference run results
src/
  run_inference.py CLI for single runs
  run_batch.py     CLI for full batch runs
  model_client.py  GeminiClient + OllamaClient + factory
  models/schema.py Pydantic validation (strict [0.0,1.0] range checking)
  evaluator.py     Baseline comparison + CSV table generation
evals/             Per-module evaluation notes and tables
docs/              Per-module writeups for submission
outputs/           Final deliverables (final_prompt.txt + sample_output.json)
```
