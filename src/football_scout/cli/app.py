"""Football Scout CLI Application."""
import asyncio
from typing import Optional, List

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from football_scout import __version__
from football_scout.core.agent import FootballScoutAI
from football_scout.exceptions import PlayerNotFoundError, FootballScoutError, NoPlayersScoutedError

app = typer.Typer(
    name="football-scout",
    help="AI-powered football scouting agent using RAG",
    no_args_is_help=True,
    rich_markup_mode="rich",
)
console = Console()

# Global agent instance for maintaining state across commands
_agent: Optional[FootballScoutAI] = None


def get_agent() -> FootballScoutAI:
    """Get or create the agent instance."""
    global _agent
    if _agent is None:
        _agent = FootballScoutAI()
    return _agent


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"[bold blue]Football Scout[/] v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False, "--version", "-V", callback=version_callback, is_eager=True,
        help="Show version and exit."
    ),
) -> None:
    """Football Scout - AI-powered football scouting agent."""
    pass


@app.command()
def scout(
    players: List[str] = typer.Argument(
        ..., help="Player names to scout (can provide multiple)"
    ),
    output_format: str = typer.Option(
        "report", "--format", "-f",
        help="Output format: report, table, or json"
    ),
    no_save: bool = typer.Option(
        False, "--no-save",
        help="Don't save results to file"
    ),
) -> None:
    """Scout one or more football players.

    Examples:
        football-scout scout "Oscar Gloukh"
        football-scout scout "Messi" "Ronaldo" --format table
    """
    agent = get_agent()

    for player_name in players:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"Scouting {player_name}...", total=None)

            try:
                report = asyncio.run(agent.scout_player(player_name, save_to_file=not no_save))
                progress.update(task, completed=True)

                if output_format == "table":
                    _display_table(report)
                elif output_format == "json":
                    _display_json(report)
                else:
                    _display_report(report)

            except PlayerNotFoundError:
                console.print(f"[red]Error:[/] Player '{player_name}' not found")
            except FootballScoutError as e:
                console.print(f"[red]Error:[/] {e}")


@app.command()
def compare(
    players: List[str] = typer.Argument(
        ..., help="Players to compare (minimum 2, must be scouted first)"
    ),
) -> None:
    """Compare two or more previously scouted players.

    Example:
        football-scout compare "Messi" "Ronaldo"
    """
    if len(players) < 2:
        console.print("[red]Error:[/] Need at least 2 players to compare")
        raise typer.Exit(1)

    agent = get_agent()

    try:
        result = asyncio.run(agent.compare_players(players))
        console.print(Panel(result, title="Player Comparison", expand=False))
    except NoPlayersScoutedError as e:
        console.print(f"[red]Error:[/] {e}")
        console.print("[yellow]Tip:[/] Scout players first using 'football-scout scout \"Player Name\"'")


@app.command()
def ask(
    question: str = typer.Argument(..., help="Question to ask about scouted players"),
) -> None:
    """Ask a follow-up question about previously scouted players.

    Example:
        football-scout ask "Who has the better goal-to-game ratio?"
    """
    agent = get_agent()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Thinking...", total=None)

        try:
            result = asyncio.run(agent.answer_question(question))
            progress.update(task, completed=True)
            console.print(Panel(result, title="AI Response", expand=False))
        except NoPlayersScoutedError:
            progress.update(task, completed=True)
            console.print("[red]Error:[/] No players scouted yet")
            console.print("[yellow]Tip:[/] Scout players first using 'football-scout scout \"Player Name\"'")
        except FootballScoutError as e:
            progress.update(task, completed=True)
            console.print(f"[red]Error:[/] {e}")


@app.command()
def gems(
    max_value: float = typer.Option(
        5_000_000, "--max-value", "-m",
        help="Maximum market value to consider"
    ),
    min_appearances: int = typer.Option(
        10, "--min-apps", "-a",
        help="Minimum career appearances"
    ),
) -> None:
    """Find hidden gems (undervalued players) from scouted players.

    Example:
        football-scout gems --max-value 10000000
    """
    agent = get_agent()

    try:
        gems_list = asyncio.run(agent.find_hidden_gems(max_value, min_appearances))

        if not gems_list:
            console.print("[yellow]No hidden gems found.[/] Try scouting more players first.")
            return

        table = Table(title="Hidden Gems - Undervalued Players")
        table.add_column("Rank", style="cyan")
        table.add_column("Player", style="green")
        table.add_column("Club", style="blue")
        table.add_column("Market Value")
        table.add_column("Goals/90")
        table.add_column("Assists/90")
        table.add_column("Value Score", style="magenta")

        for i, (player, score) in enumerate(gems_list[:10], 1):
            stats = player.normalized_stats
            table.add_row(
                str(i),
                player.info.name,
                player.info.current_club or "N/A",
                player.info.market_value or "N/A",
                f"{stats.goals_per_90:.2f}" if stats else "N/A",
                f"{stats.assists_per_90:.2f}" if stats else "N/A",
                f"{score:.2f}",
            )

        console.print(table)

    except FootballScoutError as e:
        console.print(f"[red]Error:[/] {e}")


@app.command(name="compare-age")
def compare_age(
    player1: str = typer.Argument(..., help="First player name"),
    player2: str = typer.Argument(..., help="Second player name"),
    age: int = typer.Option(
        20, "--age", "-a",
        help="Age to compare at"
    ),
) -> None:
    """Compare two players at the same age.

    Example:
        football-scout compare-age "Gloukh" "Mbappe" --age 20
    """
    agent = get_agent()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Analyzing...", total=None)

        try:
            result = asyncio.run(agent.compare_at_age(player1, player2, age))
            progress.update(task, completed=True)
            console.print(Panel(result, title=f"Age {age} Comparison", expand=False))
        except PlayerNotFoundError as e:
            progress.update(task, completed=True)
            console.print(f"[red]Error:[/] {e}")
            console.print("[yellow]Tip:[/] Make sure both players are scouted first")
        except FootballScoutError as e:
            progress.update(task, completed=True)
            console.print(f"[red]Error:[/] {e}")


@app.command()
def similar(
    player_name: str = typer.Argument(..., help="Player to find similar players for"),
    top: int = typer.Option(
        5, "--top", "-t",
        help="Number of similar players to return"
    ),
) -> None:
    """Find players similar to a given player (requires RAG setup).

    Example:
        football-scout similar "Oscar Gloukh" --top 5
    """
    console.print("[yellow]Similarity search requires ChromaDB setup.[/]")
    console.print("Run the Streamlit dashboard for full similarity search functionality.")


@app.command()
def interactive() -> None:
    """Start an interactive scouting session."""
    agent = get_agent()
    console.print(Panel(
        "[bold]Football Scout Interactive Mode[/]\n\n"
        "Commands:\n"
        "  [cyan]scout <name>[/] - Scout a player\n"
        "  [cyan]compare[/] - Compare scouted players\n"
        "  [cyan]?<question>[/] - Ask a follow-up question\n"
        "  [cyan]gems[/] - Find hidden gems\n"
        "  [cyan]exit[/] - Exit interactive mode",
        title="Welcome",
        expand=False
    ))

    while True:
        try:
            user_input = console.input("\n[bold green]>[/] ").strip()

            if not user_input:
                continue

            if user_input.lower() == 'exit':
                console.print("[blue]Thank you for using Football Scout![/]")
                break

            elif user_input.lower() == 'compare':
                players = list(agent._players.keys())
                if len(players) < 2:
                    console.print("[yellow]Scout at least two players first.[/]")
                else:
                    result = asyncio.run(agent.compare_players(players))
                    console.print(result)

            elif user_input.startswith('?'):
                question = user_input[1:].strip()
                if question:
                    try:
                        result = asyncio.run(agent.answer_question(question))
                        console.print(Panel(result, title="AI Response"))
                    except NoPlayersScoutedError:
                        console.print("[yellow]Scout some players first.[/]")

            elif user_input.lower() == 'gems':
                gems_list = asyncio.run(agent.find_hidden_gems())
                if gems_list:
                    for player, score in gems_list[:5]:
                        console.print(f"  {player.info.name}: {score:.2f}")
                else:
                    console.print("[yellow]No hidden gems found.[/]")

            elif user_input.lower().startswith('scout '):
                player_name = user_input[6:].strip()
                if player_name:
                    try:
                        with console.status(f"Scouting {player_name}..."):
                            report = asyncio.run(agent.scout_player(player_name))
                        console.print(report.report_text)
                    except PlayerNotFoundError:
                        console.print(f"[red]Player '{player_name}' not found.[/]")

            else:
                # Treat as player name to scout
                try:
                    with console.status(f"Scouting {user_input}..."):
                        report = asyncio.run(agent.scout_player(user_input))
                    console.print(report.report_text)
                except PlayerNotFoundError:
                    console.print(f"[red]Player '{user_input}' not found.[/]")

        except KeyboardInterrupt:
            console.print("\n[blue]Goodbye![/]")
            break


def _display_table(report) -> None:
    """Display player report as a Rich table."""
    player = report.player
    stats = player.normalized_stats

    table = Table(title=f"Player Report: {player.info.name}")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Position", player.info.position or "N/A")
    table.add_row("Age", player.info.age or "N/A")
    table.add_row("Nationality", player.info.nationality or "N/A")
    table.add_row("Club", player.info.current_club or "N/A")
    table.add_row("Market Value", player.info.market_value or "N/A")
    table.add_row("", "")
    table.add_row("Total Goals", str(stats.total_goals) if stats else "N/A")
    table.add_row("Total Assists", str(stats.total_assists) if stats else "N/A")
    table.add_row("Total Appearances", str(stats.total_appearances) if stats else "N/A")
    table.add_row("", "")
    table.add_row("Goals/Game", f"{stats.goals_per_game:.2f}" if stats else "N/A")
    table.add_row("Assists/Game", f"{stats.assists_per_game:.2f}" if stats else "N/A")
    table.add_row("Goals/90", f"{stats.goals_per_90:.2f}" if stats else "N/A")
    table.add_row("Assists/90", f"{stats.assists_per_90:.2f}" if stats else "N/A")

    console.print(table)


def _display_json(report) -> None:
    """Display player report as JSON."""
    import json
    console.print_json(json.dumps(report.player.model_dump(), indent=2, default=str))


def _display_report(report) -> None:
    """Display player report as text."""
    console.print(Panel(report.report_text, title="Player Report", expand=False))


if __name__ == "__main__":
    app()
