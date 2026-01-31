from datetime import datetime
from pathlib import Path
from typing import Dict, List

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import (
    Button, DataTable, Footer, Header, Label, Static
)

from .models import Investment, PortfolioSummary, Timeframe
from .storage import InvestmentStorage
from .widgets import InvestmentForm, ConfirmationDialog


class InvestmentTable(Container):
    """Custom container for the investment data table."""

    def compose(self) -> ComposeResult:
        """Compose the investment table layout."""
        yield DataTable(id="investment-table")

    def on_mount(self) -> None:
        """Setup the table when mounted."""
        table = self.query_one("#investment-table", DataTable)

        # Add columns
        table.add_columns("Name", "Timeframe", "Final Amount", "% Change", "Original Amount", "Profit/Loss")

        # Configure column widths
        table.cursor_type = "row"
        table.zebra_stripes = True

    def update_investments(self, investments: List[Investment]) -> None:
        """Update the table with investment data."""
        table = self.query_one("#investment-table", DataTable)
        table.clear()

        # Store investments for ID lookup
        self._investments = investments

        for investment in investments:
            # Color code based on profit/loss
            profit_class = "profit" if investment.is_profit else "loss"

            table.add_row(
                investment.name,
                investment.timeframe,
                investment.formatted_final_amount,
                investment.formatted_percentage,
                investment.formatted_original_amount,
                investment.formatted_profit_loss,
                key=investment.id  # Store investment ID as row key
            )

    def get_selected_investment_id(self) -> str | None:
        """Get the ID of the selected investment."""
        table = self.query_one("#investment-table", DataTable)
        if table.cursor_row is not None and hasattr(self, '_investments'):
            cursor_row = table.cursor_row
            if 0 <= cursor_row < len(self._investments):
                return self._investments[cursor_row].id
        return None

    def get_selected_investment(self) -> Investment | None:
        """Get the selected investment object."""
        table = self.query_one("#investment-table", DataTable)
        if table.cursor_row is not None and hasattr(self, '_investments'):
            cursor_row = table.cursor_row
            if 0 <= cursor_row < len(self._investments):
                return self._investments[cursor_row]
        return None


class PortfolioSummaryScreen(Screen):
    """Screen showing portfolio summary statistics."""

    def __init__(self, investments: List[Investment]):
        super().__init__()
        self.investments = investments
        self.summaries = self._calculate_summaries()

    def _calculate_summaries(self) -> Dict[Timeframe, PortfolioSummary]:
        """Calculate portfolio summaries for each timeframe."""
        summaries = {}
        
        for timeframe in Timeframe.__args__:
            timeframe_investments = [inv for inv in self.investments if inv.timeframe == timeframe]
            
            if timeframe_investments:
                total_original = sum(inv.original_amount for inv in timeframe_investments)
                total_final = sum(inv.final_amount for inv in timeframe_investments)
                total_profit_loss = total_final - total_original
                total_percentage = (total_profit_loss / total_original * 100) if total_original > 0 else 0
                
                summaries[timeframe] = PortfolioSummary(
                    timeframe=timeframe,
                    total_original=total_original,
                    total_final=total_final,
                    total_profit_loss=total_profit_loss,
                    total_percentage=total_percentage,
                    investment_count=len(timeframe_investments)
                )
        
        return summaries

    def compose(self) -> ComposeResult:
        """Compose the summary screen layout."""
        yield Header()
        
        with Container(id="summary-container"):
            yield Label("Portfolio Summary", id="summary-title")
            
            with Horizontal(id="summary-content"):
                with Vertical(id="summary-table"):
                    yield Label("Investment Performance by Timeframe")
                    yield Static(self._generate_summary_text(), id="summary-text")
                
                with Vertical(id="overall-stats"):
                    yield Label("Overall Statistics")
                    yield Static(self._generate_overall_text(), id="overall-text")
        
        yield Footer()

    def _generate_summary_text(self) -> str:
        """Generate summary text for each timeframe."""
        if not self.summaries:
            return "No investments found."
        
        lines = ["\n" + "="*50 + "\n"]
        
        for timeframe, summary in self.summaries.items():
            profit_color = "🟢" if summary.total_profit_loss >= 0 else "🔴"
            
            lines.append(f"{profit_color} {timeframe} ({summary.investment_count} investments)")
            lines.append(f"Original:  {summary.formatted_total_original}")
            lines.append(f"Current:   {summary.formatted_total_final}")
            lines.append(f"Return:    {summary.formatted_total_profit_loss}")
            lines.append(f"Rate:      {summary.formatted_total_percentage}")
            lines.append("\n" + "-"*30 + "\n")
        
        return "\n".join(lines)

    def _generate_overall_text(self) -> str:
        """Generate overall portfolio statistics."""
        if not self.investments:
            return "No investments found."
        
        total_original = sum(inv.original_amount for inv in self.investments)
        total_final = sum(inv.final_amount for inv in self.investments)
        total_profit_loss = total_final - total_original
        total_percentage = (total_profit_loss / total_original * 100) if total_original > 0 else 0
        
        profitable_count = sum(1 for inv in self.investments if inv.is_profit)
        loss_count = len(self.investments) - profitable_count
        
        lines = [
            f"\n{'='*30}\n",
            f"Total Investments: {len(self.investments)}",
            f"🟢 Profitable: {profitable_count}",
            f"🔴 Losses: {loss_count}",
            f"\nTotal Original: {total_original:,.2f}",
            f"Total Current:  {total_final:,.2f}",
            f"Total Return:   {total_profit_loss:+,.2f}",
            f"Total Rate:     {total_percentage:+.2f}%\n"
        ]
        
        return "\n".join(lines)


class InvestmentTrackerApp(App):
    """Main investment tracker application."""

    CSS = """
    InvestmentTable {
        height: 1fr;
    }

    DataTable {
        height: 1fr;
    }

    .profit {
        color: $success;
    }

    .loss {
        color: $error;
    }

    #status-bar {
        height: 3;
        background: $panel;
        color: $text;
        padding: 0 1;
    }

    #main-container {
        height: 1fr;
    }
    """

    BINDINGS = [
        Binding("a", "add_investment", "Add Investment"),
        Binding("e", "edit_investment", "Edit Investment"), 
        Binding("d", "delete_investment", "Delete Investment"),
        Binding("s", "show_summary", "Show Summary"),
        Binding("r", "refresh_data", "Refresh"),
        Binding("q", "quit", "Quit"),
    ]

    investments: reactive[List[Investment]] = reactive([])
    selected_investment_index: reactive[int] = reactive(-1)

    def __init__(self, storage_path: Path | None = None):
        super().__init__()
        self.storage = InvestmentStorage(storage_path)
        self.investments = self.storage.load_investments()

    def compose(self) -> ComposeResult:
        """Compose the main application layout."""
        yield Header()
        
        with Container(id="main-container"):
            with Container(id="content-area"):
                yield InvestmentTable()
            
            yield Container(
                Label("", id="status-bar"),
                id="status-container"
            )
        
        yield Footer()

    def on_mount(self) -> None:
        """Initialize the application when mounted."""
        self._update_table()
        self._update_status_bar()

    def _update_table(self) -> None:
        """Update the investment table with current data."""
        investment_table = self.query_one(InvestmentTable)
        investment_table.update_investments(self.investments)

    def _update_status_bar(self) -> None:
        """Update the status bar with current statistics."""
        status_text = self._generate_status_text()
        status_bar = self.query_one("#status-bar", Label)
        status_bar.update(status_text)

    def _generate_status_text(self) -> str:
        """Generate the status bar text."""
        if not self.investments:
            return "No investments. Press 'A' to add your first investment."
        else:
            total_original = sum(inv.original_amount for inv in self.investments)
            total_final = sum(inv.final_amount for inv in self.investments)
            total_profit_loss = total_final - total_original
            
            profit_count = sum(1 for inv in self.investments if inv.is_profit)
            loss_count = len(self.investments) - profit_count
            
            return (
                f"Investments: {len(self.investments)} | "
                f"Total: {total_final:,.2f} | "
                f"Return: {total_profit_loss:+,.2f} | "
                f"🟢 {profit_count} 🔴 {loss_count}"
            )

    def _show_status_message(self, message: str) -> None:
        """Display a temporary message in the status bar."""
        status_bar = self.query_one("#status-bar", Label)
        status_bar.update(message)
        
        # Reset to original status after 3 seconds
        def reset_status():
            status_bar.update(self._generate_status_text())
        
        self.set_timer(3, reset_status)

    def action_add_investment(self) -> None:
        """Show the add investment form."""
        form = InvestmentForm()
        self.push_screen(form, self._handle_investment_form_result)

    def action_edit_investment(self) -> None:
        """Edit the selected investment."""
        investment_table = self.query_one(InvestmentTable)
        investment = investment_table.get_selected_investment()

        if investment:
            form = InvestmentForm(investment)
            self.push_screen(form, self._handle_investment_form_result)
        else:
            self._show_status_message("No investment selected. Use ↑/↓ to select an investment.")

    def action_delete_investment(self) -> None:
        """Delete the selected investment."""
        investment_table = self.query_one(InvestmentTable)
        investment = investment_table.get_selected_investment()

        if investment:
            dialog = ConfirmationDialog(
                "Delete Investment",
                f"Are you sure you want to delete '{investment.name}'?",
                investment_id=investment.id
            )
            self.push_screen(dialog, self._handle_delete_result)
        else:
            self._show_status_message("No investment selected. Use ↑/↓ to select an investment.")

    def action_show_summary(self) -> None:
        """Show the portfolio summary screen."""
        summary_screen = PortfolioSummaryScreen(self.investments)
        self.push_screen(summary_screen)

    def action_refresh_data(self) -> None:
        """Refresh data from storage."""
        self.investments = self.storage.load_investments()
        self._update_table()
        self._update_status_bar()

    def _handle_investment_form_result(self, result) -> None:
        """Handle the result from the investment form."""
        if not result:
            return
        
        action, data = result
        
        if action == "create":
            investment = Investment.create_new(
                name=data["name"],
                timeframe=data["timeframe"],
                final_amount=data["final_amount"],
                percentage_change=data["percentage_change"]
            )
            self.investments.append(investment)
            
        elif action == "update":
            # Find and update the investment
            for i, inv in enumerate(self.investments):
                if inv.id == data["id"]:
                    self.investments[i] = inv.update(
                        name=data["name"],
                        timeframe=data["timeframe"],
                        final_amount=data["final_amount"],
                        percentage_change=data["percentage_change"]
                    )
                    break
        
        elif action == "delete":
            # Delete the investment
            investment_id = data
            for i, inv in enumerate(self.investments):
                if inv.id == investment_id:
                    self.investments.pop(i)
                    break
        
        # Save and update UI
        self.storage.save_investments(self.investments)
        self._update_table()
        self._update_status_bar()

    def _handle_delete_result(self, result) -> None:
        """Handle the result from the delete confirmation dialog."""
        if not result:
            return
        
        confirmed, investment_id = result
        
        if confirmed and investment_id and self.investments:
            # Find and delete the investment with matching ID
            for i, inv in enumerate(self.investments):
                if inv.id == investment_id:
                    self.investments.pop(i)
                    self.storage.save_investments(self.investments)
                    self._update_table()
                    self._update_status_bar()
                    self._show_status_message(f"Investment deleted successfully")
                    break