"""LLM client abstraction."""
import json
import logging
from typing import Optional

from langchain_groq import ChatGroq
from langchain.schema import HumanMessage, SystemMessage

from football_scout.config import get_settings
from football_scout.exceptions import LLMError
from football_scout.llm.prompts import (
    SCOUT_SYSTEM_PROMPT,
    FOLLOW_UP_SYSTEM_PROMPT,
    HIDDEN_GEMS_SYSTEM_PROMPT,
    COMPARISON_SYSTEM_PROMPT,
)

logger = logging.getLogger(__name__)


class LLMClient:
    """Client for interacting with the LLM."""

    def __init__(self) -> None:
        settings = get_settings()
        if not settings.validate_api_key():
            raise LLMError("GROQ_API_KEY not configured")

        self.llm = ChatGroq(
            groq_api_key=settings.groq_api_key,
            model_name=settings.llm_model,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
        )

    def answer_question(self, question: str, player_data: dict) -> str:
        """Answer a follow-up question about player data."""
        try:
            system_message = SystemMessage(content=FOLLOW_UP_SYSTEM_PROMPT)
            human_message = HumanMessage(content=f"""
Player data: {json.dumps(player_data, indent=2, default=str)}

Question: {question}

Please answer the question based on the available player data.
""")
            response = self.llm.invoke([system_message, human_message])
            return response.content
        except Exception as e:
            logger.exception("LLM error in answer_question")
            raise LLMError(f"Failed to get LLM response: {e}")

    def analyze_hidden_gem(self, player_data: dict, value_score: float) -> str:
        """Provide analysis of why a player might be a hidden gem."""
        try:
            system_message = SystemMessage(content=HIDDEN_GEMS_SYSTEM_PROMPT)
            human_message = HumanMessage(content=f"""
Player data: {json.dumps(player_data, indent=2, default=str)}
Value Score: {value_score:.2f}

Analyze why this player might be undervalued and their potential.
""")
            response = self.llm.invoke([system_message, human_message])
            return response.content
        except Exception as e:
            logger.exception("LLM error in analyze_hidden_gem")
            raise LLMError(f"Failed to analyze hidden gem: {e}")

    def analyze_age_comparison(self, comparison_data: dict) -> str:
        """Provide analysis of players compared at the same age."""
        try:
            system_message = SystemMessage(content=COMPARISON_SYSTEM_PROMPT)
            human_message = HumanMessage(content=f"""
Comparison data: {json.dumps(comparison_data, indent=2, default=str)}

Compare these players at the same age and provide insights.
""")
            response = self.llm.invoke([system_message, human_message])
            return response.content
        except Exception as e:
            logger.exception("LLM error in analyze_age_comparison")
            raise LLMError(f"Failed to analyze comparison: {e}")

    def generate_insight(self, prompt: str, context: str) -> str:
        """Generate a general insight based on context."""
        try:
            system_message = SystemMessage(content=SCOUT_SYSTEM_PROMPT)
            human_message = HumanMessage(content=f"""
Context: {context}

{prompt}
""")
            response = self.llm.invoke([system_message, human_message])
            return response.content
        except Exception as e:
            logger.exception("LLM error in generate_insight")
            raise LLMError(f"Failed to generate insight: {e}")
