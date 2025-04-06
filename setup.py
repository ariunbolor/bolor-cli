from setuptools import setup, find_packages

setup(
    name="bolor",
    version="0.2.7",  # Version bump for config.py import fix
    description="Local LLM-based code repair tool with self-healing capabilities",
    author="Bolorerdene Bundgaa",
    author_email="hi@photoxpedia.studio",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "ctransformers>=0.2.0",     # For local LLM
        "langchain>=0.0.208",       # For embeddings and chains
        "chromadb>=0.4.0",          # Vector storage
        "rich>=13.0.0",             # Terminal UI
        "astunparse>=1.6.3",        # Python AST manipulation
        "typer>=0.9.0",             # Modern CLI interface
        "pytest>=7.0.0",            # For testing fixes
        "urllib3>=1.26.0,<2.0.0",   # Fix dependency warning
        "charset-normalizer>=2.0.0,<3.0.0",  # Fix dependency warning
        "requests>=2.25.0,<3.0.0",   # Fix dependency issues
    ],
    scripts=["bolor-wrap", "bolor-cli"],
    entry_points={
        "console_scripts": [
            "bolor=bolor.cli:app"
        ]
    },
    long_description="""
    Bolor is a local LLM-based code repair tool with self-healing capabilities.
    It can scan codebases for issues, fix detected problems, and generate code from natural language descriptions.
    The tool is designed to work locally without requiring an internet connection.

    ## Key Features

    - **Code Scanning**: Scan your code for issues and get suggestions for improvements
    - **Code Generation**: Generate code from natural language prompts
    - **Local Operation**: Works offline with local models

    ## Commands

    - `bolor update` - Download or update local GGUF models
    - `bolor check <file>` - Analyze a file and suggest fixes
    - `bolor explain <file>` - Explain what the code does using LLM
    - `bolor optimize <file>` - Optimize code for better performance or readability
    - `bolor document <file>` - Add or improve documentation in code
    - `bolor config` - Configure Bolor settings
    """,
    long_description_content_type="text/markdown",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Debuggers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
    ],
    python_requires=">=3.8",
)
