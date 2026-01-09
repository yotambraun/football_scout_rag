"""Streamlit dashboard for Football Scout."""
import asyncio
import streamlit as st
import pandas as pd

from football_scout.core.agent import FootballScoutAI
from football_scout.core.analyzer import PlayerAnalyzer
from football_scout.rag.vector_store import PlayerVectorStore
from football_scout.exceptions import PlayerNotFoundError, FootballScoutError

# Page config
st.set_page_config(
    page_title="Football Scout AI",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize session state
if "agent" not in st.session_state:
    st.session_state.agent = FootballScoutAI()

if "vector_store" not in st.session_state:
    try:
        st.session_state.vector_store = PlayerVectorStore()
    except Exception:
        st.session_state.vector_store = None

if "scouted_players" not in st.session_state:
    st.session_state.scouted_players = []


def main():
    st.title("Football Scout AI")
    st.markdown("*AI-powered football scouting using RAG*")

    # Sidebar navigation
    page = st.sidebar.selectbox(
        "Navigation",
        ["Scout Player", "Compare Players", "Hidden Gems", "Similarity Search", "Ask AI"]
    )

    if page == "Scout Player":
        scout_player_page()
    elif page == "Compare Players":
        compare_players_page()
    elif page == "Hidden Gems":
        hidden_gems_page()
    elif page == "Similarity Search":
        similarity_search_page()
    elif page == "Ask AI":
        ask_ai_page()

    # Sidebar info
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Scouted Players")
    if st.session_state.scouted_players:
        for player in st.session_state.scouted_players:
            st.sidebar.markdown(f"- {player}")
    else:
        st.sidebar.markdown("*No players scouted yet*")


def scout_player_page():
    st.header("Scout a Player")

    col1, col2 = st.columns([3, 1])
    with col1:
        player_name = st.text_input("Enter player name", placeholder="e.g., Oscar Gloukh")
    with col2:
        scout_button = st.button("Scout", type="primary", use_container_width=True)

    if scout_button and player_name:
        with st.spinner(f"Scouting {player_name}..."):
            try:
                report = asyncio.run(st.session_state.agent.scout_player(player_name))

                # Add to scouted list
                if player_name not in st.session_state.scouted_players:
                    st.session_state.scouted_players.append(player_name)

                # Add to vector store
                if st.session_state.vector_store:
                    try:
                        st.session_state.vector_store.add_player(report.player)
                    except Exception:
                        pass

                # Display results
                st.success(f"Successfully scouted {report.player.info.name}")

                # Player info cards
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Position", report.player.info.position or "N/A")
                with col2:
                    st.metric("Age", report.player.info.age or "N/A")
                with col3:
                    st.metric("Club", report.player.info.current_club or "N/A")
                with col4:
                    st.metric("Market Value", report.player.info.market_value or "N/A")

                # Stats
                st.subheader("Performance Stats")
                if report.player.normalized_stats:
                    stats = report.player.normalized_stats
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Goals/Game", f"{stats.goals_per_game:.2f}")
                    with col2:
                        st.metric("Assists/Game", f"{stats.assists_per_game:.2f}")
                    with col3:
                        st.metric("Goals/90", f"{stats.goals_per_90:.2f}")
                    with col4:
                        st.metric("Assists/90", f"{stats.assists_per_90:.2f}")

                    # Totals
                    st.subheader("Career Totals")
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total Goals", stats.total_goals)
                    with col2:
                        st.metric("Total Assists", stats.total_assists)
                    with col3:
                        st.metric("Appearances", stats.total_appearances)
                    with col4:
                        st.metric("Minutes", f"{stats.total_minutes:,}")

                # Season breakdown
                st.subheader("Season by Season")
                if report.player.seasons:
                    season_data = []
                    for s in report.player.seasons:
                        season_data.append({
                            "Season": s.season,
                            "Apps": s.appearances,
                            "Goals": s.goals,
                            "Assists": s.assists,
                            "Minutes": s.minutes_played,
                        })
                    df = pd.DataFrame(season_data)
                    st.dataframe(df, use_container_width=True)

            except PlayerNotFoundError:
                st.error(f"Player '{player_name}' not found on Transfermarkt")
            except FootballScoutError as e:
                st.error(f"Error: {e}")


def compare_players_page():
    st.header("Compare Players")

    if len(st.session_state.scouted_players) < 2:
        st.warning("Scout at least 2 players first to compare them.")
        return

    selected = st.multiselect(
        "Select players to compare",
        st.session_state.scouted_players,
        default=st.session_state.scouted_players[:2] if len(st.session_state.scouted_players) >= 2 else []
    )

    if len(selected) >= 2:
        if st.button("Compare", type="primary"):
            with st.spinner("Comparing players..."):
                try:
                    result = asyncio.run(st.session_state.agent.compare_players(selected))
                    st.text(result)
                except FootballScoutError as e:
                    st.error(f"Error: {e}")

        # Create comparison table
        st.subheader("Quick Comparison")
        comparison_data = []
        for name in selected:
            player = st.session_state.agent.get_scouted_player(name)
            if player and player.normalized_stats:
                comparison_data.append({
                    "Player": player.info.name,
                    "Position": player.info.position or "N/A",
                    "Club": player.info.current_club or "N/A",
                    "Goals/Game": f"{player.normalized_stats.goals_per_game:.2f}",
                    "Assists/Game": f"{player.normalized_stats.assists_per_game:.2f}",
                    "Goals/90": f"{player.normalized_stats.goals_per_90:.2f}",
                    "Assists/90": f"{player.normalized_stats.assists_per_90:.2f}",
                })

        if comparison_data:
            df = pd.DataFrame(comparison_data)
            st.dataframe(df, use_container_width=True)


def hidden_gems_page():
    st.header("Hidden Gems Finder")
    st.markdown("Find undervalued players based on their statistical output relative to market value.")

    if not st.session_state.scouted_players:
        st.warning("Scout some players first to find hidden gems among them.")
        return

    col1, col2 = st.columns(2)
    with col1:
        max_value = st.number_input(
            "Maximum Market Value (EUR)",
            min_value=100000,
            max_value=100000000,
            value=5000000,
            step=500000,
            format="%d"
        )
    with col2:
        min_apps = st.number_input(
            "Minimum Appearances",
            min_value=1,
            max_value=100,
            value=10
        )

    if st.button("Find Hidden Gems", type="primary"):
        with st.spinner("Analyzing players..."):
            gems = asyncio.run(st.session_state.agent.find_hidden_gems(max_value, min_apps))

            if gems:
                st.subheader("Top Undervalued Players")

                for i, (player, score) in enumerate(gems[:10], 1):
                    with st.expander(f"#{i} {player.info.name} (Score: {score:.2f})"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"**Club:** {player.info.current_club or 'N/A'}")
                            st.markdown(f"**Position:** {player.info.position or 'N/A'}")
                            st.markdown(f"**Market Value:** {player.info.market_value or 'N/A'}")
                        with col2:
                            if player.normalized_stats:
                                st.markdown(f"**Goals/90:** {player.normalized_stats.goals_per_90:.2f}")
                                st.markdown(f"**Assists/90:** {player.normalized_stats.assists_per_90:.2f}")
                                st.markdown(f"**Appearances:** {player.normalized_stats.total_appearances}")
            else:
                st.info("No hidden gems found with the current criteria. Try adjusting the filters or scouting more players.")


def similarity_search_page():
    st.header("Player Similarity Search")

    if st.session_state.vector_store is None:
        st.error("Vector store not available. ChromaDB may not be properly configured.")
        return

    if not st.session_state.scouted_players:
        st.warning("Scout some players first to use similarity search.")
        return

    tab1, tab2 = st.tabs(["Search by Player", "Search by Description"])

    with tab1:
        selected_player = st.selectbox("Select a player", st.session_state.scouted_players)
        n_results = st.slider("Number of similar players", 1, 10, 5)

        if st.button("Find Similar Players", key="similar_player"):
            player = st.session_state.agent.get_scouted_player(selected_player)
            if player:
                with st.spinner("Searching..."):
                    similar = st.session_state.vector_store.find_similar(player, n_results)

                    if similar:
                        st.subheader(f"Players similar to {selected_player}")
                        for i, p in enumerate(similar, 1):
                            st.markdown(f"**{i}. {p['name']}** - {p['club']} ({p['position']})")
                    else:
                        st.info("No similar players found. Try scouting more players.")

    with tab2:
        query = st.text_area(
            "Describe the player you're looking for",
            placeholder="e.g., Young attacking midfielder with high goal output from German league"
        )
        n_results_text = st.slider("Number of results", 1, 10, 5, key="n_results_text")

        if st.button("Search", key="search_text"):
            if query:
                with st.spinner("Searching..."):
                    results = st.session_state.vector_store.find_similar_by_text(query, n_results_text)

                    if results:
                        st.subheader("Matching Players")
                        for i, p in enumerate(results, 1):
                            st.markdown(f"**{i}. {p['name']}** - {p['club']} ({p['position']})")
                    else:
                        st.info("No matching players found.")


def ask_ai_page():
    st.header("Ask AI")

    if not st.session_state.scouted_players:
        st.warning("Scout some players first to ask questions about them.")
        return

    st.markdown("Ask any question about the scouted players.")

    question = st.text_area(
        "Your question",
        placeholder="e.g., Who has the best goal scoring record? Which player would you recommend for a top club?"
    )

    if st.button("Ask", type="primary"):
        if question:
            with st.spinner("Thinking..."):
                try:
                    answer = asyncio.run(st.session_state.agent.answer_question(question))
                    st.markdown("### AI Response")
                    st.markdown(answer)
                except FootballScoutError as e:
                    st.error(f"Error: {e}")


if __name__ == "__main__":
    main()
