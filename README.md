# pullthrough

Did the coverage carry your message, or just your words?

Point it at a week of articles and a config of five or six narratives. It tells you, per narrative, whether the pillars survived the edit, which pieces turned the message against itself, and which pillar has never once appeared.

```
$ pullthrough run --articles out/stories.json
2026-11-12 · 5 pieces · 4 conveyed readings · report: out/pullthrough.md
```

## Why

Every comms team counts mentions. Mentions are cheap: a hostile headline that names your programme scores the same as a fair one that explains it. The question a director actually asks is different: *did the journalist carry the message we briefed?*

That question is usually answered from memory in a review meeting. This tool answers it from the text, the same way twice, with the reason printed next to the verdict.

**Four states, in order of judgement:**

| State | Rule |
|---|---|
| `absent` | no pillar keyword appears |
| `distorted` | a pillar sits within 90 characters of a reversal marker (`scraps`, `delays`, `u-turn`, `under fire`…) |
| `conveyed` | every required pillar appears, at least two pillars in total, nothing contradicts them |
| `mentioned` | a pillar appears, but not enough of the message to count |

A headline hit weighs double a body hit: the same words in the first line shape the story, in paragraph nine they decorate it.

## Install

Python 3.9+. No dependencies, no API keys, no model.

```bash
git clone https://github.com/sadok-ayari/pullthrough.git
cd pullthrough
python -m pullthrough run --articles tests/fixtures/articles.json
```

```bash
pip install -e . && pullthrough run --articles out/stories.json
```

## Configuration

`config/narratives.json`: five or six narratives, each with three to five pillars, each pillar a list of the words your spokespeople actually use.

```json
{
  "narratives": [{
    "id": "delivery",
    "name": "The money reaches the ground",
    "pillars": [
      {"id": "disbursed", "label": "Funds disbursed", "keywords": ["disbursed", "first tranche"]},
      {"id": "beneficiaries", "label": "Named beneficiaries", "keywords": ["households", "farmers"], "required": false}
    ]
  }]
}
```

`required: false` marks a pillar you would like to see but will not fail the message for. Change a keyword and the score moves: that is the point.

## Inputs

- a plain article list: `[{"title": ..., "summary": ..., "outlet": ..., "url": ..., "published": ...}]`
- a [coverage-radar](https://github.com/sadok-ayari/coverage-radar) `stories.json` export, so the two tools chain: collect and cluster coverage, then score message discipline on the same window
- anything that produces either shape (a scraper, an export from Muck Rack, a spreadsheet saved as JSON)

## Output

`out/pullthrough.md`: scorecard per narrative with pull-through percentage, the pieces that slipped with links and the reversal words that triggered it, pillars never carried, and an optional trend line from the archive.

`--json` prints the same numbers for a scheduler or a dashboard. `--trend` adds the archived series; `pullthrough trend` prints it on its own.

## How this lands in a working week

A tool nobody opens is a demo. This one is built to run on the coverage review you already hold:

- **Ritual:** the weekly coverage meeting. Its first page is this scorecard.
- **Trigger:** the same run that builds the clips digest also builds the scorecard, so nobody has to remember.
- **Format:** one screen, narratives first, numbers before narrative. Whatever the room already argues about, in the order it argues.
- **Owner:** whoever chairs the review, not the analyst. The analyst runs it.
- **Fail state:** a pillar at 0% for three weeks is either the wrong pillar or the wrong message. Both are findings.

## Honest limits

- Proximity is not comprehension. The reversal rule catches the obvious reversal and misses irony, attribution and rebuttal quotes. It is tuned to over-flag: a false "distorted" costs a check, a missed one costs a meeting.
- Pillars are words, not meaning. A journalist who conveys the narrative in her own vocabulary scores low. Fix that by adding her words to the pillar, or move to a model-based reading and accept you can no longer explain a number.
- English keyword matching by default. Config is language-agnostic; the example config is not.
- No fetching. It reads what you give it, which keeps it testable and keeps the credentials question out of scope.

## Tests

```bash
python -m unittest discover -s tests   # 27 tests, offline
```

## Licence

MIT. See [LICENSE](LICENSE).
