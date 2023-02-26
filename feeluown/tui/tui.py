import logging
import os

from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import Layout, HSplit, VSplit
from prompt_toolkit.widgets import Box, Frame, TextArea, Button

from feeluown.consts import HOME_DIR
from feeluown.utils.logger import configure_global_logger


LOGFILE = os.path.join(HOME_DIR, 'tui.log')
logger = logging.getLogger(__name__)


# Layout for displaying hello world.
# (The frame creates the border, the box takes care of the margin/padding.)
root_container = HSplit([
    VSplit([
        Button('play', lambda: logger.info('play')),
        Button('pause', lambda: logger.info('pause')),
    ]),
    Box(
        Frame(
            TextArea(
                text="Hello world!\nPress control-c to quit.",
                width=40,
                height=10,
            )
        ),
    )
])
layout = Layout(container=root_container)


# Key bindings.
kb = KeyBindings()


@kb.add("c-c")
def _(event):
    "Quit when control-c is pressed."
    event.app.exit()


# Build a main application object.
application = Application(layout=layout, key_bindings=kb, full_screen=True)


def tuimain(_):
    configure_global_logger(to_file=LOGFILE)
    application.run()
