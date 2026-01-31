import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Optional


Timeframe = Literal["1M", "3M", "6M", "1Y"]


@dataclass
class Investment:
    """Represents a single investment with calculated properties."""
    id: str
    name: str
    timeframe: Timeframe
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
            "timeframe": self.timeframe,
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
            timeframe=data["timeframe"],
            final_amount=data["final_amount"],
            percentage_change=data["percentage_change"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )

    @classmethod
    def create_new(cls, name: str, timeframe: Timeframe, final_amount: float, percentage_change: float) -> "Investment":
        """Create a new investment with generated ID and timestamps."""
        now = datetime.now()
        return cls(
            id=str(uuid.uuid4()),
            name=name,
            timeframe=timeframe,
            final_amount=final_amount,
            percentage_change=percentage_change,
            created_at=now,
            updated_at=now,
        )

    def update(self, name: Optional[str] = None, timeframe: Optional[Timeframe] = None, final_amount: Optional[float] = None, percentage_change: Optional[float] = None) -> "Investment":
        """Create an updated copy of the investment."""
        return Investment(
            id=self.id,
            name=name if name is not None else self.name,
            timeframe=timeframe if timeframe is not None else self.timeframe,
            final_amount=final_amount if final_amount is not None else self.final_amount,
            percentage_change=percentage_change if percentage_change is not None else self.percentage_change,
            created_at=self.created_at,
            updated_at=datetime.now(),
        )


@dataclass
class PortfolioSummary:
    """Summary statistics for a portfolio of investments."""
    timeframe: Timeframe
    total_original: float
    total_final: float
    total_profit_loss: float
    total_percentage: float
    investment_count: int

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