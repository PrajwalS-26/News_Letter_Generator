git remote add origin https://github.com/PrajwalS-26/News_Letter_Generator.git
git branch -M main
git push -u origin # Newsletter Generator - Salesforce AAA UVCE

An automated newsletter generation system using AI (Groq cloud or Ollama local) to collect, summarize, and generate weekly newsletters for the Salesforce AAA UVCE community.

## Features

- **RSS Feed Collection**: Automatically gathers articles from Salesforce blogs, AI news, and tech sources
- **AI-Powered Content**: Uses Groq (free, fast cloud) or Ollama (local) for content generation
- **HTML + PDF Output**: Generates both responsive HTML and downloadable PDF newsletters
- **Images**: Displays article images when available from RSS feeds
- **Web UI**: Beautiful Streamlit interface for easy use

## Quick Start (Groq - Recommended, Free)

### 1. Get Free Groq API Key

1. Go to [console.groq.com](https://console.groq.com)
2. Sign up (free)
3. Create an API key
4. Copy the key

### 2. Setup Project

```bash
cd "D:\NewsLetter generation"

# Install dependencies
pip install -r requirements.txt

# Create .env file
copy config\.env.example .env
```

### 3. Add Your API Key

Edit `.env` and add your Groq API key:

```
GROQ_API_KEY=gsk_your_key_here
```

### 4. Generate Newsletter

```bash
python generate.py
```

Or use the web UI:

```bash
streamlit run app.py
```

## Quick Start (Ollama - Local, No API Key)

### 1. Install Ollama

Download from [ollama.com](https://ollama.com/download)

### 2. Pull Model

```bash
ollama pull llama3.1:8b
```

### 3. Start Ollama

```bash
ollama serve
```

### 4. Edit Config

Change `config/newsletter.yaml`:

```yaml
llm:
  backend: "ollama"
  model: "llama3.1:8b"
```

### 5. Generate

```bash
python generate.py
```

## Usage

### Basic Commands

```bash
# Generate newsletter (HTML + PDF)
python generate.py

# Preview only (no files saved)
python generate.py --preview

# Generate HTML only (skip PDF)
python generate.py --no-pdf

# Use different model
python generate.py --model mistral
```

### Distribution

```bash
# Send via email
python generate.py --send email

# Send to multiple channels
python generate.py --send email slack

# Send with PDF attachment
python generate.py --send email --no-preview
```

### Options

| Option | Description |
|--------|-------------|
| `--preview` | Preview without saving files |
| `--send CHANNEL` | Send to email or slack |
| `--no-pdf` | Skip PDF generation |
| `--model MODEL` | Use different LLM model |
| `--output-dir DIR` | Custom output directory |
| `--date YYYY-MM-DD` | Set newsletter date |

## Configuration

### RSS Feeds (`config/feeds.yaml`)

Add or remove RSS feeds:

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
  
  llm:
    model: "llama3.1:8b"
    temperature: 0.7
  
  distribution:
    email:
      enabled: false
      smtp_host: "smtp.gmail.com"
```

### Environment Variables (`.env`)

```bash
# Ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b

# Email (Gmail example)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Slack
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
```

## Project Structure

```
newsletter-automation/
├── config/
│   ├── feeds.yaml          # RSS feed sources
│   ├── newsletter.yaml     # Newsletter settings
│   └── .env.example        # Environment template
├── src/
│   ├── collector/          # RSS & web scraping
│   ├── processor/          # Content filtering & LLM
│   ├── llm/                # Ollama client
│   ├── renderer/           # HTML & PDF generation
│   └── distribution/       # Email, Slack
├── templates/
│   └── newsletter.html     # HTML email template
├── output/                 # Generated newsletters
├── generate.py             # Entry point
└── requirements.txt        # Python dependencies
```

## Customization

### Changing the Template

Edit `templates/newsletter.html` to customize the newsletter design. The template uses Jinja2 syntax.

### Adding New Sources

1. Find the RSS feed URL
2. Add it to `config/feeds.yaml`
3. Specify the category (salesforce, ai, tech)

### Adjusting Content

Edit `config/newsletter.yaml` to change:
- Number of articles per section
- LLM temperature (creativity)
- Output formats

## Troubleshooting

### "Cannot connect to Ollama"

```bash
# Start Ollama service
ollama serve
```

### "Model not found"

```bash
# List available models
ollama list

# Pull the model
ollama pull llama3.1:8b
```

### PDF Generation Fails

WeasyPrint requires system dependencies. On Ubuntu/Debian:

```bash
sudo apt-get install libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev
```

On Windows, PDF generation may require additional setup. Use `--no-pdf` to skip.

## License

MIT License - Free to use and modify for your community.
