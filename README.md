# Auto Revenue Newsletter (Daily Curated Tech Deals/Insights)

This project automates a daily content pipeline that:

- Generates a daily curated post from free sources (Hacker News API, DEV.to API).
- Publishes it to a static site (MkDocs + GitHub Pages).
- Optionally emails it to subscribers via Buttondown (free tier) if you provide an API key.

It is intended as a starting point for a legitimate content + affiliate/sponsorship model. Revenue is not guaranteed; you must grow an audience and add monetization (affiliate links, sponsorships, your own products).

## Features

- Daily GitHub Actions cron (free) builds and deploys a site.
- Content sources are configured in `sources.yml`.
- Post generation inserts your call-to-action and affiliate links defined in `config/monetization.yml`.
- Optional Buttondown email sending (set `BUTTONDOWN_API_KEY`).

## Quick Start

1. Create a new GitHub repository and push this folder.
2. Enable GitHub Pages: Deploy from `gh-pages` branch.
3. Add repository secrets (Settings → Secrets and variables → Actions):
   - `BUTTONDOWN_API_KEY` (optional, for email sending)
   - `SITE_BASE_URL` (e.g., `https://<your-user>.github.io/<repo>`)
4. The workflow will run on a schedule daily and on every push.

## Local development

```bash
python -m venv .venv
. .venv/Scripts/activate  # on Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts/fetch_and_generate.py
mkdocs serve
```

Then open `http://127.0.0.1:8000`.

## Customize

- Edit `config/monetization.yml` to add your CTAs and affiliate links.
- Edit `sources.yml` to change sources.
- Change branding in `mkdocs.yml`.

## Monetization ideas

- Add affiliate links to relevant tools/courses in the daily post CTA.
- Offer weekly sponsorship slots in the email/newsletter.
- Sell your own templates/tools and link them from the post.

## Compliance notes

- Review each source's API/ToS before adding new sources.
- No scraping: this project uses public APIs and RSS endpoints.
- Email sending uses Buttondown; comply with their ToS and email laws.

## Disclaimer

This project does not guarantee earnings. It provides infrastructure to help you operate a small content-based business. Your execution (niche, quality, distribution) drives results.
