from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout

from feeluown.gui.widgets.selfpaint_btn import HomeButton2, StarButton2
from feeluown.gui.components import Avatar


class Navbar(QWidget):
    def __init__(self, app, parent=None) -> None:
        super().__init__(parent)

        self._app = app

        self._layout = QVBoxLayout(self)
        spacing = 6
        self._layout.setContentsMargins(spacing, spacing, spacing, 0)
        self._layout.setSpacing(spacing)
        self._layout.addWidget(HomeButton2(length=48), alignment=Qt.AlignHCenter)
        self._layout.addWidget(StarButton2(length=48), alignment=Qt.AlignHCenter)
        self._layout.addWidget(Avatar(self._app, length=48), alignment=Qt.AlignHCenter)
        self._layout.addStretch(0)
        self.setFixedWidth(60)
