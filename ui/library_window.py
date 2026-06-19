from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

import parser as notes_parser
import storage
from ui.memory_dialog import MemoryDialog


class LibraryWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("书架 - BookTrace")
        self.resize(860, 560)
        self.book_cards: dict[str, QFrame] = {}
        self.selected_path = ""
        self.memory_dialog = MemoryDialog(self)

        self.page_title = QLabel("书架")
        self.page_title.setObjectName("Title")
        self.page_summary = QLabel("所有留下过书痕的书")
        self.page_summary.setObjectName("Subtitle")

        self.book_list = QListWidget()
        self.book_list.setObjectName("bookList")
        self.book_list.setFixedWidth(340)
        self.book_list.setSpacing(18)

        self.detail_title = QLabel("还没有留下书痕")
        self.detail_title.setObjectName("LibraryDetailTitle")
        self.detail_summary = QLabel("")
        self.detail_summary.setObjectName("Subtitle")

        self.random_button = QPushButton("随机回忆")
        self.random_button.setObjectName("SecondaryButton")

        self.detail_body = QWidget()
        self.detail_body.setObjectName("thoughtList")
        self.detail_layout = QVBoxLayout(self.detail_body)
        self.detail_layout.setContentsMargins(0, 0, 0, 0)
        self.detail_layout.setSpacing(10)
        self.detail_layout.addStretch(1)

        scroll = QScrollArea()
        scroll.setObjectName("thoughtScroll")
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.detail_body)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(12)

        header = QHBoxLayout()
        header.addWidget(self.detail_title, stretch=1)
        right_layout.addLayout(header)
        right_layout.addWidget(self.detail_summary)
        right_layout.addWidget(scroll, stretch=1)

        root = QVBoxLayout(self)
        root.setContentsMargins(36, 34, 36, 36)
        root.setSpacing(18)

        title_block = QVBoxLayout()
        title_block.setSpacing(6)
        title_block.addWidget(self.page_title)
        title_block.addWidget(self.page_summary)

        page_header = QHBoxLayout()
        page_header.addLayout(title_block)
        page_header.addStretch(1)
        page_header.addWidget(self.random_button)
        root.addLayout(page_header)

        body = QHBoxLayout()
        body.setSpacing(40)
        body.addWidget(self.book_list)
        body.addWidget(right, stretch=1)
        root.addLayout(body, stretch=1)

        self.book_list.itemClicked.connect(self._select_book)
        self.book_list.itemDoubleClicked.connect(self._open_book_note)
        self.random_button.clicked.connect(self.memory_dialog.show_random)
        self.refresh()

    def refresh(self) -> None:
        self.book_list.clear()
        self.book_cards.clear()
        self.selected_path = ""
        books = notes_parser.list_books()
        total_thoughts = sum(book.thought_count for book in books)
        self.page_summary.setText(f"{len(books)} 本书 · {total_thoughts} 条书痕")

        if not books:
            self.detail_title.setText("还没有留下书痕")
            self.detail_summary.setText("")
            self._clear_thoughts("按 Ctrl + Alt + N 记下第一念。")
            return

        for book in books:
            item = QListWidgetItem()
            item.setData(Qt.UserRole, str(book.path))
            card = self._book_card(book.title, book.thought_count)
            item.setSizeHint(card.sizeHint())
            self.book_list.addItem(item)
            self.book_list.setItemWidget(item, card)
            self.book_cards[str(book.path)] = card

        self.book_list.setCurrentRow(0)
        self._show_book(books[0].title, books[0].path)

    def show_library(self) -> None:
        self.refresh()
        self.show()
        self.raise_()
        self.activateWindow()

    def show_book(self, title: str) -> bool:
        book_title = title.strip()
        self.refresh()
        self.show()
        self.raise_()
        self.activateWindow()

        if not book_title:
            return False

        for row in range(self.book_list.count()):
            item = self.book_list.item(row)
            path = Path(item.data(Qt.UserRole))
            for book in notes_parser.list_books():
                if book.path == path and book.title == book_title:
                    self.book_list.setCurrentRow(row)
                    self._show_book(book.title, book.path)
                    return True

        self.book_list.clearSelection()
        self._mark_selected(None)
        self.detail_title.setText(f"《{book_title}》")
        self.detail_summary.setText("还没有留下这本书的书痕")
        self._clear_thoughts("写下一条感想后，它会出现在这里。")
        return False

    def _select_book(self, item: QListWidgetItem) -> None:
        path = Path(item.data(Qt.UserRole))
        title = path.stem
        for book in notes_parser.list_books():
            if book.path == path:
                title = book.title
                break
        self._show_book(title, path)

    def _show_book(self, title: str, path: Path) -> None:
        self._mark_selected(path)
        self.detail_title.setText(f"《{title}》")
        thoughts = notes_parser.parse_book_notes(path)

        if not thoughts:
            self.detail_summary.setText("0 条书痕")
            self._clear_thoughts("这本书还没有具体感想。")
            return

        latest = thoughts[-1]
        self.detail_summary.setText(f"{len(thoughts)} 条书痕 · 最近记录：{latest.date} {latest.time}")
        self._clear_thoughts()
        for thought in reversed(thoughts):
            self.detail_layout.insertWidget(0, self._thought_card(thought))

    def _clear_thoughts(self, empty_text: str = "") -> None:
        while self.detail_layout.count():
            item = self.detail_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        if empty_text:
            label = QLabel(empty_text)
            label.setObjectName("emptyText")
            label.setWordWrap(True)
            self.detail_layout.addWidget(label)
        self.detail_layout.addStretch(1)

    def _book_card(self, title: str, thought_count: int) -> QWidget:
        card = QFrame()
        card.setObjectName("bookCard")
        card.setProperty("selected", False)

        layout = QHBoxLayout(card)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        stripe = QFrame()
        stripe.setObjectName("bookStripe")
        stripe.setProperty("selected", False)
        stripe.setFixedWidth(5)
        layout.addWidget(stripe)

        text_area = QWidget()
        text_layout = QVBoxLayout(text_area)
        text_layout.setContentsMargins(14, 12, 14, 12)

        title_label = QLabel(title)
        title_label.setObjectName("bookCardTitle")
        title_label.setWordWrap(True)

        count_label = QLabel(f"{thought_count} 条感想")
        count_label.setObjectName("bookCardCount")

        text_layout.addWidget(title_label)
        text_layout.addWidget(count_label)
        layout.addWidget(text_area, stretch=1)
        return card

    def _thought_card(self, thought: notes_parser.Thought) -> QWidget:
        card = QFrame()
        card.setObjectName("thoughtCard")
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)

        meta = QLabel(f"{thought.date} {thought.time}")
        meta.setObjectName("thoughtMeta")

        content = QLabel(thought.content)
        content.setObjectName("thoughtContent")
        content.setWordWrap(True)
        content.setTextInteractionFlags(Qt.TextSelectableByMouse)

        layout.addWidget(meta)
        layout.addWidget(content)
        return card

    def _mark_selected(self, path: Path | None) -> None:
        self.selected_path = str(path) if path is not None else ""
        for card_path, card in self.book_cards.items():
            selected = card_path == self.selected_path
            card.setProperty("selected", selected)
            card.style().unpolish(card)
            card.style().polish(card)
            stripe = card.findChild(QFrame, "bookStripe")
            if stripe is not None:
                stripe.setProperty("selected", selected)
                stripe.style().unpolish(stripe)
                stripe.style().polish(stripe)

    def _open_book_note(self, item: QListWidgetItem) -> None:
        path = Path(item.data(Qt.UserRole))
        if path.exists():
            storage.open_path(path)
