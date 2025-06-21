#!/usr/bin/env python3
"""
LANS CLI - Command Line Interface for Large Artificial Neural System
Allows users to interact with LANS through natural language prompts
"""

import asyncio
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.prompt import Prompt
from rich.markdown import Markdown

from .core.lans_engine import LANSEngine
from .core.config import LANSConfig
from .intelligent_coordinator import IntelligentCoordinator
from .llm.ollama_client import OllamaClient
import time

app = typer.Typer(
    name="lans",
    help="LANS - Large Artificial Neural System CLI",
    add_completion=False,
    rich_markup_mode="rich"
)

console = Console()

class LANSCLIError(Exception):
    """Custom exception for CLI errors"""
    pass

def display_banner():
    """Display LANS banner"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║    🧠 LANS - Large Artificial Neural System                 ║
    ║    Universal AI Software Generation Platform                 ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    console.print(banner, style="bold blue")

def display_help():
    """Display help information"""
    help_text = """
    ## 🚀 LANS Commands

    **Basic Usage:**
    ```bash
    lans "create a calculator app"
    lans "build a todo list with React"
    lans "make a Python script to process CSV files"
    ```

    **Interactive Mode:**
    ```bash
    lans --interactive
    ```

    **Project Management:**
    ```bash
    lans --workspace /path/to/project "add authentication to my app"
    lans --list-projects
    ```

    **Examples:**
    - `lans "create folder my_project"`
    - `lans "create file hello.py with a greeting function"`
    - `lans "build a FastAPI server with user authentication"`
    - `lans "create a React component for displaying user profiles"`
    """
    console.print(Markdown(help_text))
  
@app.command()
def main(
    prompt: Optional[str] = typer.Argument(None, help="Natural language prompt for LANS"),
    ail: bool = typer.Option(False, "--ail", help="Interpret prompt as AIL instruction"),
    interactive: bool = typer.Option(False, "--interactive", "-i", help="Start interactive mode"),
    workspace: Optional[str] = typer.Option(None, "--workspace", "-w", help="Workspace directory"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Model to use"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    list_projects: bool = typer.Option(False, "--list-projects", help="List recent projects"),
):
    """
    Main entry point for LANS CLI.
    """
    # Initialize LANS first
    try:
        workspace_path = Path(workspace) if workspace else Path.cwd()
        config = LANSConfig(
            workspace=workspace_path,
            model=model,
            verbose=verbose
        )
        lans = LANSEngine(config)
    except Exception as e:
        console.print(f"❌ Failed to initialize LANS: {e}", style="bold red")
        raise typer.Exit(1)

    # Check interactive mode first
    if interactive:
        asyncio.run(interactive_mode(lans))
    elif list_projects:
        list_recent_projects()
    elif prompt and not ail:
        asyncio.run(process_prompt(lans, prompt))
    elif prompt and ail:
        asyncio.run(process_ail_instruction(lans, prompt))
    else:
        display_banner()
        console.print("💡 Use --help for usage information or --interactive for interactive mode", style="yellow")
        display_help()

async def interactive_mode(lans: LANSEngine):
    """Interactive mode for continuous prompting"""
    display_banner()
    console.print("🎯 Interactive Mode - Type 'exit' to quit, 'help' for commands\n", style="bold green")
    
    while True:
        try:
            # Get user input
            user_input = Prompt.ask(
                "[bold blue]LANS[/bold blue]",
                default="",
                show_default=False
            ).strip()
            
            if not user_input:
                continue
                
            if user_input.lower() in ['exit', 'quit', 'q']:
                console.print("👋 Goodbye!", style="bold blue")
                break
                
            if user_input.lower() in ['help', 'h']:
                display_help()
                continue
                
            if user_input.lower() == 'clear':
                console.clear()
                display_banner()
                continue
            
            # Process the prompt
            await process_prompt(lans, user_input)
            console.print()  # Add spacing
            
        except KeyboardInterrupt:
            console.print("\n👋 Goodbye!", style="bold blue")
            break
        except Exception as e:
            console.print(f"❌ Error: {e}", style="bold red")

async def process_prompt(lans: LANSEngine, prompt: str):
    """Process a single prompt"""
    console.print(f"🎯 Processing: [italic]{prompt}[/italic]", style="bold blue")
    
    # Show spinner while processing
    with console.status("[bold green]🧠 LANS is thinking...", spinner="dots"):
        try:
            result = await lans.process_request(prompt)
            
            if result.success:
                console.print("✅ Task completed successfully!", style="bold green")
                
                # Display results
                if result.files_created:
                    console.print("\n📁 Files created:", style="bold yellow")
                    for file_path in result.files_created:
                        console.print(f"  • {file_path}", style="green")
                
                if result.commands_executed:
                    console.print("\n⚡ Commands executed:", style="bold yellow")
                    for cmd in result.commands_executed:
                        console.print(f"  • {cmd}", style="cyan")
                
                if result.message:
                    console.print(f"\n💬 {result.message}", style="white")
                    
            else:
                console.print("❌ Task failed", style="bold red")
                if result.error:
                    console.print(f"Error: {result.error}", style="red")
                    
        except Exception as e:
            console.print(f"❌ Processing failed: {e}", style="bold red")

async def process_ail_instruction(lans: LANSEngine, instruction: str):
    """Process a raw AIL instruction"""
    console.print(f"🔧 Executing AIL: [italic]{instruction}[/italic]", style="bold magenta")
    with console.status("[bold magenta]🚀 AIL executing...", spinner="bouncingBall"):
        try:
            result = await lans.process_ail_instruction(instruction)
            if result.success:
                console.print("✅ AIL instruction succeeded", style="bold green")
                if result.message:
                    console.print(f"\n💡 Result: {result.message}", style="green")
            else:
                console.print("❌ AIL instruction failed", style="bold red")
                if result.error:
                    console.print(f"Error: {result.error}", style="red")
        except Exception as e:
            console.print(f"❌ AIL processing error: {e}", style="bold red")

def list_recent_projects():
    """List recent projects"""
    console.print("📋 Recent LANS Projects:", style="bold blue")
    
    # This would integrate with the global memory system
    projects = [
        {"name": "calculator_app", "date": "2024-01-15", "type": "Python GUI"},
        {"name": "todo_react", "date": "2024-01-14", "type": "React App"},
        {"name": "api_server", "date": "2024-01-13", "type": "FastAPI"},
    ]
    
    if not projects:
        console.print("No recent projects found.", style="yellow")
        return
    
    for project in projects:
        console.print(f"  • {project['name']} ({project['type']}) - {project['date']}", style="green")

@app.command()
def init(
    path: Optional[Path] = typer.Argument(None, help="Project directory"),
    template: Optional[str] = typer.Option(None, "--template", "-t", help="Project template"),
):
    """Initialize a new LANS project"""
    project_path = path or Path.cwd()

    console.print(f"🚀 Initializing LANS project in {project_path}", style="bold blue")

    # Create project structure
    try:
        project_path.mkdir(exist_ok=True)
        (project_path / ".lans").mkdir(exist_ok=True)
        
        # Create config file
        config_content = (
            f"# LANS Project Configuration\n"
            f"project_name: {project_path.name}\n"
            f"template: {template or 'default'}\n"
            f"created: {typer.get_app_dir('lans')}\n"
        )
        (project_path / ".lans" / "config.yaml").write_text(config_content)

        console.print("✅ Project initialized successfully!", style="bold green")
        console.print(f"📁 Project directory: {project_path}", style="green")
        
    except Exception as e:
        console.print(f"❌ Failed to initialize project: {e}", style="bold red")
        raise typer.Exit(1)

@app.command()
def status():
    """Show LANS system status"""
    console.print("🔍 LANS System Status", style="bold blue")
    
    # Check system components
    status_items = [
        ("Ollama Server", check_ollama_status()),
        ("MCP Server", check_mcp_status()),
        ("Global Memory", check_memory_status()),
    ]
    
    for component, status in status_items:
        status_icon = "✅" if status else "❌"
        status_text = "Running" if status else "Not Available"
        console.print(f"  {status_icon} {component}: {status_text}")

def check_ollama_status() -> bool:
    """Check if Ollama is running"""
    import urllib.request
    try:
        response = urllib.request.urlopen("http://localhost:11434/api/tags", timeout=2)
        return response.getcode() == 200
    except Exception:
        return False

def check_mcp_status() -> bool:
    """Check if MCP server is running"""
    # Implementation would check MCP server status
    return True  # Placeholder

def check_memory_status() -> bool:
    """Check if global memory system is available"""
    # Implementation would check memory system status
    return True  # Placeholder

@app.command()
def ail_status(
    workspace: Optional[str] = typer.Option(None, "--workspace", "-w", help="Workspace directory"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Model to use"),
):
    """Check whether each agent responds to a simple AIL ping."""
    try:
        workspace_path = Path(workspace) if workspace else Path.cwd()
        config = LANSConfig(workspace=workspace_path, model=model, verbose=False)
        console.print("🔍 Initializing AIL status check...", style="bold blue")
        client = OllamaClient(config)
        coord = IntelligentCoordinator(client)
        # Allow AgentOS and GMCP to initialize
        time.sleep(2)
    except Exception as e:
        console.print(f"❌ Initialization failed: {e}", style="bold red")
        raise typer.Exit(1)

    async def run_checks():
        results = {}
        for name in coord.available_agents.keys():
            inst = coord._translate_to_ail_instruction(name, "ping")
            res = await coord._execute_ail_instruction(inst)
            results[name] = res.get("success", False)
        return results

    try:
        results = asyncio.run(run_checks())
        overall = all(results.values())
        for name, ok in results.items():
            icon = "✅" if ok else "❌"
            console.print(f"{icon} {name}", style="green" if ok else "red")
        if overall:
            console.print("🎉 All agents responded successfully via AIL", style="bold green")
        else:
            console.print("⚠️ Some agents failed AIL ping", style="bold red")
    except Exception as e:
        console.print(f"❌ AIL status check error: {e}", style="bold red")
        raise typer.Exit(1)

if __name__ == "__main__":
    app()
