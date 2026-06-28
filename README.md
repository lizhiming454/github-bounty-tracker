# 🎯 GitHub Bounty Tracker

> Automatically scans GitHub repositories for open issues tagged with bounty labels — extracts dollar amounts, ranks by reward, and outputs as a table, JSON, or CSV.

[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://python.org)
[![GitHub API](https://img.shields.io/badge/GitHub-API-black)](https://docs.github.com/en/rest)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## ✨ Features

- **Multi-repo scanning** — scan any list of GitHub repos for bounty-labeled issues
- **Public search mode** — search all of GitHub for open bounty issues at once
- **Auto amount extraction** — parses `$100`, `$500 bounty` etc. from titles and bodies
- **Ranked output** — sorts by USD reward descending
- **Multiple output formats** — pretty table, JSON, or CSV export
- **Watch mode** — runs continuously on a configurable interval
- **Rate-limit aware** — respects GitHub API limits, auto-waits when throttled

---

## 🚀 Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/lizhiming454/github-bounty-tracker.git
cd github-bounty-tracker
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure
```bash
cp .env.example .env
# Add your GitHub token (optional but recommended for higher rate limits)
```

### 4. Run it

```bash
# Scan repos listed in .env
python bounty_tracker.py

# Search ALL public GitHub issues for bounties
python bounty_tracker.py --search

# Export as CSV
python bounty_tracker.py --search --output csv

# Watch mode — re-scans every 5 minutes
python bounty_tracker.py --watch

# Extra search query filter
python bounty_tracker.py --search --query "language:python"
```

---

## 📊 Example Output

```
╭──────────────────────────────┬───────┬───────────────────────────────────────┬────────┬────────────┬────╮
│ Repo                         │ #     │ Title                                 │ Amount │ Created    │ 💬 │
├──────────────────────────────┼───────┼───────────────────────────────────────┼────────┼────────────┼────┤
│ nicehash/NiceHashQuickMiner  │ #892  │ [Bounty $500] Fix GPU detection bug   │ $500   │ 2025-05-10 │  3 │
│ some-org/their-project       │ #201  │ bounty - improve API response time    │ ?      │ 2025-06-15 │  0 │
╰──────────────────────────────┴───────┴───────────────────────────────────────┴────────┴────────────┴────╯

  Total: 2 bounty issue(s) found
```

---

## ⚙️ Configuration (`.env`)

| Variable | Default | Description |
|---|---|---|
| `GITHUB_TOKEN` | — | GitHub Personal Access Token (5000 req/hour vs 60 without) |
| `REPOS` | — | Comma-separated `owner/repo` list to scan |
| `BOUNTY_LABELS` | `bounty,Bounty,...` | Label names to look for |
| `MIN_AMOUNT` | `0` | Skip issues below this USD amount |
| `OUTPUT_FORMAT` | `table` | Default output format |
| `WATCH_INTERVAL` | `300` | Seconds between scans in watch mode |

---

## 📁 Project Structure

```
github-bounty-tracker/
├── bounty_tracker.py   # Main script (single-file, batteries included)
├── requirements.txt    # Dependencies
├── .env.example        # Config template
├── .gitignore
├── LICENSE (MIT)
└── output/             # CSV/JSON exports (auto-created)
```

---

## 📄 License

MIT License — free to use, modify, and distribute.

---

## 🤝 Contributing

Pull requests are welcome! Please open an issue first to discuss major changes.
