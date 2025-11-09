"""AI Content Auditor - Main CLI Application.

This module provides the command-line interface (CLI) entrypoint for the
content auditor. It wires together the low-level utilities (fetching,
extraction, caching), rule-based checks (SEO and accessibility), and the
optional LLM-based tone analysis chain. The Typer-based `audit` command
accepts a CSV of URLs and produces JSONL/CSV reports under the `reports/`
directory.

High level flow:
    - Load URLs from an input CSV
    - For each URL: check cache -> fetch HTML -> extract text & metadata
    - Run rule-based checks (SEO + A11y)
    - Optionally run LLM tone analysis (budget-controlled)
    - Save results to JSONL and summary CSV
"""

import csv
import json
import logging
import os
import time
from pathlib import Path
from typing import List, Optional

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from chains.tone_chain import analyze_tone
from rules.a11y_rules import check_a11y
from rules.seo_rules import check_seo
from utils.budget import BudgetManager
from utils.cache import Cache
from utils.html_fetch import fetch_page
from utils.html_to_text import extract_metadata, extract_text

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Typer app and Rich console
app = typer.Typer(help="AI Content Auditor for SEO, accessibility, and tone analysis")
console = Console()


def load_urls_from_csv(csv_path: str) -> List[str]:
    """Load URLs from CSV file.

    This helper is liberal about column names and will accept `url`, `URL`,
    `Url` or `link`. It returns a list of cleaned URL strings.
    """
    urls = []
    try:
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Try common column names
                url = row.get('url') or row.get('URL') or row.get('Url') or row.get('link')
                if url:
                    urls.append(url.strip())
        logger.info(f"Loaded {len(urls)} URLs from {csv_path}")
    except Exception as e:
        logger.error(f"Error loading URLs from CSV: {e}")
        raise
    return urls


def process_page(
    url: str,
    cache: Cache,
    budget: BudgetManager,
    use_llm: bool = True
) -> dict:
    """Process a single page.

    Steps performed:
      1. Return cached result if available.
      2. Fetch the page HTML synchronously.
      3. Extract main article text using readability + BeautifulSoup.
      4. Run zero-cost rule checks (SEO + A11y).
      5. Optionally run an LLM-based tone analysis (if budget allows).
      6. Assemble result dict and persist to disk cache.

    The returned dict is serializable to JSON and stored in the JSONL report.
    """
    logger.info(f"Processing: {url}")

    # Check cache first
    cached = cache.get(url)
    if cached:
        logger.info(f"Using cached result for {url}")
        return cached

    # Fetch HTML
    html = fetch_page(url)
    if not html:
        return {
            "url": url,
            "error": "Failed to fetch page",
            "seo_rules": {},
            "a11y_rules": {},
            "tone_summary": None
        }

    # Extract text and metadata
    text = extract_text(html)
    if not text:
        return {
            "url": url,
            "error": "Failed to extract text",
            "seo_rules": {},
            "a11y_rules": {},
            "tone_summary": None
        }

    # Run rule-based checks
    seo_results = check_seo(html, text)
    a11y_results = check_a11y(html, text)

    # Optionally run LLM tone analysis
    tone_summary = None
    if use_llm and budget.can_make_call("tone_analysis"):
        logger.info(f"Running tone analysis for {url}")
        tone_summary = analyze_tone(text)
        if tone_summary:
            budget.record_call("tone_analysis")

    # Compile results
    result = {
        "url": url,
        "seo_rules": seo_results,
        "a11y_rules": a11y_results,
        "tone_summary": tone_summary,
        "issues": seo_results.get("issues", []) + a11y_results.get("issues", []),
        "scores": {
            "seo": seo_results.get("overall_score", 0),
            "a11y": a11y_results.get("overall_score", 0)
        }
    }

    # Cache result
    cache.set(url, result)

    return result


@app.command()
def audit(
    input_csv: str = typer.Option(..., "--input", "-i", help="Path to CSV file with URLs"),
    max_pages: int = typer.Option(200, "--max-pages", help="Maximum pages to process"),
    batch_size: int = typer.Option(20, "--batch-size", help="Pages per batch"),
    no_llm: bool = typer.Option(False, "--no-llm", help="Disable LLM tone analysis"),
    max_llm_calls: int = typer.Option(200, "--max-calls", help="Maximum LLM calls"),
    cache_dir: str = typer.Option(".cache", "--cache-dir", help="Cache directory"),
    reports_dir: str = typer.Option("reports", "--reports-dir", help="Reports directory"),
    clear_cache: bool = typer.Option(False, "--clear-cache", help="Clear cache before run"),
):
    """Run content audit on URLs from CSV file."""

    console.print("\n[bold blue]AI Content Auditor[/bold blue]")
    console.print("=" * 50)

    # Initialize components
    cache = Cache(cache_dir)
    budget = BudgetManager(max_calls=max_llm_calls)

    if clear_cache:
        cache.clear()
        console.print("[yellow]Cache cleared[/yellow]")

    # Load URLs
    try:
        all_urls = load_urls_from_csv(input_csv)
    except Exception as e:
        console.print(f"[red]Error loading URLs: {e}[/red]")
        raise typer.Exit(1)

    # Limit URLs
    urls = all_urls[:max_pages]
    console.print(f"\n[green]Processing {len(urls)} pages (max: {max_pages})[/green]")
    if no_llm:
        console.print("[yellow]LLM tone analysis disabled[/yellow]")

    # Process pages
    results = []
    start_time = time.time()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Processing pages...", total=len(urls))

        for i, url in enumerate(urls, 1):
            result = process_page(url, cache, budget, use_llm=not no_llm)
            results.append(result)
            progress.update(task, advance=1, description=f"Processed {i}/{len(urls)}")

            # Stop if budget exhausted
            if not no_llm and not budget.can_make_call():
                console.print("\n[yellow]Budget limit reached, stopping early[/yellow]")
                break

    elapsed_time = time.time() - start_time

    # Save results
    reports_path = Path(reports_dir)
    reports_path.mkdir(parents=True, exist_ok=True)

    # Save JSONL (detailed per-page results)
    jsonl_path = reports_path / "pages.jsonl"
    with open(jsonl_path, 'w') as f:
        for result in results:
            f.write(json.dumps(result) + "\n")
    console.print(f"\n[green]Saved detailed results to {jsonl_path}[/green]")

    # Save CSV summary
    csv_path = reports_path / "summary.csv"
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["URL", "SEO Score", "A11y Score", "Issues Count", "Has Tone Analysis"])
        for result in results:
            writer.writerow([
                result["url"],
                f"{result['scores']['seo']:.1f}",
                f"{result['scores']['a11y']:.1f}",
                len(result["issues"]),
                "Yes" if result.get("tone_summary") else "No"
            ])
    console.print(f"[green]Saved summary to {csv_path}[/green]")

    # Display statistics
    console.print("\n[bold]Run Statistics:[/bold]")
    stats_table = Table()
    stats_table.add_column("Metric", style="cyan")
    stats_table.add_column("Value", style="green")

    stats_table.add_row("Pages Processed", str(len(results)))
    stats_table.add_row("Time Elapsed", f"{elapsed_time:.1f}s")
    stats_table.add_row("Avg Time per Page", f"{elapsed_time/len(results):.1f}s")

    if not no_llm:
        budget_stats = budget.get_stats()
        stats_table.add_row("LLM Calls Made", f"{budget_stats['total_calls']}/{budget_stats['max_calls']}")
        stats_table.add_row("Budget Used", f"{budget_stats['budget_used_percent']:.1f}%")

    cache_stats = cache.get_stats()
    stats_table.add_row("Cache Entries", str(cache_stats["total_entries"]))
    stats_table.add_row("Cache Size", f"{cache_stats['total_size_mb']}MB")

    console.print(stats_table)

    # Top issues summary
    all_issues = []
    for result in results:
        all_issues.extend(result["issues"])

    if all_issues:
        console.print("\n[bold]Top Issues:[/bold]")
        from collections import Counter
        issue_counts = Counter(all_issues).most_common(10)
        for issue, count in issue_counts:
            console.print(f"  • {issue} ({count} pages)")

    console.print("\n[bold green]Audit complete![/bold green]\n")


if __name__ == "__main__":
    app()
