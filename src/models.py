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
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Investment":
        """Create investment from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            portfolio_id=data["portfolio_id"],
            final_amount=data["final_amount"],
            percentage_change=data["percentage_change"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )

    @classmethod
    def create_new(cls, name: str, portfolio_id: str, final_amount: float, percentage_change: float) -> "Investment":
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
        )

    def update(self, name: Optional[str] = None, final_amount: Optional[float] = None, percentage_change: Optional[float] = None) -> "Investment":
        """Create an updated copy of the investment."""
        return Investment(
            id=self.id,
            name=name if name is not None else self.name,
            portfolio_id=self.portfolio_id,
            final_amount=final_amount if final_amount is not None else self.final_amount,
            percentage_change=percentage_change if percentage_change is not None else self.percentage_change,
            created_at=self.created_at,
            updated_at=datetime.now(),
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
        )


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
