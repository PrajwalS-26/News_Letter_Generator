# Salesforce AAA UVCE Official Digest

An automated **Static Site Generator** that collects RSS news, summarizes the top stories with the **Groq** LLM, and publishes a production-grade website to **`public/index.html`** — automatically hosted on **GitHub Pages**.

The pipeline runs on a **cron schedule via GitHub Actions** (every Monday, Wednesday and Friday), so the digest stays fresh without any manual work.

## Features

- **RSS Feed Collection** — gathers stories from Salesforce blogs, AI news, and tech sources (`config/feeds.yaml`)
- **AI Summarization** — Groq-powered summaries, section intros, and a newsletter introduction
- **Controllable Article Count** — choose exactly how many stories appear per section (default: 5)
- **Static Website Output** — a single `public/index.html` overwritten on every build, ready for GitHub Pages
- **Automated Publishing** — GitHub Actions cron + manual `workflow_dispatch` trigger
- **Article Images** — displays images pulled from RSS feeds when available
- **Social Footer** — Instagram and LinkedIn links to the club's official pages
- **Optional Distribution** — push a summary to Slack or email a copy after publishing

## Quick Start

### 1. Get a Free Groq API Key

1. Go to [console.groq.com](https://console.groq.com)
2. Sign up (free) and create an API key
3. Copy the key

### 2. Setup

```bash
cd News_Letter_Generator

# Install dependencies
pip install -r requirements.txt

# Create the environment file and add your key
copy config\.env.example .env
```

Set `GROQ_API_KEY=gsk_your_key_here` inside `.env`.

### 3. Generate the Site

```bash
python generate.py
```

This overwrites `public/index.html` with the latest edition.

## Controlling the Number of News

You control how many stories appear **per section** two ways:

### Option A — Config file (default)

Edit `config/newsletter.yaml`:

```yaml
newsletter:
  max_articles_per_section: 5   # stories shown under each section heading
```

A value of `5` gives at least five news items per section (Salesforce Updates, AI & Machine Learning, Tech Industry News) whenever the feeds produce enough stories in the collection window.

### Option B — CLI flag (override, no config edit)

```bash
python generate.py --articles-per-section 5
```

If a section still looks light, widen the **collection window** so the feeds have more recent stories to draw from:

```bash
python generate.py --days-back 14
```

> **Note:** each section shows up to `max_articles_per_section` stories. If a category has fewer stories published within the look-back window, that section will naturally have fewer — add more feeds in `config/feeds.yaml` or increase `--days-back` to fill it out.

## Usage

### Commands

```bash
# Build the site (default: 5 stories per section, last 7 days)
python generate.py

# Build with 6 stories per section
python generate.py --articles-per-section 6

# Collect from the last 14 days
python generate.py --days-back 14

# Build without distributing
python generate.py --preview

# Build and distribute to channels
python generate.py --send email slack
```

### Options

| Option | Description |
|--------|-------------|
| `--articles-per-section N` | Stories per section (overrides config, default 5) |
| `--days-back N` | RSS look-back window in days (default 7) |
| `--preview` | Build without sending to any channel |
| `--send CHANNEL` | Distribute to `email` and/or `slack` |
| `--model MODEL` | Override the Groq model |
| `--date YYYY-MM-DD` | Override the edition date |

## Automated Publishing (GitHub Actions)

`.github/workflows/publish.yml` runs on a schedule:

```yaml
schedule:
  - cron: "30 10 * * 1,3,5"   # Mon, Wed, Fri at 10:30 UTC
```

It also supports a manual **"Run workflow"** button via `workflow_dispatch`.

### Setup for the first deploy

1. **Add the API key** — GitHub repo → Settings → Secrets and variables → Actions → add `GROQ_API_KEY`
2. **Enable Pages** — repo → Settings → Pages → Source: **Deploy from a branch** → `gh-pages`
3. Commit and push. The workflow builds `public/` and deploys it to the `gh-pages` branch with `peaceiris/actions-gh-pages`.

Your live site will be at `https://<username>.github.io/News_Letter_Generator/`.

> **Important:** the club logo lives in `public/assets/club-logo.jpeg` and is deployed with the site. Keep it committed so it ships on every build.

## Configuration

### RSS Feeds (`config/feeds.yaml`)

Add or remove feeds per category:

```yaml
salesforce:
  - name: "Salesforce Blog"
    url: "https://www.salesforce.com/blog/feed/"
    category: "salesforce"

ai_news:
  - name: "OpenAI Blog"
    url: "https://openai.com/news/rss.xml"
    category: "ai"
```

### Newsletter Settings (`config/newsletter.yaml`)

```yaml
newsletter:
  name: "Salesforce AAA UVCE Weekly Digest"
  organization: "Salesforce AAA UVCE"
  tagline: "Your weekly dose of Salesforce & AI updates"
  max_articles_per_section: 5

  llm:
    model: "openai/gpt-oss-120b"
    temperature: 0.7

  distribution:
    email:
      enabled: false
    slack:
      enabled: false
```

### Environment Variables (`.env`)

```bash
# Required
GROQ_API_KEY=gsk_your_key_here

# Email (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_RECIPIENTS=a@example.com,b@example.com

# Slack (optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
SLACK_CHANNEL=#newsletter
```

## Project Structure

```
News_Letter_Generator/
├── .github/workflows/
│   └── publish.yml        # Cron + manual publish to GitHub Pages
├── config/
│   ├── feeds.yaml         # RSS feed sources
│   └── newsletter.yaml    # Newsletter settings & article counts
├── public/                # Published site (deployed to gh-pages)
│   ├── assets/
│   │   └── club-logo.jpeg # Brand logo served with the site
│   └── index.html         # Generated by generate.py
├── src/
│   ├── collector/         # RSS collection
│   ├── processor/         # Filtering, ranking & LLM composition
│   ├── llm/               # Groq client
│   ├── renderer/          # Jinja2 -> static HTML
│   └── distribution/      # Email & Slack
├── templates/
│   └── newsletter.html    # Website template (Jinja2)
├── app.py                 # Optional Streamlit preview UI
├── generate.py            # SSG entry point
└── requirements.txt
```

## Customization

### Changing the Template

Edit `templates/newsletter.html` (Jinja2) — the fixed header, hero, article cards, footer social links, and all CSS live there.

### Adding New Sources

1. Find the RSS feed URL
2. Add it to `config/feeds.yaml`
3. Give it a category (`salesforce`, `ai`, or `tech`)

### Previewing Locally

Serve the built site with any static server:

```bash
python -m http.server 8000 --directory public
```

Then open `http://localhost:8000/`. Or use the Streamlit dashboard:

```bash
streamlit run app.py
```

## Troubleshooting

### "GROQ_API_KEY not set"

Add your key to `.env` or set the `GROQ_API_KEY` repository secret.

### "No articles found"

- Check that the feeds in `config/feeds.yaml` are reachable
- Increase the look-back window: `python generate.py --days-back 14`
- Some sources publish infrequently; add more feeds to the category

### A section has fewer stories than `max_articles_per_section`

The section can only show as many stories as the feeds produced in the look-back window. Add more feeds or widen `--days-back`.

## License

MIT License - Free to use and modify for your community.
