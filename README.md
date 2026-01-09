# Football Scout RAG

AI-powered football scouting agent using Retrieval-Augmented Generation (RAG) to analyze player statistics from Transfermarkt and provide intelligent insights.

## Features

- **Player Scouting**: Fetch comprehensive player data including career statistics from Transfermarkt
- **Intelligent Comparison**: Compare multiple players using AI-powered analysis
- **Hidden Gems Finder**: Discover undervalued players based on statistical output vs market value
- **Similarity Search**: Find players similar to a given profile using vector embeddings
- **Age-Adjusted Comparisons**: Compare players at the same career stage
- **Natural Language Queries**: Ask follow-up questions in natural language
- **Beautiful CLI**: Rich terminal output with progress indicators and tables
- **Web Dashboard**: Interactive Streamlit dashboard for visual exploration

## Installation

### Prerequisites
- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Quick Start with uv (Recommended)

```powershell
# Clone the repository
git clone https://github.com/yourusername/football-scout-rag
cd football-scout-rag

# Create virtual environment
uv venv

# Activate (Windows PowerShell)
.venv\Scripts\activate

# Install dependencies
uv pip install -e ".[dev]"
```

### Alternative: pip install

```bash
pip install -e ".[dev]"
```

### Configuration

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Add your Groq API key to `.env`:
```
GROQ_API_KEY=your_groq_api_key_here
```

Get a free API key at [https://console.groq.com](https://console.groq.com)

## Usage

### CLI Commands

```bash
# Scout a player
football-scout scout "Oscar Gloukh"

# Scout multiple players
football-scout scout "Messi" "Ronaldo" "Haaland"

# Compare players (must be scouted first)
football-scout compare "Messi" "Ronaldo"

# Find hidden gems (undervalued players)
football-scout gems --max-value 10000000

# Compare players at the same age
football-scout compare-age "Gloukh" "Mbappe" --age 20

# Ask a follow-up question
football-scout ask "Who has the better goal-to-game ratio?"

# Interactive mode
football-scout interactive

# Output formats
football-scout scout "Player Name" --format table
football-scout scout "Player Name" --format json
```

### Web Dashboard

```bash
streamlit run src/football_scout/dashboard/app.py
```

Then open [http://localhost:8501](http://localhost:8501) in your browser.

## Project Structure

```
football_scout_rag/
├── src/football_scout/
│   ├── cli/              # Typer CLI application
│   ├── core/             # Core business logic (agent, scraper, analyzer)
│   ├── models/           # Pydantic data models
│   ├── llm/              # LLM client and prompts
│   ├── rag/              # ChromaDB vector store
│   ├── dashboard/        # Streamlit web app
│   └── config/           # Settings management
├── tests/                # pytest tests
├── data/                 # Data storage (gitignored)
├── pyproject.toml        # Modern Python packaging
└── README.md
```

## Key Features Explained

### Hidden Gems Finder
Find undervalued players by comparing their statistical output to market value:
```bash
football-scout gems --max-value 5000000 --min-apps 10
```

### Similarity Search
Find players with similar profiles using vector embeddings:
```bash
football-scout similar "Oscar Gloukh" --top 5
```

### Age-Adjusted Comparisons
Compare players at the same age to see development trajectories:
```bash
football-scout compare-age "Gloukh" "Mbappe" --age 20
```

## Running Tests

```bash
pytest tests/ -v
```

## Tech Stack

- **LLM**: Groq (mixtral-8x7b-32768)
- **Web Scraping**: aiohttp + BeautifulSoup
- **Vector Store**: ChromaDB
- **CLI**: Typer + Rich
- **Web UI**: Streamlit
- **Data Validation**: Pydantic
- **Testing**: pytest

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
