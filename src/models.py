import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import List, Literal, Optional


Timeframe = Literal["1M", "3M", "6M", "1Y"]


@dataclass
class Portfolio:
    """Represents an investment portfolio containing multiple investments."""
    id: str
    name: str
    description: str
    timeframe: Timeframe
    created_at: datetime

    def __post_init__(self):
        """Validate portfolio data after initialization."""
        if not self.name.strip():
            raise ValueError("Portfolio name cannot be empty")
        if self.timeframe not in ("1M", "3M", "6M", "1Y"):
            raise ValueError("Invalid timeframe")

    def to_dict(self) -> dict:
        """Convert portfolio to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "timeframe": self.timeframe,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Portfolio":
        """Create portfolio from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            timeframe=data["timeframe"],
            created_at=datetime.fromisoformat(data["created_at"]),
        )

    @classmethod
    def create_new(cls, name: str, description: str, timeframe: Timeframe) -> "Portfolio":
        """Create a new portfolio with generated ID and timestamp."""
        now = datetime.now()
        return cls(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            timeframe=timeframe,
            created_at=now,
        )

    def update(self, name: Optional[str] = None, description: Optional[str] = None, timeframe: Optional[Timeframe] = None) -> "Portfolio":
        """Create an updated copy of the portfolio."""
        return Portfolio(
            id=self.id,
            name=name if name is not None else self.name,
            description=description if description is not None else self.description,
            timeframe=timeframe if timeframe is not None else self.timeframe,
            created_at=self.created_at,
        )

    def get_summary(self, investments: List["Investment"]) -> "PortfolioSummary":
        """Calculate summary statistics for this portfolio based on its investments."""
        portfolio_investments = [inv for inv in investments if inv.portfolio_id == self.id]
        
        if not portfolio_investments:
            return PortfolioSummary(
                portfolio_id=self.id,
                portfolio_name=self.name,
                timeframe=self.timeframe,
                total_original=0.0,
                total_final=0.0,
                total_profit_loss=0.0,
                total_percentage=0.0,
                investment_count=0,
            )
        
        total_original = sum(inv.original_amount for inv in portfolio_investments)
        total_final = sum(inv.final_amount for inv in portfolio_investments)
        total_profit_loss = total_final - total_original
        total_percentage = (total_profit_loss / total_original * 100) if total_original > 0 else 0.0
        
        return PortfolioSummary(
            portfolio_id=self.id,
            portfolio_name=self.name,
            timeframe=self.timeframe,
            total_original=total_original,
            total_final=total_final,
            total_profit_loss=total_profit_loss,
            total_percentage=total_percentage,
            investment_count=len(portfolio_investments),
        )


@dataclass
class Investment:
    """Represents a single investment belonging to a portfolio."""
    id: str
    name: str
    portfolio_id: str
    final_amount: float
    percentage_change: float
    created_at: datetime
    updated_at: datetime
    
    # External data fields for real-world data integration
    symbol: Optional[str] = None  # Ticker/symbol for API lookup (e.g., "AAPL", "YAC")
    data_source: Optional[str] = None  # "manual", "tefas", "investiny"
    asset_type: Optional[str] = None  # "stock", "etf", "fund", "crypto", "bond", "commodity"
    currency: str = "USD"  # Investment currency (default USD)
    last_price_update: Optional[datetime] = None  # When price was last fetched
    original_symbol: Optional[str] = None  # Original search symbol for tracking

    def __post_init__(self):
        """Validate investment data after initialization."""
        if self.final_amount <= 0:
            raise ValueError("Final amount must be positive")
        if self.percentage_change < -100:
            raise ValueError("Percentage change cannot be less than -100%")
        if not self.name.strip():
            raise ValueError("Investment name cannot be empty")
        if not self.portfolio_id.strip():
            raise ValueError("Portfolio ID cannot be empty")
        if self.data_source and self.data_source not in ("manual", "tefas", "investiny"):
            raise ValueError("Invalid data source. Must be 'manual', 'tefas', or 'investiny'")

    @property
    def original_amount(self) -> float:
        """Calculate the original investment amount."""
        return self.final_amount / (1 + self.percentage_change / 100)

    @property
    def profit_loss_amount(self) -> float:
        """Calculate the profit/loss amount."""
        return self.final_amount - self.original_amount

    @property
    def is_profit(self) -> bool:
        """Check if investment is profitable."""
        return self.percentage_change > 0

    @property
    def formatted_final_amount(self) -> str:
        """Format final amount for display."""
        return f"{self.final_amount:,.2f}"

    @property
    def formatted_original_amount(self) -> str:
        """Format original amount for display."""
        return f"{self.original_amount:,.2f}"

    @property
    def formatted_profit_loss(self) -> str:
        """Format profit/loss for display."""
        return f"{self.profit_loss_amount:+,.2f}"

    @property
    def formatted_percentage(self) -> str:
        """Format percentage change for display."""
        return f"{self.percentage_change:+.2f}%"

    def to_dict(self) -> dict:
        """Convert investment to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "portfolio_id": self.portfolio_id,
            "final_amount": self.final_amount,
            "percentage_change": self.percentage_change,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            # External data fields
            "symbol": self.symbol,
            "data_source": self.data_source,
            "asset_type": self.asset_type,
            "currency": self.currency,
            "last_price_update": self.last_price_update.isoformat() if self.last_price_update else None,
            "original_symbol": self.original_symbol,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Investment":
        """Create investment from dictionary."""
        # Parse optional datetime fields
        last_price_update = None
        if data.get("last_price_update"):
            last_price_update = datetime.fromisoformat(data["last_price_update"])
        
        return cls(
            id=data["id"],
            name=data["name"],
            portfolio_id=data["portfolio_id"],
            final_amount=data["final_amount"],
            percentage_change=data["percentage_change"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            # External data fields with defaults for backward compatibility
            symbol=data.get("symbol"),
            data_source=data.get("data_source"),
            asset_type=data.get("asset_type"),
            currency=data.get("currency", "USD"),
            last_price_update=last_price_update,
            original_symbol=data.get("original_symbol"),
        )

    @classmethod
    def create_new(
        cls, 
        name: str, 
        portfolio_id: str, 
        final_amount: float, 
        percentage_change: float,
        symbol: Optional[str] = None,
        data_source: Optional[str] = "manual",
        asset_type: Optional[str] = None,
        currency: str = "USD",
        original_symbol: Optional[str] = None,
    ) -> "Investment":
        """Create a new investment with generated ID and timestamps."""
        now = datetime.now()
        return cls(
            id=str(uuid.uuid4()),
            name=name,
            portfolio_id=portfolio_id,
            final_amount=final_amount,
            percentage_change=percentage_change,
            created_at=now,
            updated_at=now,
            symbol=symbol,
            data_source=data_source,
            asset_type=asset_type,
            currency=currency,
            last_price_update=None,
            original_symbol=original_symbol or symbol,
        )

    def update(
        self, 
        name: Optional[str] = None, 
        final_amount: Optional[float] = None, 
        percentage_change: Optional[float] = None,
        symbol: Optional[str] = None,
        data_source: Optional[str] = None,
        asset_type: Optional[str] = None,
        currency: Optional[str] = None,
        last_price_update: Optional[datetime] = None,
        original_symbol: Optional[str] = None,
    ) -> "Investment":
        """Create an updated copy of the investment."""
        return Investment(
            id=self.id,
            name=name if name is not None else self.name,
            portfolio_id=self.portfolio_id,
            final_amount=final_amount if final_amount is not None else self.final_amount,
            percentage_change=percentage_change if percentage_change is not None else self.percentage_change,
            created_at=self.created_at,
            updated_at=datetime.now(),
            symbol=symbol if symbol is not None else self.symbol,
            data_source=data_source if data_source is not None else self.data_source,
            asset_type=asset_type if asset_type is not None else self.asset_type,
            currency=currency if currency is not None else self.currency,
            last_price_update=last_price_update if last_price_update is not None else self.last_price_update,
            original_symbol=original_symbol if original_symbol is not None else self.original_symbol,
        )

    def move_to_portfolio(self, new_portfolio_id: str) -> "Investment":
        """Create a copy of this investment assigned to a different portfolio."""
        return Investment(
            id=self.id,
            name=self.name,
            portfolio_id=new_portfolio_id,
            final_amount=self.final_amount,
            percentage_change=self.percentage_change,
            created_at=self.created_at,
            updated_at=datetime.now(),
            symbol=self.symbol,
            data_source=self.data_source,
            asset_type=self.asset_type,
            currency=self.currency,
            last_price_update=self.last_price_update,
            original_symbol=self.original_symbol,
        )

    def update_price(self, new_price: float, new_currency: Optional[str] = None) -> "Investment":
        """Update the investment price and recalculate percentage change.
        
        Args:
            new_price: The new current price/value
            new_currency: Optional currency code if changed
            
        Returns:
            Updated Investment instance
        """
        original = self.original_amount
        if original <= 0:
            # Can't calculate percentage without valid original amount
            new_percentage = 0.0
        else:
            new_percentage = ((new_price - original) / original) * 100
        
        return self.update(
            final_amount=new_price,
            percentage_change=new_percentage,
            currency=new_currency if new_currency else self.currency,
            last_price_update=datetime.now(),
        )

    def needs_price_update(self, max_age_hours: int = 24) -> bool:
        """Check if price data is stale and needs refreshing.
        
        Args:
            max_age_hours: Maximum acceptable age of price data
            
        Returns:
            True if price data is stale or unavailable
        """
        # Manual investments never need auto-update
        if self.data_source == "manual" or not self.data_source:
            return False
        
        if not self.last_price_update:
            return True
        
        age = datetime.now() - self.last_price_update
        return age.total_seconds() > (max_age_hours * 3600)

    def get_price_age_hours(self) -> Optional[float]:
        """Get age of last price update in hours.
        
        Returns:
            Hours since last update, or None if never updated
        """
        if not self.last_price_update:
            return None
        age = datetime.now() - self.last_price_update
        return age.total_seconds() / 3600

    def get_data_source_icon(self) -> str:
        """Get an emoji icon representing the data source.
        
        Returns:
            Emoji string for the data source
        """
        icons = {
            "tefas": "🇹🇷",
            "investiny": "🌍",
            "manual": "✋",
            None: "✋",
        }
        return icons.get(self.data_source, "✋")

    def get_price_freshness_indicator(self) -> str:
        """Get an emoji indicating price freshness.
        
        Returns:
            🟢 Fresh (< 24h), 🟡 Moderate (< 7 days), 🔴 Stale (> 7 days), or ⚪ Manual
        """
        if self.data_source == "manual" or not self.data_source:
            return "⚪"
        
        age_hours = self.get_price_age_hours()
        if age_hours is None:
            return "⚪"
        
        if age_hours < 24:
            return "🟢"
        elif age_hours < 168:  # 7 days
            return "🟡"
        else:
            return "🔴"

    @property
    def formatted_currency(self) -> str:
        """Format currency for display."""
        return self.currency or "USD"

    @property
    def formatted_price_with_currency(self) -> str:
        """Format final amount with currency symbol."""
        return f"{self.formatted_final_amount} {self.formatted_currency}"


@dataclass
class PortfolioSummary:
    """Summary statistics for a portfolio."""
    portfolio_id: str
    portfolio_name: str
    timeframe: Timeframe
    total_original: float
    total_final: float
    total_profit_loss: float
    total_percentage: float
    investment_count: int

    @property
    def is_profit(self) -> bool:
        """Check if portfolio is profitable."""
        return self.total_percentage > 0

    @property
    def formatted_total_original(self) -> str:
        return f"{self.total_original:,.2f}"

    @property
    def formatted_total_final(self) -> str:
        return f"{self.total_final:,.2f}"

    @property
    def formatted_total_profit_loss(self) -> str:
        return f"{self.total_profit_loss:+,.2f}"

    @property
    def formatted_total_percentage(self) -> str:
        return f"{self.total_percentage:+.2f}%"


@dataclass
class GrandSummary:
    """Summary statistics across all portfolios."""
    total_original: float
    total_final: float
    total_profit_loss: float
    portfolio_count: int
    total_investment_count: int

    @property
    def total_percentage(self) -> float:
        """Calculate total percentage change."""
        return (self.total_profit_loss / self.total_original * 100) if self.total_original > 0 else 0.0

    @property
    def is_profit(self) -> bool:
        """Check if overall portfolio is profitable."""
        return self.total_percentage > 0

    @property
    def formatted_total_original(self) -> str:
        return f"{self.total_original:,.2f}"

    @property
    def formatted_total_final(self) -> str:
        return f"{self.total_final:,.2f}"

    @property
    def formatted_total_profit_loss(self) -> str:
        return f"{self.total_profit_loss:+,.2f}"

    @property
    def formatted_total_percentage(self) -> str:
        return f"{self.total_percentage:+.2f}%"

    @classmethod
    def from_portfolios(cls, portfolios: List[Portfolio], investments: List[Investment]) -> "GrandSummary":
        """Calculate grand summary from all portfolios and investments."""
        total_original = 0.0
        total_final = 0.0
        
        for portfolio in portfolios:
            summary = portfolio.get_summary(investments)
            total_original += summary.total_original
            total_final += summary.total_final
        
        return cls(
            total_original=total_original,
            total_final=total_final,
            total_profit_loss=total_final - total_original,
            portfolio_count=len(portfolios),
            total_investment_count=len(investments),
        )
