from PyQt6.QtWidgets import (
    QLabel, QVBoxLayout, QDialog, QDialogButtonBox,
    QWidget, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

from controllers.notice_details_controller import NoticeDetailsController
from core.resources import APP_RESOURCES
from core.utils import float_to_display_str
from core.models import WoodItemModel, TransportNoticeModel

class NoticeDetailsWindow(QDialog):
    def __init__(self, notice: TransportNoticeModel, parent = None):
        super().__init__(parent)
        self.controller = NoticeDetailsController(notice)
        self._setup_window()
        self._build_ui()
    
    # ---------------------------------------------------------------------- #

    def _setup_window(self):
        """Setup of the window, set initial values, text, icons, stylesheet, etc."""
        self.setWindowTitle("Detalii aviz")
        self.setWindowIcon(QIcon(APP_RESOURCES.resource_path("icons/srblue.png")))
        self.setFixedSize(900, 700)
        self.setStyleSheet(APP_RESOURCES.load_stylesheet())
    
    # ---------------------------------------------------------------------- #

    def _build_ui(self):
        """Builds the ui of the window"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title panel 
        layout.addWidget(self._build_title_panel())
        # Info panel
        layout.addWidget(self._build_info_panel())
        # Wood items table
        layout.addWidget(self._build_and_populate_table())
        # Close button
        layout.addWidget(self._build_buttons(), alignment = Qt.AlignmentFlag.AlignHCenter)
    
    # ---------------------------------------------------------------------- #

    def _build_title_panel(self) -> QWidget:
        """Builds the title panel in the ui"""
        panel = QWidget()
        panel.setProperty("class", "title-panel")
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)
        
        title_label = QLabel(self.controller.get_title())
        title_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        title_label.setProperty("class", "title-label")
        
        layout.addWidget(title_label)
        
        return panel
    
    # ---------------------------------------------------------------------- #

    def _build_info_panel(self) -> QWidget:
        """Builds the info panel in the ui"""
        panel = QWidget()
        panel.setProperty("class", "details-info-panel")
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        # Build info text from controller data
        info_text = self._build_info_text()
        
        info_label = QLabel(info_text)
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        return panel
    
    # ---------------------------------------------------------------------- #

    def _build_info_text(self) -> str:
        """Builds the info text to be displayed in the ui"""
        data = self.controller.get_notice_info_data()
        
        # Get volume breakdown by good type
        breakdown = self.controller.get_volume_breakdown()
        
        # Build breakdown string (values are already formatted by the controller)
        breakdown_parts = [
            f"{good_type}: {volume} m³"
            for good_type, volume in breakdown.items()
        ]
        breakdown_str = ", ".join(breakdown_parts)

        # Volume total is already formatted by the controller
        if breakdown_str:
            volum_display = f"{data['volum_total']} m³ ({breakdown_str})"
        else:
            volum_display = f"{data['volum_total']} m³"
        
        info_text = f"""
        <div>
            <p><b>Tip:</b> {data['tip']}</p>
            <p><b>Emitent:</b> {data['emitent']}</p>
            <p><b>Destinatar:</b> {data['destinatar']}</p>
            <p><b>Proveniență:</b> {data['provenienta']}</p>
            <p><b>Volum total:</b> {volum_display}</p>
            <p><b>Punct încărcare:</b> {data['punct_incarcare']}</p>
            <p><b>Punct descărcare:</b> {data['punct_descarcare']}</p>
            <p><b>Valabilitate:</b> {data['valabilitate']}</p>
            <p><b>Mijloc transport:</b> {data['transport']}</p>
        </div>
        """
        return info_text
    
    # ---------------------------------------------------------------------- #

    def _build_and_populate_table(self) -> QTableWidget:
        """Builds the table that shows WoodItemModels and populates it"""
        table = QTableWidget()
        table.setColumnCount(9)
        table.setHorizontalHeaderLabels([
            "#", "Specie", "Sortiment", "Nr. buc.", 
            "Lungime", "Lățime", "Înălțime", "Diametru", "Volum"
        ])
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        table.setAlternatingRowColors(True)
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setDefaultSectionSize(30)
        
        # Get data from controller and populate table
        wood_items = self.controller.get_wood_items_table_data()
        table.setRowCount(len(wood_items))
        
        # Populate table rows with WoodItemModel objects
        for row, item_data in enumerate(wood_items):
            self._populate_table_row(table, row, item_data)

        if wood_items:
            self._adjust_columns_visibility(table, wood_items[0])
        
        # Configure headers
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)
        
        return table

    # ---------------------------------------------------------------------- #

    def _populate_table_row(self, table: QTableWidget, row: int, item_data: WoodItemModel):
        """Populates a table row in the ui"""
        values = [
            f"{item_data.nr_crt}",
            item_data.specie,
            item_data.sortiment,
            f"{item_data.nr_bucati}",
            f"{float_to_display_str(item_data.lungime)} m",
            f"{float_to_display_str(item_data.latime)} m",
            f"{float_to_display_str(item_data.inaltime)} m",
            f"{float_to_display_str(item_data.diametru)} cm",
            f"{float_to_display_str(item_data.volum_mc)} m³"
        ]
        
        for col, val in enumerate(values):
            item = QTableWidgetItem(val)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            table.setItem(row, col, item)
    
    # ---------------------------------------------------------------------- #

    def _build_buttons(self) -> QDialogButtonBox:
        """Builds the buttons for the ui"""
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        close_button = buttons.button(QDialogButtonBox.StandardButton.Close)
        close_button.setText("Închide")
        close_button.setProperty("class", "btn-close")
        
        return buttons
    
    # ---------------------------------------------------------------------- #

    def _adjust_columns_visibility(self, table: QTableWidget, first_item: WoodItemModel):
        """Adjusts columns visibility, for some notices we display diametru and lungime,
        while for others we display lungime, latime and inaltime"""
        COL_LUNGIME = 4
        COL_LATIME = 5
        COL_INALTIME = 6
        COL_DIAMETRU = 7

        lungime = first_item.lungime
        latime = first_item.latime
        inaltime = first_item.inaltime
        diametru = first_item.diametru

        # CASE 1: Lemn rotund (diametru > 0, lungime > 0, latime/inaltime = 0)
        if diametru > 0 and lungime > 0 and latime == 0 and inaltime == 0:
            table.setColumnHidden(COL_LUNGIME, False)
            table.setColumnHidden(COL_DIAMETRU, False)
            table.setColumnHidden(COL_LATIME, True)
            table.setColumnHidden(COL_INALTIME, True)

        # CASE 2: Lemn în metri steri (diametru = 0, lungime, latime, inaltime > 0)
        elif diametru == 0 and lungime > 0 and latime > 0 and inaltime > 0:
            table.setColumnHidden(COL_LUNGIME, False)
            table.setColumnHidden(COL_DIAMETRU, True)
            table.setColumnHidden(COL_LATIME, False)
            table.setColumnHidden(COL_INALTIME, False)