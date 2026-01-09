"""Main Football Scout AI agent."""
import json
import logging
from pathlib import Path
from typing import Optional

from football_scout.core.scraper import TransfermarktScraper
from football_scout.core.analyzer import PlayerAnalyzer
from football_scout.models.player import Player, PlayerReport
from football_scout.llm.client import LLMClient
from football_scout.exceptions import PlayerNotFoundError, NoPlayersScoutedError
from football_scout.config import get_settings

logger = logging.getLogger(__name__)


class FootballScoutAI:
    """AI-powered football scouting agent."""

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        scraper: Optional[TransfermarktScraper] = None,
    ) -> None:
        self._scraper = scraper or TransfermarktScraper()
        self._analyzer = PlayerAnalyzer()
        self._llm: Optional[LLMClient] = llm_client
        self._players: dict[str, Player] = {}
        self._settings = get_settings()

    def _get_llm(self) -> LLMClient:
        """Lazy initialization of LLM client."""
        if self._llm is None:
            self._llm = LLMClient()
        return self._llm

    async def scout_player(self, player_name: str, save_to_file: bool = True) -> PlayerReport:
        """Scout a player and return a detailed report."""
        logger.info(f"Scouting player: {player_name}")

        # Fetch data from Transfermarkt
        player_info, seasons = await self._scraper.fetch_all_player_data(player_name)

        # Calculate normalized stats
        normalized_stats = self._analyzer.normalize_stats(seasons)

        # Create player object
        player = Player(
            info=player_info,
            seasons=seasons,
            normalized_stats=normalized_stats,
        )

        # Store in memory
        self._players[player_name.lower()] = player

        # Save to file if requested
        if save_to_file:
            self._save_player_data(player)

        # Generate report
        report_text = self._analyzer.generate_report(player)

        return PlayerReport(player=player, report_text=report_text)

    def _save_player_data(self, player: Player) -> None:
        """Save player data to JSON file."""
        data_dir = Path(self._settings.data_dir)
        data_dir.mkdir(exist_ok=True)

        filename = data_dir / f"{player.info.name.replace(' ', '_').lower()}_data.json"
        with open(filename, 'w') as f:
            json.dump(player.model_dump(), f, indent=2, default=str)
        logger.info(f"Player data saved to {filename}")

    def get_scouted_player(self, player_name: str) -> Optional[Player]:
        """Get a previously scouted player."""
        return self._players.get(player_name.lower())

    def get_all_scouted_players(self) -> list[Player]:
        """Get all scouted players."""
        return list(self._players.values())

    async def compare_players(self, player_names: list[str]) -> str:
        """Compare multiple players."""
        players = [self._players.get(name.lower()) for name in player_names]
        players = [p for p in players if p is not None]

        if len(players) < 2:
            raise NoPlayersScoutedError("Need at least 2 scouted players to compare")

        comparison = "Player Comparison:\n\n"

        # Basic info comparison
        for category in ['name', 'position', 'age', 'nationality', 'current_club', 'market_value']:
            comparison += f"{category.replace('_', ' ').title()}:\n"
            for player in players:
                value = getattr(player.info, category, 'N/A') or 'N/A'
                comparison += f"  - {player.info.name}: {value}\n"
            comparison += "\n"

        # Performance metrics comparison
        comparison += "Performance Metrics:\n"
        metrics = ['goals_per_game', 'assists_per_game', 'goals_per_90', 'assists_per_90', 'minutes_per_game']
        for metric in metrics:
            comparison += f"\n{metric.replace('_', ' ').title()}:\n"
            for player in players:
                if player.normalized_stats:
                    value = getattr(player.normalized_stats, metric, 0)
                    comparison += f"  - {player.info.name}: {value:.2f}\n"
                else:
                    comparison += f"  - {player.info.name}: N/A\n"

        return comparison

    async def answer_question(self, question: str) -> str:
        """Answer a follow-up question about scouted players."""
        if not self._players:
            raise NoPlayersScoutedError("No players scouted yet")

        players_data = {
            name: player.model_dump()
            for name, player in self._players.items()
        }

        return self._get_llm().answer_question(question, players_data)

    async def find_hidden_gems(
        self,
        max_value: float = 5_000_000,
        min_appearances: int = 10
    ) -> list[tuple[Player, float]]:
        """
        Find undervalued players from scouted players.
        Returns list of (player, value_score) sorted by value score.
        """
        gems = []
        for player in self._players.values():
            if not player.normalized_stats:
                continue

            # Check minimum appearances
            if player.normalized_stats.total_appearances < min_appearances:
                continue

            # Calculate value score
            value_score = self._analyzer.calculate_value_score(player)
            if value_score > 0:
                gems.append((player, value_score))

        # Sort by value score (descending)
        gems.sort(key=lambda x: x[1], reverse=True)
        return gems

    async def compare_at_age(self, player1_name: str, player2_name: str, age: int) -> str:
        """Compare two players at the same age."""
        player1 = self._players.get(player1_name.lower())
        player2 = self._players.get(player2_name.lower())

        if not player1:
            raise PlayerNotFoundError(player1_name)
        if not player2:
            raise PlayerNotFoundError(player2_name)

        comparison_data = self._analyzer.compare_at_age(player1, player2, age)

        # Get LLM analysis
        llm_analysis = self._get_llm().analyze_age_comparison(comparison_data)

        # Build report
        report = f"Age-Adjusted Comparison at Age {age}\n"
        report += "=" * 50 + "\n\n"

        for key in ['player1', 'player2']:
            p_data = comparison_data[key]
            report += f"{p_data['name']}:\n"
            if p_data['stats']:
                stats = p_data['stats']
                report += f"  Season: {stats['season']}\n"
                report += f"  Goals: {stats['goals']}\n"
                report += f"  Assists: {stats['assists']}\n"
                report += f"  Appearances: {stats['appearances']}\n"
                report += f"  Goals/Game: {stats['goals_per_game']:.2f}\n"
            else:
                report += "  No data available for this age\n"
            report += "\n"

        report += "AI Analysis:\n"
        report += llm_analysis

        return report
