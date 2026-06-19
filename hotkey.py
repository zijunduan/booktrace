from __future__ import annotations

from PySide6.QtCore import QObject, Signal


class HotkeyManager(QObject):
    triggered = Signal()
    library_triggered = Signal()
    memory_triggered = Signal()
    current_book_triggered = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._listener = None

    def start(self) -> bool:
        if self._listener is not None:
            return True

        try:
            from pynput import keyboard
        except ImportError:
            return False

        try:
            self._listener = keyboard.GlobalHotKeys(
                {
                    "<ctrl>+<alt>+n": self._emit_triggered,
                    "<ctrl>+<alt>+b": self._emit_library_triggered,
                    "<ctrl>+<alt>+r": self._emit_memory_triggered,
                    "<ctrl>+<alt>+o": self._emit_current_book_triggered,
                }
            )
            self._listener.start()
        except Exception:  # noqa: BLE001 - fall back to tray-only mode.
            self._listener = None
            return False
        return True

    def stop(self) -> None:
        if self._listener is None:
            return
        self._listener.stop()
        self._listener = None

    def _emit_triggered(self) -> None:
        self.triggered.emit()

    def _emit_library_triggered(self) -> None:
        self.library_triggered.emit()

    def _emit_memory_triggered(self) -> None:
        self.memory_triggered.emit()

    def _emit_current_book_triggered(self) -> None:
        self.current_book_triggered.emit()
