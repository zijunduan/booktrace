from pathlib import Path
import sys

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication, QFileDialog, QMenu, QSystemTrayIcon

import config
from hotkey import HotkeyManager
import storage
from ui.capture_window import CaptureWindow
from ui.icons import create_app_icon
from ui.library_window import LibraryWindow
from ui.memory_dialog import MemoryDialog


BASE_DIR = Path(__file__).resolve().parent
_INSTANCE_MUTEX_HANDLE = None


def acquire_single_instance_lock() -> bool:
    global _INSTANCE_MUTEX_HANDLE

    if not sys.platform.startswith("win"):
        return True

    import ctypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    handle = kernel32.CreateMutexW(None, True, "Local\\BookTraceSingleInstance")
    if not handle:
        return True

    if ctypes.get_last_error() == 183:
        kernel32.CloseHandle(handle)
        return False

    _INSTANCE_MUTEX_HANDLE = handle
    return True


def release_single_instance_lock() -> None:
    global _INSTANCE_MUTEX_HANDLE

    if _INSTANCE_MUTEX_HANDLE is None or not sys.platform.startswith("win"):
        return

    import ctypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.ReleaseMutex(_INSTANCE_MUTEX_HANDLE)
    kernel32.CloseHandle(_INSTANCE_MUTEX_HANDLE)
    _INSTANCE_MUTEX_HANDLE = None


def resource_path(relative_path: str) -> Path:
    base_dir = Path(getattr(sys, "_MEIPASS", BASE_DIR))
    return base_dir / relative_path


def load_stylesheet() -> str:
    style_path = resource_path("ui/style.qss")
    try:
        return style_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""
    except OSError:
        return ""


def main() -> int:
    if not acquire_single_instance_lock():
        return 0

    app = QApplication(sys.argv)
    app.setApplicationName("BookTrace")
    app.setQuitOnLastWindowClosed(False)
    app_icon = create_app_icon()
    app.setWindowIcon(app_icon)

    stylesheet = load_stylesheet()
    if stylesheet:
        app.setStyleSheet(stylesheet)

    window = CaptureWindow()
    library_window = LibraryWindow()
    memory_dialog = MemoryDialog()
    window.setWindowIcon(app_icon)
    library_window.setWindowIcon(app_icon)
    library_window.memory_dialog.setWindowIcon(app_icon)
    memory_dialog.setWindowIcon(app_icon)
    hotkey = HotkeyManager()

    def open_notes_folder() -> None:
        try:
            storage.open_path(config.get_notes_dir())
        except Exception as exc:  # noqa: BLE001 - show a user-facing error in the UI.
            tray.showMessage("BookTrace", f"没能打开保存位置：{exc}")

    def choose_notes_folder() -> None:
        folder = QFileDialog.getExistingDirectory(
            None,
            "选择笔记文件夹",
            str(config.get_notes_dir()),
        )
        if not folder:
            return
        config.set_notes_dir(folder)
        library_window.refresh()
        tray.showMessage("BookTrace", f"保存位置已更改：\n{folder}")

    def show_current_book_trace() -> None:
        book = config.get_last_book().strip()
        if not book:
            window.prompt_for_book()
            return
        library_window.show_book(book)

    def show_book_trace(book: str) -> None:
        library_window.show_book(book)

    def quit_app() -> None:
        hotkey.stop()
        tray.hide()
        app.quit()

    window.set_view_book_callback(show_book_trace)

    tray = QSystemTrayIcon(app_icon)
    tray.setToolTip("BookTrace 书痕")

    menu = QMenu()
    capture_action = QAction("记一念    Ctrl+Alt+N", menu)
    library_action = QAction("打开书架    Ctrl+Alt+B", menu)
    random_action = QAction("随机回忆    Ctrl+Alt+R", menu)
    current_book_action = QAction("查看当前书痕    Ctrl+Alt+O", menu)
    open_folder_action = QAction("打开保存位置", menu)
    choose_folder_action = QAction("更改保存位置", menu)
    quit_action = QAction("退出", menu)

    capture_action.triggered.connect(window.show_capture)
    library_action.triggered.connect(library_window.show_library)
    random_action.triggered.connect(memory_dialog.show_random)
    current_book_action.triggered.connect(show_current_book_trace)
    open_folder_action.triggered.connect(open_notes_folder)
    choose_folder_action.triggered.connect(choose_notes_folder)
    quit_action.triggered.connect(quit_app)

    menu.addAction(capture_action)
    menu.addAction(library_action)
    menu.addAction(random_action)
    menu.addAction(current_book_action)
    menu.addSeparator()
    menu.addAction(open_folder_action)
    menu.addAction(choose_folder_action)
    menu.addSeparator()
    menu.addAction(quit_action)

    tray.setContextMenu(menu)
    tray.activated.connect(
        lambda reason: window.show_capture()
        if reason
        in (QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick)
        else None
    )

    hotkey.triggered.connect(window.show_capture)
    hotkey.library_triggered.connect(library_window.show_library)
    hotkey.memory_triggered.connect(memory_dialog.show_random)
    hotkey.current_book_triggered.connect(show_current_book_trace)
    hotkey_started = hotkey.start()
    tray.show()

    if not QSystemTrayIcon.isSystemTrayAvailable():
        window.show_capture()
    elif not hotkey_started:
        tray.showMessage(
            "BookTrace",
            "未启用 Ctrl+Alt+N：请确认已安装 pynput。",
            QSystemTrayIcon.MessageIcon.Information,
            3000,
        )

    app.aboutToQuit.connect(hotkey.stop)
    app.aboutToQuit.connect(release_single_instance_lock)

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
