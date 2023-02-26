import logging
from typing import Callable
from prompt_toolkit.key_binding import KeyBindings

from prompt_toolkit.widgets import Button
from prompt_toolkit.formatted_text import (
    StyleAndTextTuples,
)
from prompt_toolkit.layout import (
    Margin, UIControl, UIContent, Window,
    WindowRenderInfo,
)
from prompt_toolkit.data_structures import Point

from .utils import right_elide_or_fill_text


logger = logging.getLogger(__name__)



class FButton(Button):

    def __init__(self, *args, height=3, **kwargs):
        super().__init__(*args, **kwargs)
        self.window.height = height

    def _get_text_fragments(self):
        fragments = super()._get_text_fragments()
        handler = fragments[0][-1]
        fragment = ('class:button', ' ' * self.width + '\n', handler)
        fragments.insert(0, fragment)
        fragments.append(fragment)
        return fragments


class TableControl(UIControl):
    def __init__(self, items):
        self.items = items
        self.current_row = 1
        self.columns = (0.4, 0.2, 0.25, 0.15)

    def reset(self) -> None:
        # Default reset. (Doesn't have to be implemented.)
        pass

    def preferred_width(self, max_available_width: int):
        return None

    def preferred_height(
        self,
        width: int,
        max_available_height: int,
        wrap_lines: bool,
        get_line_prefix,
    ):
        return None

    def is_focusable(self) -> bool:
        """
        Tell whether this user control is focusable.
        """
        return True

    def create_content(self, width: int, height: int):
        """
        Generate the content for this user control.

        Returns a :class:`.UIContent` instance.
        """
        col_widths = [max(int(ratio * width)-1, 0) for ratio in self.columns]
        logger.debug(f'column widths: {col_widths}, {sum(col_widths)}, {width}')

        def get_line(lineno) -> StyleAndTextTuples:
            item = self.items[lineno]
            text = ''
            i = 0
            while i < len(self.columns):
                text += right_elide_or_fill_text(item[i], col_widths[i]) + ' '
                i += 1
            return [("", text)]

        return UIContent(get_line,
                         len(self.items),
                         cursor_position=Point(0, self.current_row),
                         show_cursor=False)

    def mouse_handler(self, mouse_event):
        """
        Handle mouse events.

        When `NotImplemented` is returned, it means that the given event is not
        handled by the `UIControl` itself. The `Window` or key bindings can
        decide to handle this event as scrolling or changing focus.

        :param mouse_event: `MouseEvent` instance.
        """
        return NotImplemented

    def move_cursor_down(self) -> None:
        """
        Request to move the cursor down.
        This happens when scrolling down and the cursor is completely at the
        top.
        """

    def move_cursor_up(self) -> None:
        """
        Request to move the cursor up.
        """

    def focus_next(self):
        logger.debug('focus next')
        self.current_row = (self.current_row + 1) % len(self.items)

    def focus_previous(self):
        logger.debug('focus previous')
        self.current_row = (self.current_row - 1) % len(self.items)

    def get_key_bindings(self):
        """
        The key bindings that are specific for this user control.

        Return a :class:`.KeyBindings` object if some key bindings are
        specified, or `None` otherwise.
        """
        kb = KeyBindings()

        kb.add('j')(lambda _: self.focus_next())
        kb.add('k')(lambda _: self.focus_previous())

        return kb

    def get_invalidate_events(self):
        """
        Return a list of `Event` objects. This can be a generator.
        (The application collects all these events, in order to bind redraw
        handlers to these events.)
        """
        return []


class TableMargin(Margin):
    arrow = '-> '

    def get_width(self, get_ui_content: Callable[[], UIContent]) -> int:
        """
        Return the width that this margin is going to consume.

        :param get_ui_content: Callable that asks the user control to create
            a :class:`.UIContent` instance. This can be used for instance to
            obtain the number of lines.
        """
        return len(self.arrow)

    def create_margin(
        self, window_render_info: WindowRenderInfo, width: int, height: int
    ) -> StyleAndTextTuples:
        """
        Creates a margin.
        This should return a list of (style_str, text) tuples.

        :param window_render_info:
            :class:`~prompt_toolkit.layout.containers.WindowRenderInfo`
            instance, generated after rendering and copying the visible part of
            the :class:`~prompt_toolkit.layout.controls.UIControl` into the
            :class:`~prompt_toolkit.layout.containers.Window`.
        :param width: The width that's available for this margin. (As reported
            by :meth:`.get_width`.)
        :param height: The height that's available for this margin. (The height
            of the :class:`~prompt_toolkit.layout.containers.Window`.)
        """
        current_row = window_render_info.ui_content.cursor_position.y
        total_row = window_render_info.ui_content.line_count
        l: StyleAndTextTuples = [('', '\n')] * total_row
        l[current_row] = ('fg:cyan', self.arrow)
        return l

class FTable:
    def __init__(self):
        self.control = TableControl([
            ('暧昧', '王菲', '菲主打', '01:34'),
            ('等你等到我心痛', '张学友', '精选', '02:34'),
        ])
        self.window = Window(
            self.control,
            left_margins=[TableMargin()]
        )

    def __pt_container__(self):
        return self.window
