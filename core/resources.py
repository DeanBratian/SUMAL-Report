import sys
from os.path import abspath, dirname, join

class AppResources:
    """Centralised resolver for read only and writeable resources.
    Handles the difference between running from source (project root) and
    running as a PyInstaller frozen executable (_MEIPASS / exe directory).
    """

    def __init__(self):
        if getattr(sys, 'frozen', False):
            self.PROJECT_ROOT: str = sys._MEIPASS
        else:
            # Go up two levels: resources.py -> core/ -> project root
            self.PROJECT_ROOT = dirname(dirname(abspath(__file__)))
        
        self.CACHED_STYLESHEET: str | None = None

    # ---------------------------------------------------------------------- #

    def resource_path(self, relative_path: str) -> str:
        """Resolve a project-relative path to an absolute path for read-only resources."""
        return join(self.PROJECT_ROOT, relative_path)

    # ---------------------------------------------------------------------- #

    def writable_path(self, relative_path: str) -> str:
        """Resolve a path for files the app needs to write to (logs, saved data, etc.).

        When frozen, _MEIPASS is a read-only temp directory that gets deleted
        on exit, so writable files are placed next to the .exe instead.
        """
        if getattr(sys, 'frozen', False):
            base = dirname(sys.executable)
        else:
            base = self.PROJECT_ROOT
        return join(base, relative_path)

    # ---------------------------------------------------------------------- #

    def load_stylesheet(self) -> str:
        """Load and cache the QSS stylesheet from the bundled assets."""
        if self.CACHED_STYLESHEET is None:
            try:
                with open(self.resource_path("styles.qss"), "r", encoding="utf-8") as f:
                    self.CACHED_STYLESHEET = f.read()
            except FileNotFoundError:
                self.CACHED_STYLESHEET = ""
        return self.CACHED_STYLESHEET

# ---------------------------------------------------------------------- #

APP_RESOURCES = AppResources()
