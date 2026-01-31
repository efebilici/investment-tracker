#!/usr/bin/env python3
"""
Demo script to populate the investment tracker with sample data.
"""

from pathlib import Path
from src.models import Investment, Timeframe
from src.storage import InvestmentStorage


def create_sample_data():
    """Create sample investment data for demonstration."""
    
    # Sample investments across different timeframes
    sample_investments = [
        Investment.create_new(
            name="Tech Stock Portfolio",
            timeframe="1M",
            final_amount=105000.0,
            percentage_change=5.0
        ),
        Investment.create_new(
            name="Bond Investment",
            timeframe="3M",
            final_amount=101500.0,
            percentage_change=1.5
        ),
        Investment.create_new(
            name="Crypto Assets",
            timeframe="6M",
            final_amount=145000.0,
            percentage_change=45.0
        ),
        Investment.create_new(
            name="Real Estate Fund",
            timeframe="1Y",
            final_amount=98000.0,
            percentage_change=-2.0
        ),
        Investment.create_new(
            name="Index Fund",
            timeframe="1M",
            final_amount=102500.0,
            percentage_change=2.5
        ),
        Investment.create_new(
            name="Commodities",
            timeframe="3M",
            final_amount=88000.0,
            percentage_change=-12.0
        ),
        Investment.create_new(
            name="Small Cap Stocks",
            timeframe="6M",
            final_amount=132000.0,
            percentage_change=32.0
        ),
        Investment.create_new(
            name="International Markets",
            timeframe="1Y",
            final_amount=112000.0,
            percentage_change=12.0
        ),
    ]
    
    return sample_investments


def main():
    """Populate the investment tracker with sample data."""
    print("Creating sample investment data...")
    
    # Setup storage
    data_dir = Path("data")
    storage = InvestmentStorage(data_dir)
    
    # Create sample investments
    investments = create_sample_data()
    
    # Save to storage
    storage.save_investments(investments)
    
    print(f"Created {len(investments)} sample investments:")
    print()
    
    for inv in investments:
        profit_indicator = "[PROFIT]" if inv.is_profit else "[LOSS]"
        print(f"{profit_indicator} {inv.name} ({inv.timeframe})")
        print(f"   Original: {inv.formatted_original_amount}")
        print(f"   Current:  {inv.formatted_final_amount}")
        print(f"   Return:   {inv.formatted_profit_loss} ({inv.formatted_percentage})")
        print()
    
    print("Sample data created successfully!")
    print("Run 'uv run python main.py' to start the investment tracker.")


if __name__ == "__main__":
    main()