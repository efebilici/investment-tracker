"""Widgets for Investment Tracker TUI application.

This module contains all UI components including dialogs for:
- Portfolio management (create, edit, delete)
- Investment management with external data source support
- Symbol search across data providers
- Price refresh operations
- Confirmation dialogs
"""

from typing import Any, List, Optional

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Select, Static, DataTable
from textual.validation import Function
from textual.reactive import reactive

from .models import Investment, Portfolio, Timeframe
from .data_providers import SearchResult


class PortfolioForm(ModalScreen):
    """Modal screen for adding/editing portfolios."""

    CSS = """
    PortfolioForm {
        align: center middle;
    }

    .form-container {
        width: 60;
        height: auto;
        border: thick $primary;
        background: $surface;
        padding: 1;
    }

    .form-title {
        text-align: center;
        text-style: bold;
        color: $primary;
        margin: 1 0;
    }

    .form-row {
        height: auto;
        padding: 0 1;
    }

    .form-label {
        width: 20;
        text-align: right;
        margin: 1 1 0 0;
    }

    .form-input {
        width: 35;
    }

    .button-container {
        height: 3;
        align: center middle;
    }

    Button {
        margin: 0 1;
    }
    """

    def __init__(self, portfolio: Portfolio | None = None):
        super().__init__()
        self.portfolio = portfolio
        self.title_text = "Edit Portfolio" if portfolio else "Add New Portfolio"

    def compose(self) -> ComposeResult:
        """Compose the form layout."""
        with Container(classes="form-container"):
            yield Label(self.title_text, classes="form-title")
            
            # Name input
            with Horizontal(classes="form-row"):
                yield Label("Name:", classes="form-label")
                yield Input(
                    value=self.portfolio.name if self.portfolio else "",
                    placeholder="Portfolio name",
                    id="name-input",
                    classes="form-input"
                )
            
            # Description input
            with Horizontal(classes="form-row"):
                yield Label("Description:", classes="form-label")
                yield Input(
                    value=self.portfolio.description if self.portfolio else "",
                    placeholder="Optional description",
                    id="description-input",
                    classes="form-input"
                )
            
            # Timeframe select
            with Horizontal(classes="form-row"):
                yield Label("Timeframe:", classes="form-label")
                yield Select(
                    options=[
                        ("1 Month", "1M"),
                        ("3 Months", "3M"), 
                        ("6 Months", "6M"),
                        ("1 Year", "1Y")
                    ],
                    value=self.portfolio.timeframe if self.portfolio else "1M",
                    id="timeframe-select",
                    classes="form-input"
                )
            
            # Buttons
            with Container(classes="button-container"):
                yield Button("Save", id="save-button", variant="primary")
                yield Button("Cancel", id="cancel-button")
                if self.portfolio:
                    yield Button("Delete", id="delete-button", variant="error")

    def on_mount(self) -> None:
        """Setup the form when mounted."""
        if not self.portfolio:
            self.query_one("#name-input").focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "save-button":
            self._save_portfolio()
        elif event.button.id == "cancel-button":
            self.dismiss(None)
        elif event.button.id == "delete-button" and self.portfolio:
            self.dismiss(("delete", self.portfolio.id))

    def _save_portfolio(self) -> None:
        """Validate and save the portfolio."""
        name_input = self.query_one("#name-input", Input)
        description_input = self.query_one("#description-input", Input)
        timeframe_select = self.query_one("#timeframe-select", Select)

        if not name_input.value.strip():
            name_input.focus()
            return

        portfolio_data = {
            "name": name_input.value.strip(),
            "description": description_input.value.strip(),
            "timeframe": timeframe_select.value
        }

        if self.portfolio:
            portfolio_data["id"] = self.portfolio.id
            self.dismiss(("update", portfolio_data))
        else:
            self.dismiss(("create", portfolio_data))


class SymbolSearchDialog(ModalScreen):
    """Modal dialog for searching and selecting investment symbols."""

    CSS = """
    SymbolSearchDialog {
        align: center middle;
    }

    .dialog-container {
        width: 80;
        height: auto;
        max-height: 40;
        border: thick $primary;
        background: $surface;
        padding: 1;
    }

    .dialog-title {
        text-align: center;
        text-style: bold;
        color: $primary;
        margin: 1 0;
    }

    .search-row {
        height: auto;
        padding: 0 1;
        margin: 1 0;
    }

    .search-label {
        width: 15;
        text-align: right;
        margin: 1 1 0 0;
    }

    .search-input {
        width: 40;
    }

    .filter-select {
        width: 20;
    }

    .results-container {
        height: 15;
        border: solid $accent;
        margin: 1;
    }

    .button-container {
        height: 3;
        align: center middle;
        margin: 1 0;
    }

    Button {
        margin: 0 1;
    }

    .info-text {
        text-align: center;
        color: $text-muted;
        margin: 1 0;
    }

    .error-text {
        text-align: center;
        color: $error;
        margin: 1 0;
    }

    DataTable {
        height: 100%;
    }
    """
    
    search_results: reactive[List[SearchResult]] = reactive([])
    is_searching: reactive[bool] = reactive(False)
    selected_result: reactive[Optional[SearchResult]] = reactive(None)

    def __init__(self, default_query: str = "", provider_manager=None):
        super().__init__()
        self.default_query = default_query
        self.provider_manager = provider_manager

    def compose(self) -> ComposeResult:
        with Container(classes="dialog-container"):
            yield Label("Search for Symbol", classes="dialog-title")
            
            with Horizontal(classes="search-row"):
                yield Label("Search:", classes="search-label")
                yield Input(
                    value=self.default_query,
                    placeholder="Enter company name or symbol",
                    id="search-input",
                    classes="search-input"
                )
                yield Button("Search", id="search-button", variant="primary")
            
            with Horizontal(classes="search-row"):
                yield Label("Type:", classes="search-label")
                yield Select(
                    options=[
                        ("All Types", "all"),
                        ("Stocks", "stock"),
                        ("ETFs", "etf"),
                        ("Funds", "fund"),
                        ("Crypto", "crypto"),
                    ],
                    value="all",
                    id="type-filter",
                    classes="filter-select"
                )
            
            yield Label("Enter a search term and click Search", classes="info-text", id="status-label")
            
            with Container(classes="results-container"):
                yield DataTable(id="results-table")
            
            with Container(classes="button-container"):
                yield Button("Select", id="select-button", variant="primary", disabled=True)
                yield Button("Cancel", id="cancel-button")

    def on_mount(self) -> None:
        table = self.query_one("#results-table", DataTable)
        table.add_columns("Symbol", "Name", "Type", "Source")
        table.cursor_type = "row"
        self.query_one("#search-input").focus()

    def watch_search_results(self, results: List[SearchResult]) -> None:
        table = self.query_one("#results-table", DataTable)
        table.clear()
        
        for result in results:
            table.add_row(
                result.symbol,
                result.name[:30] + "..." if len(result.name) > 30 else result.name,
                result.asset_type.title(),
                result.source,
            )
        
        status_label = self.query_one("#status-label", Label)
        if results:
            status_label.update(f"Found {len(results)} results")

    def watch_selected_result(self, result: Optional[SearchResult]) -> None:
        select_button = self.query_one("#select-button", Button)
        select_button.disabled = result is None

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "search-button":
            self._perform_search()
        elif event.button.id == "select-button":
            self._confirm_selection()
        elif event.button.id == "cancel-button":
            self.dismiss(None)

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        row_index = event.cursor_row
        if 0 <= row_index < len(self.search_results):
            self.selected_result = self.search_results[row_index]

    def _perform_search(self) -> None:
        search_input = self.query_one("#search-input", Input)
        type_filter = self.query_one("#type-filter", Select)
        
        query = search_input.value.strip()
        if not query:
            return
        
        self.is_searching = True
        
        try:
            asset_types = None
            if type_filter.value and type_filter.value != "all":
                asset_types = [type_filter.value]
            
            if self.provider_manager:
                results = self.provider_manager.search_all(query, asset_types=asset_types)
            else:
                results = []
            
            self.search_results = results
            
        except Exception as e:
            status_label = self.query_one("#status-label", Label)
            status_label.update(f"Search error: {str(e)}")
            self.search_results = []
        finally:
            self.is_searching = False

    def _confirm_selection(self) -> None:
        if self.selected_result:
            result = self.selected_result
            self.dismiss((
                result.symbol,
                result.name,
                result.asset_type,
                result.source,
                result.currency or "USD",
            ))


class PriceRefreshDialog(ModalScreen):
    """Dialog showing price refresh progress."""

    CSS = """
    PriceRefreshDialog {
        align: center middle;
    }

    .dialog-container {
        width: 60;
        height: auto;
        border: thick $primary;
        background: $surface;
        padding: 1;
    }

    .dialog-title {
        text-align: center;
        text-style: bold;
        color: $primary;
        margin: 1 0;
    }

    .results-container {
        height: 15;
        border: solid $accent;
        margin: 1;
        padding: 1;
    }

    .button-container {
        height: 3;
        align: center middle;
        margin: 1 0;
    }
    """

    def __init__(self, investments: List[Investment], provider_manager=None):
        super().__init__()
        self.investments = [inv for inv in investments if inv.symbol and inv.data_source and inv.data_source != "manual"]
        self.provider_manager = provider_manager
        self.results: List[tuple] = []

    def compose(self) -> ComposeResult:
        with Container(classes="dialog-container"):
            yield Label("Refreshing Prices", classes="dialog-title")
            
            if not self.investments:
                yield Label("No linked investments to refresh.")
                with Container(classes="button-container"):
                    yield Button("Close", id="close-button", variant="primary")
            else:
                yield Label(f"Refreshing {len(self.investments)} investments...")
                with Container(classes="results-container", id="results-container"):
                    yield Static("Starting...")
                with Container(classes="button-container"):
                    yield Button("Close", id="close-button", variant="primary")

    def on_mount(self) -> None:
        if self.investments:
            self.run_worker(self._refresh_prices())

    async def _refresh_prices(self) -> None:
        results_container = self.query_one("#results-container", Container)
        results_container.remove_children()
        
        for investment in self.investments:
            try:
                if self.provider_manager:
                    price_data = self.provider_manager.fetch_price_with_fallback(
                        investment.symbol,
                        preferred_provider=investment.data_source
                    )
                    
                    if price_data:
                        results_container.mount(
                            Static(f"✓ {investment.name}: {price_data.price:.2f}")
                        )
                        self.results.append((investment.id, price_data))
                    else:
                        results_container.mount(
                            Static(f"✗ {investment.name}: Failed")
                        )
            except Exception as e:
                results_container.mount(
                    Static(f"✗ {investment.name}: Error")
                )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "close-button":
            self.dismiss(self.results)


class InvestmentForm(ModalScreen):
    """Modal screen for adding/editing investments with external data support."""

    CSS = """
    InvestmentForm {
        align: center middle;
    }

    .form-container {
        width: 70;
        height: 45;
        border: thick $primary;
        background: $surface;
        padding: 1;
        overflow: auto;
    }

    .form-title {
        text-align: center;
        text-style: bold;
        color: $primary;
        margin: 1 0;
    }

    .form-row {
        height: auto;
        padding: 0 1;
    }

    .form-label {
        width: 20;
        text-align: right;
        margin: 1 1 0 0;
    }

    .form-input {
        width: 35;
    }

    .button-container {
        height: 3;
        align: center middle;
    }

    Button {
        margin: 0 1;
    }

    .calc-preview {
        margin: 1 1;
        padding: 1;
        border: solid $accent;
        background: $panel;
        height: 5;
    }

    .profit {
        color: $success;
    }

    .loss {
        color: $error;
    }
    
    .data-source-section {
        border: solid $accent-darken-2;
        padding: 1;
        margin: 1 1;
    }
    
    .section-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }
    """

    def __init__(self, investment: Investment | None = None, portfolio_id: str | None = None, provider_manager=None):
        super().__init__()
        self.investment = investment
        self.portfolio_id = portfolio_id
        self.provider_manager = provider_manager
        self.title_text = "Edit Investment" if investment else "Add New Investment"

    def compose(self) -> ComposeResult:
        with Container(classes="form-container"):
            yield Label(self.title_text, classes="form-title")
            
            yield Label("Basic Information", classes="section-title")
            
            with Horizontal(classes="form-row"):
                yield Label("Name:", classes="form-label")
                yield Input(
                    value=self.investment.name if self.investment else "",
                    placeholder="Investment name",
                    id="name-input",
                    classes="form-input"
                )
            
            with Container(classes="data-source-section"):
                yield Label("Data Source", classes="section-title")
                
                with Horizontal(classes="form-row"):
                    yield Label("Source:", classes="form-label")
                    yield Select(
                        options=[
                            ("Manual Entry", "manual"),
                            ("TEFAS (Turkish Funds)", "tefas"),
                            ("Global Markets", "investiny"),
                        ],
                        value=self.investment.data_source if self.investment else "manual",
                        id="data-source-select",
                        classes="form-input"
                    )
                
                with Horizontal(classes="form-row"):
                    yield Label("Type:", classes="form-label")
                    yield Select(
                        options=[
                            ("Not Specified", None),
                            ("Stock", "stock"),
                            ("ETF", "etf"),
                            ("Fund", "fund"),
                            ("Crypto", "crypto"),
                        ],
                        value=self.investment.asset_type if self.investment else None,
                        id="asset-type-select",
                        classes="form-input"
                    )
                
                with Horizontal(classes="form-row"):
                    yield Label("Symbol:", classes="form-label")
                    yield Input(
                        value=self.investment.symbol if self.investment else "",
                        placeholder="Ticker symbol",
                        id="symbol-input",
                        classes="form-input"
                    )
                    yield Button("Search", id="search-symbol-button")
                
                with Horizontal(classes="form-row"):
                    yield Label("Currency:", classes="form-label")
                    yield Select(
                        options=[
                            ("USD", "USD"),
                            ("TRY", "TRY"),
                            ("EUR", "EUR"),
                            ("GBP", "GBP"),
                        ],
                        value=self.investment.currency if self.investment else "USD",
                        id="currency-select",
                        classes="form-input"
                    )
            
            yield Label("Financial Data", classes="section-title")
            
            with Horizontal(classes="form-row"):
                yield Label("Final Amount:", classes="form-label")
                yield Input(
                    value=str(self.investment.final_amount) if self.investment else "",
                    placeholder="Current value",
                    id="final-amount-input",
                    classes="form-input"
                )
            
            with Horizontal(classes="form-row"):
                yield Label("% Change:", classes="form-label")
                yield Input(
                    value=str(self.investment.percentage_change) if self.investment else "",
                    placeholder="Profit/loss percentage",
                    id="percentage-input",
                    classes="form-input"
                )
            
            yield Container(id="calc-preview", classes="calc-preview")
            
            with Container(classes="button-container"):
                yield Button("Save", id="save-button", variant="primary")
                yield Button("Cancel", id="cancel-button")
                if self.investment:
                    yield Button("Delete", id="delete-button", variant="error")

    def on_mount(self) -> None:
        self._update_calc_preview()
        if not self.investment:
            self.query_one("#name-input").focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save-button":
            self._save_investment()
        elif event.button.id == "cancel-button":
            self.dismiss(None)
        elif event.button.id == "delete-button" and self.investment:
            self.dismiss(("delete", self.investment.id))
        elif event.button.id == "search-symbol-button":
            self._open_symbol_search()

    def _open_symbol_search(self) -> None:
        symbol_input = self.query_one("#symbol-input", Input)
        query = symbol_input.value.strip()
        
        def on_search_result(result):
            if result:
                symbol, name, asset_type, source, currency = result
                symbol_input.value = symbol
                name_input = self.query_one("#name-input", Input)
                if not name_input.value:
                    name_input.value = name
        
        self.app.push_screen(SymbolSearchDialog(query, self.provider_manager), on_search_result)

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id in ["final-amount-input", "percentage-input"]:
            self._update_calc_preview()

    def _update_calc_preview(self) -> None:
        try:
            final = self._get_float_value("#final-amount-input")
            pct = self._get_float_value("#percentage-input")
            
            if final is not None and pct is not None:
                original = final / (1 + pct / 100)
                profit = final - original
                
                text = f"Original: {original:,.2f}\nProfit/Loss: {profit:+,.2f}\nReturn: {pct:+.2f}%"
                style = "profit" if profit >= 0 else "loss"
                
                preview = self.query_one("#calc-preview", Container)
                preview.remove_children()
                preview.mount(Static(text, classes=style))
        except:
            pass

    def _get_float_value(self, selector: str) -> float | None:
        try:
            widget = self.query_one(selector, Input)
            if widget.value.strip():
                return float(widget.value)
        except:
            pass
        return None

    def _save_investment(self) -> None:
        name_input = self.query_one("#name-input", Input)
        final_input = self.query_one("#final-amount-input", Input)
        pct_input = self.query_one("#percentage-input", Input)
        source_select = self.query_one("#data-source-select", Select)
        type_select = self.query_one("#asset-type-select", Select)
        symbol_input = self.query_one("#symbol-input", Input)
        currency_select = self.query_one("#currency-select", Select)

        if not name_input.value.strip():
            name_input.focus()
            return

        try:
            final_amount = float(final_input.value)
            percentage = float(pct_input.value)
        except ValueError:
            return

        if final_amount <= 0 or percentage < -100:
            return

        data = {
            "name": name_input.value.strip(),
            "final_amount": final_amount,
            "percentage_change": percentage,
            "data_source": source_select.value,
            "asset_type": type_select.value,
            "symbol": symbol_input.value.strip() or None,
            "currency": currency_select.value,
        }

        if self.investment:
            data["id"] = self.investment.id
            data["portfolio_id"] = self.investment.portfolio_id
            self.dismiss(("update", data))
        else:
            data["portfolio_id"] = self.portfolio_id
            self.dismiss(("create", data))


class InvestmentMoveDialog(ModalScreen):
    """Modal screen for moving an investment to a different portfolio."""

    CSS = """
    InvestmentMoveDialog {
        align: center middle;
    }

    .dialog-container {
        width: 50;
        height: auto;
        border: thick $primary;
        background: $surface;
        padding: 1;
    }

    .dialog-title {
        text-align: center;
        text-style: bold;
        color: $primary;
        margin: 1 0;
    }

    .dialog-text {
        text-align: center;
        margin: 1 0;
    }

    .form-row {
        height: auto;
        padding: 0 1;
    }

    .form-label {
        width: 20;
        text-align: right;
        margin: 1 1 0 0;
    }

    .form-input {
        width: 25;
    }

    .button-container {
        height: 3;
        align: center middle;
    }

    Button {
        margin: 0 1;
    }
    """

    def __init__(self, investment: Investment, portfolios: List[Portfolio]):
        super().__init__()
        self.investment = investment
        self.portfolios = [p for p in portfolios if p.id != investment.portfolio_id]

    def compose(self) -> ComposeResult:
        with Container(classes="dialog-container"):
            yield Label("Move Investment", classes="dialog-title")
            yield Label(f"Moving: {self.investment.name}", classes="dialog-text")
            
            with Horizontal(classes="form-row"):
                yield Label("To Portfolio:", classes="form-label")
                yield Select(
                    options=[(p.name, p.id) for p in self.portfolios],
                    value=self.portfolios[0].id if self.portfolios else None,
                    id="portfolio-select",
                    classes="form-input"
                )
            
            with Container(classes="button-container"):
                yield Button("Move", id="move-button", variant="primary")
                yield Button("Cancel", id="cancel-button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "move-button":
            portfolio_select = self.query_one("#portfolio-select", Select)
            if portfolio_select.value:
                self.dismiss(("move", self.investment.id, portfolio_select.value))
        elif event.button.id == "cancel-button":
            self.dismiss(None)


class ConfirmationDialog(ModalScreen):
    """Simple confirmation dialog."""

    CSS = """
    ConfirmationDialog {
        align: center middle;
    }

    .dialog-container {
        width: 40;
        height: auto;
        border: thick $warning;
        background: $surface;
        padding: 1;
    }

    .dialog-text {
        text-align: center;
        margin: 1 0;
    }

    .button-container {
        height: 3;
        align: center middle;
    }
    """

    def __init__(self, title: str, message: str, item_id: str | None = None):
        super().__init__()
        self.title_text = title
        self.message_text = message
        self.item_id = item_id

    def compose(self) -> ComposeResult:
        with Container(classes="dialog-container"):
            yield Label(self.title_text, classes="dialog-text")
            yield Label(self.message_text, classes="dialog-text")
            with Container(classes="button-container"):
                yield Button("Yes", id="yes-button", variant="error")
                yield Button("No", id="no-button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "yes-button":
            self.dismiss((True, self.item_id))
        else:
            self.dismiss((False, None))
