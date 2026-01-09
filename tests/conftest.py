"""Pytest configuration and fixtures."""
import pytest
from football_scout.models.player import Player, PlayerInfo, SeasonStats, NormalizedStats


@pytest.fixture
def sample_player_info() -> PlayerInfo:
    """Create a sample PlayerInfo for testing."""
    return PlayerInfo(
        player_id="123456",
        name="Test Player",
        position="Attacking Midfield",
        age="23",
        nationality="Germany",
        height="180 cm",
        preferred_foot="Right",
        current_club="Test FC",
        market_value="EUR 10.00m",
    )


@pytest.fixture
def sample_season_stats() -> list[SeasonStats]:
    """Create sample season stats for testing."""
    return [
        SeasonStats(
            season="2024",
            appearances=30,
            goals=15,
            assists=10,
            yellow_cards=3,
            red_cards=0,
            minutes_played=2500,
        ),
        SeasonStats(
            season="2023",
            appearances=25,
            goals=10,
            assists=8,
            yellow_cards=2,
            red_cards=0,
            minutes_played=2000,
        ),
    ]


@pytest.fixture
def sample_normalized_stats() -> NormalizedStats:
    """Create sample normalized stats for testing."""
    return NormalizedStats(
        total_goals=25,
        total_assists=18,
        total_appearances=55,
        total_minutes=4500,
        goals_per_game=0.45,
        assists_per_game=0.33,
        minutes_per_game=81.8,
        goals_per_90=0.5,
        assists_per_90=0.36,
    )


@pytest.fixture
def sample_player(
    sample_player_info: PlayerInfo,
    sample_season_stats: list[SeasonStats],
    sample_normalized_stats: NormalizedStats,
) -> Player:
    """Create a complete sample Player for testing."""
    return Player(
        info=sample_player_info,
        seasons=sample_season_stats,
        normalized_stats=sample_normalized_stats,
    )
