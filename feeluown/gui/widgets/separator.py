from typing import TYPE_CHECKING

from PyQt5.QtWidgets import QFrame

if TYPE_CHECKING:
    from feeluown.app.gui_app import GuiApp


stylesheet = '''
QFrame[frameShape="4"],
QFrame[frameShape="5"]
{{
    border: none;
    background: {};
}}
'''


class Separator(QFrame):
    def __init__(self, app: 'GuiApp', orientation='horizontal'):
        super().__init__(parent=None)

        self._app = app

        if orientation == 'horizontal':
            self.setFrameShape(QFrame.HLine)
        else:
            self.setFrameShape(QFrame.VLine)

        self.on_theme_changed(self._app.theme_mgr.theme)
        self._app.theme_mgr.theme_changed.connect(self.on_theme_changed)

    def on_theme_changed(self, theme):
        if theme == 'dark':
            self.setStyleSheet(stylesheet.format('#444'))
            if self.frameShape() == QFrame.HLine:
                self.setMaximumHeight(1)
            else:
                self.setMaximumWidth(1)
        else:
            self.setStyleSheet('')
            self.setFrameShadow(QFrame.Sunken)
            if self.frameShape() == QFrame.HLine:
                self.setMaximumHeight(2)
            else:
                self.setMaximumWidth(2)
