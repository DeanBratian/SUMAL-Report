import sys
import traceback
from PyQt6.QtWidgets import QApplication, QMessageBox
from core.logger import Logger
from core.resources import APP_RESOURCES
from ui.main_window import MainWindow

def main() -> int:
    app = QApplication(sys.argv)
    logger = Logger(APP_RESOURCES.writable_path("logs/sumal_report.log"))

    # PyQt6 terminates the process on an unhandled exception inside a Qt slot.
    # This hook is the last line of defense: log the full traceback and show
    # the error to the user instead of crashing silently.
    def handle_unhandled_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        details = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        logger.error(f"Unhandled exception:\n{details}")
        QMessageBox.critical(
            None, "Eroare neașteptată",
            f"A apărut o eroare neașteptată:\n{exc_value}\n\n"
            "Verifică fișierul de log-uri pentru detalii."
        )

    sys.excepthook = handle_unhandled_exception

    window = MainWindow(logger)
    window.show()
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
