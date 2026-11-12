from __future__ import annotations

from typing import List

from .models import Article, Narrative, Reading
from .text import article_text, dismissed, hits, quoted_lines

CONVEYED_MIN_PILLARS = 2


def read(article: Article, narrative: Narrative) -> Reading:
    """Score one article against one narrative, and print the reason for the call.

    Four states, in order of judgement:
      absent     no pillar keyword appears
      distorted  a pillar sits beside a reversal marker ("scraps", "u-turn")
      conveyed   every required pillar appears, at least two pillars in total,
                 and nothing contradicts them
      mentioned  a pillar appears, but not enough of the message to count
    """
    title, body = article_text({"title": article.title, "summary": article.summary})
    text = title + ". " + body
    reasons: List[str] = []

    hit_ids, hit_words, missing = [], [], []
    for pillar in narrative.pillars:
        found = hits(text, pillar.keywords)
        if found:
            hit_ids.append(pillar.id)
            hit_words.extend(found)
        elif pillar.required:
            missing.append(pillar.id)

    in_title = bool(hits(title, narrative.keywords))
    if not hit_ids:
        return Reading(narrative.id, article, "absent", [], [p.id for p in narrative.pillars],
                       False, 0.0, ["absent: no pillar keyword appears"])

    reasons.append(f"pillars: {', '.join(hit_ids)}")

    quotes = quoted_lines(text, hit_words)
    if dismissed(text, hit_words):
        reasons.append("distorted: a pillar sits next to a reversal marker")
        return Reading(narrative.id, article, "distorted", hit_ids, missing,
                       in_title, float(len(hit_ids)), reasons + quotes)

    if missing:
        reasons.append(f"mentioned: required pillar missing ({', '.join(missing)})")
        return Reading(narrative.id, article, "mentioned", hit_ids, missing,
                       in_title, float(len(hit_ids)), reasons + quotes)

    if len(hit_ids) < CONVEYED_MIN_PILLARS:
        reasons.append(f"mentioned: only {len(hit_ids)} pillar; a message needs at least two")
        return Reading(narrative.id, article, "mentioned", hit_ids, missing,
                       in_title, float(len(hit_ids)), reasons + quotes)

    weight = float(len(hit_ids)) * (2.0 if in_title else 1.0)
    reasons.append("conveyed: all required pillars, no reversal marker")
    if in_title:
        reasons.append("prominence: in the headline")
    return Reading(narrative.id, article, "conveyed", hit_ids, missing,
                   in_title, weight, reasons + quotes)


def read_all(articles: List[Article], narratives: List[Narrative]) -> List[Reading]:
    return [read(article, narrative) for article in articles for narrative in narratives]
