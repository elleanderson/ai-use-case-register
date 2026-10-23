"""Build the Markdown and HTML reports."""
from __future__ import annotations

import datetime as dt
import html
from collections import Counter

from .triage import CATEGORY_LABEL, CATEGORY_ORDER, Triage

SEVERITY_ORDER = {"stop": 0, "high": 1, "medium": 2, "low": 3}
SEVERITY_LABEL = {"stop": "Stop", "high": "High", "medium": "Medium", "low": "Low"}


def _rows(items: list[tuple[dict, Triage]]):
    return sorted(items, key=lambda x: (CATEGORY_ORDER.index(x[1].category), x[0]["id"]))


def markdown(items: list[tuple[dict, Triage]], today: dt.date, org: str) -> str:
    cats = Counter(t.category for _, t in items)
    all_gaps = [(uc, s, m) for uc, t in items for s, m in t.gaps]
    lines = [
        f"# AI Use Case Register: {org}",
        "",
        f"Generated on {today.day} {today:%B %Y}. {len(items)} use cases, {len(all_gaps)} gaps to close.",
        "",
        "| " + " | ".join(CATEGORY_LABEL[c] for c in CATEGORY_ORDER) + " |",
        "|" + "---|" * len(CATEGORY_ORDER),
        "| " + " | ".join(str(cats.get(c, 0)) for c in CATEGORY_ORDER) + " |",
        "",
        "## Use Cases",
        "",
        "| ID | Use Case | Status | Indicative Category | Applies From | Gaps |",
        "|---|---|---|---|---|---|",
    ]
    for uc, t in _rows(items):
        lines.append(f"| {uc['id']} | {uc['name']} | {uc['status'].title()} | {t.label} | {t.applies_from} | {len(t.gaps)} |")
    lines += ["", "## Gaps to Close", ""]
    for uc, s, m in sorted(all_gaps, key=lambda g: (SEVERITY_ORDER[g[1]], g[0]["id"])):
        lines.append(f"- **{SEVERITY_LABEL[s]}** · {uc['id']} {uc['name']}: {m}")
    lines += ["", "_An indicative triage to help teams prioritise, not legal advice._", ""]
    return "\n".join(lines)


CSS = """
:root{--abyss:#0A1F1C;--pine:#12332E;--panel:#0F2A26;--cream:#F3EEE2;--dim:rgba(243,238,226,.66);--hair:rgba(243,238,226,.12);--gold:#CFB36A;--rust:#C7795F;--sage:#7FA89A}
*{box-sizing:border-box}body{margin:0;background:var(--abyss);color:var(--cream);font:16px/1.6 'IBM Plex Sans',system-ui,sans-serif}
.wrap{max-width:1080px;margin:0 auto;padding:40px 22px 60px}h1,h2{font-family:Fraunces,Georgia,serif;font-weight:500}
h1{font-size:clamp(30px,4vw,46px);margin:0 0 8px}h2{font-size:26px;margin:40px 0 14px}.lede{color:var(--dim);margin:0 0 26px;max-width:62ch}
.eyebrow{font:500 11.5px 'IBM Plex Mono',monospace;letter-spacing:.16em;text-transform:uppercase;color:var(--gold)}
.tiles{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}.tile{background:var(--panel);border:1px solid var(--hair);border-radius:14px;padding:16px}
.tile b{display:block;font:500 34px Fraunces,Georgia,serif}.tile span{font:11px 'IBM Plex Mono',monospace;letter-spacing:.12em;text-transform:uppercase;color:var(--dim)}
.tile.prohibited{border-color:var(--rust)}.tile.high-risk{border-color:rgba(207,179,106,.6)}
.cards{display:grid;gap:14px}.card{background:var(--panel);border:1px solid var(--hair);border-radius:14px;padding:18px 20px}
.card h3{margin:0;font:500 21px Fraunces,Georgia,serif}.meta{color:var(--dim);font-size:13.5px;margin:4px 0 10px}
.pill{display:inline-block;font:600 10.5px 'IBM Plex Mono',monospace;letter-spacing:.1em;text-transform:uppercase;padding:3px 8px;border-radius:999px;border:1px solid var(--gold);color:var(--gold);margin-right:6px}
.pill.prohibited{border-color:var(--rust);color:var(--rust)}.pill.minimal{border-color:var(--sage);color:var(--sage)}
.basis{font-size:14px;color:var(--dim)}ul.gaps{margin:10px 0 0;padding-left:0;list-style:none}ul.gaps li{padding:6px 0;border-top:1px solid var(--hair);font-size:14.5px}
.sev{font:600 10px 'IBM Plex Mono',monospace;letter-spacing:.1em;text-transform:uppercase;margin-right:8px}.sev.stop{color:var(--rust)}.sev.high{color:var(--gold)}.sev.medium{color:var(--cream)}.sev.low{color:var(--dim)}
.ok{color:var(--sage);font-size:14px;margin-top:8px}footer{margin-top:40px;color:var(--dim);font-size:13.5px;border-top:1px solid var(--hair);padding-top:16px}a{color:var(--gold)}
@media(max-width:640px){.tiles{grid-template-columns:repeat(2,minmax(0,1fr))}}
"""


def html_page(items: list[tuple[dict, Triage]], today: dt.date, org: str) -> str:
    e = html.escape
    cats = Counter(t.category for _, t in items)
    n_gaps = sum(len(t.gaps) for _, t in items)
    tiles = "".join(f'<div class="tile {c}"><b>{cats.get(c, 0)}</b><span>{CATEGORY_LABEL[c]}</span></div>' for c in CATEGORY_ORDER)
    cards = []
    for uc, t in _rows(items):
        gaps = "".join(
            f'<li><span class="sev {s}">{SEVERITY_LABEL[s]}</span>{e(m)}</li>'
            for s, m in sorted(t.gaps, key=lambda g: SEVERITY_ORDER[g[0]])
        ) or ""
        body = f'<ul class="gaps">{gaps}</ul>' if gaps else '<p class="ok">No gaps found.</p>'
        cards.append(
            f'<article class="card"><span class="pill {t.category}">{t.label}</span><span class="pill">{e(uc["status"].title())}</span>'
            f'<h3>{e(uc["id"])} &middot; {e(uc["name"])}</h3>'
            f'<p class="meta">Owner: {e(uc["owner"])} &middot; Applies from {e(t.applies_from)}</p>'
            f'<p>{e(uc["purpose"])}</p><p class="basis">{e(t.basis)}</p>{body}</article>'
        )
    return f"""<!doctype html>
<html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AI Use Case Register. {e(org)}</title>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500&family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@400;600&display=swap" rel="stylesheet">
<style>{CSS}</style></head><body><div class="wrap">
<p class="eyebrow">AI Use Case Register</p><h1>{e(org)}</h1>
<p class="lede">{len(items)} AI use cases, sorted by indicative EU AI Act category, with {n_gaps} governance gaps to close. Generated on {today.day} {today:%B %Y}.</p>
<div class="tiles">{tiles}</div>
<h2>Use Cases</h2><div class="cards">{''.join(cards)}</div>
<footer>An indicative triage to help teams prioritise, not legal advice. Dates follow the AI Act as amended by Regulation (EU) 2026/1744.
Built with <a href="https://github.com/elleanderson/ai-use-case-register">AI Use Case Register</a> by <a href="https://andersonco.uk">Elle Anderson</a>.</footer>
</div></body></html>"""
