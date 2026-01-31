#!/usr/bin/env python3
"""
Test script to verify the investment tracker functionality.
"""

from pathlib import Path
from src.models import Investment, Timeframe
from src.storage import InvestmentStorage


def test_models():
    """Test the investment models."""
    print("Testing investment models...")
    
    # Test creating a new investment
    investment = Investment.create_new(
        name="Test Stock",
        timeframe="1M",
        final_amount=1050.0,
        percentage_change=5.0
    )
    
    print(f"Created investment: {investment.name}")
    print(f"Original amount: {investment.formatted_original_amount}")
    print(f"Final amount: {investment.formatted_final_amount}")
    print(f"Profit/Loss: {investment.formatted_profit_loss}")
    print(f"Percentage: {investment.formatted_percentage}")
    print("Model test passed\n")


def test_storage():
    """Test the storage functionality."""
    print("Testing storage functionality...")
    
    # Create test data directory
    data_dir = Path("test_data")
    storage = InvestmentStorage(data_dir)
    
    # Create test investment
    investment = Investment.create_new(
        name="Test Investment",
        timeframe="3M",
        final_amount=1200.0,
        percentage_change=20.0
    )
    
    # Save investment
    storage.save_investments([investment])
    print("Investment saved")
    
    # Load investments
    loaded_investments = storage.load_investments()
    print(f"Loaded {len(loaded_investments)} investment(s)")
    
    if loaded_investments:
        inv = loaded_investments[0]
        print(f"Loaded investment: {inv.name}")
    
    # Clean up
    if data_dir.exists():
        import shutil
        shutil.rmtree(data_dir)
    
    print("Storage test passed\n")


def test_calculations():
    """Test investment calculations."""
    print("Testing calculations...")
    
    # Test profit
    inv_profit = Investment.create_new(
        name="Profit Test",
        timeframe="1M", 
        final_amount=1100.0,
        percentage_change=10.0
    )
    assert abs(inv_profit.original_amount - 1000.0) < 0.01
    assert abs(inv_profit.profit_loss_amount - 100.0) < 0.01
    print("Profit calculation correct")
    
    # Test loss
    inv_loss = Investment.create_new(
        name="Loss Test",
        timeframe="6M",
        final_amount=900.0,
        percentage_change=-10.0
    )
    assert abs(inv_loss.original_amount - 1000.0) < 0.01
    assert abs(inv_loss.profit_loss_amount + 100.0) < 0.01
    print("Loss calculation correct")
    
    print("Calculation test passed\n")


def main():
    """Run all tests."""
    print("Running Investment Tracker Tests\n")
    print("=" * 40)
    
    try:
        test_models()
        test_storage()
        test_calculations()
        
        print("=" * 40)
        print("All tests passed! The app should work correctly.")
        
    except Exception as e:
        print(f"Test failed: {e}")
        raise


if __name__ == "__main__":
    main()