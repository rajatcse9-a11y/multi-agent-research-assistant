import os
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from langchain.tools import tool
from tavily import TavilyClient

load_dotenv()

_api_key = os.getenv("TAVILY_API_KEY")
if not _api_key:
    raise RuntimeError("TAVILY_API_KEY .env file mein set nahi hai.")

tavily = TavilyClient(api_key=_api_key)

MAX_SCRAPE_CHARS = 3000  # Groq free tier ke TPM limit ke liye chhota rakha hai


@tool
def web_search(query: str) -> str:
    """Search the web for recent and reliable information on a topic. Returns titles, URLs and snippets."""
    try:
        results = tavily.search(query=query, max_results=5)
    except Exception as e:
        return f"Search failed: {type(e).__name__}: {e}"

    items = results.get("results", [])
    if not items:
        return "No results found."

    out = []
    for r in items:
        title = r.get("title", "")
        url = r.get("url", "")
        snippet = (r.get("content") or "")[:300]
        out.append(f"Title: {title}\nURL: {url}\nSnippet: {snippet}\n")

    return "\n----\n".join(out)


@tool
def scrape_url(url: str) -> str:
    """Scrape and return clean text content from a given URL for deeper reading."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return "Could not scrape URL: invalid URL (http/https required)."

    try:
        resp = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()  # 403/404/500 pe error de, junk text nahi

        content_type = resp.headers.get("Content-Type", "").lower()
        if "html" not in content_type and "text" not in content_type:
            return f"Could not scrape URL: unsupported content type ({content_type or 'unknown'})."

        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript", "form"]):
            tag.decompose()

        text = soup.get_text(separator=" ", strip=True)
        if not text:
            return "Could not scrape URL: no readable text found on the page."

        return text[:MAX_SCRAPE_CHARS]
    except Exception as e:
        return f"Could not scrape URL: {type(e).__name__}: {e}"