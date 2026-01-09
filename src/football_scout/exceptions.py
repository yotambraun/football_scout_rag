"""Custom exceptions for Football Scout."""


class FootballScoutError(Exception):
    """Base exception for football scout."""
    pass


class PlayerNotFoundError(FootballScoutError):
    """Raised when a player cannot be found."""

    def __init__(self, player_name: str) -> None:
        self.player_name = player_name
        super().__init__(f"Player '{player_name}' not found on Transfermarkt")


class ScrapingError(FootballScoutError):
    """Raised when scraping fails."""
    pass


class LLMError(FootballScoutError):
    """Raised when LLM operations fail."""
    pass


class NoPlayersScoutedError(FootballScoutError):
    """Raised when trying to compare players but none have been scouted."""
    pass
