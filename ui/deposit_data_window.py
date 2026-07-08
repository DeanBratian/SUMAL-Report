from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QScrollArea, QWidget, QFrame, QLabel
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from core.resources import APP_RESOURCES
from controllers.deposit_data_controller import DepositDataController
from core.models import DepozitDataModel
from ui.deposit_card_widget import DepositCardWidget

class DepositDataWindow(QDialog):
    def __init__(self, initial_data: list[DepozitDataModel], parent=None):
        super().__init__(parent)
        self.controller = DepositDataController(initial_data)
        self.cards: list[DepositCardWidget] = []
        self._setup_window()
        self._build_ui()
    
    # ---------------------------------------------------------------------- #
    
    def _setup_window(self) -> None:
        """Setup of the window, set initial values, text, icons, stylesheet, etc."""
        self.setWindowTitle("Editare date depozite")
        self.setWindowIcon(QIcon(APP_RESOURCES.resource_path("icons/srblue.png")))
        self.setFixedSize(900, 700)
        self.setStyleSheet(APP_RESOURCES.load_stylesheet())
    
    # ---------------------------------------------------------------------- #
    
    def _build_ui(self) -> None:
        """Builds the ui of the window"""
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(15)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        c_layout = QVBoxLayout(container)
        c_layout.setContentsMargins(0, 0, 0, 0)
        c_layout.setSpacing(15)
        
        c_layout.addWidget(self._build_title_panel())
        
        # Add deposit cards
        for depozit in self.controller.get_initial_data():
            card = DepositCardWidget(depozit)
            self.cards.append(card)
            c_layout.addWidget(card)
        
        c_layout.addStretch()
        scroll.setWidget(container)
        root.addWidget(scroll, 1)
        
        root.addWidget(self._build_buttons())
    
    # ---------------------------------------------------------------------- #

    def _build_title_panel(self) -> QWidget:
        """Builds the title panel in the ui"""
        panel = QWidget()
        panel.setProperty("class", "title-panel")
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)
        
        title_label = QLabel("Date și prețuri depozite")
        title_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        title_label.setProperty("class", "title-label")
        
        layout.addWidget(title_label)
        
        return panel
    
    # ---------------------------------------------------------------------- #
    
    def _build_buttons(self) -> QWidget:
        """Builds the save and close buttons in the ui"""
        footer = QWidget()
        layout = QHBoxLayout(footer)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        layout.addStretch()
        
        btn_cancel = QPushButton("Închide")
        btn_cancel.setProperty("class", "btn-close")
        btn_cancel.clicked.connect(self.reject)
        
        btn_save = QPushButton("Salvează")
        btn_save.setProperty("class", "btn-save")
        btn_save.clicked.connect(self._on_save)
        
        layout.addWidget(btn_cancel)
        layout.addWidget(btn_save)
        layout.addStretch()
        
        return footer
    
    # ---------------------------------------------------------------------- #
    
    def _on_save(self) -> None:
        """Save the entered data and give it back to main window when user saves"""
        self.controller.save_data([card._apply_changes() for card in self.cards])
        self.accept()