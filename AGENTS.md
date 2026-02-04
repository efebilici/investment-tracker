# AGENTS.md - Investment Tracker TUI

## Project Overview
A terminal-based portfolio management application built with Python 3.12 and Textual framework.

## Build/Lint/Test Commands

### Running the Application
```bash
# Using UV (recommended)
uv run python main.py

# Alternative with pip
python main.py
```

### Running Tests
```bash
# Run all tests
uv run python test_app.py

# Run a single test function
uv run python -c "from test_app import test_portfolio_model; test_portfolio_model()"

# Alternative without UV
python test_app.py
```

### Package Management
```bash
# Sync dependencies (install from pyproject.toml)
uv sync

# Add new dependency
uv add <package-name>

# Install from requirements.txt
uv pip install -r requirements.txt
```

### Linting/Formatting (Manual)
This project doesn't have linting configured. If adding linting:
```bash
# Suggested commands for manual use
ruff check .
black .
mypy src/
```

## Code Style Guidelines

### Imports
- Standard library imports first
- Third-party imports second
- Local imports last (use `from .module` for relative imports)
- Group imports with blank lines between sections
- Use type hint imports from `typing` module

Example:
```python
import json
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import List, Literal, Optional

from textual.app import App
from textual.widgets import Button

from .models import Investment, Portfolio
```

### Formatting
- Use 4 spaces for indentation
- Maximum line length: 88-100 characters (follow existing patterns)
- Use double quotes for strings
- Add trailing commas in multi-line collections

### Types
- Use type hints for all function parameters and return types
- Use `Optional[X]` instead of `X | None` for broader compatibility
- Use `List[X]` instead of `list[X]` (Python 3.8+ compatibility)
- Define custom type aliases at module level (e.g., `Timeframe = Literal["1M", "3M", "6M", "1Y"]`)

### Naming Conventions
- Classes: PascalCase (e.g., `InvestmentTrackerApp`)
- Functions/methods: snake_case (e.g., `get_selected_portfolio`)
- Variables: snake_case (e.g., `portfolio_id`)
- Constants: UPPER_SNAKE_CASE at module level
- Private methods: prefix with underscore (e.g., `_save_data`)

### Error Handling
- Use specific exceptions, avoid bare `except:`
- Use `__post_init__` in dataclasses for validation
- Return meaningful error messages for user-facing errors
- Use assertions only in tests, not production code

### Architecture Patterns
- Use dataclasses for data models with `to_dict()` and `from_dict()` methods
- Use immutable updates: create new objects instead of modifying (e.g., `portfolio.update(...)`)
- Separate UI (widgets.py, app.py) from business logic (models.py)
- Use Textual's reactive attributes for state management

### Documentation
- Add docstrings to all classes and public methods
- Use Google-style docstrings
- Keep comments minimal; code should be self-documenting

### Testing
- Tests are in `test_app.py` as simple Python functions
- No pytest configured; tests run directly
- Test functions should print status and return test data
- Use assertions for critical validations

## Project Structure
```
src/
  __init__.py      - Package init
  app.py           - Main TUI application (Textual App)
  models.py        - Data models (Portfolio, Investment, etc.)
  storage.py       - JSON persistence and backup logic
  widgets.py       - UI components and dialogs
main.py            - Application entry point
test_app.py        - Test suite
data/              - Data storage (gitignored)
  investments.json - Main data file
  backups/         - Automatic backups
pyproject.toml     - UV project config
requirements.txt   - Pip dependencies
```

## Key Technologies
- Python 3.12+
- Textual (TUI framework)
- UV (package manager)
- Dataclasses for models
- JSON for persistence

## Notes for Agents
- Always use relative imports for local modules: `from .models import ...`
- Follow the immutable update pattern for model changes
- Use the `create_new()` factory methods for creating new entities
- Textual uses CSS-in-Python for styling (see app.py CSS strings)
- Data validation happens in `__post_init__` methods
- Storage handles migration from v1.0 to v2.0 data format automatically
