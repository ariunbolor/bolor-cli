#!/usr/bin/env python
"""
CLI implementation for Bolor.

This module handles command-line arguments and dispatches to the appropriate functionality.
"""

import os
import sys
import warnings
import typer
import re
from pathlib import Path
from typing import List, Optional, Sequence, Union, Any, Dict
from rich.console import Console
from rich import print as rprint
from rich.prompt import Prompt

# Suppress dependency warnings from requests library
warnings.filterwarnings("ignore", category=Warning)

# Import bolor_core modules
from bolor_core.gguf_downloader import ensure_models
from bolor_core.code_checker import analyze_file_and_suggest_fixes, explain_file, optimize_file
from bolor_core.git_utils import apply_patch
from bolor_core.llm_runner import get_default_llm, LocalLLM

# Initialize custom Typer app and console
class BolarCliContext(typer.Context):
    """Custom Context class that always uses 'bolor' as the command path."""
    
    @property
    def command_path(self) -> str:
        """Override to always return 'bolor'."""
        return "bolor"

# Patch the command name to always be 'bolor'
if hasattr(typer, '_utils'):
    if hasattr(typer._utils, 'get_command_name'):
        original_get_command_name = typer._utils.get_command_name
        
        def patched_get_command_name(*args, **kwargs):
            return "bolor"
        
        typer._utils.get_command_name = patched_get_command_name

# Create a basic wrapper around Typer for consistent command naming
class BolarTyper(typer.Typer):
    """Custom Typer subclass for consistent command naming."""
    
    def __init__(self, *args, **kwargs):
        """Initialize with bolor-specific settings."""
        # Force click parameters to always show bolor as command name
        if "context_settings" not in kwargs:
            kwargs["context_settings"] = {}
        if "help_option_names" not in kwargs["context_settings"]:
            kwargs["context_settings"]["help_option_names"] = ["--help", "-h"]
            
        # Set additional variables that Click/Typer might use
        os.environ["FORCE_COMMAND_NAME"] = "bolor"
        
        # Initialize with these settings
        super().__init__(*args, **kwargs)
        
        # Apply patches to click
        self._patch_click()
    
    def _patch_click(self):
        """Patch underlying click mechanisms that determine command name."""
        try:
            import click
            # Force the determination of command name to always be 'bolor'
            original_format_usage = getattr(click.core.Context, "format_usage", None)
            if original_format_usage:
                def patched_format_usage(self, *args, **kwargs):
                    result = original_format_usage(self, *args, **kwargs)
                    return result.replace("python -m bolor.bolor", "bolor")
                click.core.Context.format_usage = patched_format_usage
                
            # Patch get_usage
            original_get_usage = getattr(click.core.Context, "get_usage", None)
            if original_get_usage:
                def patched_get_usage(self, *args, **kwargs):
                    result = original_get_usage(self, *args, **kwargs)
                    return result.replace("python -m bolor.bolor", "bolor")
                click.core.Context.get_usage = patched_get_usage
                
            # Patch help formatting
            if hasattr(click, "formatting"):
                original_wrap_text = getattr(click.formatting, "wrap_text", None)
                if original_wrap_text:
                    def patched_wrap_text(text, *args, **kwargs):
                        result = original_wrap_text(text, *args, **kwargs)
                        return result.replace("python -m bolor.bolor", "bolor")
                    click.formatting.wrap_text = patched_wrap_text
        except:
            pass
    
    def get_command_error_suggestion(self, command: str) -> str:
        """Override error suggestion to use 'bolor'."""
        return "Try 'bolor --help' for help."
    
    def format_help(self, ctx, formatter):
        """Override help formatting to replace command names."""
        result = super().format_help(ctx, formatter)
        if hasattr(formatter, "buffer"):
            # Process each line in the buffer
            for i, line in enumerate(formatter.buffer):
                if isinstance(line, str) and "python -m bolor" in line:
                    formatter.buffer[i] = line.replace("python -m bolor.bolor", "bolor")
                    formatter.buffer[i] = formatter.buffer[i].replace("python -m bolor", "bolor")
        return result
    
    def make_context(self, info_name: str, args: list, parent=None, **kwargs):
        """Override to use our custom context class."""
        # Always use 'bolor' as the info_name
        info_name = "bolor"
        kwargs["obj"] = kwargs.get("obj", {})
        return BolarCliContext(info_name, parent=parent, **kwargs)
    
    def __call__(self, *args, **kwargs):
        """Override to ensure consistent command name."""
        # Save current argv
        original_argv = sys.argv.copy()
        
        # Force command name to be 'bolor'
        if len(sys.argv) > 0:
            sys.argv[0] = "bolor"
        
        try:
            return super().__call__(*args, **kwargs)
        finally:
            # Restore original argv
            sys.argv = original_argv

# Create the Typer app with our custom class
app = BolarTyper(
    help="Bolor: Local LLM-based code repair tool with self-healing capabilities.",
    add_completion=False,
    no_args_is_help=True,
    context_settings={"help_option_names": ["--help", "-h"]},
)
console = Console()

# Define constants
BOLOR_HOME = Path.home() / ".bolor"
MODELS_DIR = BOLOR_HOME / "models"

@app.command()
def update():
    """Download or update local GGUF models."""
    console.print("[bold cyan]🔄 Checking for model updates...")
    ensure_models(MODELS_DIR)
    console.print("[green]✅ Models are up to date.")

@app.command()
def check(
    file: str,
    apply_fixes: bool = typer.Option(
        False, "--apply", "-a", help="Automatically apply suggested fixes"
    )
):
    """Analyze a file and suggest fixes."""
    file_path = Path(file)
    if not file_path.exists():
        console.print(f"[red]❌ File not found: {file}")
        raise typer.Exit()

    suggestions = analyze_file_and_suggest_fixes(file_path)
    if not suggestions:
        console.print("[green]✅ No issues found.")
        return

    for idx, (line, message, fix) in enumerate(suggestions, 1):
        console.print(f"[yellow]⚠️ Issue {idx} at line {line}:")
        console.print(f"  {message}")
        console.print(f"  Suggested fix: {fix}\n")

    if apply_fixes or Prompt.ask("Apply suggested fixes?", choices=["y", "n"], default="n") == "y":
        apply_patch(file_path, suggestions)
        console.print("[green]✅ Fixes applied.")
    else:
        console.print("[blue]ℹ️ Skipping fix application.")

@app.command()
def explain(
    file: str,
    output: Optional[str] = typer.Option(
        None, "--output", "-o", help="Output file to save explanation (optional)"
    )
):
    """Explain what the code does using the LLM."""
    file_path = Path(file)
    if not file_path.exists():
        console.print(f"[red]❌ File not found: {file}")
        raise typer.Exit()
    
    console.print(f"[bold cyan]🧠 Analyzing {file}...")
    explanation = explain_file(file_path)
    
    console.print("[bold green]📝 Explanation:[/bold green]")
    console.print(f"[green]{explanation}[/green]")
    
    if output:
        output_path = Path(output)
        output_path.write_text(explanation)
        console.print(f"[blue]ℹ️ Explanation saved to {output}")

@app.command()
def optimize(
    file: str,
    output: Optional[str] = typer.Option(
        None, "--output", "-o", help="Output file to save optimized code (optional)"
    ),
    apply: bool = typer.Option(
        False, "--apply", "-a", help="Apply optimizations to the original file (creates backup)"
    )
):
    """Optimize code for better performance or readability."""
    file_path = Path(file)
    if not file_path.exists():
        console.print(f"[red]❌ File not found: {file}")
        raise typer.Exit()
    
    console.print(f"[bold cyan]🧠 Optimizing {file}...")
    explanation, optimized_code = optimize_file(file_path)
    
    console.print("[bold green]📝 Optimization explanation:[/bold green]")
    console.print(f"[green]{explanation}[/green]")
    
    console.print("[bold green]📄 Optimized code:[/bold green]")
    console.print(optimized_code)
    
    if output:
        output_path = Path(output)
        output_path.write_text(optimized_code)
        console.print(f"[blue]ℹ️ Optimized code saved to {output}")
    
    if apply:
        # Backup original file
        backup_path = file_path.with_suffix(file_path.suffix + ".bak")
        file_path.rename(backup_path)
        
        # Write optimized code to original location
        file_path.write_text(optimized_code)
        console.print(f"[green]✅ Optimizations applied. Original saved as {backup_path.name}")

@app.command()
def document(
    file: str,
    output: Optional[str] = typer.Option(
        None, "--output", "-o", help="Output file to save documented code (optional)"
    ),
    apply: bool = typer.Option(
        False, "--apply", "-a", help="Apply documentation to the original file (creates backup)"
    )
):
    """Add or improve documentation in code."""
    file_path = Path(file)
    if not file_path.exists():
        console.print(f"[red]❌ File not found: {file}")
        raise typer.Exit()
    
    # First check for missing docstrings and other issues
    suggestions = analyze_file_and_suggest_fixes(file_path)
    
    if not suggestions:
        console.print("[green]✅ Code is already well-documented.")
        return
    
    # Filter for documentation-related issues
    doc_suggestions = [s for s in suggestions if "docstring" in s[1].lower() or "comment" in s[1].lower()]
    
    if not doc_suggestions:
        console.print("[yellow]⚠️ Found issues, but none related to documentation.")
        # Display all issues instead
        for idx, (line, message, fix) in enumerate(suggestions, 1):
            console.print(f"[yellow]⚠️ Issue {idx} at line {line}:")
            console.print(f"  {message}")
    else:
        console.print(f"[yellow]⚠️ Found {len(doc_suggestions)} documentation issues:")
        for idx, (line, message, fix) in enumerate(doc_suggestions, 1):
            console.print(f"[yellow]⚠️ Issue {idx} at line {line}:")
            console.print(f"  {message}")
            console.print(f"  Suggested fix: {fix}\n")
        
        if apply or Prompt.ask("Apply documentation fixes?", choices=["y", "n"], default="n") == "y":
            apply_patch(file_path, doc_suggestions)
            console.print("[green]✅ Documentation fixes applied.")
        else:
            console.print("[blue]ℹ️ Skipping documentation fixes.")

@app.command()
def generate(
    prompt: str,
    output: Optional[str] = typer.Option(
        None, "--output", "-o", help="Output file to save generated code (optional)"
    ),
    language: Optional[str] = typer.Option(
        None, "--language", "-l", help="Programming language (default: auto-detect)"
    )
):
    """Generate code from a natural language prompt."""
    console.print(f"[bold cyan]🧠 Generating code for: {prompt}...")
    
    # Import only when needed to avoid circular imports
    from bolor.agent.generator import generate_code_from_prompt
    
    try:
        generated_code = generate_code_from_prompt(prompt, language=language)
        
        console.print("[bold green]📄 Generated code:[/bold green]")
        console.print(generated_code)
        
        if output:
            output_path = Path(output)
            output_path.write_text(generated_code)
            console.print(f"[green]✅ Code saved to {output}")
    except Exception as e:
        console.print(f"[red]❌ Error generating code: {str(e)}")

@app.command()
def scan(
    path: str,
    apply_fixes: bool = typer.Option(
        False, "--apply", "-a", help="Automatically apply suggested fixes"
    ),
    recursive: bool = typer.Option(
        False, "--recursive", "-r", help="Scan directories recursively"
    )
):
    """Scan files or directories for issues and suggest fixes."""
    target_path = Path(path)
    if not target_path.exists():
        console.print(f"[red]❌ Path not found: {path}")
        raise typer.Exit()
    
    # Process a single file
    if target_path.is_file():
        check(str(target_path), apply_fixes=apply_fixes)
        return
    
    # Process a directory
    console.print(f"[bold cyan]🔍 Scanning directory: {path}...")
    
    # Get Python files
    if recursive:
        files = list(target_path.glob("**/*.py"))
    else:
        files = list(target_path.glob("*.py"))
    
    if not files:
        console.print("[yellow]⚠️ No Python files found in this directory.")
        return
    
    console.print(f"[blue]Found {len(files)} Python files to check.")
    
    # Process each file
    issues_found = 0
    for file in files:
        console.print(f"[cyan]Checking {file.relative_to(target_path)}...")
        suggestions = analyze_file_and_suggest_fixes(file)
        
        if suggestions:
            issues_found += len(suggestions)
            for idx, (line, message, fix) in enumerate(suggestions, 1):
                console.print(f"[yellow]⚠️ Issue {idx} at line {line}:")
                console.print(f"  {message}")
                console.print(f"  Suggested fix: {fix}\n")
            
            if apply_fixes:
                apply_patch(file, suggestions)
                console.print(f"[green]✅ Applied {len(suggestions)} fixes to {file.relative_to(target_path)}")
    
    if issues_found:
        console.print(f"[yellow]Found {issues_found} issues in {len(files)} files.")
    else:
        console.print(f"[green]✅ No issues found in {len(files)} files.")

@app.command()
def config(
    model: Optional[str] = typer.Option(
        None, "--model", "-m", help="Set default model: phi-2 or starcoder2-3b"
    ),
    mode: Optional[str] = typer.Option(
        None, "--mode", help="Set inference mode: fast or accurate"
    ),
    show: bool = typer.Option(
        False, "--show", "-s", help="Show current configuration"
    )
):
    """Configure Bolor settings."""
    import json
    
    config_dir = BOLOR_HOME / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file = config_dir / "config.json"
    
    # Load existing config
    if config_file.exists():
        try:
            with open(config_file, "r") as f:
                config_data = json.load(f)
        except json.JSONDecodeError:
            console.print("[yellow]⚠️ Config file exists but is invalid. Creating new config.")
            config_data = {}
    else:
        config_data = {}
    
    if show:
        console.print("[bold cyan]Current Configuration:[/bold cyan]")
        for key, value in config_data.items():
            if isinstance(value, dict):
                console.print(f"[cyan]{key}:[/cyan]")
                for subkey, subvalue in value.items():
                    console.print(f"  [cyan]{subkey}:[/cyan] {subvalue}")
            else:
                console.print(f"[cyan]{key}:[/cyan] {value}")
        return
    
    # Update configuration
    changed = False
    
    if model:
        if model not in ["phi-2", "starcoder2-3b"]:
            console.print(f"[red]❌ Invalid model: {model}. Must be 'phi-2' or 'starcoder2-3b'")
        else:
            if "model" not in config_data:
                config_data["model"] = {}
            config_data["model"]["name"] = model
            console.print(f"[green]✅ Default model set to {model}")
            changed = True
    
    if mode:
        if mode not in ["fast", "accurate"]:
            console.print(f"[red]❌ Invalid mode: {mode}. Must be 'fast' or 'accurate'")
        else:
            config_data["mode"] = mode
            console.print(f"[green]✅ Inference mode set to {mode}")
            changed = True
    
    # Save updated config
    if changed:
        with open(config_file, "w") as f:
            json.dump(config_data, f, indent=2)
        console.print(f"[green]✅ Configuration saved to {config_file}")
    elif not show:
        console.print("[blue]ℹ️ No configuration changes made")

def main():
    """Main entry point for the CLI."""
    # Determine the command name - prioritize environment variable if set
    command_name = os.environ.get("BOLOR_CLI_COMMAND_NAME", "bolor")
    
    # Force the command name to always be consistent
    original_argv0 = ""
    if len(sys.argv) > 0:
        original_argv0 = sys.argv[0]
        sys.argv[0] = command_name
    
    # Apply global patches to typer
    if hasattr(typer, '_main'):
        if hasattr(typer._main, '_get_command_name'):
            # Override command name function
            def patched_command_name(*args, **kwargs):
                return "bolor"
            typer._main._get_command_name = patched_command_name
    
    try:
        # Call the app directly
        app()
    except Exception as e:
        # Special error handling to fix command name in error messages
        message = str(e)
        if "python" in message and "bolor" in message:
            # Fix the error message
            fixed = message
            patterns = [
                "python -m bolor.bolor", "python3 -m bolor.bolor",
                "python -m bolor", "python3 -m bolor",
                "python -mbolor", "python3 -mbolor"
            ]
            for pattern in patterns:
                fixed = fixed.replace(pattern, "bolor")
            
            print(fixed, file=sys.stderr)
            sys.exit(1)
        raise
    finally:
        # Always restore original command name
        if original_argv0 and len(sys.argv) > 0:
            sys.argv[0] = original_argv0

if __name__ == "__main__":
    main()
