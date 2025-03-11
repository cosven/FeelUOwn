import json
import logging
from typing import TYPE_CHECKING, cast, List
from dataclasses import dataclass

from openai import AsyncOpenAI
from PyQt5.QtCore import QEvent, QSize, Qt
from PyQt5.QtGui import QResizeEvent, QColor, QPainter
from PyQt5.QtWidgets import (
    QHBoxLayout, QVBoxLayout, QWidget, QLabel, QScrollArea, QPlainTextEdit,
    QFrame, QTextEdit,
)
from PyQt5.QtGui import QTextOption

from feeluown.ai import a_handle_stream
from feeluown.utils.aio import run_afn_ref
from feeluown.library import fmt_artists_names
from feeluown.library.text2song import create_dummy_brief_song
from feeluown.gui.helpers import esc_hide_widget
from feeluown.gui.widgets.textbtn import TextButton
from feeluown.gui.widgets.header import MidHeader


if TYPE_CHECKING:
    from feeluown.app.gui_app import GuiApp

logger = logging.getLogger(__name__)


QUERY_PROMPT = '''你是一个音乐播放器助手。'''
EXTRACT_PROMPT = '''\
提取歌曲信息，歌手名为空的话，你需要补全，每首歌一行 JSON，用类似下面这样的格式返回
    {"title": "t1", "artists": ["a1", "a11"], "description": "推荐理由1"}
    {"title": "t2", "artists": ["a11"], "description": "推荐理由2"}

注意，你返回的内容只应该有几行 JSON，其它信息都不需要。也不要用 markdown 格式返回。
'''


@dataclass
class ChatContext:
    client: AsyncOpenAI
    messages: List


class AIChatOverlay(QWidget):
    def __init__(self, app: 'GuiApp', parent=None):
        super().__init__(parent=parent)
        self._app = app

        self.body = Body(app, self)
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(100, 80, 100, 80)
        self._layout.addWidget(self.body)
        self.setFocusPolicy(Qt.ClickFocus)
        # Add ClickFocus for the body so that when Overlay will not
        # get focus when user click the body.
        self.body.setFocusPolicy(Qt.ClickFocus)
        esc_hide_widget(self)

    def paintEvent(self, a0):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 100))

    def showEvent(self, e):
        self.resize(self._app.size())
        super().showEvent(e)
        self.raise_()

    def eventFilter(self, obj, event):
        if self.isVisible() and obj is self._app and event.type() == QEvent.Resize:
            event = cast(QResizeEvent, event)
            self.resize(event.size())
        return False

    def focusInEvent(self, event):
        self.hide()
        super().focusInEvent(event)


class Body(QWidget):
    def __init__(self, app: 'GuiApp', parent=None):
        super().__init__(parent=parent)
        self._app = app

        # 对话历史显示区域
        self._history_area = QScrollArea(self)
        self._history_area.setFrameShape(QFrame.NoFrame)
        self._history_widget = QWidget()
        self._history_layout = QVBoxLayout(self._history_widget)
        self._history_layout.setContentsMargins(0, 0, 0, 0)
        self._history_layout.setSpacing(5)
        self._history_area.setWidget(self._history_widget)
        self._history_area.setWidgetResizable(True)

        # 用户输入区域
        self._input_area = QScrollArea(self)
        self._input_area.setFrameShape(QFrame.NoFrame)
        self._editor = QPlainTextEdit(self)
        self._editor.setPlaceholderText(
            '在这里输入你的问题...\n\n'
            '例如：推荐一些周杰伦的经典歌曲'
        )
        self._editor.setFrameShape(QFrame.NoFrame)
        self._input_area.setWidget(self._editor)
        self._msg_label = QLabel(self)
        self._msg_label.setWordWrap(True)
        self._hide_btn = TextButton('关闭窗口', self)
        self._extract_and_play_btn = TextButton('提取歌曲并播放', self)
        self._extract_10_and_play_btn = TextButton('提取10首并播放', self)
        self._send_btn = TextButton('发送', self)
        self._clear_history_btn = TextButton('清空对话', self)

        self.setup_ui()
        self._hide_btn.clicked.connect(self._hide)
        self._extract_and_play_btn.clicked.connect(
            lambda: run_afn_ref(self.extract_and_play))
        self._extract_10_and_play_btn.clicked.connect(
            lambda: run_afn_ref(self.extract_10_and_play))
        self._send_btn.clicked.connect(
            lambda: run_afn_ref(self.exec_user_query, self._editor.toPlainText()))
        self._clear_history_btn.clicked.connect(self.clear_history)

        self._chat_context = None
        self.setAutoFillBackground(True)

    def setup_ui(self):
        self._msg_label.setWordWrap(True)
        self._input_area.setWidgetResizable(True)
        self._app.installEventFilter(self)
        self._msg_label.setTextFormat(Qt.RichText)

        self._root_layout = QVBoxLayout(self)
        self._layout = QHBoxLayout()
        self._v_layout = QVBoxLayout()
        self._btn_layout = QVBoxLayout()

        self._root_layout.addWidget(MidHeader('AI 助手'))
        self._root_layout.addLayout(self._layout)
        self._layout.addStretch(0)
        self._layout.addLayout(self._v_layout)
        self._layout.setStretch(1, 1)
        self._layout.addLayout(self._btn_layout)
        self._layout.addStretch(0)
        self._root_layout.setContentsMargins(10, 10, 10, 10)
        self._root_layout.setSpacing(10)

        # 调整布局，增加对话历史区域
        self._v_layout.addWidget(self._history_area, stretch=3)
        self._v_layout.addWidget(self._input_area, stretch=1)
        self._v_layout.addWidget(self._msg_label)
        self._btn_layout.addWidget(self._extract_and_play_btn)
        self._btn_layout.addWidget(self._extract_10_and_play_btn)
        self._btn_layout.addWidget(self._send_btn)
        self._btn_layout.addWidget(self._clear_history_btn)
        self._btn_layout.addWidget(self._hide_btn)
        self._btn_layout.addStretch(0)

    def _add_message_to_history(self, role, content):
        """将消息添加到对话历史"""
        label = QLabel()
        label.setText(content)
        label.setWordWrap(True)
        label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        label.setFrameStyle(QFrame.NoFrame)
        if role == 'user':
            label.setPalette(self.palette())
            label.setAutoFillBackground(True)
            pal = label.palette()
            pal.setColor(pal.Background, pal.color(pal.Highlight))
            pal.setColor(pal.Foreground, pal.color(pal.HighlightedText))
            label.setPalette(pal)
        else:
            label.setPalette(self.palette())
            label.setAutoFillBackground(True)
            pal = label.palette() 
            pal.setColor(pal.Background, pal.color(pal.Base))
            pal.setColor(pal.Foreground, pal.color(pal.Text))
            label.setPalette(pal)
            
        label.setStyleSheet("""
            padding: 8px;
            border-radius: 4px;
            margin: 4px;
        """)
        
        if role == 'user':
            label.setAlignment(Qt.AlignRight)
        else:
            label.setAlignment(Qt.AlignLeft)
        
        self._history_layout.addWidget(label)
        # 滚动到底部
        self._history_area.verticalScrollBar().setValue(
            self._history_area.verticalScrollBar().maximum()
        )

    async def exec_user_query(self, query):
        self.set_msg('等待 AI 返回中...', level='hint')
        client = self._app.ai.get_async_client()
        
        # 添加用户消息到历史
        self._add_message_to_history('user', query)
        
        # 初始化或更新对话上下文
        if self._chat_context is None:
            messages = [
                {'role': 'system', 'content': QUERY_PROMPT},
                {'role': 'user', 'content': query}
            ]
            self._chat_context = ChatContext(client, messages)
        else:
            messages = self._chat_context.messages
            messages.append({'role': 'user', 'content': query})
        
        try:
            stream = await client.chat.completions.create(
                model=self._app.config.OPENAI_MODEL,
                messages=messages,
                stream=True,
            )
        except Exception as e:  # noqa
            self.set_msg(f'调用 AI 接口失败: {e}', level='err')
            logger.exception('AI request failed')
        else:
            # 创建AI回复的标签
            ai_label = QLabel()
            ai_label.setWordWrap(True)
            ai_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            ai_label.setFrameStyle(QFrame.NoFrame)
            ai_label.setPalette(self.palette())
            ai_label.setAutoFillBackground(True)
            pal = ai_label.palette()
            pal.setColor(pal.Background, pal.color(pal.Base))
            pal.setColor(pal.Foreground, pal.color(pal.Text))
            ai_label.setPalette(pal)
            
            ai_label.setStyleSheet("""
                padding: 8px;
                border-radius: 4px;
                margin: 4px;
            """)
            ai_label.setAlignment(Qt.AlignLeft)
            self._history_layout.addWidget(ai_label)
            
            content = ''
            async for chunk in stream:
                self.set_msg('AI 返回中...', level='hint')
                delta_content = chunk.choices[0].delta.content or ''
                content += delta_content
                # 实时更新AI回复内容
                ai_label.setText(content)
                # 滚动到底部
                self._history_area.verticalScrollBar().setValue(
                    self._history_area.verticalScrollBar().maximum()
                )
            
            # 更新对话上下文
            assistant_message = {"role": "assistant", "content": content}
            self._chat_context.messages.append(assistant_message)
            self.set_msg('AI 内容返回结束', level='hint')
            
            # 清空输入框
            self._editor.clear()

    def show_chat_message(self, text):
        """这个方法现在只用于显示AI返回的流式内容"""
        pass

    def set_msg(self, text, level='hint'):
        if level == 'hint':
            color = 'green'
        elif level == 'warn':
            color = 'yellow'
        else:  # err
            color = 'magenta'
        self._msg_label.setText(f'<span style="color: {color}">{text}</span>')

    async def extract_and_play(self):
        await self._extract_and_play(EXTRACT_PROMPT)

    async def extract_10_and_play(self):
        await self._extract_and_play(f'{EXTRACT_PROMPT}\n随机提取最多10首即可')

    async def _extract_and_play(self, extract_prompt):
        if self._chat_context is None:
            self._chat_context = ChatContext(
                client=self._app.ai.get_async_client(),
                messages=[
                    {'role': 'system', 'content': extract_prompt},
                    {'role': 'user', 'content': self._editor.toPlainText()},
                ],
            )
        else:
            message = {'role': 'user', 'content': extract_prompt}
            self._chat_context.messages.append(message)
        self.set_msg('正在让 AI 解析歌曲信息，这可能会花费一些时间...')
        try:
            stream = await self._chat_context.client.chat.completions.create(
                model=self._app.config.OPENAI_MODEL,
                messages=self._chat_context.messages,
                stream=True,
            )
        except Exception as e:  # noqa
            self.set_msg(f'调用 AI 接口失败: {e}', level='err')
            logger.exception('AI request failed')
            return

        rr, rw, wtask = await a_handle_stream(stream)
        ok_count = 0
        fail_count = 0
        while True:
            try:
                line = await rr.readline()
                line = line.decode('utf-8')
                logger.debug(f'read a line: {line}')
                if not line:
                    self.set_msg(f'解析结束，成功解析{ok_count}首歌曲，失败{fail_count}首歌。',
                                 level='hint')
                    break
                try:
                    jline = json.loads(line)
                    title, artists = jline['title'], jline['artists']
                    artists_name = fmt_artists_names(artists)
                except:  # noqa
                    fail_count += 1
                    logger.exception(f'failed to parse a line: {line}')
                    self.set_msg(f'成功解析{ok_count}首歌曲，失败{fail_count}首歌',
                                 level='yellow')
                else:
                    song = create_dummy_brief_song(title, artists_name)
                    ok_count += 1
                    self.set_msg(f'成功解析{ok_count}首歌曲，失败{fail_count}首歌',
                                 level='hint')
                    self._app.playlist.add(song)
                    if ok_count == 1:
                        self._app.playlist.play_model(song)
            except:  # noqa
                logger.exception('extract and play failed')
                break

        await wtask
        rw.close()
        await rw.wait_closed()

    def clear_history(self):
        """清空对话历史"""
        while self._history_layout.count():
            item = self._history_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self._chat_context = None

    def _hide(self):
        self.clear_history()
        self.parent().hide()

    def hide(self):
        self._hide()
        super().hide()


if __name__ == '__main__':
    import os
    from PyQt5.QtWidgets import QWidget
    from feeluown.gui.debug import simple_layout, mock_app

    with simple_layout(theme='dark') as layout, mock_app() as app:
        app.size.return_value = QSize(600, 400)
        app.config.OPENAI_API_KEY = os.environ.get('DEEPSEEK_API_KEY')
        app.config.OPENAI_API_BASEURL = 'https://api.deepseek.com'
        app.config.OPENAI_MODEL = 'deepseek-chat'
        widget = AIChatOverlay(app)
        widget.resize(600, 400)
        layout.addWidget(widget)
        widget.show()
        widget.body.show_chat_message('Hello, feeluown!' * 100)
        widget.body.set_msg('error', level='err')
