"""Player data models."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class PlayerInfo(BaseModel):
    """Player biographical information."""
    player_id: str
    name: str
    position: Optional[str] = None
    age: Optional[str] = None
    nationality: Optional[str] = None
    height: Optional[str] = None
    preferred_foot: Optional[str] = None
    current_club: Optional[str] = None
    market_value: Optional[str] = None
    joined_current_club: Optional[str] = None
    contract_expires: Optional[str] = None


class SeasonStats(BaseModel):
    """Statistics for a single season."""
    season: str
    appearances: int = 0
    goals: int = 0
    assists: int = 0
    yellow_cards: int = 0
    red_cards: int = 0
    minutes_played: int = 0


class NormalizedStats(BaseModel):
    """Normalized per-game statistics."""
    total_goals: int = 0
    total_assists: int = 0
    total_appearances: int = 0
    total_minutes: int = 0
    goals_per_game: float = 0.0
    assists_per_game: float = 0.0
    minutes_per_game: float = 0.0
    goals_per_90: float = 0.0
    assists_per_90: float = 0.0


class Player(BaseModel):
    """Complete player data."""
    info: PlayerInfo
    seasons: list[SeasonStats] = Field(default_factory=list)
    normalized_stats: Optional[NormalizedStats] = None
    scouted_at: datetime = Field(default_factory=datetime.now)

    def to_embedding_text(self) -> str:
        """Convert player data to text for embedding."""
        parts = [
            f"Player: {self.info.name}",
            f"Position: {self.info.position or 'Unknown'}",
            f"Age: {self.info.age or 'Unknown'}",
            f"Nationality: {self.info.nationality or 'Unknown'}",
            f"Club: {self.info.current_club or 'Unknown'}",
            f"Market Value: {self.info.market_value or 'Unknown'}",
        ]

        if self.normalized_stats:
            parts.extend([
                f"Goals per game: {self.normalized_stats.goals_per_game:.2f}",
                f"Assists per game: {self.normalized_stats.assists_per_game:.2f}",
                f"Total goals: {self.normalized_stats.total_goals}",
                f"Total assists: {self.normalized_stats.total_assists}",
                f"Total appearances: {self.normalized_stats.total_appearances}",
            ])

        return " | ".join(parts)


class PlayerReport(BaseModel):
    """Generated player report."""
    player: Player
    report_text: str
    generated_at: datetime = Field(default_factory=datetime.now)
