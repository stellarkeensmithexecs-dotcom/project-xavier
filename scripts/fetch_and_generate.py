import os
import json
import datetime as dt
import requests
import yaml
import frontmatter
from pathlib import Path
from jinja2 import Template
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
POSTS_DIR = DOCS / "posts"
CONFIG_DIR = ROOT / "config"

POST_TEMPLATE = """---
title: "{{ title }}"
date: "{{ date }}"
description: "{{ description }}"
---

# {{ title }}

{{ intro }}

## Top Picks

{% for item in items %}
- **[{{ item.title }}]({{ item.url }})** — {{ item.summary }}
{% endfor %}

## Calls to Action

{% for aff in affiliates %}
- **[{{ aff.title }}]({{ aff.url }})**
{% endfor %}

---

{{ footer_note }}
"""

EMAIL_TEMPLATE = """
Subject: {{ subject }}

{{ body }}
"""

def load_yaml(path: Path, default: dict):
    if not path.exists():
        return default
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or default


def fetch_hn(cfg: dict):
    if not cfg.get("enabled", True):
        return []
    try:
        top_ids = requests.get(cfg["api_top"], timeout=15).json()[: cfg.get("top_n", 10)]
        items = []
        for _id in top_ids:
            data = requests.get(cfg["api_item"].format(id=_id), timeout=10).json()
            if not data:
                continue
            if data.get("score", 0) < cfg.get("min_score", 0):
                continue
            title = data.get("title")
            url = data.get("url") or f"https://news.ycombinator.com/item?id={data.get('id')}"
            items.append({
                "title": title,
                "url": url,
                "summary": f"HN score {data.get('score', 0)}"
            })
        return items
    except Exception as e:
        print("[warn] HN fetch failed:", e)
        return []


def fetch_devto(cfg: dict):
    if not cfg.get("enabled", True):
        return []
    try:
        res = requests.get(cfg["api"], timeout=15)
        res.raise_for_status()
        articles = res.json()[:20]
        items = []
        for a in articles:
            items.append({
                "title": a.get("title"),
                "url": a.get("url"),
                "summary": f"by @{a.get('user', {}).get('username', 'unknown')}"
            })
        return items
    except Exception as e:
        print("[warn] DEV.to fetch failed:", e)
        return []


def collect_items(sources_cfg: dict):
    items = []
    items += fetch_hn(sources_cfg.get("hacker_news", {}))
    items += fetch_devto(sources_cfg.get("devto", {}))
    # Future: add RSS, GitHub search, etc. using only ToS-compliant endpoints
    # dedupe by URL
    seen = set()
    deduped = []
    for it in items:
        if it["url"] in seen:
            continue
        seen.add(it["url"])
        deduped.append(it)
    return deduped[:30]


def add_utm(url: str, source: str, medium: str, campaign: str) -> str:
    try:
        parts = urlparse(url)
        q = dict(parse_qsl(parts.query, keep_blank_values=True))
        q.setdefault("utm_source", source)
        q.setdefault("utm_medium", medium)
        q.setdefault("utm_campaign", campaign)
        new_query = urlencode(q, doseq=True)
        return urlunparse((parts.scheme, parts.netloc, parts.path, parts.params, new_query, parts.fragment))
    except Exception:
        return url


def render_post(items, monetization_cfg, medium: str = "site"):
    today = dt.datetime.utcnow().date()
    title = f"Daily Dev Picks — {today.isoformat()}"
    description = "Daily curated insights for IT, AI, and Fintech: tools, articles, and playbooks."
    if medium == "email":
        intro = "Today’s IT/AI/Fintech picks — short, actionable, and vetted."
    else:
        intro = monetization_cfg.get("cta_subtitle", "Daily picks. No fluff.")
    raw_affiliates = monetization_cfg.get("affiliates", [])
    # UTM tagging for affiliates/CTAs
    source = "project-xavier"
    campaign = today.isoformat()
    affiliates = []
    for aff in raw_affiliates:
        u = aff.get("url", "")
        aff_url = add_utm(u, source=source, medium=medium, campaign=campaign) if u else u
        affiliates.append({"title": aff.get("title", ""), "url": aff_url})
    footer_note = monetization_cfg.get("footer_note", "")
    tpl = Template(POST_TEMPLATE)
    content = tpl.render(
        title=title,
        date=today.isoformat(),
        description=description,
        intro=intro,
        items=items,
        affiliates=affiliates,
        footer_note=footer_note,
    )
    return title, content


def write_post(title, content):
    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{dt.datetime.utcnow().date().isoformat()}.md"
    path = POSTS_DIR / filename
    if path.exists():
        print("[info] Post already exists, overwriting")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    # update posts index with newest-first list
    post_files = sorted(POSTS_DIR.glob("*.md"), reverse=True)
    with open(POSTS_DIR / "index.md", "w", encoding="utf-8") as f:
        f.write("# Posts\n\n")
        for p in post_files:
            if p.name == "index.md":
                continue
            f.write(f"- [{p.stem}]({p.name})\n")
    return path


def maybe_send_buttondown_email(subject: str, markdown_body: str):
    api_key = os.getenv("BUTTONDOWN_API_KEY")
    if not api_key:
        print("[info] BUTTONDOWN_API_KEY not set; skipping email")
        return
    try:
        # Create draft
        resp = requests.post(
            "https://api.buttondown.email/v1/emails",
            headers={"Authorization": f"Token {api_key}"},
            json={
                "subject": subject,
                "body": markdown_body,
                "publish_date": None,
                "to": "Everyone",
            },
            timeout=20,
        )
        resp.raise_for_status()
        email = resp.json()
        print("[info] Created Buttondown email draft:", email.get("id"))
    except Exception as e:
        print("[warn] Buttondown email failed:", e)


def main():
    sources_cfg = load_yaml(ROOT / "sources.yml", {})
    monetization_cfg = load_yaml(CONFIG_DIR / "monetization.yml", {})
    items = collect_items(sources_cfg)
    if not items:
        print("[warn] No items collected; generating CTA-only post")
    title, content = render_post(items, monetization_cfg, medium="site")
    path = write_post(title, content)
    print(f"[info] Wrote post: {path}")
    # Render a refined email body with email-specific UTM params
    _, email_body = render_post(items, monetization_cfg, medium="email")
    maybe_send_buttondown_email(title, email_body)


if __name__ == "__main__":
    main()
