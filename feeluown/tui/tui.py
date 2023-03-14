import logging
import os

from prompt_toolkit.application import Application, get_app
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import (
    DynamicContainer, Layout, HSplit, VSplit, Window, ConditionalContainer,
)
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import Box, Frame, Button, TextArea

from feeluown.consts import HOME_DIR
from feeluown.utils.logger import configure_global_logger
from .widgets import FButton, FTable


LOGFILE = os.path.join(HOME_DIR, 'tui.log')
logger = logging.getLogger(__name__)


STYLE = Style([
    ('button', 'bg:green'),
])


def landscape_orientation() -> bool:
    size = get_app().output.get_size()
    return size.rows * 2 < size.columns

def portrait_orientation():
    return not landscape_orientation()


# Layout for displaying hello world.
# (The frame creates the border, the box takes care of the margin/padding.)
root_container = HSplit([
    FTable(),
    ConditionalContainer(
        HSplit([
            Window(),
            VSplit([
                Window(),
                FButton('previous', lambda: logger.info('previous')),
                Window(),
                FButton('play', lambda: logger.info('play')),
                Window(),
                FButton('next', lambda: logger.info('next')),
                Window(),
            ]),
        ]),
        landscape_orientation,
    ),
])

layout = Layout(
    container=root_container,
    focused_element=root_container.children[-1],
)


# Key bindings.
kb = KeyBindings()


@kb.add("q")
def _(event):
    "Quit when control-c is pressed."
    event.app.exit()


@kb.add('tab')
def _(event):
    event.app.layout.focus_next()


class App(Application):
    def _on_resize(self):
        super()._on_resize()


# Build a main application object.
application = Application(layout=layout,
                          key_bindings=kb,
                          style=STYLE,
                          full_screen=True,
                          mouse_support=True)


def tuimain(_):
    configure_global_logger(2, to_file=LOGFILE)
    application.run()
