<div align="center">

# Football Scout RAG

A football scouting tool powered by RAG (Retrieval-Augmented Generation) that analyzes player statistics from Transfermarkt.

[Installation](#installation) •
[Usage](#usage) •
[Features](#features) •
[Documentation](#project-structure)

</div>

---

## Overview

Football Scout RAG combines web scraping, vector search, and LLM capabilities to provide data-driven player analysis. It fetches real player data from Transfermarkt and uses Groq's LLM for intelligent insights.

**Key capabilities:**
- Scout players and retrieve comprehensive statistics
- Compare players side-by-side with normalized metrics
- Find undervalued players ("hidden gems") based on value-to-performance ratio
- Search for similar players using vector embeddings
- Query player data using natural language

---

## Installation

**Requirements:** Python 3.11+

```bash
# Clone and enter directory
git clone https://github.com/yourusername/football-scout-rag
cd football-scout-rag

# Create virtual environment (using uv)
uv venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Install
uv pip install -e ".[dev]"
```

**Configuration:**

```bash
cp .env.example .env
```

Add your [Groq API key](https://console.groq.com) to `.env`:

```
GROQ_API_KEY=your_key_here
```

---

## Usage

### Command Line

| Command | Description |
|---------|-------------|
| `football-scout scout "Player Name"` | Scout a player |
| `football-scout compare "Player1" "Player2"` | Compare scouted players |
| `football-scout gems --max-value 5000000` | Find undervalued players |
| `football-scout compare-age "P1" "P2" --age 20` | Compare at same age |
| `football-scout ask "question"` | Query with natural language |
| `football-scout interactive` | Interactive session |

**Examples:**

```bash
# Scout multiple players
football-scout scout "Oscar Gloukh" "Florian Wirtz"

# Compare with table output
football-scout scout "Haaland" --format table

# Find hidden gems under €10M
football-scout gems --max-value 10000000 --min-apps 20
```

### Web Dashboard

```bash
streamlit run src/football_scout/dashboard/app.py
```

Opens at `http://localhost:8501`

---

## Features

### Hidden Gems Finder

Identifies undervalued players by calculating a value score:

```
value_score = (statistical_output / market_value) × normalization_factor
```

Players with high goals/assists per 90 minutes relative to their market value rank higher.

### Similarity Search

Uses ChromaDB to store player embeddings and find similar profiles based on:
- Position and playing style
- Statistical output (goals, assists, minutes)
- Age and market value bracket

### Age-Adjusted Comparisons

Compare players at equivalent career stages. Useful for evaluating young talent against established players at the same age.

---

## Project Structure

```
src/football_scout/
├── cli/           # Command-line interface (Typer)
├── core/          # Business logic
│   ├── agent.py       # Main orchestrator
│   ├── scraper.py     # Transfermarkt scraper
│   └── analyzer.py    # Statistics & comparisons
├── models/        # Pydantic data models
├── llm/           # LLM client (Groq)
├── rag/           # Vector store (ChromaDB)
├── dashboard/     # Streamlit web UI
└── config/        # Settings
```

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| LLM | Groq (Mixtral 8x7B) |
| Vector Store | ChromaDB |
| Web Scraping | aiohttp, BeautifulSoup |
| CLI | Typer, Rich |
| Web UI | Streamlit |
| Validation | Pydantic |

---

## Development

```bash
# Run tests
pytest tests/ -v

# Run specific test file
pytest tests/unit/test_analyzer.py -v
```

---

## License

MIT
