#!/usr/bin/env python
"""
Main entry point for Bolor CLI.

This module handles command-line arguments and dispatches to the appropriate functionality.
"""

import os
import sys
import warnings
import typer
from pathlib import Path
from typing import List, Optional
from rich.console import Console
from rich import print as rprint

# Suppress dependency warnings from requests library
warnings.filterwarnings("ignore", category=Warning)

from bolor.utils.config import Config
from bolor.agent.scanner import Scanner
from bolor.agent.fixer import Fixer
from bolor.agent.planner import Planner
from bolor.agent.generator import Generator
from bolor.agent.dataset_loader import DatasetLoader

# Initialize typer app and console
app = typer.Typer(
    help="Bolor: Local LLM-based code repair tool with self-healing capabilities.",
    add_completion=False,
)
console = Console()


@app.command()
def scan(
    project_path: str = typer.Argument(
        ".", help="Path to the project to scan"
    ),
    fix: bool = typer.Option(
        False, "--fix", "-f", help="Automatically apply fixes for detected issues"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
):
    """
    Scan a codebase for issues and optionally fix them.
    """
    console.print(f"[bold blue]Scanning project: {project_path}[/bold blue]")
    
    # Initialize components
    config = Config()
    config.set("verbose", verbose)
    scanner = Scanner(config)
    
    # Scan for issues
    try:
        project_path = Path(project_path).resolve()
        if not project_path.exists():
            console.print(f"[bold red]Error: Project path {project_path} does not exist[/bold red]")
            return 1
        
        issues = scanner.scan_directory(project_path)
        if not issues:
            console.print("[green]No issues found![/green]")
            return 0
        
        console.print(f"[yellow]Found {len(issues)} potential issues[/yellow]")
        for i, issue in enumerate(issues, 1):
            console.print(f"[yellow]Issue {i}:[/yellow] {issue.description}")
            console.print(f"  [dim]File:[/dim] {issue.file_path}:{issue.line_number}")
            if verbose:
                console.print(f"  [dim]Code:[/dim] {issue.code_snippet}")
        
        # Apply fixes if requested
        if fix:
            console.print("\n[bold blue]Applying fixes...[/bold blue]")
            fixer = Fixer(config)
            fixed_issues = fixer.fix_issues(issues)
            
            console.print(f"[green]Successfully fixed {len(fixed_issues)} issues[/green]")
            for i, issue in enumerate(fixed_issues, 1):
                console.print(f"[green]Fix {i}:[/green] {issue.description}")
                console.print(f"  [dim]File:[/dim] {issue.file_path}:{issue.line_number}")
                if verbose:
                    console.print(f"  [dim]Before:[/dim] {issue.code_snippet}")
                    console.print(f"  [dim]After:[/dim] {issue.fixed_code_snippet}")
        
        return 0
        
    except Exception as e:
        console.print(f"[bold red]Error during scan: {str(e)}[/bold red]")
        if verbose:
            console.print_exception()
        return 1


@app.command()
def plan(
    project_path: str = typer.Argument(
        ".", help="Path to the project to analyze"
    ),
    output_format: str = typer.Option(
        "text", "--format", "-f", help="Output format: text, markdown, or json"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
):
    """
    Analyze a codebase and suggest improvements.
    """
    console.print(f"[bold blue]Planning improvements for: {project_path}[/bold blue]")
    
    # Initialize components
    config = Config()
    config.set("verbose", verbose)
    config.set("output_format", output_format)
    planner = Planner(config)
    
    # Analyze project
    try:
        project_path = Path(project_path).resolve()
        if not project_path.exists():
            console.print(f"[bold red]Error: Project path {project_path} does not exist[/bold red]")
            return 1
        
        suggestions = planner.analyze_project(project_path)
        if not suggestions:
            console.print("[green]No improvement suggestions found.[/green]")
            return 0
        
        console.print(f"[green]Found {len(suggestions)} improvement suggestions:[/green]")
        for i, suggestion in enumerate(suggestions, 1):
            console.print(f"[green]Suggestion {i}:[/green] {suggestion.title}")
            console.print(f"  [dim]Type:[/dim] {suggestion.type}")
            console.print(f"  [dim]Description:[/dim] {suggestion.description}")
            if verbose and suggestion.code_example:
                console.print(f"  [dim]Example:[/dim]\n{suggestion.code_example}")
        
        return 0
        
    except Exception as e:
        console.print(f"[bold red]Error during planning: {str(e)}[/bold red]")
        if verbose:
            console.print_exception()
        return 1


@app.command()
def deploy_check(
    project_path: str = typer.Argument(
        ".", help="Path to the project to check"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
):
    """
    Check a codebase for deployment issues.
    """
    console.print(f"[bold blue]Checking deployment for: {project_path}[/bold blue]")
    
    # Initialize components
    config = Config()
    config.set("verbose", verbose)
    scanner = Scanner(config)
    
    # Check for deployment issues
    try:
        project_path = Path(project_path).resolve()
        if not project_path.exists():
            console.print(f"[bold red]Error: Project path {project_path} does not exist[/bold red]")
            return 1
        
        issues = scanner.scan_ci_config(project_path)
        if not issues:
            console.print("[green]No deployment issues found![/green]")
            return 0
        
        console.print(f"[yellow]Found {len(issues)} potential deployment issues:[/yellow]")
        for i, issue in enumerate(issues, 1):
            console.print(f"[yellow]Issue {i}:[/yellow] {issue.description}")
            console.print(f"  [dim]File:[/dim] {issue.file_path}")
            if verbose:
                console.print(f"  [dim]Details:[/dim] {issue.details}")
        
        return 0
        
    except Exception as e:
        console.print(f"[bold red]Error during deployment check: {str(e)}[/bold red]")
        if verbose:
            console.print_exception()
        return 1


@app.command()
def update(
    force: bool = typer.Option(
        False, "--force", "-f", help="Force re-download of models and resources"
    ),
    no_model: bool = typer.Option(
        False, "--no-model", help="Set up in no-model mode without downloading models"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
):
    """
    Update models and resources for Bolor.
    
    This command will download or update the necessary model files and configuration
    for Bolor to function properly. Use --no-model to skip model download and operate
    in limited functionality mode.
    """
    console.print("[bold blue]Bolor Update Tool[/bold blue]")
    config = Config()
    config.set("verbose", verbose)
    
    # Import necessary modules inside the function to avoid reference errors
    import os as os_module
    import time
    import json
    import requests
    from pathlib import Path as PathClass
    
    # Create the config file directory
    config_dir = PathClass(os_module.path.expanduser("~/.bolor/config"))
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file = config_dir / "config.json"
    
    # Define model information
    MODEL_INFO = {
        "name": "phi-2",
        "fallback_file": "phi-2.Q2_K.gguf",
        "fallback_url": "https://huggingface.co/TheBloke/phi-2-GGUF/resolve/main/phi-2.Q2_K.gguf",
        "fallback_size": 1500000000,  # ~1.5GB (approximate)
    }
    
    if no_model:
        try:
            # Set up in no-model mode (limited functionality)
            console.print("[green]Setting up Bolor in no-model mode...[/green]")
            
            # Create a no-model config
            config_data = {
                "model": {
                    "name": "phi-2",
                    "file": "phi-2.Q2_K.gguf",
                    "type": "llama"
                },
                "no_model_mode": True
            }
            
            # Save the config
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
                
            console.print(f"[green]Created no-model configuration at {config_file}[/green]")
            console.print("[green]Bolor will now operate in limited functionality mode[/green]")
            console.print("[green]You can use these commands:[/green]")
            console.print("[green]  bolor scan [directory][/green]")
            console.print("[green]  bolor plan [directory][/green]")
            console.print("[green]  bolor generate \"your prompt\"[/green]")
            
            return 0
        
        except Exception as e:
            console.print(f"[bold red]Error setting up no-model mode: {str(e)}[/bold red]")
            return 1
    
    else:
        try:
            # Actually download the model
            console.print("[blue]Setting up Bolor with Phi-2 model...[/blue]")
    
            # Determine Bolor's data directory
            BOLOR_DIR = os_module.path.expanduser("~/.bolor")
            models_dir = PathClass(BOLOR_DIR) / "models"
            model_dir = models_dir / MODEL_INFO["name"]
            model_dir.mkdir(parents=True, exist_ok=True)
            fallback_model_path = model_dir / MODEL_INFO["fallback_file"]
            
            console.print(f"[blue]Model directory: {model_dir}[/blue]")
            
            # Download the model
            console.print(f"[blue]Downloading Phi-2 model from {MODEL_INFO['fallback_url']}[/blue]")
            console.print("[blue]This may take a while (~1.5GB)...[/blue]")
            
            try:
                # Create a backup of the existing file if it exists and force is True
                if force and os_module.path.exists(fallback_model_path):
                    backup_path = fallback_model_path.with_suffix('.bak')
                    console.print(f"[blue]Creating backup of existing model file to {backup_path}[/blue]")
                    os_module.rename(fallback_model_path, backup_path)
                
                # Only download if the file doesn't exist or force is True
                if force or not os_module.path.exists(fallback_model_path):
                    # Stream the download to show progress
                    with requests.get(MODEL_INFO["fallback_url"], stream=True) as r:
                        r.raise_for_status()
                        total_size = int(r.headers.get('content-length', 0))
                        downloaded = 0
                        progress_step = max(total_size // 100, 1024 * 1024)  # 1% or 1MB minimum
                        next_progress = progress_step
                        
                        with open(fallback_model_path, 'wb') as f:
                            start_time = time.time()
                            for chunk in r.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                                    downloaded += len(chunk)
                                    
                                    # Show progress
                                    if downloaded >= next_progress:
                                        percent = min(downloaded * 100 // total_size, 100)
                                        elapsed = time.time() - start_time
                                        speed = downloaded / (elapsed * 1024 * 1024) if elapsed > 0 else 0
                                        console.print(f"[blue]Downloaded: {percent}% ({downloaded//(1024*1024)}MB / {total_size//(1024*1024)}MB) - {speed:.1f} MB/s[/blue]")
                                        next_progress = downloaded + progress_step
                    
                    console.print(f"[green]Download completed: {fallback_model_path}[/green]")
                else:
                    console.print(f"[green]Model file already exists at {fallback_model_path}[/green]")
                
                # Update config with the model information
                console.print("[blue]Updating configuration...[/blue]")
                
                # Create or load the config
                if config_file.exists():
                    with open(config_file, 'r') as f:
                        config_data = json.load(f)
                else:
                    config_data = {}
                
                # Make sure model settings exist
                if "model" not in config_data:
                    config_data["model"] = {}
                
                # Set the model configuration
                config_data["model"]["name"] = MODEL_INFO["name"]
                config_data["model"]["file"] = MODEL_INFO["fallback_file"]
                config_data["model"]["type"] = "llama"
                config_data["no_model_mode"] = False
                
                # Save the updated config
                with open(config_file, 'w') as f:
                    json.dump(config_data, f, indent=2)
                
                console.print(f"[green]Updated configuration in {config_file}[/green]")
                console.print("[bold green]Bolor setup completed successfully![/bold green]")
                console.print("[green]You can now use Bolor with the following commands:[/green]")
                console.print("[green]  bolor scan [directory][/green]")
                console.print("[green]  bolor plan [directory][/green]")
                console.print("[green]  bolor generate \"your prompt\"[/green]")
                return 0
                
            except requests.RequestException as e:
                console.print(f"[bold red]Error downloading model: {e}[/bold red]")
                if os_module.path.exists(str(fallback_model_path) + ".bak"):
                    console.print("[blue]Restoring backup...[/blue]")
                    os_module.rename(str(fallback_model_path) + ".bak", fallback_model_path)
                raise
            
        except Exception as e:
            console.print(f"[bold red]Error updating Bolor: {str(e)}[/bold red]")
            if verbose:
                console.print_exception()
            return 1
    
    # Original update command code below (not used)
    """
    Update models and resources for Bolor.
    
    This command will download or update the necessary model files and configuration
    for Bolor to function properly, bypassing issues with model loading.
    """
    # DIRECT IMPLEMENTATION: We're not using the generator at all to avoid the OptionInfo bug
    console.print("[bold blue]Updating Bolor resources...[/bold blue]")
    console.print("[yellow]Using direct update method - bypassing model dependency[/yellow]")
    
    # Initialize configuration
    config = Config()
    config.set("verbose", verbose)
    
    try:
        # SKIP ANY LLM USAGE COMPLETELY
        console.print("[blue]Downloading model...[/blue]")
        
        # Import necessary modules
        import os
        import requests
        import time
        import json
        from pathlib import Path
        
        # Define model information
        MODEL_INFO = {
            "name": "phi-2",
            "fallback_file": "phi-2.Q2_K.gguf",
            "fallback_url": "https://huggingface.co/TheBloke/phi-2-GGUF/resolve/main/phi-2.Q2_K.gguf",
            "fallback_size": 1500000000,  # ~1.5GB (approximate)
        }
        
        # Determine Bolor's data directory
        BOLOR_DIR = os.path.expanduser("~/.bolor")
        models_dir = Path(BOLOR_DIR) / "models"
        model_dir = models_dir / MODEL_INFO["name"]
        model_dir.mkdir(parents=True, exist_ok=True)
        fallback_model_path = model_dir / MODEL_INFO["fallback_file"]
        
        console.print(f"[blue]Model directory: {model_dir}[/blue]")
        
        # Download the fallback model (smaller and potentially more compatible)
        console.print(f"[blue]Downloading fallback model from {MODEL_INFO['fallback_url']}[/blue]")
        console.print("[blue]This may take a while (~1.5GB)...[/blue]")
        
        try:
            # Create a backup of the existing file if it exists and force is True
            if force and os.path.exists(fallback_model_path):
                backup_path = fallback_model_path.with_suffix('.bak')
                console.print(f"[blue]Creating backup of existing model file to {backup_path}[/blue]")
                os.rename(fallback_model_path, backup_path)
            
            # Only download if the file doesn't exist or force is True
            if force or not os.path.exists(fallback_model_path):
                # Stream the download to show progress
                with requests.get(MODEL_INFO["fallback_url"], stream=True) as r:
                    r.raise_for_status()
                    total_size = int(r.headers.get('content-length', 0))
                    downloaded = 0
                    progress_step = max(total_size // 100, 1024 * 1024)  # 1% or 1MB minimum
                    next_progress = progress_step
                    
                    with open(fallback_model_path, 'wb') as f:
                        start_time = time.time()
                        for chunk in r.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                downloaded += len(chunk)
                                
                                # Show progress
                                if downloaded >= next_progress:
                                    percent = min(downloaded * 100 // total_size, 100)
                                    elapsed = time.time() - start_time
                                    speed = downloaded / (elapsed * 1024 * 1024) if elapsed > 0 else 0
                                    console.print(f"[blue]Downloaded: {percent}% ({downloaded//(1024*1024)}MB / {total_size//(1024*1024)}MB) - {speed:.1f} MB/s[/blue]")
                                    next_progress = downloaded + progress_step
                
                console.print(f"[green]Download completed: {fallback_model_path}[/green]")
            else:
                console.print(f"[green]Model file already exists at {fallback_model_path}[/green]")
            
            # Update config with the model information
            console.print("[blue]Updating configuration...[/blue]")
            config_dir = Path(BOLOR_DIR) / "config"
            config_dir.mkdir(parents=True, exist_ok=True)
            config_file = config_dir / "config.json"
            
            # Create or load the config
            if config_file.exists():
                with open(config_file, 'r') as f:
                    config_data = json.load(f)
            else:
                config_data = {}
            
            # Make sure model settings exist
            if "model" not in config_data:
                config_data["model"] = {}
            
            # Set the model configuration
            config_data["model"]["name"] = MODEL_INFO["name"]
            config_data["model"]["file"] = MODEL_INFO["fallback_file"]
            config_data["model"]["type"] = "phi"  # Default to phi, will be updated if another type works
            
            # Try different model types with ctransformers
            console.print("[blue]Testing model loading with different model types...[/blue]")
            try:
                from ctransformers import AutoModelForCausalLM
                
                # Try different model types since 'phi' might not be supported in this version
                model_types = ["phi", "gpt2", "gptj", "gpt_neox", "bloom", "mpt", "falcon", "starcoder", "llama"]
                successful_model_type = None
                
                for model_type in model_types:
                    try:
                        console.print(f"[blue]Trying to load model with type: {model_type}[/blue]")
                        model = AutoModelForCausalLM.from_pretrained(
                            str(model_dir),
                            model_file=MODEL_INFO["fallback_file"],
                            model_type=model_type
                        )
                        console.print(f"[green]Successfully loaded model with type: {model_type}[/green]")
                        successful_model_type = model_type
                        break
                    except Exception as e:
                        if verbose:
                            console.print(f"[yellow]Failed to load with '{model_type}' type: {e}[/yellow]")
                
                if successful_model_type:
                    # Update config with the successful model type
                    config_data["model"]["type"] = successful_model_type
                    console.print(f"[green]Model can be loaded with type: {successful_model_type}[/green]")
                else:
                    console.print("[yellow]Could not find a compatible model type. Will keep 'phi' as default.[/yellow]")
                    console.print("[yellow]You may need to reinstall ctransformers with: pip install --force-reinstall ctransformers[/yellow]")
            except ImportError:
                console.print("[yellow]ctransformers not installed. Please install with 'pip install ctransformers'[/yellow]")
            
            # Save the updated config
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            console.print(f"[green]Updated configuration in {config_file}[/green]")
            
            # Skip dataset download as it requires a working model
            console.print("[yellow]Skipping dataset download (requires working model)[/yellow]")
            console.print("[yellow]Skipping vector store building (requires working model)[/yellow]")
            
            console.print("[bold green]Bolor update completed successfully![/bold green]")
            console.print("[green]You can now use Bolor with the following commands:[/green]")
            console.print("[green]  bolor scan [directory][/green]")
            console.print("[green]  bolor plan [directory][/green]")
            console.print("[green]  bolor generate \"your prompt here\"[/green]")
            return 0
            
        except requests.RequestException as e:
            console.print(f"[bold red]Error downloading model: {e}[/bold red]")
            if os.path.exists(str(fallback_model_path) + ".bak"):
                console.print("[blue]Restoring backup...[/blue]")
                os.rename(str(fallback_model_path) + ".bak", fallback_model_path)
            raise
        
    except Exception as e:
        console.print(f"[bold red]Error updating Bolor: {str(e)}[/bold red]")
        if verbose:
            console.print_exception()
        return 1


@app.command()
def generate(
    prompt: str = typer.Argument(
        ..., help="Natural language description of what to generate"
    ),
    output_file: Optional[str] = typer.Option(
        None, "--output", "-o", help="File to save the generated code to"
    ),
    language: Optional[str] = typer.Option(
        None, "--language", "-l", help="Programming language to generate in (auto-detected if not specified)"
    ),
    no_comments: bool = typer.Option(
        False, "--no-comments", help="Generate code without explanatory comments"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
):
    """
    Generate code from a natural language description.
    """
    console.print(f"[bold blue]Generating code for: {prompt}[/bold blue]")
    
    # Initialize components
    config = Config()
    config.set("verbose", verbose)
    generator = Generator(config)
    
    # Generate code
    try:
        generated_code = generator.generate_from_prompt(
            prompt=prompt, 
            language=language,
            add_comments=not no_comments
        )
        
        console.print(f"[green]Generated code:[/green]")
        console.print(generated_code)
        
            # Save to file if requested
        if output_file:
            try:
                # Check if output_file is an OptionInfo object (common error)
                if hasattr(output_file, "__class__") and output_file.__class__.__name__ == "OptionInfo":
                    # Don't try to use it as a path
                    console.print("[bold red]Error: Cannot save to OptionInfo object[/bold red]")
                    console.print("[yellow]This is a known issue with the Bolor CLI.[/yellow]")
                    console.print("[green]Your code was generated successfully (but not saved to file):[/green]")
                    console.print(generated_code)
                else:
                    # Convert output_file to string and use it as a path
                    output_file_str = str(output_file)
                    output_path = Path(output_file_str)
                    
                    # If directory doesn't exist, create it
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    with open(output_path, 'w') as f:
                        f.write(generated_code)
                    console.print(f"[green]Code saved to: {output_file_str}[/green]")
            except Exception as e:
                console.print(f"[yellow]Warning: Error writing to file: {str(e)}[/yellow]")
                console.print("[green]Your code was generated successfully (but not saved to file):[/green]")
                console.print(generated_code)
        
        return 0
        
    except Exception as e:
        console.print(f"[bold red]Error generating code: {str(e)}[/bold red]")
        if verbose:
            console.print_exception()
        return 1


# Default command handler for natural language interface
@app.callback(invoke_without_command=True)
def main_callback(
    ctx: typer.Context,
    prompt: Optional[str] = typer.Argument(
        None, help="Natural language prompt (if no command is specified)"
    ),
):
    """
    If no command is specified but a prompt is provided,
    treat it as a generate command.
    """
    # Only process if no command was specified but a prompt was provided
    if ctx.invoked_subcommand is None and prompt:
        # Call the generate command with the provided prompt
        return generate(prompt=prompt)


def preprocess_args():
    """Process command line arguments before passing to Typer."""
    # Get all command arguments
    args = sys.argv[1:] if len(sys.argv) > 1 else []
    
    # If no arguments, just return None to let Typer handle it
    if not args:
        return None
    
    # Extract the first argument (potential command)
    cmd = args[0]
    
    # Define known commands
    KNOWN_COMMANDS = {"scan", "plan", "deploy_check", "deploy-check", 
                     "download_resources", "download-resources", "generate", "update"}
    
    # Check if it's a known command
    cmd_normalized = cmd.replace("-", "_")  # normalize command name
    if cmd_normalized in KNOWN_COMMANDS:
        # Let Typer handle command arguments - don't do any special processing
        return None
    
    # If it's not a known command, assume it's a generate prompt
    # Join all arguments as the prompt
    prompt = " ".join(args)
    
    # Replace sys.argv with a generate command followed by the prompt
    sys.argv = [sys.argv[0], "generate", prompt]
    return None
def main():
    """Main entry point for the CLI."""
    # First preprocess the arguments
    preprocess_args()
    
    # Then run the app
    try:
        return app()
    except Exception as e:
        console = Console()
        console.print(f"[bold red]Unexpected error: {str(e)}[/bold red]")
        console.print_exception()
        return 1