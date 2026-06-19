from __future__ import annotations

import random

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

import parser as notes_parser


class MemoryDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("随机回忆 - BookTrace")
        self.setObjectName("MemoryDialog")
        self.setModal(False)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFixedSize(560, 360)
        self._current_key: tuple[str, str, str, str] | None = None

        self.title_label = QLabel("随机回忆")
        self.title_label.setObjectName("Title")

        self.book_label = QLabel("")
        self.book_label.setObjectName("MemoryBook")
        self.book_label.setWordWrap(True)

        self.content_label = QLabel("")
        self.content_label.setObjectName("MemoryContent")
        self.content_label.setWordWrap(True)
        self.content_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self.meta_label = QLabel("")
        self.meta_label.setObjectName("MemoryMeta")

        self.again_button = QPushButton("再来一条")
        self.again_button.setObjectName("SecondaryButton")
        self.close_button = QPushButton("收起")
        self.close_button.setObjectName("PrimaryButton")

        self._build_ui()
        self.again_button.clicked.connect(self.load_random)
        self.close_button.clicked.connect(self.close)

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(22, 22, 22, 22)

        card = QFrame()
        card.setObjectName("MemoryCard")
        root.addWidget(card)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(32, 30, 32, 28)
        card_layout.setSpacing(16)

        card_layout.addWidget(self.title_label)
        card_layout.addWidget(self.book_label)

        quote_row = QHBoxLayout()
        quote_row.setSpacing(14)
        quote_mark = QFrame()
        quote_mark.setObjectName("QuoteStripe")
        quote_mark.setFixedWidth(4)
        quote_row.addWidget(quote_mark)
        quote_row.addWidget(self.content_label, stretch=1)
        card_layout.addLayout(quote_row, stretch=1)

        card_layout.addWidget(self.meta_label)

        buttons = QHBoxLayout()
        buttons.setSpacing(12)
        buttons.addStretch(1)
        buttons.addWidget(self.again_button)
        buttons.addWidget(self.close_button)
        card_layout.addLayout(buttons)

    def show_random(self) -> None:
        self.load_random()
        self.show()
        self.raise_()
        self.activateWindow()

    def load_random(self) -> None:
        choices = self._all_choices()
        if not choices:
            self.book_label.setText("")
            self.content_label.setText("还没有留下书痕。")
            self.meta_label.setText("")
            self.again_button.hide()
            return

        self.again_button.show()
        self.again_button.setEnabled(len(choices) > 1)
        if len(choices) > 1 and self._current_key is not None:
            choices = [choice for choice in choices if self._choice_key(choice) != self._current_key]

        book_title, thought = random.choice(choices)
        self._current_key = self._choice_key((book_title, thought))
        self.book_label.setText(f"《{book_title}》")
        self.content_label.setText(thought.content)
        self.meta_label.setText(f"{thought.date} {thought.time}")

    def _all_choices(self) -> list[tuple[str, notes_parser.Thought]]:
        choices: list[tuple[str, notes_parser.Thought]] = []
        for book in notes_parser.list_books():
            choices.extend((book.title, thought) for thought in notes_parser.parse_book_notes(book.path))
        return choices

    def _choice_key(self, choice: tuple[str, notes_parser.Thought]) -> tuple[str, str, str, str]:
        book_title, thought = choice
        return (book_title, thought.date, thought.time, thought.content)
