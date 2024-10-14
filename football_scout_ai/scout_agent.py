import os
import re
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.schema import HumanMessage, SystemMessage
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found in environment variables")

class FootballScoutAI:
    def __init__(self):
        self.llm = ChatGroq(
            groq_api_key=GROQ_API_KEY,
            model_name="mixtral-8x7b-32768",
            temperature=0.5,
            max_tokens=1024,
        )
        self.base_url = "https://www.transfermarkt.com"
        self.headers = {
            'User-Agent': 'FootballScoutAI/1.0 (contact@example.com)'
        }
        self.players_data = {}

    async def fetch_url(self, url: str) -> str:
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.get(url) as response:
                return await response.text()

    async def search_player(self, player_name: str) -> str:
        search_url = f"{self.base_url}/schnellsuche/ergebnis/schnellsuche?query={player_name}&x=0&y=0"
        content = await self.fetch_url(search_url)
        player_id_match = re.search(r'/spieler/(\d+)', content)
        if player_id_match:
            return player_id_match.group(1)
        logger.error(f"Player {player_name} not found")
        return None

    async def fetch_player_seasons(self, player_id: str) -> list:
        url = f"{self.base_url}/spieler/leistungsdaten/spieler/{player_id}"
        content = await self.fetch_url(url)
        soup = BeautifulSoup(content, 'html.parser')
        season_options = soup.select('select[name="saison"] option')
        seasons = [option['value'] for option in season_options if option['value'] != 'ges']
        return seasons

    async def fetch_season_data(self, player_id: str, season: str) -> dict:
        url = f"{self.base_url}/spieler/leistungsdaten/spieler/{player_id}/plus/0?saison={season}"
        content = await self.fetch_url(url)
        soup = BeautifulSoup(content, 'html.parser')

        summary_data = {}
        summary_row = soup.select_one('tfoot tr')
        if summary_row:
            cells = summary_row.select('td')
            if len(cells) >= 3:
                summary_data = {
                    'appearances': cells[-6].text.strip() if len(cells) > 5 else 'N/A',
                    'goals': cells[-5].text.strip() if len(cells) > 4 else 'N/A',
                    'assists': cells[-4].text.strip() if len(cells) > 3 else 'N/A',
                    'yellow_cards': cells[-3].text.strip() if len(cells) > 2 else 'N/A',
                    'red_cards': cells[-2].text.strip() if len(cells) > 1 else 'N/A',
                    'minutes': cells[-1].text.strip() if len(cells) > 0 else 'N/A',
                }

        return {
            'season': season,
            'summary_data': summary_data
        }

    async def fetch_player_info(self, player_id: str) -> dict:
        url = f"{self.base_url}/spieler/profil/spieler/{player_id}"
        content = await self.fetch_url(url)
        soup = BeautifulSoup(content, 'html.parser')

        info = {}

        def safe_extract(selector, default='Not found'):
            element = soup.select_one(selector)
            return element.text.strip() if element else default

        info['name'] = safe_extract('h1.data-header__headline-wrapper')
        info['position'] = safe_extract('.data-header__position')
        info['age'] = safe_extract('.data-header__content[itemprop="birthDate"]')
        info['nationality'] = safe_extract('.data-header__content[itemprop="nationality"]')
        info['height'] = safe_extract('.data-header__content[itemprop="height"]')
        info['foot'] = safe_extract('li.data-header__label:contains("Foot")')
        info['current_club'] = safe_extract('.data-header__club')
        info['market_value'] = safe_extract('.data-header__market-value-wrapper')
        info['joined_current_club'] = safe_extract('li.data-header__label:contains("Joined")')
        info['contract_expires'] = safe_extract('li.data-header__label:contains("Contract expires")')

        return info

    async def fetch_player_data(self, player_name: str) -> dict:
        player_id = await self.search_player(player_name)
        if not player_id:
            raise ValueError(f"Player {player_name} not found")

        player_info = await self.fetch_player_info(player_id)
        seasons = await self.fetch_player_seasons(player_id)
        player_data = {
            'player_id': player_id,
            'player_info': player_info,
            'seasons_data': []
        }

        for season in seasons:
            season_data = await self.fetch_season_data(player_id, season)
            player_data['seasons_data'].append(season_data)

        return player_data

    def normalize_data(self, player_data: dict) -> dict:
        total_goals = sum(int(season['summary_data'].get('goals', '0').replace('-', '0')) for season in player_data['seasons_data'])
        total_assists = sum(int(season['summary_data'].get('assists', '0').replace('-', '0')) for season in player_data['seasons_data'])
        total_appearances = sum(int(season['summary_data'].get('appearances', '0').replace('-', '0')) for season in player_data['seasons_data'])
        total_minutes = sum(int(float(season['summary_data'].get('minutes', '0').replace("'", "").replace('-', '0').replace(',', '.'))) for season in player_data['seasons_data'])

        player_data['normalized_data'] = {
            'goals_per_game': total_goals / total_appearances if total_appearances > 0 else 0,
            'assists_per_game': total_assists / total_appearances if total_appearances > 0 else 0,
            'minutes_per_game': total_minutes / total_appearances if total_appearances > 0 else 0,
        }
        return player_data

    async def analyze_player(self, player_name: str) -> str:
        try:
            player_data = await self.fetch_player_data(player_name)
            normalized_data = self.normalize_data(player_data)
            self.players_data[player_name] = normalized_data

            with open(f"{player_name}_data.json", 'w') as f:
                json.dump(normalized_data, f, indent=2)

            logger.info(f"Player data saved to {player_name}_data.json")

            return self.generate_player_report(normalized_data)
        except Exception as e:
            logger.exception(f"Error in player analysis: {str(e)}")
            return f"Error analyzing player: {str(e)}"

    def generate_player_report(self, player_data: dict) -> str:
        report = f"""
    Player Report for {player_data['player_info']['name']}

    1. Player Overview:
      - Position: {player_data['player_info'].get('position', 'Not available')}
      - Age: {player_data['player_info'].get('age', 'Not available')}
      - Nationality: {player_data['player_info'].get('nationality', 'Not available')}
      - Current Club: {player_data['player_info'].get('current_club', 'Not available')}
      - Market Value: {player_data['player_info'].get('market_value', 'Not available')}

    2. Performance Analysis:
      - Goals per game: {player_data['normalized_data'].get('goals_per_game', 'N/A'):.2f}
      - Assists per game: {player_data['normalized_data'].get('assists_per_game', 'N/A'):.2f}
      - Minutes per game: {player_data['normalized_data'].get('minutes_per_game', 'N/A'):.2f}

    3. Season by Season Breakdown:
    """
        for season in player_data['seasons_data']:
            report += f"""
      {season['season']} Season:
      - Appearances: {season['summary_data'].get('appearances', 'N/A')}
      - Goals: {season['summary_data'].get('goals', 'N/A')}
      - Assists: {season['summary_data'].get('assists', 'N/A')}
      - Minutes: {season['summary_data'].get('minutes', 'N/A')}
    """
        return report

    async def compare_players(self, player_names: list) -> str:
        players_to_compare = [self.players_data.get(name) for name in player_names if name in self.players_data]
        if len(players_to_compare) < 2:
            return "Not enough players to compare. Please scout at least two players first."

        comparison = "Player Comparison:\n\n"
        for category in ['name', 'position', 'age', 'nationality', 'current_club', 'market_value']:
            comparison += f"{category.capitalize()}:\n"
            for player in players_to_compare:
                comparison += f"- {player['player_info']['name']}: {player['player_info'].get(category, 'N/A')}\n"
            comparison += "\n"

        comparison += "Performance Metrics:\n"
        for metric in ['goals_per_game', 'assists_per_game', 'minutes_per_game']:
            comparison += f"{metric.replace('_', ' ').capitalize()}:\n"
            for player in players_to_compare:
                comparison += f"- {player['player_info']['name']}: {player['normalized_data'][metric]:.2f}\n"
            comparison += "\n"

        return comparison

    async def answer_follow_up_question(self, question: str) -> str:
        system_message = SystemMessage(content="You are an AI football scout assistant. Answer the follow-up question based on the previously analyzed player data.")
        human_message = HumanMessage(content=f"""
            Players data: {json.dumps(self.players_data, indent=2)}
            Question: {question}

            Please answer the question based on the available player data. If the question is about information not present in the data, state that you don't have that specific information.
            """)

        messages = [system_message, human_message]

        response = self.llm.invoke(messages)
        return response.content