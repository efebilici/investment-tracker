from datetime import datetime
from pathlib import Path
from typing import Dict, List

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import (
    Button, DataTable, Header, Label, Static
)

from .models import Investment, Portfolio, PortfolioSummary, GrandSummary
from .storage import InvestmentStorage
from .widgets import (
    InvestmentForm, PortfolioForm, InvestmentMoveDialog, ConfirmationDialog
)


class PortfolioList(Container):
    """Custom container for the portfolio data table."""

    def compose(self) -> ComposeResult:
        """Compose the portfolio table layout."""
        yield DataTable(id="portfolio-table")

    def on_mount(self) -> None:
        """Setup the table when mounted."""
        table = self.query_one("#portfolio-table", DataTable)

        # Add columns
        table.add_columns("Name", "Timeframe", "Investments", "Total Value", "Return %", "Profit/Loss")

        # Configure column widths
        table.cursor_type = "row"
        table.zebra_stripes = True

    def update_portfolios(self, portfolios: List[Portfolio], investments: List[Investment]) -> None:
        """Update the table with portfolio data."""
        table = self.query_one("#portfolio-table", DataTable)
        table.clear()

        # Store portfolios for ID lookup
        self._portfolios = portfolios

        for portfolio in portfolios:
            summary = portfolio.get_summary(investments)
            
            # Color code based on profit/loss
            profit_class = "profit" if summary.is_profit else "loss"

            table.add_row(
                portfolio.name,
                portfolio.timeframe,
                str(summary.investment_count),
                summary.formatted_total_final,
                summary.formatted_total_percentage,
                summary.formatted_total_profit_loss,
                key=portfolio.id
            )

    def get_selected_portfolio(self) -> Portfolio | None:
        """Get the selected portfolio object."""
        table = self.query_one("#portfolio-table", DataTable)
        if table.cursor_row is not None and hasattr(self, '_portfolios'):
            cursor_row = table.cursor_row
            if 0 <= cursor_row < len(self._portfolios):
                return self._portfolios[cursor_row]
        return None


class InvestmentTable(Container):
    """Custom container for the investment data table within a portfolio."""

    def compose(self) -> ComposeResult:
        """Compose the investment table layout."""
        yield DataTable(id="investment-table")

    def on_mount(self) -> None:
        """Setup the table when mounted."""
        table = self.query_one("#investment-table", DataTable)

        # Add columns (no timeframe column as it's at portfolio level)
        table.add_columns("Name", "Final Amount", "% Change", "Original Amount", "Profit/Loss")

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
                investment.formatted_final_amount,
                investment.formatted_percentage,
                investment.formatted_original_amount,
                investment.formatted_profit_loss,
                key=investment.id
            )

    def get_selected_investment(self) -> Investment | None:
        """Get the selected investment object."""
        table = self.query_one("#investment-table", DataTable)
        if table.cursor_row is not None and hasattr(self, '_investments'):
            cursor_row = table.cursor_row
            if 0 <= cursor_row < len(self._investments):
                return self._investments[cursor_row]
        return None


class PortfolioDetailScreen(Screen):
    """Screen showing portfolio details and its investments."""
    
    BINDINGS = [
        Binding("a", "add_investment", "Add Investment"),
        Binding("e", "edit", "Edit Investment"),
        Binding("d", "delete", "Delete Investment"),
        Binding("m", "move_investment", "Move Investment"),
        Binding("b", "app.pop_screen", "Back"),
        Binding("r", "app.refresh_data", "Refresh"),
        Binding("s", "show_summary", "Show Summary"),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self, portfolio: Portfolio, portfolios: List[Portfolio], investments: List[Investment]):
        super().__init__()
        self.portfolio = portfolio
        self.all_portfolios = portfolios
        self.all_investments = investments
        self.portfolio_investments = [inv for inv in investments if inv.portfolio_id == portfolio.id]

    def compose(self) -> ComposeResult:
        """Compose the portfolio detail layout."""
        yield Header()
        
        with Container(id="portfolio-detail-container"):
            # Portfolio header
            with Container(id="portfolio-header"):
                yield Label(f"📁 {self.portfolio.name}", id="portfolio-title")
                if self.portfolio.description:
                    yield Label(self.portfolio.description, id="portfolio-description")
                yield Label(f"Timeframe: {self.portfolio.timeframe}", id="portfolio-timeframe")
            
            # Portfolio summary
            summary = self.portfolio.get_summary(self.all_investments)
            with Container(id="portfolio-summary"):
                yield Label(
                    f"Investments: {summary.investment_count} | "
                    f"Value: {summary.formatted_total_final} | "
                    f"Original: {summary.formatted_total_original} | "
                    f"Return: {summary.formatted_total_profit_loss} ({summary.formatted_total_percentage})",
                    id="portfolio-stats"
                )
            
            # Investment table
            with Container(id="investments-container"):
                yield InvestmentTable()
            
            # Status bar
            yield Container(
                Label("A: Add | E: Edit | D: Delete | M: Move | B: Back | S: Summary", id="detail-status-bar"),
                id="detail-status-container"
            )

    def on_mount(self) -> None:
        """Initialize the screen when mounted."""
        investment_table = self.query_one(InvestmentTable)
        investment_table.update_investments(self.portfolio_investments)

    def action_add_investment(self) -> None:
        """Forward add investment action to app."""
        from typing import cast
        cast(InvestmentTrackerApp, self.app).action_add_investment()

    def action_edit(self) -> None:
        """Forward edit action to app."""
        from typing import cast
        cast(InvestmentTrackerApp, self.app).action_edit_investment()

    def action_delete(self) -> None:
        """Forward delete action to app."""
        from typing import cast
        cast(InvestmentTrackerApp, self.app).action_delete_investment()

    def action_move_investment(self) -> None:
        """Forward move investment action to app."""
        from typing import cast
        cast(InvestmentTrackerApp, self.app).action_move_investment()


class GrandSummaryScreen(Screen):
    """Screen showing grand summary across all portfolios."""
    
    BINDINGS = [
        Binding("b", "app.pop_screen", "Back"),
        Binding("q", "app.quit", "Quit"),
    ]

    def __init__(self, portfolios: List[Portfolio], investments: List[Investment]):
        super().__init__()
        self.portfolios = portfolios
        self.investments = investments
        self.grand_summary = GrandSummary.from_portfolios(portfolios, investments)
        self.portfolio_summaries = {p.id: p.get_summary(investments) for p in portfolios}

    def compose(self) -> ComposeResult:
        """Compose the summary screen layout."""
        yield Header()
        
        with Container(id="summary-container"):
            yield Label("Portfolio Summary", id="summary-title")
            
            with Horizontal(id="summary-content"):
                with Vertical(id="summary-table"):
                    yield Label("Performance by Portfolio")
                    yield Static(self._generate_summary_text(), id="summary-text")
                
                with Vertical(id="overall-stats"):
                    yield Label("Overall Statistics")
                    yield Static(self._generate_overall_text(), id="overall-text")
            
            # Status bar with back instruction
            yield Container(
                Label("B: Back to Portfolios | Q: Quit", id="summary-status-bar"),
                id="summary-status-container"
            )

    def _generate_summary_text(self) -> str:
        """Generate summary text for each portfolio."""
        if not self.portfolio_summaries:
            return "No portfolios found."
        
        lines = ["\n" + "="*60 + "\n"]
        
        for portfolio in self.portfolios:
            summary = self.portfolio_summaries.get(portfolio.id)
            if summary and summary.investment_count > 0:
                profit_color = "🟢" if summary.is_profit else "🔴"
                
                lines.append(f"{profit_color} {portfolio.name} ({portfolio.timeframe})")
                lines.append(f"   Investments: {summary.investment_count}")
                lines.append(f"   Original:    {summary.formatted_total_original}")
                lines.append(f"   Current:     {summary.formatted_total_final}")
                lines.append(f"   Return:      {summary.formatted_total_profit_loss}")
                lines.append(f"   Rate:        {summary.formatted_total_percentage}")
                lines.append("\n" + "-"*40 + "\n")
        
        return "\n".join(lines)

    def _generate_overall_text(self) -> str:
        """Generate overall portfolio statistics."""
        if not self.investments:
            return "No investments found."
        
        profitable_count = sum(1 for inv in self.investments if inv.is_profit)
        loss_count = len(self.investments) - profitable_count
        
        lines = [
            f"\n{'='*40}\n",
            f"Portfolios: {self.grand_summary.portfolio_count}",
            f"Total Investments: {self.grand_summary.total_investment_count}",
            f"🟢 Profitable: {profitable_count}",
            f"🔴 Losses: {loss_count}",
            f"\nTotal Original: {self.grand_summary.formatted_total_original}",
            f"Total Current:  {self.grand_summary.formatted_total_final}",
            f"Total Return:   {self.grand_summary.formatted_total_profit_loss}",
            f"Total Rate:     {self.grand_summary.formatted_total_percentage}\n"
        ]
        
        return "\n".join(lines)


class InvestmentTrackerApp(App):
    """Main investment tracker application with portfolio support."""

    CSS = """
    PortfolioList, InvestmentTable {
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

    #status-bar, #detail-status-bar, #summary-status-bar {
        height: 3;
        background: $panel;
        color: $text;
        padding: 0 1;
    }

    #main-container, #portfolio-detail-container {
        height: 1fr;
    }

    #portfolio-header {
        height: auto;
        background: $panel;
        padding: 1;
        border: solid $primary;
    }

    #portfolio-title {
        text-style: bold;
        color: $primary;
        text-align: center;
    }

    #portfolio-description {
        text-align: center;
        color: $text-muted;
    }

    #portfolio-timeframe {
        text-align: center;
        color: $accent;
    }

    #portfolio-summary {
        height: auto;
        background: $surface;
        padding: 1;
        border: solid $accent;
    }

    #portfolio-stats {
        text-align: center;
    }

    #investments-container {
        height: 1fr;
    }

    #summary-container {
        height: 1fr;
    }

    #summary-content {
        height: 1fr;
    }

    #summary-status-container {
        height: 3;
    }
    """

    BINDINGS = [
        Binding("f", "add_portfolio", "Add Portfolio"),
        Binding("enter", "enter_portfolio", "Enter Portfolio", priority=True),
        Binding("s", "show_summary", "Show Summary"),
        Binding("r", "refresh_data", "Refresh"),
        Binding("q", "quit", "Quit"),
        # Context-aware edit and delete - work on both portfolios and investments
        Binding("e", "edit", "Edit Selected"),
        Binding("d", "delete", "Delete Selected"),
    ]

    portfolios: reactive[List[Portfolio]] = reactive([])
    investments: reactive[List[Investment]] = reactive([])
    current_portfolio: reactive[Portfolio | None] = reactive(None)

    def __init__(self, storage_path: Path | None = None):
        super().__init__()
        self.storage = InvestmentStorage(storage_path)
        self.portfolios, self.investments = self.storage.load_all()

    def compose(self) -> ComposeResult:
        """Compose the main application layout."""
        yield Header()
        
        with Container(id="main-container"):
            with Container(id="content-area"):
                yield PortfolioList()
            
            yield Container(
                Label("", id="status-bar"),
                id="status-container"
            )

    def on_mount(self) -> None:
        """Initialize the application when mounted."""
        self._update_portfolio_table()
        self._update_status_bar()

    def _update_portfolio_table(self) -> None:
        """Update the portfolio table with current data."""
        portfolio_list = self.query_one(PortfolioList)
        portfolio_list.update_portfolios(self.portfolios, self.investments)
        
        # Auto-select first portfolio if exists
        if self.portfolios:
            table = portfolio_list.query_one("#portfolio-table", DataTable)
            if table.cursor_row is None and table.row_count > 0:
                table.move_cursor(row=0)

    def _update_status_bar(self) -> None:
        """Update the status bar with current statistics."""
        status_text = self._generate_status_text()
        status_bar = self.query_one("#status-bar", Label)
        status_bar.update(status_text)

    def _generate_status_text(self) -> str:
        """Generate the status bar text."""
        if not self.portfolios:
            return "No portfolios. Press 'F' to create your first portfolio. | S: Summary | Q: Quit"
        
        grand_summary = GrandSummary.from_portfolios(self.portfolios, self.investments)
        
        return (
            f"Portfolios: {grand_summary.portfolio_count} | "
            f"Investments: {grand_summary.total_investment_count} | "
            f"Total: {grand_summary.formatted_total_final} | "
            f"Return: {grand_summary.formatted_total_profit_loss} | "
            f"F: Add | E: Edit | D: Delete | Enter: Open | S: Summary | Q: Quit"
        )

    def _show_status_message(self, message: str) -> None:
        """Display a temporary message in the status bar."""
        status_bar = self.query_one("#status-bar", Label)
        status_bar.update(message)
        
        def reset_status():
            status_bar.update(self._generate_status_text())
        
        self.set_timer(3, reset_status)

    def _save_data(self) -> None:
        """Save all data to storage."""
        self.storage.save_all(self.portfolios, self.investments)

    # Context-aware Actions
    def action_edit(self) -> None:
        """Edit the currently selected item (portfolio or investment based on context)."""
        current_screen = self.screen
        
        if isinstance(current_screen, PortfolioDetailScreen):
            # We're inside a portfolio - edit investment
            self.action_edit_investment()
        else:
            # We're on the main screen - edit portfolio
            self.action_edit_portfolio()

    def action_delete(self) -> None:
        """Delete the currently selected item (portfolio or investment based on context)."""
        current_screen = self.screen
        
        if isinstance(current_screen, PortfolioDetailScreen):
            # We're inside a portfolio - delete investment
            self.action_delete_investment()
        else:
            # We're on the main screen - delete portfolio
            self.action_delete_portfolio()

    # Portfolio Actions
    def action_add_portfolio(self) -> None:
        """Show the add portfolio form."""
        form = PortfolioForm()
        self.push_screen(form, self._handle_portfolio_form_result)

    def action_edit_portfolio(self) -> None:
        """Edit the selected portfolio."""
        portfolio_list = self.query_one(PortfolioList)
        portfolio = portfolio_list.get_selected_portfolio()

        if portfolio:
            form = PortfolioForm(portfolio)
            self.push_screen(form, self._handle_portfolio_form_result)
        else:
            self._show_status_message("No portfolio selected. Use ↑/↓ to select a portfolio.")

    def action_delete_portfolio(self) -> None:
        """Delete the selected portfolio."""
        portfolio_list = self.query_one(PortfolioList)
        portfolio = portfolio_list.get_selected_portfolio()

        if portfolio:
            # Check if portfolio has investments
            portfolio_investments = [inv for inv in self.investments if inv.portfolio_id == portfolio.id]
            if portfolio_investments:
                self._show_status_message(f"Cannot delete: portfolio has {len(portfolio_investments)} investments. Move or delete them first.")
                return
            
            dialog = ConfirmationDialog(
                "Delete Portfolio",
                f"Are you sure you want to delete '{portfolio.name}'?",
                item_id=portfolio.id
            )
            self.push_screen(dialog, self._handle_portfolio_delete_result)
        else:
            self._show_status_message("No portfolio selected. Use ↑/↓ to select a portfolio.")

    def action_enter_portfolio(self) -> None:
        """Enter the selected portfolio to view/manage its investments."""
        portfolio_list = self.query_one(PortfolioList)
        portfolio = portfolio_list.get_selected_portfolio()

        if portfolio:
            self.current_portfolio = portfolio
            detail_screen = PortfolioDetailScreen(portfolio, self.portfolios, self.investments)
            self.push_screen(detail_screen)
        else:
            self._show_status_message("No portfolio selected. Use ↑/↓ to select a portfolio.")

    def _handle_portfolio_form_result(self, result) -> None:
        """Handle the result from the portfolio form."""
        if not result:
            return
        
        action, data = result
        
        if action == "create":
            portfolio = Portfolio.create_new(
                name=data["name"],
                description=data["description"],
                timeframe=data["timeframe"]
            )
            self.portfolios.append(portfolio)
            self._show_status_message(f"Portfolio '{portfolio.name}' created successfully")
            
        elif action == "update":
            for i, port in enumerate(self.portfolios):
                if port.id == data["id"]:
                    self.portfolios[i] = port.update(
                        name=data["name"],
                        description=data["description"],
                        timeframe=data["timeframe"]
                    )
                    self._show_status_message(f"Portfolio '{data['name']}' updated successfully")
                    break
        
        elif action == "delete":
            portfolio_id = data
            self.portfolios = [p for p in self.portfolios if p.id != portfolio_id]
            self._show_status_message("Portfolio deleted successfully")
        
        self._save_data()
        self._update_portfolio_table()
        self._update_status_bar()

    def _handle_portfolio_delete_result(self, result) -> None:
        """Handle the result from the portfolio delete confirmation dialog."""
        if not result:
            return
        
        confirmed, portfolio_id = result
        
        if confirmed and portfolio_id:
            self.portfolios = [p for p in self.portfolios if p.id != portfolio_id]
            self._save_data()
            self._update_portfolio_table()
            self._update_status_bar()
            self._show_status_message("Portfolio deleted successfully")

    # Investment Actions (when inside a portfolio)
    def action_add_investment(self) -> None:
        """Show the add investment form (when inside portfolio detail)."""
        if self.current_portfolio:
            form = InvestmentForm(portfolio_id=self.current_portfolio.id)
            self.push_screen(form, self._handle_investment_form_result)

    def action_edit_investment(self) -> None:
        """Edit the selected investment (when inside portfolio detail)."""
        if not self.current_portfolio:
            return
            
        # Get the current screen (should be PortfolioDetailScreen)
        current_screen = self.screen
        if isinstance(current_screen, PortfolioDetailScreen):
            investment_table = current_screen.query_one(InvestmentTable)
            investment = investment_table.get_selected_investment()

            if investment:
                form = InvestmentForm(investment=investment, portfolio_id=investment.portfolio_id)
                self.push_screen(form, self._handle_investment_form_result)
            else:
                self._show_status_message("No investment selected. Use ↑/↓ to select an investment.")

    def action_delete_investment(self) -> None:
        """Delete the selected investment (when inside portfolio detail)."""
        if not self.current_portfolio:
            return
            
        current_screen = self.screen
        if isinstance(current_screen, PortfolioDetailScreen):
            investment_table = current_screen.query_one(InvestmentTable)
            investment = investment_table.get_selected_investment()

            if investment:
                dialog = ConfirmationDialog(
                    "Delete Investment",
                    f"Are you sure you want to delete '{investment.name}'?",
                    item_id=investment.id
                )
                self.push_screen(dialog, self._handle_investment_delete_result)
            else:
                self._show_status_message("No investment selected. Use ↑/↓ to select an investment.")

    def action_move_investment(self) -> None:
        """Move the selected investment to another portfolio."""
        if not self.current_portfolio:
            return
            
        current_screen = self.screen
        if isinstance(current_screen, PortfolioDetailScreen):
            investment_table = current_screen.query_one(InvestmentTable)
            investment = investment_table.get_selected_investment()

            if investment:
                dialog = InvestmentMoveDialog(investment, self.portfolios)
                self.push_screen(dialog, self._handle_investment_move_result)
            else:
                self._show_status_message("No investment selected. Use ↑/↓ to select an investment.")

    def _handle_investment_form_result(self, result) -> None:
        """Handle the result from the investment form."""
        if not result:
            return
        
        action, data = result
        
        if action == "create":
            investment = Investment.create_new(
                name=data["name"],
                portfolio_id=data["portfolio_id"],
                final_amount=data["final_amount"],
                percentage_change=data["percentage_change"]
            )
            self.investments.append(investment)
            
        elif action == "update":
            for i, inv in enumerate(self.investments):
                if inv.id == data["id"]:
                    self.investments[i] = inv.update(
                        name=data["name"],
                        final_amount=data["final_amount"],
                        percentage_change=data["percentage_change"]
                    )
                    break
        
        elif action == "delete":
            investment_id = data
            self.investments = [inv for inv in self.investments if inv.id != investment_id]
        
        self._save_data()
        
        # Refresh the portfolio detail screen if active
        current_screen = self.screen
        if isinstance(current_screen, PortfolioDetailScreen):
            current_screen.portfolio_investments = [inv for inv in self.investments if inv.portfolio_id == current_screen.portfolio.id]
            investment_table = current_screen.query_one(InvestmentTable)
            investment_table.update_investments(current_screen.portfolio_investments)

    def _handle_investment_delete_result(self, result) -> None:
        """Handle the result from the investment delete confirmation dialog."""
        if not result:
            return
        
        confirmed, investment_id = result
        
        if confirmed and investment_id:
            self.investments = [inv for inv in self.investments if inv.id != investment_id]
            self._save_data()
            
            # Refresh the portfolio detail screen
            current_screen = self.screen
            if isinstance(current_screen, PortfolioDetailScreen):
                current_screen.portfolio_investments = [inv for inv in self.investments if inv.portfolio_id == current_screen.portfolio.id]
                investment_table = current_screen.query_one(InvestmentTable)
                investment_table.update_investments(current_screen.portfolio_investments)

    def _handle_investment_move_result(self, result) -> None:
        """Handle the result from the investment move dialog."""
        if not result:
            return
        
        action, investment_id, new_portfolio_id = result
        
        if action == "move" and investment_id and new_portfolio_id:
            # Find and move the investment
            for i, inv in enumerate(self.investments):
                if inv.id == investment_id:
                    self.investments[i] = inv.move_to_portfolio(new_portfolio_id)
                    break
            
            self._save_data()
            
            # Refresh the portfolio detail screen
            current_screen = self.screen
            if isinstance(current_screen, PortfolioDetailScreen):
                current_screen.portfolio_investments = [inv for inv in self.investments if inv.portfolio_id == current_screen.portfolio.id]
                investment_table = current_screen.query_one(InvestmentTable)
                investment_table.update_investments(current_screen.portfolio_investments)
                self._show_status_message("Investment moved successfully")

    # Summary and Navigation
    def action_show_summary(self) -> None:
        """Show the grand summary screen."""
        summary_screen = GrandSummaryScreen(self.portfolios, self.investments)
        self.push_screen(summary_screen)

    def action_refresh_data(self) -> None:
        """Refresh data from storage."""
        self.portfolios, self.investments = self.storage.load_all()
        self._update_portfolio_table()
        self._update_status_bar()

    async def action_quit(self) -> None:
        """Quit the application."""
        self.exit()
