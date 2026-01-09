"""Tests for the PlayerAnalyzer."""
import pytest
from football_scout.core.analyzer import PlayerAnalyzer
from football_scout.models.player import SeasonStats, Player


class TestPlayerAnalyzer:
    """Tests for PlayerAnalyzer class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = PlayerAnalyzer()

    def test_normalize_stats_basic(self, sample_season_stats):
        """Test basic stats normalization."""
        stats = self.analyzer.normalize_stats(sample_season_stats)

        assert stats.total_goals == 25
        assert stats.total_assists == 18
        assert stats.total_appearances == 55
        assert stats.total_minutes == 4500

    def test_normalize_stats_per_game(self, sample_season_stats):
        """Test per-game calculations."""
        stats = self.analyzer.normalize_stats(sample_season_stats)

        # 25 goals / 55 appearances = 0.4545...
        assert abs(stats.goals_per_game - 0.4545) < 0.01
        # 18 assists / 55 appearances = 0.327...
        assert abs(stats.assists_per_game - 0.327) < 0.01

    def test_normalize_stats_per_90(self, sample_season_stats):
        """Test per-90-minute calculations."""
        stats = self.analyzer.normalize_stats(sample_season_stats)

        # (25 goals / 4500 minutes) * 90 = 0.5
        assert abs(stats.goals_per_90 - 0.5) < 0.01
        # (18 assists / 4500 minutes) * 90 = 0.36
        assert abs(stats.assists_per_90 - 0.36) < 0.01

    def test_normalize_stats_empty(self):
        """Test normalization with empty seasons."""
        stats = self.analyzer.normalize_stats([])

        assert stats.total_goals == 0
        assert stats.total_assists == 0
        assert stats.goals_per_game == 0.0
        assert stats.goals_per_90 == 0.0

    def test_normalize_stats_zero_appearances(self):
        """Test normalization when appearances are zero."""
        seasons = [SeasonStats(season="2024", appearances=0, goals=0, assists=0)]
        stats = self.analyzer.normalize_stats(seasons)

        assert stats.goals_per_game == 0.0
        assert stats.assists_per_game == 0.0

    def test_parse_market_value_millions(self):
        """Test parsing market value in millions."""
        assert self.analyzer._parse_market_value("EUR 10.00m") == 10_000_000
        assert self.analyzer._parse_market_value("EUR 25.50m") == 25_500_000
        assert self.analyzer._parse_market_value("$5m") == 5_000_000

    def test_parse_market_value_thousands(self):
        """Test parsing market value in thousands."""
        assert self.analyzer._parse_market_value("EUR 500k") == 500_000
        assert self.analyzer._parse_market_value("EUR 1.5k") == 1_500

    def test_parse_market_value_invalid(self):
        """Test parsing invalid market values."""
        assert self.analyzer._parse_market_value(None) == 0.0
        assert self.analyzer._parse_market_value("Not found") == 0.0
        assert self.analyzer._parse_market_value("") == 0.0

    def test_calculate_value_score(self, sample_player):
        """Test value score calculation."""
        score = self.analyzer.calculate_value_score(sample_player)

        # Should return a positive score for a player with good stats
        assert score > 0

    def test_calculate_value_score_no_stats(self, sample_player_info):
        """Test value score with no normalized stats."""
        player = Player(info=sample_player_info, seasons=[], normalized_stats=None)
        score = self.analyzer.calculate_value_score(player)

        assert score == 0.0

    def test_generate_report(self, sample_player):
        """Test report generation."""
        report = self.analyzer.generate_report(sample_player)

        assert "Test Player" in report
        assert "Position:" in report
        assert "Goals per game:" in report
        assert "Season by Season Breakdown:" in report

    def test_parse_age(self):
        """Test age parsing."""
        assert self.analyzer._parse_age("23 years old") == 23
        assert self.analyzer._parse_age("23") == 23
        assert self.analyzer._parse_age(None) is None
        assert self.analyzer._parse_age("") is None
