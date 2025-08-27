# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.




## Project Structure
This project is about learning ontology setup and usage. Currently it has directories:
- inspirations - with docs and texts serving as notes in which the project has to go
- chunking - a folder with python script with working implementation of text chunker
- sources - a folder with text sources which are used as example content to be chunked and analyzed further


- `pyproject.toml` - Project configuration using modern Python packaging standards
- `.python-version` - Specifies Python 3.10 as the target version
- `README.md` - Currently empty project documentation

## Development Commands

### Package Manager
This project is configured to use `uv` as the package manager. Always use `uv` for dependency management and running Python code.

### Running the Application
```bash
uv run main.py
```

### Package Management
The project uses `pyproject.toml` for dependency management with uv.

#### Adding Dependencies
```bash
# Add a new dependency
uv add package-name

# Add a development dependency
uv add --dev package-name

# Add with version constraints
uv add "package-name>=1.0.0"
```

#### Installing Dependencies
```bash
# Install all dependencies (creates virtual environment automatically)
uv sync

# Install in development mode
uv sync --dev
```

#### Running Python Scripts
scripts are always run from main directory (it is important in scope of relative imports)
```bash
# Run any Python script through uv
uv run python script.py

# Run main.py
uv run main.py

# Execute Python commands
uv run python -c "print('Hello World')"
```

#### Virtual Environment Management
uv automatically manages virtual environments, but you can also:
```bash
# Activate the virtual environment
source .venv/bin/activate

# Or run commands in the virtual environment
uv run <command>
```
#### environmental variables

if env variables necessary add this:
```
from dotenv import load_dotenv
load_dotenv()
```
currently in env file there is:
OPENAI_API_KEY=...
OPENAI_MODEL=...
MIN_CONFIDENCE=...
SOURCES_DIR=...
OUTPUT_FILE=...
VERBOSE=...


## Python Environment

- Target Python version: 3.10 (specified in `.python-version`)
- The project expects Python >=3.10 as specified in `pyproject.toml`
- uv will automatically create and manage the virtual environment in `.venv/`

## Architecture Notes

- This is a minimal Python project without any frameworks or libraries
- No testing framework is currently configured
- No linting or formatting tools are set up
- The project structure suggests it may be intended for GraphRAG (Graph Retrieval-Augmented Generation) functionality based on the name, but no such implementation exists yet
- Use `uv` for all Python package management and script execution


## reading instructions
if you hwave file ipynb, read them with python json