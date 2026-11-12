from __future__ import annotations

from typing import Dict, List, Optional

from .models import Narrative, Reading

STATES = ("conveyed", "mentioned", "distorted", "absent")


def summary(readings: List[Reading]) -> Dict[str, Dict[str, object]]:
    out: Dict[str, Dict[str, object]] = {}
    for reading in readings:
        row = out.setdefault(reading.narrative, {state: 0 for state in STATES})
        row[reading.state] += 1  # type: ignore[operator]
    for row in out.values():
        total = sum(int(row[state]) for state in STATES)  # type: ignore[arg-type]
        row["total"] = total
        row["share"] = round(100.0 * int(row["conveyed"]) / total, 1) if total else 0.0  # type: ignore[arg-type]
    return out


def render(readings: List[Reading], narratives: List[Narrative], day: str,
           trend: Optional[Dict[str, Dict[str, int]]] = None, title: str = "Message pull-through") -> str:
    names = {n.id: n.name for n in narratives}
    counts = summary(readings)
    total_articles = len({r.article.key for r in readings})

    out = [f"# {title} — {day}", ""]
    out.append(f"**{total_articles} pieces read against {len(narratives)} narratives. "
               f"Conveyed means the required pillars appeared and nothing contradicted them.**")

    out += ["", "## Scorecard", ""]
    for narrative in narratives:
        row = counts.get(narrative.id)
        if not row:
            out.append(f"- **{narrative.name}:** no coverage in this window")
            continue
        out.append(
            f"- **{narrative.name}:** {row['conveyed']} conveyed, {row['mentioned']} mentioned, "
            f"{row['distorted']} distorted, {row['absent']} absent — {row['share']}% pull-through"
            f" of {row['total']} pieces")

    slipped = [r for r in readings if r.state == "distorted"]
    if slipped:
        out += ["", "## Where it slipped", "",
                "_A pillar beside a reversal marker. Check each one: the rule is blunt, the story may not be._"]
        for reading in slipped[:8]:
            link = f"[{reading.article.outlet or 'link'}]({reading.article.url})" if reading.article.url else (reading.article.outlet or "unattributed")
            out.append(f"- **{names.get(reading.narrative, reading.narrative)}** — {reading.article.title} ({link})")
            for reason in reading.reasons[1:3]:
                out.append(f"  - {reason}")

    gaps: Dict[str, List[str]] = {}
    carried: Dict[str, set] = {}
    for reading in readings:
        carried.setdefault(reading.narrative, set()).update(reading.pillars_hit)
    for narrative in narratives:
        hit = carried.get(narrative.id, set())
        never = [p.id for p in narrative.pillars if p.id not in hit]
        if never:
            gaps[narrative.id] = never
    if gaps:
        out += ["", "## Pillars never carried", ""]
        labels = {p.id: p.label for n in narratives for p in n.pillars}
        for narrative_id, pillar_ids in gaps.items():
            named = ", ".join(labels.get(pid, pid) for pid in pillar_ids)
            out.append(f"- **{names.get(narrative_id, narrative_id)}:** {named}")

    if trend:
        out += ["", "## Trend", ""]
        for narrative_id, series in trend.items():
            if not series:
                continue
            points = []
            for trend_day, states in series:
                total = sum(states.values()) or 1
                points.append(f"{trend_day[5:]}: {round(100 * states.get('conveyed', 0) / total)}%")
            out.append(f"- **{names.get(narrative_id, narrative_id)}:** " + " · ".join(points))

    out += ["", "---", "",
            "_Deterministic by design: keyword pillars, a proximity rule for reversal, "
            "a two-pillar floor for conveyance. Change a rule, then change a score._"]
    return "\n".join(out) + "\n"
