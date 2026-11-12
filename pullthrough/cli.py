from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone

from . import __version__, report, score
from .models import articles_from, load_json, narratives_from
from .store import Store


def today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pullthrough",
                                     description="Score whether coverage carried your narrative.")
    parser.add_argument("--version", action="version", version=f"pullthrough {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="read articles against the narrative config")
    run.add_argument("--config", default="config/narratives.json")
    run.add_argument("--articles", required=True,
                     help="article JSON, or a coverage-radar stories.json export")
    run.add_argument("--out", default="out")
    run.add_argument("--db", default="pullthrough.db")
    run.add_argument("--day", default=None, help="archive day, default today (UTC)")
    run.add_argument("--trend", action="store_true", help="include the archived trend")
    run.add_argument("--json", action="store_true")

    show = sub.add_parser("trend", help="print archived pull-through by narrative")
    show.add_argument("--db", default="pullthrough.db")
    show.add_argument("--limit", type=int, default=14)
    show.add_argument("--config", default="config/narratives.json")
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "trend":
        narratives = narratives_from(load_json(args.config))
        store = Store(args.db)
        for narrative in narratives:
            series = store.history(narrative.id, args.limit)
            points = []
            for day, states in series:
                total = sum(states.values()) or 1
                points.append(f"{day}: {round(100 * states.get('conveyed', 0) / total)}%")
            print(f"{narrative.name}: " + (" · ".join(points) if points else "no history"))
        store.close()
        return 0

    try:
        config = load_json(args.config)
        narratives = narratives_from(config)
        articles = articles_from(args.articles)
    except (OSError, ValueError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if not narratives:
        print("error: config has no narratives", file=sys.stderr)
        return 2

    readings = score.read_all(articles, narratives)
    day = args.day or today()
    store = Store(args.db)
    store.save(day, readings)
    trend = None
    if args.trend:
        trend = {n.id: store.history(n.id) for n in narratives}
    store.close()

    os.makedirs(args.out, exist_ok=True)
    path = os.path.join(args.out, "pullthrough.md")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(report.render(readings, narratives, day, trend,
                                   title=config.get("title", "Message pull-through")))

    counts = report.summary(readings)
    if args.json:
        print(json.dumps({
            "day": day,
            "articles": len({r.article.key for r in readings}),
            "narratives": {k: v for k, v in counts.items()},
            "report": path,
        }, indent=2))
    else:
        conveyed = sum(int(v["conveyed"]) for v in counts.values())  # type: ignore[arg-type]
        print(f"{day} · {len(articles)} pieces · {conveyed} conveyed readings · report: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
