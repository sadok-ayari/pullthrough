from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Tuple

TAG_RE = re.compile(r"<[^>]+>")
SPACE_RE = re.compile(r"\s+")

# Words and phrases that turn a mention into a reversal. Deliberately blunt and
# visible: a reader can add or delete one and see the score move.
DISMISS_MARKERS = (
    "scrap", "scrapped", "ditch", "ditched", "abandon", "abandoned", "shelve",
    "shelved", "u-turn", "uturn", "backtrack", "backtracks", "backtracked",
    "delay", "delayed", "delays", "fail", "failed", "fails", "failure",
    "reject", "rejected", "slashes", "slashed", "cut", "cuts", "axed", "ax",
    "water down", "watered down", "row over", "slam", "slammed", "blasted",
    "criticised", "criticized", "under fire", "broken promise", "no plan",
    "unclear", "confused", "backlash", "scrapped",
)

QUOTE_RE = re.compile(r"[\u2018\u2019\u201c\u201d\"']([^\u2018\u2019\u201c\u201d\"']{4,120})[\u2018\u2019\u201c\u201d\"']")


def strip_html(text: str) -> str:
    return SPACE_RE.sub(" ", TAG_RE.sub(" ", text or "")).strip()


def sentences(text: str) -> List[str]:
    flat = strip_html(text)
    parts = re.split(r"(?<=[.!?])\s+", flat)
    return [p.strip() for p in parts if p.strip()]


def compiled(keywords: Iterable[str]) -> List[re.Pattern]:
    return [re.compile(r"(?<!\w)" + re.escape(k.lower()) + r"(?!\w)", re.I) for k in keywords if k]


def hits(text: str, keywords: Iterable[str]) -> List[str]:
    low = (text or "").lower()
    found = []
    for keyword in keywords:
        if not keyword:
            continue
        if re.search(r"(?<!\w)" + re.escape(keyword.lower()) + r"(?!\w)", low):
            found.append(keyword)
    return found


def dismissed(text: str, keywords: Iterable[str], window: int = 90) -> bool:
    """A pillar keyword sitting next to a reversal marker reads as distortion.

    This is a proximity rule, not comprehension: it catches "ministry scraps
    green bond plan" and misses irony entirely. That limit is the price of a
    score a minister can audit line by line.
    """
    low = (text or "").lower()
    for keyword in keywords:
        kw = keyword.lower()
        if not kw:
            continue
        for match in re.finditer(r"(?<!\w)" + re.escape(kw) + r"(?!\w)", low):
            left = max(0, match.start() - window)
            right = min(len(low), match.end() + window)
            window_text = low[left:right]
            for marker in DISMISS_MARKERS:
                # Inflections: "scraps", "scrapped", "delays", "watering down".
                pattern = r"(?<!\w)" + re.escape(marker) + r"(?:s|es|ed|ped|ping|ing)?(?!\w)"
                if re.search(pattern, window_text):
                    return True
    return False


def quoted_lines(text: str, keywords: Iterable[str]) -> List[str]:
    """Quotes that touch a pillar: the sound-bite evidence for a briefing."""
    out = []
    for quote in QUOTE_RE.findall(strip_html(text)):
        if any(k.lower() in quote.lower() for k in keywords if k):
            out.append(quote.strip())
    return out[:2]


def article_text(article: Dict[str, Any]) -> Tuple[str, str]:
    title = article.get("title") or article.get("lead_title") or ""
    body = article.get("summary") or article.get("description") or article.get("body") or ""
    return strip_html(title), strip_html(body)
