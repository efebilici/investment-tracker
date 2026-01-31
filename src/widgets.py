from typing import Any, List

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Select, Static
from textual.validation import Function

from .models import Investment, Portfolio, Timeframe


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


class InvestmentForm(ModalScreen):
    """Modal screen for adding/editing investments within a portfolio."""

    CSS = """
    InvestmentForm {
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

    .calc-preview {
        margin: 1 1;
        padding: 1;
        border: solid $accent;
        background: $panel;
        height: 6;
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
    """

    def __init__(self, investment: Investment | None = None, portfolio_id: str | None = None):
        super().__init__()
        self.investment = investment
        self.portfolio_id = portfolio_id
        self.title_text = "Edit Investment" if investment else "Add New Investment"

    def compose(self) -> ComposeResult:
        """Compose the form layout."""
        with Container(classes="form-container"):
            yield Label(self.title_text, classes="form-title")
            
            # Name input
            with Horizontal(classes="form-row"):
                yield Label("Name:", classes="form-label")
                yield Input(
                    value=self.investment.name if self.investment else "",
                    placeholder="Investment name",
                    id="name-input",
                    classes="form-input"
                )
            
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

    def on_input_changed(self, event: Input.Changed) -> None:
        """Update calculation preview when inputs change."""
        if event.input.id in ["final-amount-input", "percentage-input"]:
            self._update_calc_preview()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "save-button":
            self._save_investment()
        elif event.button.id == "cancel-button":
            self.dismiss(None)
        elif event.button.id == "delete-button" and self.investment:
            self.dismiss(("delete", self.investment.id))

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
            "percentage_change": percentage
        }

        if self.investment:
            investment_data["id"] = self.investment.id
            investment_data["portfolio_id"] = self.investment.portfolio_id
            self.dismiss(("update", investment_data))
        else:
            investment_data["portfolio_id"] = self.portfolio_id
            self.dismiss(("create", investment_data))


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
        """Compose the dialog layout."""
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
        """Handle button press events."""
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
        """Compose the dialog layout."""
        with Container(classes="dialog-container"):
            yield Label(self.title_text, classes="dialog-text")
            yield Label(self.message_text, classes="dialog-text")
            with Container(classes="button-container"):
                yield Button("Yes", id="yes-button", variant="error")
                yield Button("No", id="no-button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "yes-button":
            self.dismiss((True, self.item_id))
        else:
            self.dismiss((False, None))
