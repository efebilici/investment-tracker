# Investment Tracker TUI

A terminal-based investment tracking application built with Python 3.12 and Textual.

## Features

- ✨ **Modern TUI Interface**: Clean, intuitive terminal user interface
- 📊 **Investment Tracking**: Track investments across multiple timeframes (1M, 3M, 6M, 1Y)
- 💰 **Automatic Calculations**: Original amount and profit/loss calculated automatically
- 💾 **Data Persistence**: JSON-based storage with automatic backups
- 📈 **Portfolio Summary**: View performance statistics by timeframe
- 🎨 **Visual Indicators**: Color-coded profits (green) and losses (red)

## Installation

### Prerequisites
- Python 3.11 or higher
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

### Adding Investments

1. Press `A` or click "Add Investment" to open investment form
2. Enter investment details:
   - **Name**: Descriptive name for your investment
   - **Timeframe**: Investment period (1 Month, 3 Months, 6 Months, 1 Year)
   - **Final Amount**: Current value of the investment
   - **% Change**: Profit (+) or loss (-) percentage

The app will automatically calculate:
- Original investment amount
- Absolute profit/loss amount
- Return rate

### Managing Investments

- **Edit**: Press `E` to edit the selected investment
- **Delete**: Press `D` to delete the selected investment
- **Summary**: Press `S` to view portfolio statistics
- **Refresh**: Press `R` to reload data from storage

### Example Investment

For an investment that started at $100,000 and is now worth $105,000 with a 5% profit over 1 month:

- **Final Amount**: `105000`
- **% Change**: `5`
- **Calculated Original Amount**: `100,000.00`
- **Calculated Profit**: `+5,000.00`

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `A` | Add new investment |
| `E` | Edit selected investment |
| `D` | Delete selected investment |
| `S` | Show portfolio summary |
| `R` | Refresh data |
| `Q` | Quit application |
| `↑/↓` | Navigate investments |
| `Enter` | Select/confirm |
| `Esc` | Cancel/exit dialog |

## Data Storage

- **Location**: `data/investments.json`
- **Backup**: Automatic backups created in `data/backups/`
- **Format**: JSON with timestamps and metadata

### Data Structure

```json
{
  "version": "1.0",
  "last_updated": "2025-01-31T10:30:00Z",
  "investments": [
    {
      "id": "uuid-string",
      "name": "Stock Portfolio",
      "timeframe": "1M",
      "final_amount": 105000.0,
      "percentage_change": 5.0,
      "created_at": "2025-01-31T10:30:00Z",
      "updated_at": "2025-01-31T10:30:00Z"
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
│   ├── models.py         # Data models
│   ├── storage.py        # Data persistence
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

- [ ] Investment grouping by category
- [ ] Historical performance tracking
- [ ] CSV export/import functionality
- [ ] Multiple currency support
- [ ] Investment comparison charts
- [ ] Data synchronization with cloud storage