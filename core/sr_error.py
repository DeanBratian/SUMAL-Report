class SRError(Exception):
    """
    Raised when the application encounters an unrecoverable error that must
    stop the current operation and surface a message to the user.

    Attributes
    ----------
    message : Human-readable explanation shown in the dialog body.
    title: Dialog window title (default: "Eroare").
    """

    def __init__(self, message: str, title: str = "Eroare"):
        super().__init__(message)
        self.message = message
        self.title = title

    # ---------------------------------------------------------------------- #

    def __str__(self) -> str:
        return f"[{self.title}] {self.message}"