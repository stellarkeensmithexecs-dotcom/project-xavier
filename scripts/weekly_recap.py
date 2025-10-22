import datetime as dt
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
POSTS_DIR = DOCS / "posts"

WEEKLY_TEMPLATE = """---
title: "Weekly Recap — Week {{ week }} of {{ year }}"
date: "{{ date }}"
description: "Top IT/AI/Fintech picks of the week with a product CTA."
---

# Weekly Recap — Week {{ week }} of {{ year }}

A concise recap of the week’s best in IT, AI, and Fintech.

## Top Links of the Week

{% for item in items %}
- **[{{ item.title }}]({{ item.url }})**
{% endfor %}

## Product Spotlight

- **[PROJECT XAVIER: AI/Fintech Daily Edge Pack]({{ product_url }})** — Sharpen decisions with briefs, playbooks, templates.

---

This email/site may include affiliate links.
"""

from jinja2 import Template

def parse_daily_links(md_path: Path):
    links = []
    try:
        for line in md_path.read_text(encoding="utf-8").splitlines():
            # Match lines like: - **[Title](URL)** — summary
            m = re.match(r"^- \*\*\[(.+?)\]\((https?://[^\s)]+)\)\*\*", line.strip())
            if m:
                title, url = m.group(1), m.group(2)
                links.append({"title": title, "url": url})
    except Exception:
        pass
    return links


def collect_week_links(days=7):
    today = dt.date.today()
    start = today - dt.timedelta(days=days)
    items = []
    for p in sorted(POSTS_DIR.glob("*.md"), reverse=True):
        if p.name == "index.md":
            continue
        # Expect filenames like YYYY-MM-DD.md
        try:
            stem = p.stem
            d = dt.date.fromisoformat(stem)
        except Exception:
            continue
        if d < start:
            continue
        items.extend(parse_daily_links(p))
    # Deduplicate by URL and cap
    seen = set()
    deduped = []
    for it in items:
        if it["url"] in seen:
            continue
        seen.add(it["url"])
        deduped.append(it)
    return deduped[:25]


def main():
    today = dt.date.today()
    iso = today.isocalendar()
    week = f"{iso.week:02d}"
    year = iso.year
    items = collect_week_links(days=7)
    tpl = Template(WEEKLY_TEMPLATE)
    product_url = "https://www.paypal.com/ncp/payment/9AGGT2R7M8A6C?utm_source=site&utm_medium=weekly&utm_campaign=" + today.isoformat()
    content = tpl.render(week=week, year=year, date=today.isoformat(), items=items, product_url=product_url)
    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    out = POSTS_DIR / f"weekly-{year}-W{week}.md"
    out.write_text(content, encoding="utf-8")
    # update posts index
    post_files = sorted(POSTS_DIR.glob("*.md"), reverse=True)
    with open(POSTS_DIR / "index.md", "w", encoding="utf-8") as f:
        f.write("# Posts\n\n")
        for p in post_files:
            if p.name == "index.md":
                continue
            f.write(f"- [{p.stem}]({p.name})\n")
    print(f"[info] Wrote weekly recap: {out}")

if __name__ == "__main__":
    main()
