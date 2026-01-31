#!/usr/bin/env python3
"""
Investment Tracker - A TUI application for tracking investments.

Run this script to start the investment tracker application.
"""

from pathlib import Path

from src.app import InvestmentTrackerApp


def main():
    """Main entry point for the investment tracker application."""
    # Set up the data directory relative to the script location
    script_dir = Path(__file__).parent
    data_dir = script_dir / "data"
    
    # Create and run the application
    app = InvestmentTrackerApp(storage_path=data_dir)
    app.run()


if __name__ == "__main__":
    main()