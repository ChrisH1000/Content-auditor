# AI Content Auditor

Cost-aware AI-powered content auditor for SEO, accessibility, and brand tone analysis.

## Features

- **Rule-Based Checks**: Zero-cost SEO and accessibility analysis
- **Optional LLM Analysis**: Tone and readability assessment using local Ollama
- **Budget Management**: Enforce strict LLM call limits
- **Smart Caching**: Avoid redundant processing
- **Batch Processing**: Handle hundreds of pages efficiently
- **Rich Reporting**: JSONL + CSV outputs with detailed metrics

## Requirements

- Python 3.11+
- [Ollama](https://ollama.ai/) (for LLM features)
- 4GB+ RAM recommended for Ollama models

## Installation

### 1. Clone and Setup

```bash
cd /path/to/Content\ auditor
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .
```

### 2. Install Ollama and Models

```bash
# Install Ollama (see https://ollama.ai/)
curl -fsSL https://ollama.ai/install.sh | sh

# Pull required models
ollama pull llama3.1:8b-instruct
ollama pull bge-small
```

### 3. Configure Environment

Copy `.env.example` to `.env` and adjust settings as needed:

```bash
cp .env.example .env
```

Default configuration:
```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b-instruct
MAX_LLM_CALLS=200
BATCH_SIZE=20
MAX_PAGES=200
```

## Usage

### Basic Audit (with LLM)

```bash
python main.py audit --input urls.csv
```

### Rule-Based Only (No LLM Costs)

```bash
python main.py audit --input urls.csv --no-llm
```

### Custom Limits

```bash
python main.py audit \
  --input urls.csv \
  --max-pages 50 \
  --max-calls 100 \
  --batch-size 10
```

### Clear Cache

```bash
python main.py audit --input urls.csv --clear-cache
```

## Input Format

Create a CSV file with URLs:

```csv
url
https://example.com/page1
https://example.com/page2
https://example.com/page3
```

Other supported column names: `URL`, `Url`, `link`

## Output

### JSONL Report (`reports/pages.jsonl`)

Detailed per-page analysis:

```json
{
  "url": "https://example.com/page",
  "seo_rules": {
    "overall_score": 85.0,
    "scores": {
      "title": 100,
      "meta_description": 75,
      "h1": 100,
      "canonical": 100,
      "word_count": 75
    },
    "metrics": {
      "title_length": 45,
      "meta_desc_length": 145,
      "h1_count": 1,
      "word_count": 520
    },
    "issues": ["Meta description too short"]
  },
  "a11y_rules": {
    "overall_score": 91.7,
    "scores": {
      "image_alts": 100,
      "heading_hierarchy": 100,
      "link_text": 75
    },
    "metrics": {
      "images_total": 5,
      "images_with_alt": 5,
      "links_total": 12,
      "links_with_text": 12
    },
    "issues": ["3 links use generic text"]
  },
  "tone_summary": {
    "readability": "Content is clear and accessible...",
    "tone": "Professional and informative...",
    "risks": "No significant risks identified..."
  },
  "issues": [...],
  "scores": {
    "seo": 85.0,
    "a11y": 91.7
  }
}
```

### CSV Summary (`reports/summary.csv`)

Quick overview:

```csv
URL,SEO Score,A11y Score,Issues Count,Has Tone Analysis
https://example.com/page1,85.0,91.7,4,Yes
https://example.com/page2,72.0,83.3,7,Yes
```

## Rule Checks

### SEO Rules (Zero LLM Cost)

- **Title Tag**: Length validation (30-60 chars)
- **Meta Description**: Length validation (120-160 chars)
- **H1 Tags**: Presence and uniqueness
- **Canonical URL**: Presence check
- **Word Count**: Minimum content threshold (300+ words)

### Accessibility Rules (Zero LLM Cost)

- **Image Alt Text**: Coverage percentage
- **Heading Hierarchy**: Proper H1-H6 ordering
- **Link Text**: Quality and descriptiveness

### LLM Analysis (Optional, ~1 call/page)

- **Readability**: Content clarity assessment
- **Tone**: Brand voice analysis
- **Risks**: Potential issues identification

## Performance

Typical performance on a laptop with local Ollama:

- **Rule-based only** (`--no-llm`): ~2-3 pages/second
- **With LLM analysis**: ~3-5 seconds/page
- **200 pages with LLM**: ~15-20 minutes

## Caching

Results are cached by URL in `.cache/`. Re-running with identical URLs will use cached data.

Clear cache with `--clear-cache` flag or manually delete `.cache/` directory.

## Budget Management

LLM calls are strictly limited by `--max-calls` (default: 200). Processing stops when limit is reached.

Monitor usage in the run statistics output.

## Troubleshooting

### Ollama Connection Issues

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama service
ollama serve
```

### Model Not Found

```bash
# List installed models
ollama list

# Pull missing models
ollama pull llama3.1:8b-instruct
```

### Memory Issues

Reduce batch size or max pages:

```bash
python main.py audit --input urls.csv --batch-size 10 --max-pages 50
```

## Development

### Run Tests

```bash
pip install -e ".[dev]"
pytest tests/
```

### Format Code

```bash
black .
ruff check .
```

## Architecture

```
main.py              # CLI orchestrator (Typer)
├── rules/           # Zero-cost rule checks
│   ├── seo_rules.py
│   └── a11y_rules.py
├── chains/          # LLM integrations
│   └── tone_chain.py
└── utils/           # Core utilities
    ├── html_fetch.py
    ├── html_to_text.py
    ├── cache.py
    └── budget.py
```

## License

MIT

## Contributing

Contributions welcome! Please open an issue or pull request.
