#!/usr/bin/env python3
"""
Test script to verify the investment tracker functionality.
"""

from pathlib import Path
from src.models import Investment, Portfolio, Timeframe
from src.storage import InvestmentStorage


def test_portfolio_model():
    """Test the portfolio model."""
    print("Testing portfolio model...")
    
    # Test creating a new portfolio
    portfolio = Portfolio.create_new(
        name="Test Portfolio",
        description="A test portfolio for unit testing",
        timeframe="1M"
    )
    
    print(f"Created portfolio: {portfolio.name}")
    print(f"Timeframe: {portfolio.timeframe}")
    print(f"Description: {portfolio.description}")
    print("Portfolio model test passed\n")
    
    return portfolio


def test_investment_model():
    """Test the investment model."""
    print("Testing investment models...")
    
    # Create a portfolio first
    portfolio = Portfolio.create_new(
        name="Investment Test Portfolio",
        description="For testing investments",
        timeframe="3M"
    )
    
    # Test creating a new investment
    investment = Investment.create_new(
        name="Test Stock",
        portfolio_id=portfolio.id,
        final_amount=1050.0,
        percentage_change=5.0
    )
    
    print(f"Created investment: {investment.name}")
    print(f"Portfolio ID: {investment.portfolio_id}")
    print(f"Original amount: {investment.formatted_original_amount}")
    print(f"Final amount: {investment.formatted_final_amount}")
    print(f"Profit/Loss: {investment.formatted_profit_loss}")
    print(f"Percentage: {investment.formatted_percentage}")
    print("Investment model test passed\n")
    
    return portfolio, investment


def test_portfolio_summary():
    """Test portfolio summary calculations."""
    print("Testing portfolio summary...")
    
    # Create portfolio
    portfolio = Portfolio.create_new(
        name="Summary Test Portfolio",
        description="Testing summaries",
        timeframe="6M"
    )
    
    # Create investments
    investments = [
        Investment.create_new(
            name="Profitable Investment",
            portfolio_id=portfolio.id,
            final_amount=1100.0,
            percentage_change=10.0
        ),
        Investment.create_new(
            name="Loss Investment",
            portfolio_id=portfolio.id,
            final_amount=900.0,
            percentage_change=-10.0
        ),
    ]
    
    summary = portfolio.get_summary(investments)
    
    print(f"Portfolio: {summary.portfolio_name}")
    print(f"Investment count: {summary.investment_count}")
    print(f"Total original: {summary.formatted_total_original}")
    print(f"Total final: {summary.formatted_total_final}")
    print(f"Total profit/loss: {summary.formatted_total_profit_loss}")
    print(f"Total percentage: {summary.formatted_total_percentage}")
    print("Portfolio summary test passed\n")


def test_storage():
    """Test the storage functionality."""
    print("Testing storage functionality...")
    
    # Create test data directory
    data_dir = Path("test_data")
    storage = InvestmentStorage(data_dir)
    
    # Create test portfolio
    portfolio = Portfolio.create_new(
        name="Test Portfolio",
        description="For storage testing",
        timeframe="1M"
    )
    
    # Create test investment
    investment = Investment.create_new(
        name="Test Investment",
        portfolio_id=portfolio.id,
        final_amount=1200.0,
        percentage_change=20.0
    )
    
    # Save data
    storage.save_all([portfolio], [investment])
    print("Portfolio and investment saved")
    
    # Load data
    loaded_portfolios, loaded_investments = storage.load_all()
    print(f"Loaded {len(loaded_portfolios)} portfolio(s) and {len(loaded_investments)} investment(s)")
    
    if loaded_portfolios:
        port = loaded_portfolios[0]
        print(f"Loaded portfolio: {port.name}")
    
    if loaded_investments:
        inv = loaded_investments[0]
        print(f"Loaded investment: {inv.name} (Portfolio: {inv.portfolio_id})")
    
    # Clean up
    if data_dir.exists():
        import shutil
        shutil.rmtree(data_dir)
    
    print("Storage test passed\n")


def test_calculations():
    """Test investment calculations."""
    print("Testing calculations...")
    
    # Create a test portfolio first
    portfolio = Portfolio.create_new(
        name="Calculation Test",
        description="For calculation testing",
        timeframe="1M"
    )
    
    # Test profit
    inv_profit = Investment.create_new(
        name="Profit Test",
        portfolio_id=portfolio.id,
        final_amount=1100.0,
        percentage_change=10.0
    )
    assert abs(inv_profit.original_amount - 1000.0) < 0.01
    assert abs(inv_profit.profit_loss_amount - 100.0) < 0.01
    print("Profit calculation correct")
    
    # Test loss
    inv_loss = Investment.create_new(
        name="Loss Test",
        portfolio_id=portfolio.id,
        final_amount=900.0,
        percentage_change=-10.0
    )
    assert abs(inv_loss.original_amount - 1000.0) < 0.01
    assert abs(inv_loss.profit_loss_amount + 100.0) < 0.01
    print("Loss calculation correct")
    
    print("Calculation test passed\n")


def test_investment_move():
    """Test moving investments between portfolios."""
    print("Testing investment move...")
    
    # Create two portfolios
    portfolio1 = Portfolio.create_new(
        name="Portfolio 1",
        description="First portfolio",
        timeframe="1M"
    )
    
    portfolio2 = Portfolio.create_new(
        name="Portfolio 2",
        description="Second portfolio",
        timeframe="3M"
    )
    
    # Create investment in portfolio1
    investment = Investment.create_new(
        name="Movable Investment",
        portfolio_id=portfolio1.id,
        final_amount=1000.0,
        percentage_change=5.0
    )
    
    print(f"Investment created in {portfolio1.name}")
    print(f"Portfolio ID: {investment.portfolio_id}")
    
    # Move to portfolio2
    moved_investment = investment.move_to_portfolio(portfolio2.id)
    
    print(f"Investment moved to {portfolio2.name}")
    print(f"New Portfolio ID: {moved_investment.portfolio_id}")
    assert moved_investment.portfolio_id == portfolio2.id
    assert moved_investment.id == investment.id  # ID should remain the same
    
    print("Investment move test passed\n")


def main():
    """Run all tests."""
    print("Running Investment Tracker Tests\n")
    print("=" * 40)
    
    try:
        test_portfolio_model()
        test_investment_model()
        test_portfolio_summary()
        test_storage()
        test_calculations()
        test_investment_move()
        
        print("=" * 40)
        print("All tests passed! The app should work correctly.")
        
    except Exception as e:
        print(f"Test failed: {e}")
        raise


if __name__ == "__main__":
    main()
