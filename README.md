# 🛡️ PatchWatch

AI-powered security vulnerability scanner that hooks into your GitHub repos. Every push triggers an automated security review of your code changes.

## What It Does

```
Push to GitHub → Webhook fires → PatchWatch fetches the diff → AI scans for vulnerabilities → Report generated → Context saved for next commit
```

1. **Webhook Listener** — Receives GitHub push events in real-time
2. **Diff Fetcher** — Pulls the exact code changes from the commit via GitHub API
3. **AI Security Scanner** — Two models (MiniMax M2.7 + Qwen 3 Coder) analyze the diff in parallel using LangChain
4. **Memory Layer** — Saves a condensed summary after each scan so the next commit can be compared against it (new vs recurring vs resolved issues)
5. **Report Generator** — Structured markdown report per commit with severity breakdown

## How It Handles Large Commits (2000+ lines)

Large commits don't break PatchWatch. The system handles them through a multi-layer filtering pipeline:

1. **Skip noise files** — `package-lock.json`, `.min.js`, images, build artifacts, and lock files are filtered out before anything reaches the AI. This alone cuts most large commits in half.

2. **Chunk by file** — The diff is split per file. Each file is scanned individually with its own LLM call. A 2000-line commit touching 15 files becomes 15 separate, manageable scans.

3. **Extract only changed lines** — From each file's patch, only the `+` (added) and `-` (removed) lines are sent to the AI, not the full file. A 500-line file with 20 changed lines becomes a 20-line scan.

4. **Prioritize by risk** — Files are sorted by security risk before scanning. `.env`, auth files, config files, SQL migrations go first. If the commit is massive, the highest-risk files always get scanned.

5. **Parallel dual-model scan** — Both AI models scan each file simultaneously, so wall-clock time stays low even with many files.

The result: a 2000-line commit with 30 files might produce only 5-8 actual AI calls on ~200 lines of meaningful changed code.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Server | FastAPI |
| AI | LangChain + ChatOpenAI (MiniMax M2.7, Qwen 3 Coder via OpenRouter) |
| Database | SQLAlchemy + SQLite (async) |
| GitHub | httpx + Webhooks |

## API

| Method | Endpoint | What it does |
|--------|----------|-------------|
| `POST` | `/webhook/github` | Receives push events from GitHub |
| `POST` | `/scan/` | Manual scan — pass any repo + commit SHA |
| `GET` | `/reports/` | List scan reports (filter by repo, branch) |
| `GET` | `/reports/{id}` | Full vulnerability report |
| `GET` | `/reports/{id}/markdown` | Just the markdown report |
| `GET` | `/reports/commit/{sha}` | Lookup report by commit SHA |

## Project Structure

```
app/
├── main.py                    # FastAPI entry point
├── config.py                  # Environment settings
├── database.py                # Async SQLAlchemy + SQLite
├── models.py                  # ScanReport + CommitMemory tables
├── schemas.py                 # Pydantic models
├── routers/
│   ├── webhook.py             # GitHub webhook handler
│   ├── reports.py             # Report retrieval API
│   └── scan.py                # Manual scan endpoint
├── services/
│   ├── github_service.py      # GitHub API client
│   ├── scanner.py             # LangChain dual-model security scanner
│   ├── memory.py              # Cross-commit memory & comparison
│   └── report_generator.py    # Markdown report builder
└── utils/
    └── diff_parser.py         # Diff filtering, prioritization & chunking
```

## Environment Variables

```
GITHUB_WEBHOOK_SECRET    # Secret for verifying webhook signatures
GITHUB_TOKEN             # GitHub PAT (needed for private repos)
MINIMAX_API_KEY          # MiniMax API key (primary scanner)
OPENROUTER_API_KEY       # OpenRouter API key (Qwen 3 Coder)
```
