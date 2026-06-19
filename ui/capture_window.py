from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QCloseEvent, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

import config
import parser as notes_parser
import storage


class CaptureWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("书痕 - BookTrace")
        self.setFixedSize(680, 560)
        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        self._view_book_callback: Callable[[str], None] | None = None

        self.book_input = QLineEdit()
        self.book_input.setObjectName("bookInput")
        self.book_input.setPlaceholderText("比如：沙丘")
        self.book_input.setText(config.get_last_book())
        self.book_input.setFixedHeight(44)
        self.book_error_label = QLabel("请先写下书名")
        self.book_error_label.setObjectName("ErrorLabel")
        self.book_error_label.hide()
        self.trace_info_label = QLabel("")
        self.trace_info_label.setObjectName("TraceInfo")
        self.view_trace_button = QPushButton("查看")
        self.view_trace_button.setObjectName("InlineLinkButton")
        self.view_trace_button.setCursor(Qt.PointingHandCursor)

        self.thought_input = QTextEdit()
        self.thought_input.setObjectName("thoughtInput")
        self.thought_input.setPlaceholderText("刚刚想到什么？")
        self.thought_input.setFixedHeight(130)
        self.thought_error_label = QLabel("请先写下这一念")
        self.thought_error_label.setObjectName("ErrorLabel")
        self.thought_error_label.hide()

        self.save_button = QPushButton("保存")
        self.save_button.setObjectName("PrimaryButton")
        self.save_button.setFixedWidth(130)
        self.cancel_button = QPushButton("取消")
        self.cancel_button.setObjectName("SecondaryButton")
        self.cancel_button.setFixedWidth(110)
        self.status_label = QLabel("")
        self.status_label.setObjectName("StatusLabel")

        self._build_ui()
        self._connect_signals()
        self._install_shortcuts()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(36, 36, 36, 36)

        card = QFrame()
        card.setObjectName("Card")
        root.addWidget(card)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(32, 30, 32, 28)
        layout.setSpacing(10)

        title = QLabel("记一念")
        title.setObjectName("Title")
        layout.addWidget(title)

        subtitle = QLabel("把刚刚闪过的想法留下来")
        subtitle.setObjectName("Subtitle")
        layout.addWidget(subtitle)

        book_label = QLabel("正在读")
        book_label.setObjectName("FieldLabel")
        layout.addSpacing(4)
        layout.addWidget(book_label)
        layout.addWidget(self.book_input)
        layout.addWidget(self.book_error_label)
        trace_row = QHBoxLayout()
        trace_row.setSpacing(6)
        trace_row.addWidget(self.trace_info_label)
        trace_row.addWidget(self.view_trace_button)
        trace_row.addStretch(1)
        layout.addLayout(trace_row)

        thought_label = QLabel("此刻想到")
        thought_label.setObjectName("FieldLabel")
        layout.addSpacing(10)
        layout.addWidget(thought_label)
        layout.addWidget(self.thought_input)
        layout.addWidget(self.thought_error_label)
        layout.addSpacing(10)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(16)
        button_layout.addStretch(1)
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.save_button)
        layout.addLayout(button_layout)

        layout.addWidget(self.status_label)

    def _connect_signals(self) -> None:
        self.view_trace_button.clicked.connect(self.open_current_book_note)
        self.save_button.clicked.connect(self.save)
        self.cancel_button.clicked.connect(self.hide)
        self.book_input.textChanged.connect(self._clear_book_error)
        self.book_input.textChanged.connect(self._refresh_trace_info)
        self.thought_input.textChanged.connect(self._clear_thought_error)

    def _install_shortcuts(self) -> None:
        save_return = QShortcut(QKeySequence("Ctrl+Return"), self)
        save_return.activated.connect(self.save)

        save_enter = QShortcut(QKeySequence("Ctrl+Enter"), self)
        save_enter.activated.connect(self.save)

        cancel = QShortcut(QKeySequence("Esc"), self)
        cancel.activated.connect(self.hide)

        focus_book = QShortcut(QKeySequence("Ctrl+L"), self)
        focus_book.activated.connect(self._focus_book_input)

        clear_thought = QShortcut(QKeySequence("Ctrl+K"), self)
        clear_thought.activated.connect(self.thought_input.clear)

    def show_capture(self) -> None:
        self.status_label.clear()
        self.book_input.setText(config.get_last_book())
        self._refresh_trace_info()
        self.show()
        self.raise_()
        self.activateWindow()
        self.thought_input.setFocus()

    def save(self) -> None:
        book = self.book_input.text().strip()
        thought = self.thought_input.toPlainText().strip()

        if not book:
            self._show_book_error("请先写下书名")
            self.book_input.setFocus()
            return
        if not thought:
            self._show_thought_error("请先写下这一念")
            self.thought_input.setFocus()
            return

        try:
            storage.save_thought(book, thought)
            config.set_last_book(book)
        except Exception as exc:  # noqa: BLE001 - show a user-facing error in the UI.
            self._set_status(f"没能保存这条书痕：{exc}", "error")
            return

        self.thought_input.clear()
        self._refresh_trace_info()
        self._set_status(f"已保存到《{book}》", "success")
        QTimer.singleShot(1000, self.hide)
        QTimer.singleShot(1200, self._clear_status)

    def open_current_book_note(self) -> None:
        book = self.book_input.text().strip()
        if not book:
            self._show_book_error("请先写下书名")
            self.book_input.setFocus()
            return

        if self._view_book_callback is not None:
            self._view_book_callback(book)
            return

        self._set_status("书架还没有准备好", "error")

    def _focus_book_input(self) -> None:
        self.book_input.setFocus()
        self.book_input.selectAll()

    def _clear_status(self) -> None:
        self.status_label.clear()
        self.status_label.setProperty("state", "")
        self._refresh_style(self.status_label)

    def set_view_book_callback(self, callback: Callable[[str], None]) -> None:
        self._view_book_callback = callback

    def prompt_for_book(self) -> None:
        self.show_capture()
        self._show_book_error("请先写下书名")
        self.book_input.setFocus()

    def _refresh_trace_info(self) -> None:
        book = self.book_input.text().strip()
        if not book:
            self.trace_info_label.setText("输入书名后查看书痕")
            self.view_trace_button.setEnabled(False)
            return

        count = 0
        try:
            path = storage.get_book_note_path(book)
            if path.exists():
                count = len(notes_parser.parse_book_notes(path))
        except ValueError:
            count = 0

        if count:
            self.trace_info_label.setText(f"已留下 {count} 条书痕")
        else:
            self.trace_info_label.setText("还没有留下这本书的书痕")
        self.view_trace_button.setEnabled(True)

    def _show_book_error(self, text: str) -> None:
        self.book_error_label.setText(text)
        self.book_error_label.show()
        self._set_input_error(self.book_input, True)

    def _show_thought_error(self, text: str) -> None:
        self.thought_error_label.setText(text)
        self.thought_error_label.show()
        self._set_input_error(self.thought_input, True)

    def _clear_book_error(self) -> None:
        self.book_error_label.hide()
        self._set_input_error(self.book_input, False)

    def _clear_thought_error(self) -> None:
        self.thought_error_label.hide()
        self._set_input_error(self.thought_input, False)

    def _set_input_error(self, widget: QWidget, has_error: bool) -> None:
        widget.setProperty("hasError", has_error)
        self._refresh_style(widget)

    def _set_status(self, text: str, state: str) -> None:
        self.status_label.setText(text)
        self.status_label.setProperty("state", state)
        self._refresh_style(self.status_label)

    def _refresh_style(self, widget: QWidget) -> None:
        widget.style().unpolish(widget)
        widget.style().polish(widget)

    def closeEvent(self, event: QCloseEvent) -> None:
        event.ignore()
        self.hide()
