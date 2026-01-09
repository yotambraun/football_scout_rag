"""Transfermarkt web scraper."""
import re
import logging
import aiohttp
from bs4 import BeautifulSoup
from typing import Optional

from football_scout.models.player import PlayerInfo, SeasonStats
from football_scout.exceptions import PlayerNotFoundError, ScrapingError
from football_scout.config import get_settings

logger = logging.getLogger(__name__)


class TransfermarktScraper:
    """Scrapes player data from Transfermarkt."""

    def __init__(self) -> None:
        settings = get_settings()
        self.base_url = settings.transfermarkt_base_url
        self.headers = {"User-Agent": settings.user_agent}
        self.timeout = settings.request_timeout

    async def fetch_url(self, url: str) -> str:
        """Fetch content from a URL."""
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(url, timeout=self.timeout) as response:
                    if response.status != 200:
                        raise ScrapingError(f"HTTP {response.status} for {url}")
                    return await response.text()
        except aiohttp.ClientError as e:
            raise ScrapingError(f"Failed to fetch {url}: {e}")

    async def search_player(self, player_name: str) -> str:
        """Search for a player and return their ID."""
        search_url = f"{self.base_url}/schnellsuche/ergebnis/schnellsuche?query={player_name}&x=0&y=0"
        content = await self.fetch_url(search_url)

        player_id_match = re.search(r'/spieler/(\d+)', content)
        if player_id_match:
            return player_id_match.group(1)

        raise PlayerNotFoundError(player_name)

    async def fetch_player_info(self, player_id: str) -> PlayerInfo:
        """Fetch player biographical information."""
        url = f"{self.base_url}/spieler/profil/spieler/{player_id}"
        content = await self.fetch_url(url)
        soup = BeautifulSoup(content, 'html.parser')

        def safe_extract(selector: str, default: str = "Not found") -> str:
            element = soup.select_one(selector)
            return element.text.strip() if element else default

        name = safe_extract('h1.data-header__headline-wrapper')
        # Clean up name (remove jersey number if present)
        name = re.sub(r'#\d+', '', name).strip()

        return PlayerInfo(
            player_id=player_id,
            name=name,
            position=safe_extract('.data-header__position'),
            age=safe_extract('.data-header__content[itemprop="birthDate"]'),
            nationality=safe_extract('.data-header__content[itemprop="nationality"]'),
            height=safe_extract('.data-header__content[itemprop="height"]'),
            preferred_foot=None,  # This selector doesn't work reliably
            current_club=safe_extract('.data-header__club'),
            market_value=safe_extract('.data-header__market-value-wrapper'),
            joined_current_club=None,
            contract_expires=None,
        )

    async def fetch_player_seasons(self, player_id: str) -> list[str]:
        """Fetch available seasons for a player."""
        url = f"{self.base_url}/spieler/leistungsdaten/spieler/{player_id}"
        content = await self.fetch_url(url)
        soup = BeautifulSoup(content, 'html.parser')

        season_options = soup.select('select[name="saison"] option')
        seasons = [option['value'] for option in season_options if option.get('value') and option['value'] != 'ges']
        return seasons

    async def fetch_season_data(self, player_id: str, season: str) -> SeasonStats:
        """Fetch statistics for a specific season."""
        url = f"{self.base_url}/spieler/leistungsdaten/spieler/{player_id}/plus/0?saison={season}"
        content = await self.fetch_url(url)
        soup = BeautifulSoup(content, 'html.parser')

        summary_row = soup.select_one('tfoot tr')
        if not summary_row:
            return SeasonStats(season=season)

        cells = summary_row.select('td')
        if len(cells) < 6:
            return SeasonStats(season=season)

        def parse_int(value: str) -> int:
            """Parse string to int, handling dashes and empty values."""
            cleaned = value.strip().replace('-', '0').replace("'", "").replace(',', '.')
            try:
                return int(float(cleaned))
            except ValueError:
                return 0

        return SeasonStats(
            season=season,
            appearances=parse_int(cells[-6].text) if len(cells) > 5 else 0,
            goals=parse_int(cells[-5].text) if len(cells) > 4 else 0,
            assists=parse_int(cells[-4].text) if len(cells) > 3 else 0,
            yellow_cards=parse_int(cells[-3].text) if len(cells) > 2 else 0,
            red_cards=parse_int(cells[-2].text) if len(cells) > 1 else 0,
            minutes_played=parse_int(cells[-1].text) if len(cells) > 0 else 0,
        )

    async def fetch_all_player_data(self, player_name: str) -> tuple[PlayerInfo, list[SeasonStats]]:
        """Fetch complete player data including all seasons."""
        player_id = await self.search_player(player_name)
        player_info = await self.fetch_player_info(player_id)
        seasons = await self.fetch_player_seasons(player_id)

        season_stats = []
        for season in seasons:
            stats = await self.fetch_season_data(player_id, season)
            season_stats.append(stats)

        return player_info, season_stats
