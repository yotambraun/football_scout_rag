import os
from dotenv import load_dotenv
import logging
import nest_asyncio
import asyncio
from football_scout_ai.scout_agent import FootballScoutAI
from config import settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found in environment variables")


async def main():
    scout_ai = FootballScoutAI()
    while True:
        user_input = input("\nEnter player names to scout (comma-separated), 'compare' to compare players, '?' for a follow-up question, or 'exit' to quit: ")
        if user_input.lower() == 'exit':
            print("Thank you for using the Football Scout AI!")
            break
        elif user_input.lower() == 'compare':
            player_names = list(scout_ai.players_data.keys())
            if len(player_names) < 2:
                print("Please scout at least two players before comparing.")
            else:
                result = await scout_ai.compare_players(player_names)
                print(result)
        elif user_input.startswith('?'):
            result = await scout_ai.answer_follow_up_question(user_input[1:].strip())
            print(result)
        else:
            player_list = [name.strip() for name in user_input.split(',')]
            for player_name in player_list:
                result = await scout_ai.analyze_player(player_name)
                print(result)


if __name__ == "__main__":

    nest_asyncio.apply()
    asyncio.run(main())