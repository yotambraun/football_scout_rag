# Football Scout RAG ⚽️🤖

Welcome to **Football Scout RAG**, an AI-powered football scouting agent designed to scrape data from Transfermarkt and provide advanced player statistics and comparisons.

## Overview

This project uses **LangChain**, **Groq**, and **BeautifulSoup** to fetch, analyze, and compare player data from Transfermarkt. With this agent, you can:

- Search for player information from Transfermarkt
- Get season-by-season breakdowns of goals, assists, and minutes
- Compare multiple players on key performance metrics
- Generate advanced statistics (e.g., goals per 90 minutes, assists per 90 minutes)
- Answer follow-up questions about scouted players based on available data

## Features

- **Player Search**: Find player details by name and fetch historical season data.
- **Performance Analysis**: Get advanced stats like goals, assists, and minutes per game.
- **Player Comparison**: Compare two or more players side by side.
- **Follow-up Questions**: Ask follow-up questions about scouted players, and the agent will provide relevant answers.

## Installation

To install the dependencies, run:

```bash
pip install -r requirements.txt
```

## Usage
**Note**: Make sure to set up your .env file with the **GROQ_API_KEY**:
GROQ_API_KEY=your_api_key_here

1. **Scouting Players:**
Run the main script and enter player names:

```bash
python main.py
```

Example:
```bash
Enter player names to scout (comma-separated): Oscar Gloukh, Dor Turgeman
```
The agent will fetch their data and generate a report:

```yaml
Player Report for Oscar Gloukh:
- Goals per game: 1.24
- Assists per game: 0.28
- Minutes per game: 64.08
```

2. **Comparing Players:**
After scouting at least two players, you can compare them:

```bash
compare
```

Example output:
```yaml
Player Comparison:
- Goals per game:
  - Oscar Gloukh: 1.24
  - Dor Turgeman: 0.48
```

3. **Advanced Stats:**
You can ask for more detailed statistics:

```bash
? give advanced statistics about those players?
```

Example output:
```diff
- Oscar Gloukh: 2.03 goals per 90 minutes
- Dor Turgeman: 0.82 goals per 90 minutes
```

4. **Follow-up Questions:**
You can ask a follow-up question about the scouted players:

```bash
? What are the key strengths of these players based on their stats?
```

Example output:
```yaml
Based on the stats:
- Oscar Gloukh has a high goal involvement rate with 2.03 goals per 90 minutes.
- Dor Turgeman is an effective playmaker with balanced goals and assists.
```