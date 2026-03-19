"""
AI Web Scraper using ScrapeGraphAI + Ollama
Uses local AI model - no API keys needed!

Usage:
    python ai_scraper.py "https://example.com" "Extract title and description"
    python ai_scraper.py --file urls.txt "Extract all links"
"""

import sys
import os
import click

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scrapegraphai.graphs import SmartScraperGraph
import json

# Configuration
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:0.5b")

GRAPH_CONFIG = {
    "llm": {
        "model": f"ollama/{OLLAMA_MODEL}",
        "format": "json",
        "temperature": 0,
    },
    "verbose": True,
}


def scrape_website(url: str, prompt: str) -> dict:
    """Scrape a website using AI"""
    try:
        smart_scraper_graph = SmartScraperGraph(
            prompt=prompt,
            source=url,
            config=GRAPH_CONFIG
        )
        result = smart_scraper_graph.run()
        return result
    except Exception as e:
        return {"error": str(e)}


@click.command()
@click.argument("url")
@click.argument("prompt")
@click.option("--model", "-m", default=None, help="Ollama model to use")
def main(url: str, prompt: str, model: str):
    """Scrape a website using local AI"""
    
    if model:
        GRAPH_CONFIG["llm"]["model"] = f"ollama/{model}"
    
    click.echo(f"🔍 Scraping: {url}")
    click.echo(f"📝 Prompt: {prompt}")
    click.echo(f"🤖 Model: {GRAPH_CONFIG['llm']['model']}")
    click.echo()
    
    result = scrape_website(url, prompt)
    
    click.echo("✅ Result:")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
