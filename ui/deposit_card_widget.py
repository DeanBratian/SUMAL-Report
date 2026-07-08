from PyQt6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QVBoxLayout,
    QHBoxLayout, QToolButton, QFrame
)
from PyQt6.QtGui import QIntValidator, QIcon
from PyQt6.QtCore import Qt
from core.models import DepozitDataModel
from core.config import DEPOSIT_DATA_ENABLED_FIELDS_BY_TYPE
from core.enums import DepositType, DepozitSource
from core.resources import APP_RESOURCES
from core.utils import refresh_style

class DepositCardWidget(QWidget):
    def __init__(self, deposit_data: DepozitDataModel, parent = None):
        super().__init__(parent)
        # Each widget holds a deposit data object
        self.deposit_data = deposit_data
        # Fields to be displayed for each deposit
        self.inputs: dict[str, QLineEdit] = {}
        # Expand/collapse functionality
        self.expanded = False
        self.setProperty("class", "deposit-card")
        self._build_ui()

    # ---------------------------------------------------------------------- #

    def _build_ui(self) -> None:
        """Builds the ui of the widget"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.header = self._build_header()
        self.price_panel = self._build_price_panel()

        layout.addWidget(self.header)
        layout.addWidget(self.price_panel)

        self._update_completion_status()
        self._configure_fields_by_deposit_type()

    # ---------------------------------------------------------------------- #

    def _build_header(self) -> QWidget:
        """Builds the card widget header"""
        header = QWidget()
        header.setProperty("class", "deposit-card-header")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # Expand / collapse icon button
        self.btn_toggle = QToolButton()
        self.btn_toggle.setIcon(QIcon(APP_RESOURCES.resource_path("icons/expand.png")))
        self.btn_toggle.setCheckable(True)
        self.btn_toggle.setAutoRaise(True)
        self.btn_toggle.clicked.connect(self._toggle)
        self.btn_toggle.setFixedSize(32, 32)

        # Deposit name label
        self.lbl_name = QLabel(self.deposit_data.nume_depozit)
        self.lbl_name.setProperty("class", "deposit-name")

        # Deposit type label
        self.lbl_type = QLabel(str(self.deposit_data.tip_depozit))
        self.lbl_type.setProperty("class", "deposit-type-badge")
        self.lbl_type.setProperty("tip_depozit", self._deposit_type_key())

        # Deposit source label
        self.lbl_source = QLabel(self.deposit_data.sursa_depozit)
        self.lbl_source.setProperty("class", "deposit-source-badge")
        self.lbl_source.setProperty("sursa_depozit", self._deposit_source_key())
        
        # Completion status label
        self.lbl_status = QLabel("🗙")
        self.lbl_status.setProperty("class", "label-status")
        self.lbl_status.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        for lbl in (self.lbl_name, self.lbl_type, self.lbl_source, self.lbl_status):
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # ---------------------------------------------------------------------- #
    
        def make_separator() -> QFrame:
            sep = QFrame()
            sep.setFixedWidth(1)
            sep.setProperty("class", "card-separator")
            return sep

        # ---------------------------------------------------------------------- #

        layout.addWidget(self.btn_toggle, 0)
        layout.addWidget(make_separator())
        layout.addWidget(self.lbl_name, 3)
        layout.addWidget(make_separator())
        layout.addWidget(self.lbl_type, 1)
        layout.addWidget(self.lbl_source, 1)
        layout.addWidget(make_separator())
        layout.addWidget(self.lbl_status, 0)

        return header

    # ---------------------------------------------------------------------- #

    def _build_price_panel(self) -> QWidget:
        """Builds the expandable panel for the text boxes"""
        panel = QWidget()
        panel.setProperty("class", "price-panel")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        prices = self.deposit_data.price_data
        
        # ---------------------------------------------------------------------- #

        def int_edit(value) -> QLineEdit:
            edit = QLineEdit(str(value) if value > 0 else "")
            edit.setValidator(QIntValidator(1, 1_000_000))
            edit.setFixedWidth(90)
            edit.setFixedHeight(28)
            edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
            edit.textChanged.connect(self._update_completion_status)
            return edit
        
        # ---------------------------------------------------------------------- #

        # All fields, some might be disabled
        self.inputs = {
            "p_intrare_lr_mc": int_edit(prices.p_intrare_lr_mc),
            "p_intrare_lf_mc": int_edit(prices.p_intrare_lf_mc),
            "p_intrare_ch_mc": int_edit(prices.p_intrare_ch_mc),
            "p_transport_mc": int_edit(prices.p_transport_mc),
            "p_iesire_lr_mc": int_edit(prices.p_iesire_lr_mc),
            "p_iesire_lf_mc": int_edit(prices.p_iesire_lf_mc),
            "p_iesire_ch_mc": int_edit(prices.p_iesire_ch_mc),
            "p_expl_mc": int_edit(prices.p_expl_mc)
        }
        # Labels for all fields
        labels = [
            ("p_intrare_lr_mc", "Preț intrare lemn rotund"),
            ("p_intrare_lf_mc", "Preț intrare lemn foc"),
            ("p_intrare_ch_mc", "Preț intrare cherestele"),
            ("p_transport_mc", "Preț transport"),
            ("p_iesire_lr_mc", "Preț ieșire lemn rotund"),
            ("p_iesire_lf_mc", "Preț ieșire lemn foc"),
            ("p_iesire_ch_mc", "Preț ieșire cherestele"),
            ("p_expl_mc", "Preț exploatare")
        ]
        # Create 2 bordered rows
        for row_idx in range(2):
            # Create container for each row
            row_container = QWidget()
            row_container.setProperty("class", "price-row")
            row_layout = QHBoxLayout(row_container)
            row_layout.setContentsMargins(12, 12, 12, 12)
            row_layout.setSpacing(20)

            # Add 4 columns per row
            for col_idx in range(4):
                idx = row_idx * 4 + col_idx
                if idx < len(labels):
                    key, text = labels[idx]

                    col_widget = QWidget()
                    col_widget.setProperty("class", "card-widget")
                    col_layout = QVBoxLayout(col_widget)
                    col_layout.setSpacing(8)
                    col_layout.setContentsMargins(0, 0, 0, 0)

                    label = QLabel(text)
                    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    label.setWordWrap(True)

                    col_layout.addWidget(label)
                    col_layout.addWidget(self.inputs.get(key), 0, Qt.AlignmentFlag.AlignHCenter)

                    row_layout.addWidget(col_widget, 1)

            layout.addWidget(row_container)

        panel.setVisible(False)
        return panel

    # ---------------------------------------------------------------------- #

    def _configure_fields_by_deposit_type(self) -> None:
        """Enable/disable fields based on deposit type"""
        enabled_fields = DEPOSIT_DATA_ENABLED_FIELDS_BY_TYPE[self.deposit_data.tip_depozit]
        for key in self.inputs:
            self._set_field_enabled(key, key in enabled_fields)

    # ---------------------------------------------------------------------- #

    def _set_field_enabled(self, field_key: str, enabled: bool) -> None:
        """Enable or disable a field and set its value to 0 if disabled"""
        field = self.inputs.get(field_key)
        if field:
            field.setEnabled(enabled)
            if not enabled:
                field.setText("-")

    # ---------------------------------------------------------------------- #

    def _is_complete(self) -> bool:
        """Checks if all the enabled edit text are populated inside a card"""
        return all(
            edit.text().isdigit() and int(edit.text()) > 0
            for edit in self.inputs.values() if edit.isEnabled()
        )

    # ---------------------------------------------------------------------- #

    def _update_completion_status(self) -> None:
        """Update the indicator if the deposit data is valid and complete"""
        if self._is_complete():
            self.lbl_status.setText("✔")
            self.lbl_status.setProperty("state", "valid")
        else:
            self.lbl_status.setText("🗙")
            self.lbl_status.setProperty("state", "invalid")
        refresh_style(self.lbl_status)

    # ---------------------------------------------------------------------- #

    def _toggle(self) -> None:
        """Creates expand-collapse behaviour for the panel"""
        self.expanded = not self.expanded
        self.price_panel.setVisible(self.expanded)
        self.btn_toggle.setChecked(self.expanded)
        if self.expanded:
            self.btn_toggle.setIcon(QIcon(APP_RESOURCES.resource_path("icons/collapse.png")))
        else:
            self.btn_toggle.setIcon(QIcon(APP_RESOURCES.resource_path("icons/expand.png")))

        expanded_str = "true" if self.expanded else "false"
        self.lbl_name.setProperty("expanded", expanded_str)
        refresh_style(self.lbl_name)

    # ---------------------------------------------------------------------- #

    def _apply_changes(self) -> DepozitDataModel:
        """Read all input fields and write their values back to deposit_data."""
        prices = self.deposit_data.price_data
        for key, edit in self.inputs.items():
            if not edit.isEnabled():
                setattr(prices, key, 0)
                continue
            try:
                value = int(edit.text()) if edit.text().strip() else 0
            except ValueError:
                value = 0
            
            setattr(prices, key, value)
        
        return self.deposit_data

    # ---------------------------------------------------------------------- #

    def _deposit_type_key(self) -> str:
        """Get QSS class based on owned deposit type"""
        tip = self.deposit_data.tip_depozit
        if tip == DepositType.DEPOZIT_TEMPORAR_LR:
            return "lr"
        elif tip == DepositType.DEPOZIT_PRINCIPAL:
            return "principal"
        return "extern"

    # ---------------------------------------------------------------------- #

    def _deposit_source_key(self) -> str:
        """Get QSS class based on owned deposit source"""
        sursa = self.deposit_data.sursa_depozit
        if sursa == DepozitSource.EXCEL_SUMAL:
            return "excel"
        elif sursa == DepozitSource.AVIZE:
            return "avize"
