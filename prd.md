# Project: AI Content Auditor (Cost-Aware)

**Purpose**
Audit ECU pages for SEO, accessibility, and brand tone with minimal/zero API cost.

## 1) Objectives
- Run locally (no paid APIs required).
- Minimise LLM use by prioritising **rule-based checks**; use LLM only for nuanced tone/readability.
- Output JSON + CSV summaries; optional Google Sheets export when available.

## 2) Low-Cost Mode (defaults)
- **Models:** Ollama `llama3.1:8b-instruct` (chat); embeddings `bge-small`.
- **Vector store:** Chroma (local).
- **Fetch:** local sitemap/URL list → `httpx` + `readability-lxml` → text only.
- **Rules first:**
  - SEO (title len, meta desc len, H1 present, canonical present, word count).
  - A11y (img@alt presence %, headings order, link text heuristics).
- **LLM second (optional):** tone/readability summary for each page (≤ 1 call/page).
- **Batching:** 20 pages/batch; max 200 pages/run (configurable).
- **Budget guardrails:** `max_calls=200`.

## 3) Functional Requirements
| Area | Description |
|------|-------------|
| Input | CSV of URLs or sitemap.xml (downloaded locally) |
| Processing | Clean HTML → text; compute rule-based scores |
| LLM Analysis | Optional tone/readability (short prompt, ≤600 tokens output) |
| Output | `reports/pages.jsonl`, `reports/summary.csv` |
| Storage | Cache page text + rule results; LLM outputs keyed by hash |
| Monitoring | Local logs; simple run stats (calls, time, failures) |

## 4) Technical Stack
- Python 3.11; `langchain`, `chromadb`, `ollama`, `readability-lxml`, `beautifulsoup4`, `httpx`, `pydantic`, `python-dotenv`, `typer`.
- Optional: `google-api-python-client` for Sheets (guarded by flag).

## 5) Acceptance Criteria
- ✅ Rule-based SEO/A11y checks run with **zero LLM calls** when `--no-llm` is set.
- ✅ With LLM enabled, ≤ 1 call/page; **stop** when BudgetManager limits reached.
- ✅ JSONL per page with fields: `url`, `seo_rules`, `a11y_rules`, `tone_summary?`, `issues[]`, `scores{}`.
- ✅ Process 200 pages in < 20 minutes on a typical laptop (network dependent).
- ✅ Re-running with same inputs uses cache for identical outputs.

## 6) Developer Notes

/ai-content-auditor/
├─ main.py                # CLI: ingest -> rules -> (llm?) -> export
├─ rules/                 # pure-Python rule checks, no LLM
│   ├─ seo_rules.py
│   └─ a11y_rules.py
├─ chains/
│   └─ tone_chain.py      # single concise prompt, structured JSON
├─ utils/
│   ├─ html_fetch.py
│   ├─ html_to_text.py
│   ├─ cache.py
│   └─ budget.py
└─ reports/

### Tone prompt (short)
- System: “You are concise. 3 bullet points max. Output JSON with keys: `readability`, `tone`, `risks`.”
- User: “Summarise tone and readability of this page text (≤1200 words). Return JSON only.