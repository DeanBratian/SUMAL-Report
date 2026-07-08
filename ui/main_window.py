from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QVBoxLayout,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QSplitter, QMessageBox, QHBoxLayout, QFileDialog, QScrollArea, QDialog
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon

from core.logger import Logger
from controllers.main_controller import MainController
from ui.deposit_data_window import DepositDataWindow
from ui.notice_details_window import NoticeDetailsWindow
from core.enums import AppState, FolderStatus, NoticeType
from core.resources import APP_RESOURCES
from core.utils import refresh_style
from datetime import datetime
from core.sr_error import SRError
from core.models import TransportNoticeModel
from ui.toggle_switch_button import ToggleSwitch

class MainWindow(QWidget):
    def __init__(self, logger: Logger):
        super().__init__()
        self.logger = logger
        self.logger.info("Starting SUMAL Report")
        self.controller = MainController(self.logger)
        self._toggle_widgets: list[ToggleSwitch] = [] # parallel to notices
        self._setup_window()
        self._build_ui()
        self._connect_signals()
    
    # ---------------------------------------------------------------------- #

    def _setup_window(self):
        """Setup of the window, set initial values, text, icons, stylesheet, etc."""
        self.setWindowTitle("SUMAL Report")
        self.setWindowIcon(QIcon(APP_RESOURCES.resource_path("icons/srblue.png")))
        self.setFixedSize(1350, 870)
        self.setStyleSheet(APP_RESOURCES.load_stylesheet())
    
    # ---------------------------------------------------------------------- #

    def _build_ui(self):
        """Builds the ui of the window"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        self.splitter = QSplitter(Qt.Orientation.Vertical)
        self.splitter.setHandleWidth(1)

        top_panel = self._build_top_panel()
        bottom_panel = self._build_bottom_panel()

        # IMPORTANT: set minimum height so splitter cannot go higher than this
        top_panel.setMinimumHeight(287)

        self.splitter.addWidget(top_panel)
        self.splitter.addWidget(bottom_panel)

        main_layout.addWidget(self.splitter)

        QTimer.singleShot(0, lambda: self.splitter.setSizes([
            top_panel.minimumHeight(),
            self.height() - top_panel.minimumHeight()
        ]))

        self._set_initial_button_states()
    
    # ---------------------------------------------------------------------- #

    def _build_top_panel(self) -> QFrame:
        """Builds the top panel in the ui"""
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        frame.setProperty("class", "main-frame")

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Button row - all 4 buttons in one row
        button_row = self._build_button_row()
        layout.addLayout(button_row)
        
        # Info row - folder label and file list side by side
        info_row = self._build_info_row()
        layout.addLayout(info_row)
        
        # Status label
        self.status_label = QLabel("Așteaptă alegerea folder-ului")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setProperty("class", "status-label-waiting")
        layout.addWidget(self.status_label)
        
        return frame
    
    # ---------------------------------------------------------------------- #

    def _build_button_row(self) -> QHBoxLayout:
        """Builds the top side control button row in the ui"""
        row = QHBoxLayout()
        row.setSpacing(12)
        
        # Button 1: Select folder
        self.btn_select = QPushButton("Alege folder")
        self.btn_select.setMinimumHeight(40)
        self.btn_select.setProperty("class", "btn-select")
        
        # Button 2: Parse files
        self.btn_parse = QPushButton("Procesează fișiere")
        self.btn_parse.setMinimumHeight(40)
        self.btn_parse.setProperty("class", "btn-parse")
        
        # Button 3: Edit date depozite
        self.btn_edit_deposit_data = QPushButton("Editează date depozite")
        self.btn_edit_deposit_data.setMinimumHeight(40)
        self.btn_edit_deposit_data.setProperty("class", "btn-deposit-data")
        
        # Button 4: Generate reports
        self.btn_gen_report = QPushButton("Generare rapoarte")
        self.btn_gen_report.setMinimumHeight(40)
        self.btn_gen_report.setProperty("class", "btn-reports")
        
        # Add buttons in order
        for btn in (self.btn_select, self.btn_parse,
                    self.btn_edit_deposit_data, self.btn_gen_report):
            row.addWidget(btn)
        
        return row
    
    # ---------------------------------------------------------------------- #

    def _build_info_row(self) -> QHBoxLayout:
        """Builds the info row in the ui"""
        row = QHBoxLayout()
        row.setSpacing(15)
        
        # Left side: Folder info
        row.addWidget(self._build_folder_info_panel(), 1)
        # Right side: File list
        row.addWidget(self._build_file_list_panel(), 1)
        
        return row
    
    # ---------------------------------------------------------------------- #

    def _build_folder_info_panel(self) -> QFrame:
        """Builds the folder info panel in the ui"""
        frame = QFrame()
        frame.setProperty("class", "info-frame")
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(12)
        
        # Folder label
        self.folder_label = QLabel("Nici un folder selectat")
        self.folder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.folder_label.setWordWrap(True)
        self.folder_label.setTextFormat(Qt.TextFormat.RichText)
        self.folder_label.setProperty("class", "folder-label")
        
        layout.addWidget(self.folder_label)
        
        return frame
    
    # ---------------------------------------------------------------------- #

    def _build_file_list_panel(self) -> QFrame:
        """Builds the file list info panel in the ui"""
        frame = QFrame()
        frame.setProperty("class", "info-frame")
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(12)
        
        # Scrollable file list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        scroll_container = QWidget()
        scroll_layout = QVBoxLayout(scroll_container)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        
        self.file_list_box = QLabel("Nici un fișier de afișat")
        self.file_list_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.file_list_box.setWordWrap(True)
        self.file_list_box.setTextFormat(Qt.TextFormat.RichText)
        self.file_list_box.setProperty("class", "file-list-box")
        
        scroll_layout.addWidget(self.file_list_box)
        scroll.setWidget(scroll_container)
        
        layout.addWidget(scroll, 1)
        
        return frame
    
    # ---------------------------------------------------------------------- #

    def _build_bottom_panel(self) -> QFrame:
        """Builds the bottom panel with the table in the ui"""
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        frame.setProperty("class", "main-frame")
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Create table
        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(
            ["#", "Cod unic aviz", "Data/Ora", "Emitent", "Destinatar", "Volum", "Tip aviz", "Prestări"]
        )
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # Configure table headers
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(50)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        
        layout.addWidget(self.table)
        
        return frame
    
    # ---------------------------------------------------------------------- #

    def _connect_signals(self):
        """Connects handlers to buttons and table in the ui"""
        self.btn_select.clicked.connect(self._on_select_folder)
        self.btn_parse.clicked.connect(self._on_parse_files)
        self.btn_gen_report.clicked.connect(self._on_generate_report)
        self.btn_edit_deposit_data.clicked.connect(self._on_edit_deposit_data_click)
        self.table.cellDoubleClicked.connect(self._on_table_double_click)
    
    # ---------------------------------------------------------------------- #

    def _set_initial_button_states(self):
        """Sets the initial state of the buttons in the ui, only choosing folder active"""
        self.btn_parse.setEnabled(False)
        self.btn_edit_deposit_data.setEnabled(False)
        self.btn_gen_report.setEnabled(False)

    # ---------------------------------------------------------------------- #

    def _update_button_states(self):
        """Updates the button states after chosing folder or parsing etc."""
        can_parse = self.controller.can_start_parsing()
        can_edit = self.controller.can_edit_deposit_data()
        can_report = self.controller.can_generate_reports()
        self.logger.debug(f"Button states: parse = {can_parse}, edit_deposit = {can_edit}, generate_report = {can_report}")
        self.btn_parse.setEnabled(can_parse)
        self.btn_edit_deposit_data.setEnabled(can_edit)
        self.btn_gen_report.setEnabled(can_report)
    
    # ---------------------------------------------------------------------- #

    def _on_select_folder(self):
        """Defines the behaviour when the user selects a folder"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Selectează folderul care conține fișierele CSV și Excel",
            ""
        )
        
        if not folder:
            return

        self.logger.info(f"User selected folder: {folder}")
        folder_changed = self.controller.set_folder(folder)

        if not folder_changed:
            self.logger.debug("Same folder selected, no action taken")
            return
        
        self.table.setRowCount(0)

        try:
            status, data = self.controller.validate_folder_files()
        except SRError as e:
            self._set_status(AppState.WAITING)
            self._update_button_states()
            self._show_message(e.title, e.message, QMessageBox.Icon.Critical)
            return
        except Exception as e:
            self.logger.error(f"Unexpected error validating folder: {e}")
            self._set_status(AppState.WAITING)
            self._update_button_states()
            self._show_message(
                "Eroare validare folder",
                f"Fișierele din folder nu au putut fi verificate:\n{e}",
                QMessageBox.Icon.Critical
            )
            return

        pending_message = None

        if status == FolderStatus.NO_FILES:
            self._update_folder_label(folder, data, '<span style="color:#d50000">🗙</span>')
            self._set_status(AppState.WAITING)
            pending_message = (
                "Nici un fișier găsit",
                "Folderul ales nu conține nici un fișier CSV sau Excel!",
                QMessageBox.Icon.Warning
            )

        elif status == FolderStatus.MISSING_XL:
            self._update_folder_label(folder, data, '<span style="color:#d50000">🗙</span>')
            self._set_status(AppState.WAITING)
            pending_message = (
                "Fișiere Excel lipsă",
                f"Numărul fișierelor Excel nu corespunde numărului așteptat!\n\n"
                f"Programul necesită: {data['expected_xl_count']} fișiere Excel, "
                f"în folder există: {data['xl_count']} fișiere Excel\n"
                f"Sunt necesare: Intrari_.xlsx, Aviz_.xlsx si Depozite_.xlsx descarcate din SUMAL",
                QMessageBox.Icon.Warning
            )

        elif status == FolderStatus.MISSING_CSV:
            self._update_folder_label(folder, data, '<span style="color:#d50000">🗙</span>')
            self._set_status(AppState.WAITING)
            pending_message = (
                "Fișiere CSV lipsă",
                f"Numărul fișierelor CSV nu corespunde numărului așteptat!\n\n"
                f"Din Excel deducem: {data['expected_csv_count']} fișiere CSV, "
                f"în folder există: {data['all_csv_count']} fișiere CSV",
                QMessageBox.Icon.Warning
            )

        else:
            self._update_folder_label(folder, data, '<span style="color:#2e7d32">✔</span>')
            self._set_status(AppState.READY)

        self._update_file_list_display()
        self._update_button_states()

        if pending_message:
            self._show_message(*pending_message)
    
    # ---------------------------------------------------------------------- #

    def _update_folder_label(self, folder: str, data: dict, status_icon: str = ""):
        """Creates folder label text based on folder validation data"""
        header = f"<b>{status_icon} Folder selectat:</b><br>{folder}<br>"

        xl_line = f"<b>{data['xl_count']}</b> fișiere Excel găsite"
        if data["xl_count"] != data["expected_xl_count"]:
            xl_line += (
                f", necesare <b><span style='color:red;'>"
                f"{data['expected_xl_count']}</span></b>"
            )

        csv_line = (
            f"<b>{data['unique_csv_count']}</b> fișiere CSV unice găsite "
            f"din <b>{data['all_csv_count']}</b> total"
        )
        if data["xl_count"] == data["expected_xl_count"] and data["all_csv_count"] != data["expected_csv_count"]:
            csv_line += (
                f", necesare: <b><span style='color:red;'>"
                f"{data['expected_csv_count']}</span></b>"
            )

        self.folder_label.setText(f"{header}{csv_line}<br>{xl_line}")

    # ---------------------------------------------------------------------- #

    def _update_file_list_display(self):
        """Updates the files to be displayed in the file list scrollable area"""
        file_list_parts = []
        error_files = self.controller.get_error_files()
        # 1. Display CSV names
        if self.controller.csv_files_dict["unique"]:
            csv_list_items = []
            for i, f in enumerate(self.controller.csv_files_dict["unique"]):
                if f in error_files:
                    csv_list_items.append(f'{i+1}. <span style="color:red;">{f}</span>')
                else:
                    csv_list_items.append(f"{i+1}. {f}")

            csv_list_html = "<br>".join(csv_list_items)
            file_list_parts.append(f"<b>Fișiere CSV:</b><br>{csv_list_html}")
        # 2. Display Excel names
        if self.controller.xl_files_dict:
            excel_list_items = []
            index = 1
            if "intrari" in self.controller.xl_files_dict:
                f = self.controller.xl_files_dict["intrari"]
                entries = self.controller.intrari_xl_row_count
                excel_list_items.append(f"{index}. {f} - <b>{entries} avize</b>")
                index += 1
            if "aviz" in self.controller.xl_files_dict:
                f = self.controller.xl_files_dict["aviz"]
                entries = self.controller.aviz_xl_row_count
                excel_list_items.append(f"{index}. {f} - <b>{entries} avize</b>")
                index += 1
            if "depozite" in self.controller.xl_files_dict:
                f = self.controller.xl_files_dict["depozite"]
                entries = self.controller.depozite_xl_row_count
                excel_list_items.append(f"{index}. {f} - <b>{entries} depozite</b>")
                index += 1

            excel_list_html = "<br>".join(excel_list_items)
            file_list_parts.append(f"<b>Fișiere Excel:</b><br>{excel_list_html}")
        # 3. Final output
        if file_list_parts:
            final_html = "<br><br>".join(file_list_parts)
            self.file_list_box.setText(final_html)
        else:
            self.file_list_box.setText("<i>Nici un fișier găsit</i>")

    # ---------------------------------------------------------------------- #

    def _on_parse_files(self):
        """Defines behaviour when user starts data parsing, a.k.a correct number of files was provided"""
        if self.controller.is_parsed:
            return

        self._set_status(AppState.PROCESSING)
        QApplication.processEvents()

        try:
            self.controller.parse_files()
        except SRError as e:
            self.logger.error(f"Parsing failed: {e.message}")
            self._show_message(e.title, e.message, QMessageBox.Icon.Critical)
            # get_error_files() counts CSV parse errors only — a validation
            # failure (orphan codes, volume mismatch, ...) leaves it at 0, so
            # only show counts when files actually failed to parse.
            error_count = len(self.controller.get_error_files())
            message = (
                f"{len(self.controller.notices)} avize procesate, număr erori: {error_count}"
                if error_count else None
            )
            self._set_status(AppState.PROCESSED_WITH_ERRORS, message)
            self._update_button_states()
            self._update_file_list_display()
            return
        except Exception as e:
            self.logger.error(f"Unexpected error during parsing: {e}")
            self._show_message(
                "Eroare procesare",
                f"Fișierele nu au putut fi procesate:\n{e}",
                QMessageBox.Icon.Critical
            )
            self._set_status(AppState.PROCESSED_WITH_ERRORS)
            self._update_button_states()
            self._update_file_list_display()
            return

        # Success path
        self._update_table()
        self._update_file_list_display()
        self._set_status(
            AppState.SUCCESS,
            f"{len(self.controller.notices)} avize procesate cu succes"
        )

        try:
            external_deposits, ignored_deposits = self.controller.initialize_deposit_data()
        except SRError as e:
            self._show_message(e.title, e.message, QMessageBox.Icon.Critical)
            self._set_status(AppState.PROCESSED_WITH_ERRORS)
            self._update_button_states()
            return
        except Exception as e:
            self.logger.error(f"Unexpected error initializing deposit data: {e}")
            self._show_message(
                "Eroare date depozite",
                f"Datele despre depozite nu au putut fi inițializate:\n{e}",
                QMessageBox.Icon.Critical
            )
            self._set_status(AppState.PROCESSED_WITH_ERRORS)
            self._update_button_states()
            return
        if external_deposits or ignored_deposits:
            self._show_open_deposit_data_message(external_deposits, ignored_deposits)

        self._update_button_states()
    
    # ---------------------------------------------------------------------- #

    def _show_open_deposit_data_message(self, external_deposits: set, ignored_deposits: set[str]):
        """Defines the message that is shown to the user after parsing is done"""
        msg = QMessageBox(self)
        msg.setWindowTitle("Editează date depozite")

        parts = []
        if external_deposits:
            external_list = "\n".join(f"  • {ep}" for ep in sorted(external_deposits))
            parts.append(
                f"Am găsit {len(external_deposits)} depozite externe:\n{external_list}"
            )
        if ignored_deposits:
            ignored_list = "\n".join(f"  • {name}" for name in sorted(ignored_deposits))
            parts.append(
                f"Am eliminat următoarele depozite (nu există avize):\n{ignored_list}"
            )
        text = "\n\n".join(parts)

        msg.setText(text)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setFont(self.font())
        msg.setStandardButtons(QMessageBox.StandardButton.NoButton)

        close_button = QPushButton("Închide")
        close_button.setProperty("class", "btn-close")
        msg.addButton(close_button, QMessageBox.ButtonRole.RejectRole)

        edit_button = QPushButton("Editează")
        edit_button.setProperty("class", "btn-save")
        msg.addButton(edit_button, QMessageBox.ButtonRole.AcceptRole)

        msg.exec()

        if msg.clickedButton() is edit_button:
            self._open_deposit_data_window()
    
    # ---------------------------------------------------------------------- #

    def _on_edit_deposit_data_click(self):
        """Wrapper for opening deposit data window via the button up top"""
        if self.controller.is_parsed and self.controller.deposit_data:
            self._open_deposit_data_window()
            self._update_button_states()
    
    # ---------------------------------------------------------------------- #

    def _open_deposit_data_window(self):
        """Defines the behaviour when the user opens deposit data window"""
        dlg = DepositDataWindow(self.controller.deposit_data, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            # Update the persistent data with the edited values
            saved_data = dlg.controller.get_saved_data()
            self.controller.set_deposit_data(saved_data)
            self.logger.info(f"User saved deposit data for {len(saved_data)} deposits")
            for dep in saved_data:
                prices = dep.price_data
                self.logger.info(
                    f"Deposit '{dep.nume_depozit}' (type = {dep.tip_depozit.name}, source = {dep.sursa_depozit.name}) | "
                    f"Intrare: LR = {prices.p_intrare_lr_mc}, LF = {prices.p_intrare_lf_mc}, CH = {prices.p_intrare_ch_mc} | "
                    f"Iesire: LR = {prices.p_iesire_lr_mc}, LF = {prices.p_iesire_lf_mc}, CH = {prices.p_iesire_ch_mc} | "
                    f"Transport = {prices.p_transport_mc}, Exploatare = {prices.p_expl_mc}"
                )
        else:
            self.logger.info("User closed deposit data window without saving")
    
    # ---------------------------------------------------------------------- #

    def _update_table(self):
        """Populates the main table with summary data about parsed notices"""
        table_data = self.controller.get_main_window_table_data()
        self._toggle_widgets.clear()
        self.table.setRowCount(len(table_data))

        for row, data in enumerate(table_data):
            notice = self.controller.get_notice(row)

            # Determine whether this notice type allows prestări toggling
            # INTRARE_DIN_PARTIDA_PROPRIE → always OFF, disabled
            # All other types → starts OFF, user can toggle
            is_partida_proprie = (
                notice is not None and
                notice.type == NoticeType.INTRARE_DIN_PARTIDA_PROPRIE
            )
            
            values = [
                str(row + 1),
                data["cod_unic"],
                data["data"],
                data["emitent"],
                data["destinatar"],
                data["volum"],
                data["tip"]
            ]

            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, col, item)

            # Prestări toggle (column 7) 
            interactive = not is_partida_proprie
            toggle = ToggleSwitch(interactive)
            self._toggle_widgets.append(toggle)

            # Centre the widget inside a container frame so it looks tidy
            container = QWidget()
            container_layout = QHBoxLayout(container)
            container_layout.addWidget(toggle)
            container_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            container_layout.setContentsMargins(0, 0, 0, 0)
            container.setStyleSheet("background: transparent;")

            self.table.setCellWidget(row, 7, container)
    
    # ---------------------------------------------------------------------- #

    def _on_table_double_click(self, row: int, column: int):
        """Opens notice details window when double clicking a notice in the table"""
        notice = self.controller.get_notice(row)
        if notice:
            self.logger.debug(f"Viewing notice details: {notice.cod_unic}")
            dlg = NoticeDetailsWindow(notice, self)
            dlg.exec()
    
    # ---------------------------------------------------------------------- #

    def _set_status(self, status_type: AppState, message: str = None):
        """Updates the status label state"""
        self.logger.debug(f"Status transition → {status_type.name}" + (f" - msg: {message}" if message else ""))
        status_configs = {
            AppState.WAITING: {
                "class": "status-label-waiting",
                "text": "Așteaptă alegerea folder-ului"
            },
            AppState.READY: {
                "class": "status-label-ready",
                "text": "Așteaptă procesarea"
            },
            AppState.PROCESSING: {
                "class": "status-label-processing",
                "text": "Se procesează fișierele..."
            },
            AppState.SUCCESS: {
                "class": "status-label-success",
                "text": "Procesare completă"
            },
            AppState.PROCESSED_WITH_ERRORS: {
                "class": "status-label-processed-with-errors",
                "text": "Procesare finalizată cu erori"
            },
            AppState.REPORT_COMPLETE: {
                "class": "status-label-report-complete",
                "text": "Raport generat cu succes"
            }
        }

        config = status_configs.get(status_type)
        self.status_label.setText(message or config["text"])
        self.status_label.setProperty("class", config["class"])
        # Force style refresh
        refresh_style(self.status_label)
    
    # ---------------------------------------------------------------------- #

    def _show_message(self, title: str, text: str, icon: QMessageBox.Icon):
        """Standard way to display a message box, used in multiple cases"""
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setIcon(icon)
        msg.setFont(self.font())

        msg.setStandardButtons(QMessageBox.StandardButton.NoButton)
        
        ok_button = QPushButton("Închide")
        ok_button.setProperty("class", "btn-close")
        ok_button.clicked.connect(msg.accept)
        msg.addButton(ok_button, QMessageBox.ButtonRole.AcceptRole)
        msg.exec()

    # ---------------------------------------------------------------------- #

    def _on_generate_report(self):
        """Handler for the generate report button click - generates comprehensive multi-sheet report"""

        default = f"Raport_SUMAL_{datetime.now().strftime('%d-%m-%Y_%H-%M-%S')}.xlsx"
        output_path, _ = QFileDialog.getSaveFileName(
            self, "Salvează raportul", default, "Excel Files (*.xlsx)"
        )
        if not output_path:
            return

        prestari_notices = self._get_prestari_notices()
        self.logger.info(
            f"Generating report: {output_path} | "
            f"Notices = {len(self.controller.notices)}, Prestări = {len(prestari_notices)}"
        )

        try:
            self.controller.generate_report(output_path, prestari_notices)
        except SRError as e:
            self.logger.error(f"Report generation failed: {e.message}")
            self._show_message(e.title, e.message, QMessageBox.Icon.Critical)
            return
        except PermissionError as e:
            self.logger.error(f"Output file is locked: {e}")
            self._show_message(
                "Fișier blocat",
                "Raportul nu a putut fi salvat deoarece fișierul este deschis "
                "în Excel sau în alt program.\n\nÎnchideți fișierul și încercați din nou.",
                QMessageBox.Icon.Critical
            )
            return
        except Exception as e:
            self.logger.error(f"Unexpected error during report generation: {e}")
            self._show_message(
                "Eroare generare raport",
                f"Raportul nu a putut fi salvat:\n{e}",
                QMessageBox.Icon.Critical
            )
            return

        self.logger.info(f"Report generated successfully: {output_path}")
        prestari_count = len(prestari_notices)
        self._set_status(AppState.REPORT_COMPLETE)
        extra = f"\n\nAvize marcate ca prestări servicii: {prestari_count}"
        self._show_message(
            "Succes",
            f"Raportul a fost generat cu succes!\n\nLocație: {output_path}{extra}",
            QMessageBox.Icon.Information
        )

    # ---------------------------------------------------------------------- #

    def _get_prestari_notices(self) -> list[TransportNoticeModel]:
        """Return the subset of notices where the Prestări toggle is ON."""
        prestari = []
        for idx, toggle in enumerate(self._toggle_widgets):
            if toggle.isChecked():
                notice = self.controller.get_notice(idx)
                if notice is not None:
                    prestari.append(notice)
        self.logger.debug(
            f"Prestări selection: {len(prestari)} of {len(self._toggle_widgets)} notices marked"
            + (f" — codes: {[n.cod_unic for n in prestari]}" if prestari else "")
        )
        return prestari
