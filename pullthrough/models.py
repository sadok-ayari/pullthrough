from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Pillar:
    id: str
    label: str
    keywords: List[str]
    required: bool = True


@dataclass
class Narrative:
    id: str
    name: str
    pillars: List[Pillar]

    @property
    def keywords(self) -> List[str]:
        return [k for pillar in self.pillars for k in pillar.keywords]


@dataclass
class Article:
    title: str
    outlet: str = ""
    url: str = ""
    published: Optional[str] = None
    summary: str = ""

    @property
    def key(self) -> str:
        return self.url or self.title.lower()


@dataclass
class Reading:
    """One article read against one narrative."""

    narrative: str
    article: Article
    state: str                      # conveyed | mentioned | distorted | absent
    pillars_hit: List[str] = field(default_factory=list)
    pillars_missing: List[str] = field(default_factory=list)
    in_title: bool = False
    weight: float = 0.0
    reasons: List[str] = field(default_factory=list)


def load_json(path: str) -> Dict[str, Any]:
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def narratives_from(config: Dict[str, Any]) -> List[Narrative]:
    out = []
    for raw in config.get("narratives", []):
        pillars = [
            Pillar(id=p["id"], label=p.get("label", p["id"]),
                   keywords=list(p.get("keywords", [])), required=bool(p.get("required", True)))
            for p in raw.get("pillars", [])
        ]
        out.append(Narrative(id=raw["id"], name=raw.get("name", raw["id"]), pillars=pillars))
    return out


def articles_from(path: str) -> List[Article]:
    """Read either a plain article list or a coverage-radar stories export."""
    payload = load_json(path)
    if isinstance(payload, dict) and "stories" in payload:
        articles = []
        for story in payload["stories"]:
            articles.append(Article(
                title=story.get("lead_title", ""),
                outlet=(story.get("outlets") or [""])[0],
                url=story.get("url", ""),
                published=story.get("published"),
                summary=story.get("summary", "") or "",
            ))
        return [a for a in articles if a.title]
    rows = payload if isinstance(payload, list) else payload.get("articles", [])
    return [
        Article(title=row.get("title", ""), outlet=row.get("outlet", ""), url=row.get("url", ""),
                published=row.get("published"), summary=row.get("summary", "") or row.get("description", "") or "")
        for row in rows if row.get("title")
    ]


def ensure_dir(path: str) -> None:
    if path and not os.path.isdir(path):
        os.makedirs(path, exist_ok=True)
