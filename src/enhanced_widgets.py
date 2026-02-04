"""Enhanced widgets with symbol search and external data support."""

from typing import Any, List, Optional

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, Grid
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Select, Static, DataTable, LoadingIndicator
from textual.validation import Function
from textual.reactive import reactive

from .models import Investment, Portfolio, Timeframe
from .data_providers import SearchResult


class SymbolSearchDialog(ModalScreen):
    """Modal dialog for searching and selecting investment symbols.
    
    This dialog allows users to search across all available data providers
    (TEFAS, Investiny) and select the correct symbol for their investment.
    
    Example:
        >>> def on_search_result(self, result):
        ...     symbol, name, asset_type, source = result
        ...     print(f"Selected: {name} ({symbol}) from {source}")
        >>> 
        >>> self.push_screen(SymbolSearchDialog(), on_search_result)
    """

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
    
    # Reactive variables for search state
    search_results: reactive[List[SearchResult]] = reactive([])
    is_searching: reactive[bool] = reactive(False)
    selected_result: reactive[Optional[SearchResult]] = reactive(None)

    def __init__(self, default_query: str = "", provider_manager=None):
        """Initialize the search dialog.
        
        Args:
            default_query: Optional default search query
            provider_manager: DataProviderManager instance for searching
        """
        super().__init__()
        self.default_query = default_query
        self.provider_manager = provider_manager

    def compose(self) -> ComposeResult:
        """Compose the dialog layout."""
        with Container(classes="dialog-container"):
            yield Label("Search for Symbol", classes="dialog-title")
            
            # Search input row
            with Horizontal(classes="search-row"):
                yield Label("Search:", classes="search-label")
                yield Input(
                    value=self.default_query,
                    placeholder="Enter company name or symbol (e.g., 'Apple' or 'AAPL')",
                    id="search-input",
                    classes="search-input"
                )
                yield Button("🔍 Search", id="search-button", variant="primary")
            
            # Filter row
            with Horizontal(classes="search-row"):
                yield Label("Type:", classes="search-label")
                yield Select(
                    options=[
                        ("All Types", "all"),
                        ("Stocks", "stock"),
                        ("ETFs", "etf"),
                        ("Funds", "fund"),
                        ("Crypto", "crypto"),
                        ("Bonds", "bond"),
                        ("Commodities", "commodity"),
                    ],
                    value="all",
                    id="type-filter",
                    classes="filter-select"
                )
            
            # Results area
            yield Label("Enter a search term and click Search", classes="info-text", id="status-label")
            
            with Container(classes="results-container"):
                yield DataTable(id="results-table")
            
            # Buttons
            with Container(classes="button-container"):
                yield Button("Select", id="select-button", variant="primary", disabled=True)
                yield Button("Cancel", id="cancel-button")

    def on_mount(self) -> None:
        """Setup the dialog when mounted."""
        table = self.query_one("#results-table", DataTable)
        table.add_columns("Symbol", "Name", "Type", "Source", "Exchange")
        table.cursor_type = "row"
        
        # Focus search input
        search_input = self.query_one("#search-input", Input)
        search_input.focus()
        
        # Auto-search if default query provided
        if self.default_query:
            self._perform_search()

    def watch_search_results(self, results: List[SearchResult]) -> None:
        """Update table when search results change."""
        table = self.query_one("#results-table", DataTable)
        table.clear()
        
        for result in results:
            source_icon = "🇹🇷" if result.source == "tefas" else "🌍"
            table.add_row(
                result.symbol,
                result.name[:30] + "..." if len(result.name) > 30 else result.name,
                result.asset_type.title(),
                f"{source_icon} {result.source}",
                result.exchange or "-",
            )
        
        status_label = self.query_one("#status-label", Label)
        if results:
            status_label.update(f"Found {len(results)} results")
            status_label.remove_class("error-text")
        else:
            status_label.update("No results found. Try a different search term.")

    def watch_is_searching(self, searching: bool) -> None:
        """Update UI during search."""
        status_label = self.query_one("#status-label", Label)
        search_button = self.query_one("#search-button", Button)
        
        if searching:
            status_label.update("Searching...")
            search_button.disabled = True
        else:
            search_button.disabled = False

    def watch_selected_result(self, result: Optional[SearchResult]) -> None:
        """Enable/disable select button based on selection."""
        select_button = self.query_one("#select-button", Button)
        select_button.disabled = result is None

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "search-button":
            self._perform_search()
        elif event.button.id == "select-button":
            self._confirm_selection()
        elif event.button.id == "cancel-button":
            self.dismiss(None)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key in search input."""
        if event.input.id == "search-input":
            self._perform_search()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection in results table."""
        row_index = event.cursor_row
        if 0 <= row_index < len(self.search_results):
            self.selected_result = self.search_results[row_index]

    def _perform_search(self) -> None:
        """Execute the search across all providers."""
        search_input = self.query_one("#search-input", Input)
        type_filter = self.query_one("#type-filter", Select)
        
        query = search_input.value.strip()
        if not query:
            return
        
        self.is_searching = True
        
        try:
            # Build asset type filter
            asset_types = None
            if type_filter.value and type_filter.value != "all":
                asset_types = [type_filter.value]
            
            # Search using provider manager
            if self.provider_manager:
                results = self.provider_manager.search_all(query, asset_types=asset_types)
            else:
                # Fallback: no results if no provider manager
                results = []
            
            self.search_results = results
            
        except Exception as e:
            status_label = self.query_one("#status-label", Label)
            status_label.update(f"Search error: {str(e)}")
            status_label.add_class("error-text")
            self.search_results = []
        finally:
            self.is_searching = False

    def _confirm_selection(self) -> None:
        """Confirm the selected result and dismiss dialog."""
        if self.selected_result:
            result = self.selected_result
            self.dismiss((
                result.symbol,
                result.name,
                result.asset_type,
                result.source,
                result.currency or "USD",
                result.exchange,
            ))


class PriceRefreshDialog(ModalScreen):
    """Dialog showing price refresh progress and results."""

    CSS = """
    PriceRefreshDialog {
        align: center middle;
    }

    .dialog-container {
        width: 60;
        height: auto;
        max-height: 35;
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

    .progress-text {
        text-align: center;
        margin: 1 0;
    }

    .results-container {
        height: 15;
        border: solid $accent;
        margin: 1;
        padding: 1;
    }

    .success-text {
        color: $success;
    }

    .error-text {
        color: $error;
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
        """Compose the dialog layout."""
        with Container(classes="dialog-container"):
            yield Label("Refreshing Prices", classes="dialog-title")
            
            if not self.investments:
                yield Label("No linked investments to refresh.", classes="progress-text")
                with Container(classes="button-container"):
                    yield Button("Close", id="close-button", variant="primary")
            else:
                yield Label(f"Refreshing {len(self.investments)} investments...", classes="progress-text", id="progress-label")
                with Container(classes="results-container", id="results-container"):
                    yield Static("Starting refresh...")
                with Container(classes="button-container"):
                    yield Button("Close", id="close-button", variant="primary")

    def on_mount(self) -> None:
        """Start the refresh process when mounted."""
        if self.investments:
            self.run_worker(self._refresh_prices())

    async def _refresh_prices(self) -> None:
        """Refresh prices for all linked investments."""
        results_container = self.query_one("#results-container", Container)
        progress_label = self.query_one("#progress-label", Label)
        
        results_container.remove_children()
        
        updated_count = 0
        failed_count = 0
        
        for i, investment in enumerate(self.investments, 1):
            progress_label.update(f"Refreshing {i}/{len(self.investments)}: {investment.name}...")
            
            try:
                if self.provider_manager:
                    price_data = self.provider_manager.fetch_price_with_fallback(
                        investment.symbol,
                        preferred_provider=investment.data_source
                    )
                    
                    if price_data:
                        updated_count += 1
                        results_container.mount(
                            Static(
                                f"✓ {investment.name}: {price_data.price:.2f} {price_data.currency}",
                                classes="success-text"
                            )
                        )
                        self.results.append((investment.id, price_data))
                    else:
                        failed_count += 1
                        results_container.mount(
                            Static(f"✗ {investment.name}: Failed to fetch price", classes="error-text")
                        )
                else:
                    failed_count += 1
                    results_container.mount(
                        Static(f"✗ {investment.name}: No provider available", classes="error-text")
                    )
                    
            except Exception as e:
                failed_count += 1
                results_container.mount(
                    Static(f"✗ {investment.name}: {str(e)}", classes="error-text")
                )
        
        progress_label.update(f"Complete: {updated_count} updated, {failed_count} failed")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "close-button":
            self.dismiss(self.results)


# Import original widgets and extend InvestmentForm
from .widgets_original import (
    PortfolioForm as OriginalPortfolioForm,
    InvestmentForm as OriginalInvestmentForm,
    InvestmentMoveDialog,
    ConfirmationDialog,
)

# Re-export original widgets
PortfolioForm = OriginalPortfolioForm


class InvestmentForm(ModalScreen):
    """Enhanced modal screen for adding/editing investments with external data support."""

    CSS = """
    InvestmentForm {
        align: center middle;
    }

    .form-container {
        width: 70;
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

    .calc-preview {
        margin: 1 1;
        padding: 1;
        border: solid $accent;
        background: $panel;
        height: 8;
    }

    .error-text {
        color: $error;
        text-style: italic;
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
    
    .symbol-row {
        height: auto;
    }
    
    .search-button {
        width: 15;
        margin-left: 1;
    }
    
    .currency-display {
        color: $text-muted;
        margin: 1 0;
    }
    """

    def __init__(
        self, 
        investment: Investment | None = None, 
        portfolio_id: str | None = None,
        provider_manager=None
    ):
        super().__init__()
        self.investment = investment
        self.portfolio_id = portfolio_id
        self.provider_manager = provider_manager
        self.title_text = "Edit Investment" if investment else "Add New Investment"

    def compose(self) -> ComposeResult:
        """Compose the form layout."""
        with Container(classes="form-container"):
            yield Label(self.title_text, classes="form-title")
            
            # Basic info section
            yield Label("Basic Information", classes="section-title")
            
            # Name input
            with Horizontal(classes="form-row"):
                yield Label("Name:", classes="form-label")
                yield Input(
                    value=self.investment.name if self.investment else "",
                    placeholder="Investment name",
                    id="name-input",
                    classes="form-input"
                )
            
            # Data source section
            with Container(classes="data-source-section"):
                yield Label("Data Source", classes="section-title")
                
                # Data source select
                with Horizontal(classes="form-row"):
                    yield Label("Source:", classes="form-label")
                    yield Select(
                        options=[
                            ("Manual Entry", "manual"),
                            ("🇹🇷 TEFAS (Turkish Funds)", "tefas"),
                            ("🌍 Global Markets (Investiny)", "investiny"),
                        ],
                        value=self.investment.data_source if self.investment else "manual",
                        id="data-source-select",
                        classes="form-input"
                    )
                
                # Asset type select
                with Horizontal(classes="form-row"):
                    yield Label("Type:", classes="form-label")
                    yield Select(
                        options=[
                            ("Not Specified", None),
                            ("Stock", "stock"),
                            ("ETF", "etf"),
                            ("Fund", "fund"),
                            ("Crypto", "crypto"),
                            ("Bond", "bond"),
                            ("Commodity", "commodity"),
                        ],
                        value=self.investment.asset_type if self.investment else None,
                        id="asset-type-select",
                        classes="form-input"
                    )
                
                # Symbol input with search
                with Horizontal(classes="form-row symbol-row"):
                    yield Label("Symbol:", classes="form-label")
                    yield Input(
                        value=self.investment.symbol if self.investment else "",
                        placeholder="Ticker symbol (e.g., AAPL)",
                        id="symbol-input",
                        classes="form-input"
                    )
                    yield Button("🔍 Search", id="search-symbol-button", classes="search-button")
                
                # Currency select
                with Horizontal(classes="form-row"):
                    yield Label("Currency:", classes="form-label")
                    yield Select(
                        options=[
                            ("USD - US Dollar", "USD"),
                            ("TRY - Turkish Lira", "TRY"),
                            ("EUR - Euro", "EUR"),
                            ("GBP - British Pound", "GBP"),
                            ("JPY - Japanese Yen", "JPY"),
                            ("CHF - Swiss Franc", "CHF"),
                            ("CAD - Canadian Dollar", "CAD"),
                            ("AUD - Australian Dollar", "AUD"),
                        ],
                        value=self.investment.currency if self.investment else "USD",
                        id="currency-select",
                        classes="form-input"
                    )
            
            # Financial data section
            yield Label("Financial Data", classes="section-title")
            
            # Final amount input
            with Horizontal(classes="form-row"):
                yield Label("Final Amount:", classes="form-label")
                yield Input(
                    value=str(self.investment.final_amount) if self.investment else "",
                    placeholder="Current value",
                    id="final-amount-input",
                    validators=[
                        Function(lambda x: self._validate_positive_float(x), "Must be a positive number")
                    ],
                    classes="form-input"
                )
            
            # Percentage change input
            with Horizontal(classes="form-row"):
                yield Label("% Change:", classes="form-label")
                yield Input(
                    value=str(self.investment.percentage_change) if self.investment else "",
                    placeholder="Profit/loss percentage",
                    id="percentage-input",
                    validators=[
                        Function(lambda x: self._validate_percentage(x), "Must be >= -100%")
                    ],
                    classes="form-input"
                )
            
            # Calculation preview
            yield Container(id="calc-preview", classes="calc-preview")
            
            # Buttons
            with Container(classes="button-container"):
                yield Button("Save", id="save-button", variant="primary")
                yield Button("Cancel", id="cancel-button")
                if self.investment:
                    yield Button("Delete", id="delete-button", variant="error")

    def on_mount(self) -> None:
        """Setup the form when mounted."""
        self._update_calc_preview()
        
        if not self.investment:
            self.query_one("#name-input").focus()

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle select changes."""
        if event.select.id == "data-source-select":
            self._on_data_source_changed(event.value)

    def _on_data_source_changed(self, source: str) -> None:
        """Update UI based on data source selection."""
        symbol_input = self.query_one("#symbol-input", Input)
        search_button = self.query_one("#search-symbol-button", Button)
        asset_type_select = self.query_one("#asset-type-select", Select)
        
        if source == "manual":
            symbol_input.disabled = True
            search_button.disabled = True
            symbol_input.placeholder = "Not applicable for manual entry"
        else:
            symbol_input.disabled = False
            search_button.disabled = False
            
            if source == "tefas":
                symbol_input.placeholder = "Fund code (e.g., YAC, AAK)"
                # Default to Fund type for TEFAS
                asset_type_select.value = "fund"
            else:  # investiny
                symbol_input.placeholder = "Ticker symbol (e.g., AAPL, BTC)"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "save-button":
            self._save_investment()
        elif event.button.id == "cancel-button":
            self.dismiss(None)
        elif event.button.id == "delete-button" and self.investment:
            self.dismiss(("delete", self.investment.id))
        elif event.button.id == "search-symbol-button":
            self._open_symbol_search()

    def _open_symbol_search(self) -> None:
        """Open symbol search dialog."""
        symbol_input = self.query_one("#symbol-input", Input)
        data_source = self.query_one("#data-source-select", Select).value
        
        if data_source == "manual":
            return
        
        query = symbol_input.value.strip() or symbol_input.placeholder.split("(")[-1].rstrip(")")
        
        def on_search_result(result):
            if result:
                symbol, name, asset_type, source, currency, exchange = result
                symbol_input.value = symbol
                
                # Update other fields if found
                name_input = self.query_one("#name-input", Input)
                if not name_input.value:
                    name_input.value = name
                
                asset_type_select = self.query_one("#asset-type-select", Select)
                if asset_type:
                    asset_type_select.value = asset_type
                
                currency_select = self.query_one("#currency-select", Select)
                if currency:
                    currency_select.value = currency
        
        self.app.push_screen(SymbolSearchDialog(query, self.provider_manager), on_search_result)

    def on_input_changed(self, event: Input.Changed) -> None:
        """Update calculation preview when inputs change."""
        if event.input.id in ["final-amount-input", "percentage-input"]:
            self._update_calc_preview()

    def _validate_positive_float(self, value: str) -> bool:
        """Validate that input is a positive float."""
        try:
            return float(value) > 0
        except ValueError:
            return False

    def _validate_percentage(self, value: str) -> bool:
        """Validate that percentage is >= -100."""
        try:
            return float(value) >= -100
        except ValueError:
            return False

    def _update_calc_preview(self) -> None:
        """Update the calculation preview display."""
        try:
            final_amount = self._get_float_value("#final-amount-input")
            percentage = self._get_float_value("#percentage-input")
            
            if final_amount is not None and percentage is not None:
                original_amount = final_amount / (1 + percentage / 100)
                profit_loss = final_amount - original_amount
                
                preview_text = (
                    f"Original Investment: {original_amount:,.2f}\n"
                    f"Profit/Loss Amount: {profit_loss:+,.2f}\n"
                    f"Return Rate: {percentage:+.2f}%"
                )
                
                style_class = "profit" if profit_loss >= 0 else "loss"
                
                preview = self.query_one("#calc-preview", Container)
                preview.remove_children()
                preview.mount(Static(preview_text, classes=f"calc-text {style_class}"))
            else:
                self._clear_calc_preview()
                
        except (ValueError, ZeroDivisionError):
            self._clear_calc_preview()

    def _clear_calc_preview(self) -> None:
        """Clear the calculation preview."""
        preview = self.query_one("#calc-preview", Container)
        preview.remove_children()
        preview.mount(Static("Enter valid amounts to see calculations"))

    def _get_float_value(self, selector: str) -> float | None:
        """Get float value from input widget."""
        try:
            input_widget = self.query_one(selector, Input)
            if input_widget.value.strip():
                return float(input_widget.value)
        except (ValueError, AttributeError):
            pass
        return None

    def _save_investment(self) -> None:
        """Validate and save the investment."""
        name_input = self.query_one("#name-input", Input)
        final_amount_input = self.query_one("#final-amount-input", Input)
        percentage_input = self.query_one("#percentage-input", Input)
        data_source_select = self.query_one("#data-source-select", Select)
        asset_type_select = self.query_one("#asset-type-select", Select)
        symbol_input = self.query_one("#symbol-input", Input)
        currency_select = self.query_one("#currency-select", Select)

        if not name_input.value.strip():
            name_input.focus()
            return

        try:
            final_amount = float(final_amount_input.value)
            percentage = float(percentage_input.value)
        except ValueError:
            return

        if final_amount <= 0 or percentage < -100:
            return

        investment_data = {
            "name": name_input.value.strip(),
            "final_amount": final_amount,
            "percentage_change": percentage,
            "data_source": data_source_select.value,
            "asset_type": asset_type_select.value,
            "symbol": symbol_input.value.strip() if symbol_input.value.strip() else None,
            "currency": currency_select.value,
        }

        if self.investment:
            investment_data["id"] = self.investment.id
            investment_data["portfolio_id"] = self.investment.portfolio_id
            self.dismiss(("update", investment_data))
        else:
            investment_data["portfolio_id"] = self.portfolio_id
            self.dismiss(("create", investment_data))
