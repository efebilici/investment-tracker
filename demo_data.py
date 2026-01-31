#!/usr/bin/env python3
"""
Demo script to populate the investment tracker with sample data.
"""

from pathlib import Path
from src.models import Investment, Portfolio
from src.storage import InvestmentStorage


def create_sample_data():
    """Create sample portfolio and investment data for demonstration."""
    
    # Create sample portfolios
    portfolios = [
        Portfolio.create_new(
            name="Short Term Growth",
            description="High growth potential investments for 1 month",
            timeframe="1M"
        ),
        Portfolio.create_new(
            name="Quarterly Balanced",
            description="Balanced risk/reward investments for 3 months",
            timeframe="3M"
        ),
        Portfolio.create_new(
            name="Medium Term Value",
            description="Value-based investments for 6 months",
            timeframe="6M"
        ),
        Portfolio.create_new(
            name="Long Term Holdings",
            description="Long-term strategic investments for 1 year",
            timeframe="1Y"
        ),
    ]
    
    # Build a lookup for portfolio IDs by timeframe
    portfolio_by_timeframe = {p.timeframe: p for p in portfolios}
    
    # Sample investments distributed across portfolios
    sample_investments = [
        # 1M Portfolio investments
        Investment.create_new(
            name="Tech Stock Portfolio",
            portfolio_id=portfolio_by_timeframe["1M"].id,
            final_amount=105000.0,
            percentage_change=5.0
        ),
        Investment.create_new(
            name="Index Fund",
            portfolio_id=portfolio_by_timeframe["1M"].id,
            final_amount=102500.0,
            percentage_change=2.5
        ),
        
        # 3M Portfolio investments
        Investment.create_new(
            name="Bond Investment",
            portfolio_id=portfolio_by_timeframe["3M"].id,
            final_amount=101500.0,
            percentage_change=1.5
        ),
        Investment.create_new(
            name="Commodities",
            portfolio_id=portfolio_by_timeframe["3M"].id,
            final_amount=88000.0,
            percentage_change=-12.0
        ),
        
        # 6M Portfolio investments
        Investment.create_new(
            name="Crypto Assets",
            portfolio_id=portfolio_by_timeframe["6M"].id,
            final_amount=145000.0,
            percentage_change=45.0
        ),
        Investment.create_new(
            name="Small Cap Stocks",
            portfolio_id=portfolio_by_timeframe["6M"].id,
            final_amount=132000.0,
            percentage_change=32.0
        ),
        
        # 1Y Portfolio investments
        Investment.create_new(
            name="Real Estate Fund",
            portfolio_id=portfolio_by_timeframe["1Y"].id,
            final_amount=98000.0,
            percentage_change=-2.0
        ),
        Investment.create_new(
            name="International Markets",
            portfolio_id=portfolio_by_timeframe["1Y"].id,
            final_amount=112000.0,
            percentage_change=12.0
        ),
    ]
    
    return portfolios, sample_investments


def main():
    """Populate the investment tracker with sample data."""
    print("Creating sample portfolio and investment data...")
    
    # Setup storage
    data_dir = Path("data")
    storage = InvestmentStorage(data_dir)
    
    # Create sample data
    portfolios, investments = create_sample_data()
    
    # Save to storage
    storage.save_all(portfolios, investments)
    
    print(f"Created {len(portfolios)} portfolios with {len(investments)} investments:")
    print()
    
    for portfolio in portfolios:
        print(f"[PORTFOLIO] {portfolio.name} ({portfolio.timeframe})")
        if portfolio.description:
            print(f"   {portfolio.description}")
        
        # Show investments in this portfolio
        portfolio_investments = [inv for inv in investments if inv.portfolio_id == portfolio.id]
        for inv in portfolio_investments:
            profit_indicator = "[PROFIT]" if inv.is_profit else "[LOSS]"
            print(f"   {profit_indicator} {inv.name}")
            print(f"      Original: {inv.formatted_original_amount}")
            print(f"      Current:  {inv.formatted_final_amount}")
            print(f"      Return:   {inv.formatted_profit_loss} ({inv.formatted_percentage})")
        
        # Show portfolio summary
        summary = portfolio.get_summary(investments)
        print(f"   [SUMMARY] Portfolio Total: {summary.formatted_total_final} ({summary.formatted_total_percentage})")
        print()
    
    # Show grand summary
    from src.models import GrandSummary
    grand_summary = GrandSummary.from_portfolios(portfolios, investments)
    print("=" * 50)
    print(f"GRAND TOTAL: {grand_summary.formatted_total_final}")
    print(f"Overall Return: {grand_summary.formatted_total_profit_loss} ({grand_summary.formatted_total_percentage})")
    print("=" * 50)
    print()
    
    print("Sample data created successfully!")
    print("Run 'uv run python main.py' to start the investment tracker.")


if __name__ == "__main__":
    main()
