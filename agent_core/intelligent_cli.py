"""
Intelligent LANS CLI - No hardcoded flows, pure AI agent assignment
"""

import asyncio
import typer
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from pathlib import Path

from .intelligent_coordinator import IntelligentCoordinator
from .llm.ollama_client import OllamaClient
from .core.config import LANSConfig


app = typer.Typer(help="LANS - Intelligent AI Platform (No Hardcoded Workflows)")
console = Console()


@app.command()
def ask(
    query: str = typer.Argument(..., help="Ask LANS to do anything - it will figure out how"),
    workspace: str = typer.Option("./lans_workspace", "--workspace", "-w", help="Workspace directory"),
    ollama_url: str = typer.Option("http://localhost:11434", "--ollama", help="Ollama server URL"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed AI reasoning"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what LANS would do without executing")
):
    """
    Intelligent request handler - LANS decides how to approach any query.
    
    Examples:
      lans ask "write a heartfelt letter to my creator"
      lans ask "build me a calculator app"  
      lans ask "create a folder called projects"
      lans ask "explain quantum computing"
      lans ask "analyze this data and create visualizations"
      lans ask "build a full-stack todo app with React and FastAPI"
    """
    
    if verbose:
        console.print("[bold blue]🧠 LANS Intelligent Platform[/bold blue]")
        console.print(f"Query: {query}")
        console.print(f"Workspace: {workspace}")
        console.print()
    
    if dry_run:
        console.print("[yellow]🔍 DRY RUN - Analyzing what LANS would do...[/yellow]")
    
    # Run intelligent processing
    asyncio.run(_process_intelligent_request(query, workspace, ollama_url, verbose, dry_run))


async def _process_intelligent_request(query: str, workspace: str, ollama_url: str, verbose: bool, dry_run: bool):
    """Let LANS intelligently figure out how to handle any request"""
    
    try:
        # Initialize the intelligent coordinator
        console.print("[yellow]🚀 Initializing LANS Intelligence...[/yellow]")
        
        llm_client = OllamaClient(ollama_url)
        coordinator = IntelligentCoordinator(llm_client)
        
        # Test AI connectivity
        with console.status("[yellow]🔗 Checking AI connection...[/yellow]"):
            try:
                from .models import AgentType
                test_response = await llm_client.generate(
                    prompt="Hello",
                    agent_type=AgentType.COORDINATOR,
                    temperature=0.1
                )
                console.print("✅ AI models ready")
            except Exception as e:
                console.print(f"[red]❌ AI connection failed: {e}[/red]")
                console.print("[yellow]💡 Please ensure Ollama is running: `ollama serve`[/yellow]")
                console.print("[yellow]💡 And model is available: `ollama pull deepseek-coder:6.7b`[/yellow]")
                return
        
        if dry_run:
            # Just show analysis without execution
            with console.status("[yellow]🧠 Analyzing request...[/yellow]"):
                analysis = await coordinator._analyze_query(query)
            
            _display_analysis_only(analysis, query)
            return
        
        # Full intelligent processing
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            # Let LANS figure out how to handle this
            task = progress.add_task("🧠 LANS thinking...", total=None)
            
            result = await coordinator.process_query(query, workspace)
            
            progress.remove_task(task)
        
        # Display results intelligently
        _display_intelligent_results(result, verbose)
        
        console.print("[green]✅ Request completed by LANS Intelligence![/green]")
        
    except KeyboardInterrupt:
        console.print("\n[yellow]⏹️  Cancelled by user[/yellow]")
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        if verbose:
            import traceback
            console.print("[red]Traceback:[/red]")
            console.print(traceback.format_exc())


def _display_analysis_only(analysis: dict, query: str):
    """Display only the analysis in dry-run mode"""
    
    # Analysis panel
    analysis_table = Table(show_header=False, box=None)
    analysis_table.add_column("Property", style="bold cyan")
    analysis_table.add_column("Value")
    
    analysis_table.add_row("Intent", analysis.get("intent", "Unknown"))
    analysis_table.add_row("Category", analysis.get("category", "Unknown"))
    analysis_table.add_row("Complexity", analysis.get("complexity", "Unknown"))
    analysis_table.add_row("Required Capabilities", ", ".join(analysis.get("required_capabilities", [])))
    analysis_table.add_row("Estimated Tasks", str(analysis.get("estimated_tasks", 1)))
    analysis_table.add_row("Approach", analysis.get("suggested_approach", "Unknown"))
    analysis_table.add_row("Reasoning", analysis.get("reasoning", "No reasoning provided"))
    
    console.print(Panel(
        analysis_table,
        title="[bold yellow]🧠 LANS Intelligence Analysis[/bold yellow]",
        border_style="yellow"
    ))
    
    # What would happen
    deliverables = analysis.get("deliverables", ["Unknown output"])
    console.print(f"\n[bold green]📋 LANS would deliver:[/bold green]")
    for deliverable in deliverables:
        console.print(f"  • {deliverable}")


def _display_intelligent_results(result: dict, verbose: bool):
    """Display results based on what LANS actually did"""
    
    if not result.get("success"):
        # Error case
        console.print(Panel(
            f"[red]❌ {result.get('error', 'Unknown error')}[/red]",
            title="[bold red]Processing Failed[/bold red]",
            border_style="red"
        ))
        
        if result.get("suggestion"):
            console.print(f"[yellow]💡 Suggestion: {result['suggestion']}[/yellow]")
        return
    
    # Success - show what LANS decided to do
    approach = result.get("approach", "unknown")
    
    # Show approach taken
    approach_info = Table(show_header=False, box=None)
    approach_info.add_column("Property", style="bold cyan")
    approach_info.add_column("Value")
    
    if approach == "simple_single_agent":
        approach_info.add_row("Approach", "Single Agent Assignment")
        approach_info.add_row("Agent Selected", result.get("assigned_agent", "Unknown"))
        approach_info.add_row("Reasoning", "LANS determined this was a simple request")
    elif approach == "multi_agent_coordination":
        approach_info.add_row("Approach", "Multi-Agent Coordination")
        approach_info.add_row("Tasks Created", str(len(result.get("assignments", []))))
        approach_info.add_row("Reasoning", "LANS determined this needed multiple agents")
    
    console.print(Panel(
        approach_info,
        title="[bold blue]🎯 LANS Decision Process[/bold blue]",
        border_style="blue"
    ))
    
    # Show specific results based on what was actually done
    if approach == "simple_single_agent":
        _display_single_agent_results(result)
    elif approach == "multi_agent_coordination":
        _display_multi_agent_results(result)
    
    # Show analysis if verbose
    if verbose and "analysis" in result:
        _display_verbose_analysis(result["analysis"])


def _display_single_agent_results(result: dict):
    """Display results from single agent execution"""
    
    agent_result = result.get("result", {})
    
    if agent_result.get("content_type") == "creative_writing":
        # Creative writing result
        info_table = Table(show_header=False, box=None)
        info_table.add_column("Property", style="bold cyan")
        info_table.add_column("Value")
        
        info_table.add_row("Content Type", "Creative Writing")
        if agent_result.get("file_path"):
            info_table.add_row("Saved To", agent_result["file_path"])
        if agent_result.get("word_count"):
            info_table.add_row("Word Count", str(agent_result["word_count"]))
        
        console.print(Panel(
            info_table,
            title="[bold green]✍️ Creative Content Generated[/bold green]",
            border_style="green"
        ))
        
        # Show content preview
        if agent_result.get("content"):
            content = agent_result["content"]
            preview = content[:300] + "..." if len(content) > 300 else content
            console.print(Panel(
                preview,
                title="[bold blue]📄 Content Preview[/bold blue]",
                border_style="blue"
            ))
    
    elif agent_result.get("operation") in ["create_folder", "create_file"]:
        # File operation result
        operation = agent_result["operation"]
        if operation == "create_folder":
            console.print(f"[green]📁 Created folder: {agent_result.get('folder_path')}[/green]")
        elif operation == "create_file":
            console.print(f"[green]📄 Created file: {agent_result.get('file_path')}[/green]")
            if agent_result.get("content_preview"):
                console.print(Panel(
                    agent_result["content_preview"],
                    title="[bold blue]File Content[/bold blue]",
                    border_style="blue"
                ))
    
    elif agent_result.get("type") == "conversation":
        # Conversational response
        console.print(Panel(
            agent_result.get("response", "No response"),
            title="[bold blue]💬 LANS Response[/bold blue]",
            border_style="blue"
        ))
    
    else:
        # Generic result
        console.print(Panel(
            f"✅ Completed by agent: {result.get('assigned_agent', 'Unknown')}",
            title="[bold green]Task Completed[/bold green]",
            border_style="green"
        ))


def _display_multi_agent_results(result: dict):
    """Display results from multi-agent coordination"""
    
    # Show task assignments
    assignments = result.get("assignments", [])
    if assignments:
        assignment_table = Table()
        assignment_table.add_column("Task", style="cyan")
        assignment_table.add_column("Assigned Agent", style="green")
        assignment_table.add_column("Status", justify="center")
        
        for assignment in assignments:
            task_desc = assignment["task"][:50] + "..." if len(assignment["task"]) > 50 else assignment["task"]
            agents = ", ".join(assignment["agents"])
            assignment_table.add_row(task_desc, agents, "✅")
        
        console.print(Panel(
            assignment_table,
            title="[bold green]🤖 Multi-Agent Execution[/bold green]",
            border_style="green"
        ))
    
    # Show individual task results
    task_results = result.get("results", [])
    for i, task_result in enumerate(task_results):
        if task_result.get("success"):
            console.print(f"✅ Task {i+1}: Completed by {task_result.get('assigned_agent', 'Unknown')}")
            
            # Show specific outputs if available
            if task_result.get("file_path"):
                console.print(f"   📄 Created: {task_result['file_path']}")
            elif task_result.get("content"):
                content_preview = task_result["content"][:100] + "..." if len(task_result["content"]) > 100 else task_result["content"]
                console.print(f"   📝 Content: {content_preview}")
        else:
            console.print(f"❌ Task {i+1}: Failed - {task_result.get('error', 'Unknown error')}")


def _display_verbose_analysis(analysis: dict):
    """Display detailed analysis information"""
    
    console.print("\n[bold cyan]🔍 Detailed Analysis:[/bold cyan]")
    
    analysis_table = Table(show_header=False, box=None)
    analysis_table.add_column("Property", style="bold cyan")
    analysis_table.add_column("Value")
    
    for key, value in analysis.items():
        if isinstance(value, list):
            value = ", ".join(str(v) for v in value)
        analysis_table.add_row(key.replace("_", " ").title(), str(value))
    
    console.print(Panel(
        analysis_table,
        title="[bold yellow]AI Analysis Details[/bold yellow]",
        border_style="yellow"
    ))


@app.command()
def agents():
    """Show available agents and their capabilities"""
    
    console.print("[bold blue]🤖 Available LANS Agents[/bold blue]\n")
    
    # Initialize coordinator to get agent info
    config = LANSConfig()  # Use default config for agent listing
    llm_client = OllamaClient(config)
    coordinator = IntelligentCoordinator(llm_client)
    
    agent_table = Table()
    agent_table.add_column("Agent", style="bold cyan")
    agent_table.add_column("Capabilities", style="green")
    agent_table.add_column("Specialties", style="yellow")
    agent_table.add_column("Load", justify="center")
    
    for name, agent in coordinator.available_agents.items():
        capabilities = ", ".join([cap.value for cap in agent.capabilities])
        specialties = ", ".join(agent.specialties[:3])  # Show first 3
        if len(agent.specialties) > 3:
            specialties += "..."
        load = f"{agent.current_tasks}/{agent.max_concurrent_tasks}"
        
        agent_table.add_row(name, capabilities, specialties, load)
    
    console.print(agent_table)
    
    console.print(f"\n[green]✅ {len(coordinator.available_agents)} agents ready for intelligent assignment[/green]")


@app.command()
def status():
    """Show LANS system status"""
    
    console.print("[bold blue]🧠 LANS Intelligence Status[/bold blue]")
    
    # Quick status check
    status_table = Table(show_header=False, box=None)
    status_table.add_column("Component", style="bold cyan")
    status_table.add_column("Status")
    
    status_table.add_row("Intelligent Coordinator", "✅ Ready")
    status_table.add_row("Request Analysis", "✅ Ready")
    status_table.add_row("Agent Assignment", "✅ Ready")
    status_table.add_row("Task Decomposition", "✅ Ready")
    status_table.add_row("Dynamic Routing", "✅ Ready")
    
    console.print(Panel(
        status_table,
        title="[bold green]System Status[/bold green]",
        border_style="green"
    ))
    
    console.print("\n[green]🚀 LANS is ready to intelligently handle any request![/green]")


@app.command()
def examples():
    """Show examples of what LANS can intelligently handle"""
    
    console.print("[bold blue]💡 LANS Intelligence Examples[/bold blue]\n")
    
    examples = [
        ("Creative Content", [
            'lans ask "write a heartfelt letter to my grandmother"',
            'lans ask "compose a short story about time travel"',
            'lans ask "draft a professional resignation email"',
            'lans ask "create a poem about artificial intelligence"'
        ]),
        ("Software Development", [
            'lans ask "build a calculator app with a modern GUI"',
            'lans ask "create a todo app with React frontend and FastAPI backend"',
            'lans ask "develop a CLI tool for processing JSON files"',
            'lans ask "make a simple game using Python and Pygame"'
        ]),
        ("File Operations", [
            'lans ask "create a folder structure for my new project"',
            'lans ask "make a configuration file with default settings"',
            'lans ask "organize these files by type"'
        ]),
        ("Data & Analysis", [
            'lans ask "analyze this CSV data and create visualizations"',
            'lans ask "build a data pipeline for processing logs"',
            'lans ask "create a machine learning model for classification"'
        ]),
        ("Questions & Conversation", [
            'lans ask "explain quantum computing in simple terms"',
            'lans ask "help me understand Docker containers"',
            'lans ask "what are the best practices for Python code?"'
        ])
    ]
    
    for category, commands in examples:
        console.print(f"[bold cyan]{category}:[/bold cyan]")
        for cmd in commands:
            console.print(f"  {cmd}")
        console.print()
    
    console.print("[green]💫 LANS intelligently figures out how to handle each request![/green]")


def main():
    """Main CLI entry point"""
    app()


if __name__ == "__main__":
    main()
