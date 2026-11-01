import json
import logging
import re
import urllib.parse
import urllib.request
from typing import Any, Dict, List

from duckduckgo_search import DDGS

logger = logging.getLogger(__name__)

STOP_WORDS = {"had", "have", "has", "the", "a", "an", "is", "was", "were", "that", "this", "it"}


def _clean_query(text: str) -> str:
    """Removes conversational filler words to help search engines find the exact topic."""
    words = [w for w in re.findall(r"\b\w+\b", text) if w.lower() not in STOP_WORDS]
    return " ".join(words) if words else text


def _search_wikipedia_fallback(claim: str, max_results: int = 3) -> List[Dict[str, Any]]:
    evidence_list = []

    # Cleaned query (e.g. "India won t20 world cup 2024")
    smart_query = _clean_query(claim)

    try:
        clean_query = urllib.parse.quote(smart_query)
        url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={clean_query}&format=json&utf8=1"
        headers = {"User-Agent": "TruthGraph/1.0 (academic; fact-checking research)"}

        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=6) as response:
            data = json.loads(response.read().decode("utf-8"))
            results = data.get("query", {}).get("search", [])

            for item in results[:max_results]:
                title = item.get("title", "")
                raw_snippet = item.get("snippet", "")
                clean_snippet = re.sub(r"<[^>]+>", "", raw_snippet).strip()
                pageid = item.get("pageid")

                if clean_snippet:
                    evidence_list.append({
                        "text": f"{title}: {clean_snippet}",
                        "source_url": f"https://en.wikipedia.org/?curid={pageid}" if pageid else "https://en.wikipedia.org",
                        "source_medium": "Wikipedia",
                        "claim_date": None,
                        "evidence_date": None,
                        "question": ""
                    })
        print(f"[RETRIEVER] Wikipedia found {len(evidence_list)} evidence snippets for query: '{smart_query}'")
    except Exception as e:
        print(f"[RETRIEVER ERROR - WIKIPEDIA]: {e}")

    return evidence_list


def retrieve_live_evidence(claim: str, max_results: int = 3) -> List[Dict[str, Any]]:
    evidence_list = []
    smart_query = _clean_query(claim.strip())
    print(f"\n[RETRIEVER] Searching live web evidence for: '{smart_query}'")

    # 1. DuckDuckGo Search (using html/lite backend to avoid rate limits)
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(smart_query, max_results=max_results, backend="lite"))
            for item in results:
                title = item.get("title", "").strip()
                snippet = item.get("body", "").strip()
                url = item.get("href", "")

                full_text = f"{title}. {snippet}" if title else snippet
                if full_text:
                    evidence_list.append({
                        "text": full_text,
                        "source_url": url or None,
                        "source_medium": "Web",
                        "claim_date": None,
                        "evidence_date": None,
                        "question": f"Did {claim}?"
                    })
        print(f"[RETRIEVER] DuckDuckGo found {len(evidence_list)} evidence snippets.")
    except Exception as e:
        print(f"[RETRIEVER ERROR - DUCKDUCKGO]: {e}")

    # 2. Wikipedia Fallback with Smart Query
    if not evidence_list:
        print("[RETRIEVER] Triggering Wikipedia fallback...")
        evidence_list = _search_wikipedia_fallback(claim, max_results=max_results)

    return evidence_list