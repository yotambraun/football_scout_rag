"""Tests for Pydantic models."""
import pytest
from football_scout.models.player import Player, PlayerInfo, SeasonStats, NormalizedStats


class TestPlayerInfo:
    """Tests for PlayerInfo model."""

    def test_create_player_info(self):
        """Test creating a PlayerInfo instance."""
        info = PlayerInfo(
            player_id="123",
            name="Test Player",
            position="Forward",
        )

        assert info.player_id == "123"
        assert info.name == "Test Player"
        assert info.position == "Forward"

    def test_player_info_optional_fields(self):
        """Test that optional fields default to None."""
        info = PlayerInfo(player_id="123", name="Test")

        assert info.age is None
        assert info.nationality is None
        assert info.market_value is None


class TestSeasonStats:
    """Tests for SeasonStats model."""

    def test_create_season_stats(self):
        """Test creating a SeasonStats instance."""
        stats = SeasonStats(
            season="2024",
            appearances=30,
            goals=15,
            assists=10,
        )

        assert stats.season == "2024"
        assert stats.appearances == 30
        assert stats.goals == 15

    def test_season_stats_defaults(self):
        """Test that numeric fields default to 0."""
        stats = SeasonStats(season="2024")

        assert stats.appearances == 0
        assert stats.goals == 0
        assert stats.assists == 0
        assert stats.minutes_played == 0


class TestNormalizedStats:
    """Tests for NormalizedStats model."""

    def test_create_normalized_stats(self):
        """Test creating a NormalizedStats instance."""
        stats = NormalizedStats(
            total_goals=25,
            total_assists=18,
            goals_per_game=0.5,
        )

        assert stats.total_goals == 25
        assert stats.goals_per_game == 0.5

    def test_normalized_stats_defaults(self):
        """Test that all fields default to 0."""
        stats = NormalizedStats()

        assert stats.total_goals == 0
        assert stats.goals_per_90 == 0.0


class TestPlayer:
    """Tests for Player model."""

    def test_create_player(self, sample_player_info, sample_season_stats):
        """Test creating a Player instance."""
        player = Player(
            info=sample_player_info,
            seasons=sample_season_stats,
        )

        assert player.info.name == "Test Player"
        assert len(player.seasons) == 2

    def test_player_to_embedding_text(self, sample_player):
        """Test embedding text generation."""
        text = sample_player.to_embedding_text()

        assert "Test Player" in text
        assert "Attacking Midfield" in text
        assert "Test FC" in text

    def test_player_scouted_at_default(self, sample_player_info):
        """Test that scouted_at is automatically set."""
        player = Player(info=sample_player_info, seasons=[])

        assert player.scouted_at is not None
