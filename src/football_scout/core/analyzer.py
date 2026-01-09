"""Data analysis and normalization for player statistics."""
from football_scout.models.player import Player, SeasonStats, NormalizedStats


class PlayerAnalyzer:
    """Analyzes and normalizes player statistics."""

    def normalize_stats(self, seasons: list[SeasonStats]) -> NormalizedStats:
        """Calculate normalized statistics from season data."""
        total_goals = sum(s.goals for s in seasons)
        total_assists = sum(s.assists for s in seasons)
        total_appearances = sum(s.appearances for s in seasons)
        total_minutes = sum(s.minutes_played for s in seasons)

        goals_per_game = total_goals / total_appearances if total_appearances > 0 else 0.0
        assists_per_game = total_assists / total_appearances if total_appearances > 0 else 0.0
        minutes_per_game = total_minutes / total_appearances if total_appearances > 0 else 0.0

        # Per 90 minutes stats
        goals_per_90 = (total_goals / total_minutes) * 90 if total_minutes > 0 else 0.0
        assists_per_90 = (total_assists / total_minutes) * 90 if total_minutes > 0 else 0.0

        return NormalizedStats(
            total_goals=total_goals,
            total_assists=total_assists,
            total_appearances=total_appearances,
            total_minutes=total_minutes,
            goals_per_game=goals_per_game,
            assists_per_game=assists_per_game,
            minutes_per_game=minutes_per_game,
            goals_per_90=goals_per_90,
            assists_per_90=assists_per_90,
        )

    def calculate_value_score(self, player: Player) -> float:
        """
        Calculate a value score for finding hidden gems.
        Higher score = more undervalued (stats >> market value).
        """
        if not player.normalized_stats:
            return 0.0

        # Parse market value (e.g., "€25.00m" -> 25000000)
        market_value = self._parse_market_value(player.info.market_value)
        if market_value <= 0:
            return 0.0

        stats = player.normalized_stats

        # Calculate statistical output score
        # Weight goals more heavily than assists
        stat_score = (stats.goals_per_90 * 10) + (stats.assists_per_90 * 5)

        # Value score = stat output / market value (normalized)
        # Higher is better (more stats per euro spent)
        value_score = (stat_score / market_value) * 10_000_000

        return value_score

    def _parse_market_value(self, value_str: str | None) -> float:
        """Parse market value string to float."""
        if not value_str or value_str == "Not found":
            return 0.0

        # Remove currency symbols and whitespace
        cleaned = value_str.replace("€", "").replace("$", "").replace("£", "").strip()

        multiplier = 1.0
        if "m" in cleaned.lower():
            multiplier = 1_000_000
            cleaned = cleaned.lower().replace("m", "")
        elif "k" in cleaned.lower():
            multiplier = 1_000
            cleaned = cleaned.lower().replace("k", "")

        try:
            return float(cleaned) * multiplier
        except ValueError:
            return 0.0

    def compare_at_age(self, player1: Player, player2: Player, age: int) -> dict:
        """
        Compare two players at the same age.
        Returns stats for each player at that age.
        """
        def get_stats_at_age(player: Player, target_age: int) -> dict | None:
            # This is a simplified version - would need birth date to be accurate
            # For now, we'll use early seasons as a proxy for younger age
            if not player.seasons:
                return None

            # Use early seasons for younger comparison
            current_age = self._parse_age(player.info.age)
            if current_age is None:
                return None

            seasons_back = current_age - target_age
            if seasons_back < 0 or seasons_back >= len(player.seasons):
                return None

            # Get the season at that age
            target_season = player.seasons[seasons_back] if seasons_back < len(player.seasons) else None
            if not target_season:
                return None

            return {
                "season": target_season.season,
                "goals": target_season.goals,
                "assists": target_season.assists,
                "appearances": target_season.appearances,
                "minutes": target_season.minutes_played,
                "goals_per_game": target_season.goals / target_season.appearances if target_season.appearances > 0 else 0,
            }

        return {
            "age": age,
            "player1": {
                "name": player1.info.name,
                "stats": get_stats_at_age(player1, age)
            },
            "player2": {
                "name": player2.info.name,
                "stats": get_stats_at_age(player2, age)
            }
        }

    def _parse_age(self, age_str: str | None) -> int | None:
        """Parse age from string."""
        if not age_str:
            return None
        try:
            # Extract just the number
            import re
            match = re.search(r'\d+', age_str)
            if match:
                return int(match.group())
        except ValueError:
            pass
        return None

    def generate_report(self, player: Player) -> str:
        """Generate a text report for a player."""
        info = player.info
        stats = player.normalized_stats

        report = f"""
Player Report for {info.name}

1. Player Overview:
   - Position: {info.position or 'Not available'}
   - Age: {info.age or 'Not available'}
   - Nationality: {info.nationality or 'Not available'}
   - Current Club: {info.current_club or 'Not available'}
   - Market Value: {info.market_value or 'Not available'}

2. Performance Analysis:
   - Goals per game: {stats.goals_per_game:.2f if stats else 'N/A'}
   - Assists per game: {stats.assists_per_game:.2f if stats else 'N/A'}
   - Minutes per game: {stats.minutes_per_game:.2f if stats else 'N/A'}
   - Goals per 90 min: {stats.goals_per_90:.2f if stats else 'N/A'}
   - Assists per 90 min: {stats.assists_per_90:.2f if stats else 'N/A'}

3. Career Totals:
   - Total Goals: {stats.total_goals if stats else 'N/A'}
   - Total Assists: {stats.total_assists if stats else 'N/A'}
   - Total Appearances: {stats.total_appearances if stats else 'N/A'}
   - Total Minutes: {stats.total_minutes if stats else 'N/A'}

4. Season by Season Breakdown:
"""
        for season in player.seasons:
            report += f"""
   {season.season} Season:
   - Appearances: {season.appearances}
   - Goals: {season.goals}
   - Assists: {season.assists}
   - Minutes: {season.minutes_played}
"""
        return report
