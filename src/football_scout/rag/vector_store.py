"""Vector store for player similarity search using ChromaDB."""
import logging
from pathlib import Path
from typing import Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from football_scout.models.player import Player
from football_scout.config import get_settings

logger = logging.getLogger(__name__)


class PlayerVectorStore:
    """Vector store for player embeddings and similarity search."""

    def __init__(self, persist_directory: Optional[str] = None) -> None:
        settings = get_settings()
        self.persist_dir = persist_directory or str(Path(settings.data_dir) / "chroma")

        # Initialize ChromaDB client with persistence
        self.client = chromadb.Client(ChromaSettings(
            chroma_db_impl="duckdb+parquet",
            persist_directory=self.persist_dir,
            anonymized_telemetry=False,
        ))

        # Get or create collection for players
        self.collection = self.client.get_or_create_collection(
            name="players",
            metadata={"description": "Football player embeddings for similarity search"}
        )

    def add_player(self, player: Player) -> None:
        """Add a player to the vector store."""
        # Create embedding text from player data
        embedding_text = player.to_embedding_text()

        # Create metadata for filtering
        metadata = {
            "name": player.info.name,
            "position": player.info.position or "Unknown",
            "club": player.info.current_club or "Unknown",
            "nationality": player.info.nationality or "Unknown",
            "age": player.info.age or "Unknown",
            "market_value": player.info.market_value or "Unknown",
        }

        if player.normalized_stats:
            metadata.update({
                "goals_per_game": player.normalized_stats.goals_per_game,
                "assists_per_game": player.normalized_stats.assists_per_game,
                "total_goals": player.normalized_stats.total_goals,
                "total_assists": player.normalized_stats.total_assists,
                "total_appearances": player.normalized_stats.total_appearances,
            })

        # Use player name as ID
        player_id = player.info.name.lower().replace(" ", "_")

        try:
            # Upsert (add or update)
            self.collection.upsert(
                ids=[player_id],
                documents=[embedding_text],
                metadatas=[metadata],
            )
            logger.info(f"Added player {player.info.name} to vector store")
        except Exception as e:
            logger.error(f"Failed to add player to vector store: {e}")
            raise

    def find_similar(self, player: Player, n_results: int = 5) -> list[dict]:
        """Find players similar to the given player."""
        embedding_text = player.to_embedding_text()

        try:
            results = self.collection.query(
                query_texts=[embedding_text],
                n_results=n_results + 1,  # +1 to account for the player itself
            )

            similar_players = []
            player_id = player.info.name.lower().replace(" ", "_")

            for i, doc_id in enumerate(results["ids"][0]):
                # Skip the player itself
                if doc_id == player_id:
                    continue

                similar_players.append({
                    "id": doc_id,
                    "name": results["metadatas"][0][i].get("name", "Unknown"),
                    "position": results["metadatas"][0][i].get("position", "Unknown"),
                    "club": results["metadatas"][0][i].get("club", "Unknown"),
                    "distance": results["distances"][0][i] if results.get("distances") else None,
                    "metadata": results["metadatas"][0][i],
                })

                if len(similar_players) >= n_results:
                    break

            return similar_players

        except Exception as e:
            logger.error(f"Failed to find similar players: {e}")
            return []

    def find_similar_by_text(self, query: str, n_results: int = 5) -> list[dict]:
        """Find players similar to a text query."""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
            )

            similar_players = []
            for i, doc_id in enumerate(results["ids"][0]):
                similar_players.append({
                    "id": doc_id,
                    "name": results["metadatas"][0][i].get("name", "Unknown"),
                    "position": results["metadatas"][0][i].get("position", "Unknown"),
                    "club": results["metadatas"][0][i].get("club", "Unknown"),
                    "distance": results["distances"][0][i] if results.get("distances") else None,
                    "metadata": results["metadatas"][0][i],
                })

            return similar_players

        except Exception as e:
            logger.error(f"Failed to find similar players by text: {e}")
            return []

    def get_all_players(self) -> list[dict]:
        """Get all players in the vector store."""
        try:
            results = self.collection.get()
            players = []
            for i, doc_id in enumerate(results["ids"]):
                players.append({
                    "id": doc_id,
                    "name": results["metadatas"][i].get("name", "Unknown"),
                    "position": results["metadatas"][i].get("position", "Unknown"),
                    "club": results["metadatas"][i].get("club", "Unknown"),
                    "metadata": results["metadatas"][i],
                })
            return players
        except Exception as e:
            logger.error(f"Failed to get all players: {e}")
            return []

    def delete_player(self, player_name: str) -> bool:
        """Delete a player from the vector store."""
        player_id = player_name.lower().replace(" ", "_")
        try:
            self.collection.delete(ids=[player_id])
            logger.info(f"Deleted player {player_name} from vector store")
            return True
        except Exception as e:
            logger.error(f"Failed to delete player: {e}")
            return False

    def count(self) -> int:
        """Get the number of players in the vector store."""
        return self.collection.count()

    def persist(self) -> None:
        """Persist the vector store to disk."""
        try:
            self.client.persist()
            logger.info("Vector store persisted to disk")
        except Exception as e:
            logger.error(f"Failed to persist vector store: {e}")
