# Investment Tracker TUI

A terminal-based portfolio management application built with Python 3.12 and Textual.

## Features

- ✨ **Modern TUI Interface**: Clean, intuitive terminal user interface
- 📁 **Portfolio Management**: Organize investments into multiple portfolios (investment packages)
- 💰 **Hierarchical Structure**: Portfolios contain multiple investments with shared timeframe
- 📊 **Investment Tracking**: Track investments across timeframes (1M, 3M, 6M, 1Y)
- 🔄 **Investment Mobility**: Move investments between portfolios easily
- 💾 **Data Persistence**: JSON-based storage (v2.0) with automatic backups
- 📈 **Portfolio Summary**: View performance statistics by portfolio and overall
- 🎨 **Visual Indicators**: Color-coded profits (green) and losses (red)
- 🔄 **Context-Aware Shortcuts**: Smart keyboard shortcuts that adapt to your current view

## Installation

### Prerequisites
- Python 3.12 or higher
- UV package manager (optional)

### Setup

1. Clone or download project:
```bash
git clone https://github.com/efebilici/investment-tracker.git
cd investment-tracker
```

2. Install dependencies with UV:
```bash
uv sync
# OR using pip with UV:
uv pip install -r requirements.txt
```

**Alternative (without UV):**
```bash
pip install -r requirements.txt
```

3. Run application:
```bash
uv run python main.py
```

## Usage

### Getting Started

The app uses a **hierarchical structure**: 
1. **Portfolios** are investment containers (e.g., "Short Term", "Long Term Holdings")
2. Each portfolio has a timeframe (1M, 3M, 6M, 1Y) that applies to all investments within it
3. **Investments** belong to a specific portfolio

### Managing Portfolios

**Main Screen - Portfolio List:**
1. App opens with list of all portfolios
2. First portfolio is automatically selected
3. Use ↑/↓ to navigate between portfolios
4. Press **Enter** to open a portfolio and view its investments

**Creating Portfolios:**
1. Press `F` to create a new portfolio
2. Enter portfolio name, description (optional), and timeframe
3. Portfolio appears in the list

**Editing Portfolios:**
1. Navigate to portfolio with ↑/↓
2. Press `E` to edit name, description, or timeframe
3. Press `D` to delete (only if empty)

### Managing Investments

**Inside a Portfolio:**
1. Press `Enter` to open selected portfolio
2. Portfolio detail screen shows all investments
3. Use ↑/↓ to navigate between investments

**Adding Investments:**
1. Press `A` to add a new investment to current portfolio
2. Enter investment name, final amount, and percentage change
3. Timeframe is automatically inherited from the portfolio

**Editing Investments:**
1. Navigate to investment with ↑/↓
2. Press `E` to edit name, final amount, or percentage change
3. Press `D` to delete the investment

**Moving Investments:**
1. Navigate to investment with ↑/↓
2. Press `M` to move it to a different portfolio
3. Select target portfolio from the list

**Going Back:**
- Press `B` to return to the portfolio list from investment view
- Press `B` to return from summary screen

### Viewing Summary

Press `S` from any screen to see:
- Performance statistics for each portfolio
- Overall grand total across all portfolios
- Investment counts and return rates

## Keyboard Shortcuts

### Main Screen (Portfolio List)

When viewing the list of portfolios:

| Key | Action |
|-----|--------|
| `F` | Add new portfolio |
| `E` | Edit selected portfolio |
| `D` | Delete selected portfolio (must be empty) |
| `Enter` | Enter selected portfolio to view investments |
| `S` | Show portfolio summary |
| `R` | Refresh data from storage |
| `Q` | Quit application |
| `↑/↓` | Navigate between portfolios |

### Inside Portfolio (Investment List)

When viewing investments within a portfolio:

| Key | Action |
|-----|--------|
| `A` | Add new investment to current portfolio |
| `E` | Edit selected investment |
| `D` | Delete selected investment |
| `M` | Move selected investment to different portfolio |
| `B` | Back to portfolio list |
| `S` | Show portfolio summary |
| `R` | Refresh data |
| `Q` | Quit application |
| `↑/↓` | Navigate between investments |

**Note:** `E` and `D` are **context-aware** - they edit/delete whatever is currently selected (portfolio in main screen, investment inside portfolio).

## Data Storage

- **Location**: `data/investments.json`
- **Backup**: Automatic backups created in `data/backups/`
- **Format**: JSON v2.0 with portfolios and investments

### Data Structure (v2.0)

```json
{
  "version": "2.0",
  "last_updated": "2026-01-31T10:30:00Z",
  "portfolios": [
    {
      "id": "uuid-string",
      "name": "Short Term Growth",
      "description": "High growth investments",
      "timeframe": "1M",
      "created_at": "2026-01-31T10:30:00Z"
    }
  ],
  "investments": [
    {
      "id": "uuid-string",
      "name": "Tech Stock Portfolio",
      "portfolio_id": "portfolio-uuid",
      "final_amount": 105000.0,
      "percentage_change": 5.0,
      "created_at": "2026-01-31T10:30:00Z",
      "updated_at": "2026-01-31T10:30:00Z"
    }
  ]
}
```

## Development

### Project Structure

```
investment-tracker/
├── src/
│   ├── __init__.py
│   ├── app.py            # Main application
│   ├── models.py         # Data models (Portfolio, Investment)
│   ├── storage.py        # Data persistence with migration
│   └── widgets.py        # UI components
├── data/
│   ├── investments.json  # Main data file
│   └── backups/         # Backup directory
├── main.py              # Application entry point
├── test_app.py          # Test suite
├── pyproject.toml       # Project configuration (UV)
├── requirements.txt     # Dependencies (pip)
└── README.md           # This file
```

### Running Tests

```bash
uv run python test_app.py
```

### Virtual Environment

The application uses UV for dependency management:

```bash
# Activate virtual environment
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Install new dependencies
uv add <package-name>

# Update dependencies
uv sync
```

## Troubleshooting

### Common Issues

1. **CSS Errors**: If you see CSS parsing errors, the app should still work with default styling
2. **Data Loading**: If data fails to load, check `data/backups/` directory for recent backups
3. **Unicode Issues**: The app uses UTF-8 encoding; ensure your terminal supports it

### Recovery

If your data becomes corrupted:
1. Check `data/backups/` for recent backup files
2. Restore from a backup by copying it to `data/investments.json`
3. Restart the application

## License

This project is open source. See the license file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## Roadmap

- [x] Portfolio management with multiple investment packages
- [ ] Historical performance tracking
- [x] CSV export/import functionality
- [ ] Multiple currency support
- [ ] Investment comparison charts
- [ ] Data synchronization with cloud storage
