"""aireg validate register/   and   aireg report register/ --out site/"""
from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

from .register import load_register, validate
from .report import html_page, markdown
from .triage import triage


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="aireg", description="Validate and report on an AI use case register.")
    sub = p.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("validate", help="check every entry against the schema")
    v.add_argument("folder", nargs="?", default="register")
    r = sub.add_parser("report", help="triage every entry and write Markdown and HTML reports")
    r.add_argument("folder", nargs="?", default="register")
    r.add_argument("--out", default="site")
    r.add_argument("--org", default="Example Retail Ltd (fictional)")
    r.add_argument("--today", help="report date, YYYY-MM-DD (defaults to today)")
    r.add_argument("--fail-on", choices=["stop", "high", "never"], default="stop",
                   help="exit 1 if any gap at this severity or worse is found")
    a = p.parse_args(argv)

    entries = load_register(Path(a.folder))
    errors = validate(entries)
    if errors:
        print("\n".join(errors))
        print(f"\n{len(errors)} schema error(s) in {len(entries)} file(s).")
        return 1
    if a.cmd == "validate":
        print(f"All {len(entries)} use cases are valid.")
        return 0

    today = dt.date.fromisoformat(a.today) if a.today else dt.date.today()
    items = [(uc, triage(uc, today)) for _, uc in entries]
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    md = markdown(items, today, a.org)
    (out / "register.md").write_text(md, encoding="utf-8")
    (out / "index.html").write_text(html_page(items, today, a.org), encoding="utf-8")
    print(md)
    worst = {"stop": 0, "high": 1, "medium": 2, "low": 3}
    if a.fail_on != "never":
        limit = worst[a.fail_on]
        if any(worst[s] <= limit for _, t in items for s, _ in t.gaps):
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
