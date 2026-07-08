from PyQt6.QtWidgets import (
    QAbstractButton
)

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QColor, QPainter

# ---------------------------------------------------------------------- #
# Toggle geometry (all values in pixels)
#
# Widget size: 42 x 23 (fixed)
#
#   ┌──────────────────────────────────────────┐  y = 0
#   │ ╭────────────────────────────────────────╮│  y = 1   track_top = (23 - 20) // 2
#   │ │                                        ││
#   │ │  ╭──╮        TRACK (42 x 20)           ││  y = 3   thumb_top = (23 - 16) // 2
#   │ │  │  │        track_radius = 20 // 2    ││
#   │ │  ╰──╯        (fully rounded ends)      ││
#   │ │  thumb (16 x 16 circle)                ││  y = 19  thumb bottom
#   │ │                                        ││
#   │ ╰────────────────────────────────────────╯│  y = 21  track bottom
#   └──────────────────────────────────────────┘  y = 23
#
# Thumb position (4px inset from track edge):
#   OFF → thumb_left = 4 (snapped left)
#   ON  → thumb_left = 42 - 16 - 4 = 22 (snapped right)
#
# Colours:
#   State       │ Track   │ Thumb
#   ────────────┼─────────┼────────
#   Disabled    │ #CCCCCC │ #F0F0F0
#   OFF         │ #707070 │ #FFFFFF
#   ON          │ #0067C0 │ #FFFFFF
#
# Note: floor division (//) shifts track and thumb ~1px above true
# centre (1px gap above vs 2px below for the track, 3px vs 4px for
# the thumb).
# ---------------------------------------------------------------------- #

class ToggleSwitch(QAbstractButton):
    """A custom iOS-style toggle switch.
    Pass `interactive=False` to render it locked in the OFF position
    (used for INTRARE_DIN_PARTIDA_PROPRIE notices).
    """

    def __init__(self, interactive: bool = True, parent = None):
        """Initialize the switch: checkable, starts OFF, fixed widget size.
        When `interactive` is False, the switch is disabled and shows a
        forbidden cursor so the user cannot toggle it"""
        super().__init__(parent)
        self.setCheckable(True)
        self.setChecked(False)
        self._TOGGLE_WIDTH = 42
        self._TOGGLE_HEIGHT = 23
        self.setFixedSize(self._TOGGLE_WIDTH, self._TOGGLE_HEIGHT)
        self.setEnabled(interactive)
        self.setCursor(
            Qt.CursorShape.PointingHandCursor if interactive
            else Qt.CursorShape.ForbiddenCursor
        )

    # ---------------------------------------------------------------------- #

    def paintEvent(self, event) -> None:
        """Custom-draws the toggle each time Qt requests a repaint: a rounded
        track plus a circular thumb positioned left (OFF) or right (ON).
        Colours change based on enabled/checked state"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Compute geometry: center the 20px track and 16px thumb vertically.
        widget_width, widget_height = self.width(), self.height()
        track_height = 20
        track_top = (widget_height - track_height) // 2
        thumb_diameter = 16
        thumb_top = (widget_height - thumb_diameter) // 2

        # Pick colours: grey when disabled, blue when ON, dark grey when OFF.
        if not self.isEnabled():
            track_color = QColor("#CCCCCC")
            thumb_color = QColor("#F0F0F0")
        elif self.isChecked():
            track_color = QColor("#0067C0")
            thumb_color = QColor("#FFFFFF")
        else:
            track_color = QColor("#707070")
            thumb_color = QColor("#FFFFFF")

        # Draw the pill-shaped track (fully rounded ends).
        painter.setBrush(track_color)
        painter.setPen(Qt.PenStyle.NoPen)
        track_radius = track_height // 2
        painter.drawRoundedRect(0, track_top, widget_width, track_height, track_radius, track_radius)

        # Draw the thumb: snapped to the right edge when ON, left edge when OFF
        # (4px inset from the track edge on either side).
        thumb_left = widget_width - thumb_diameter - 4 if self.isChecked() else 4
        painter.setBrush(thumb_color)
        painter.drawEllipse(thumb_left, thumb_top, thumb_diameter, thumb_diameter)
        painter.end()

    # ---------------------------------------------------------------------- #

    def sizeHint(self) -> QSize:
        """Tells Qt's layout system the widget's preferred size (matches the
        fixed size set in __init__ so layouts reserve the correct space)"""
        return QSize(self._TOGGLE_WIDTH, self._TOGGLE_HEIGHT)
    


