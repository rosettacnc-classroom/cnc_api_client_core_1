"""QT Utilities."""
#-------------------------------------------------------------------------------
# Name:         qt_utils
#
# Purpose:      QT PySide 6 Utilities
#
# Note          Compatible with API server version 1.5.3
#               1 (on 1.x.y) means interface contract
#               x (on 1.x.y) means version
#               y (on 1.x.y) means release
#
# Note          Checked with Python 3.11.9
#
# Author:       rosettacnc-classroom@gmail.com
#
# Created:      10/03/2026
# Copyright:    RosettaCNC (c) 2016-2026
# Licence:      RosettaCNC License 1.0 (RCNC-1.0)
# Coding Style  https://www.python.org/dev/peps/pep-0008/
#-------------------------------------------------------------------------------
# pylint: disable=C0301 -> line-too-long
# pylint: disable=R0903 -> too-few-public-methods
#-------------------------------------------------------------------------------
from pathlib import Path

from PySide6.QtCore import QByteArray, QFile, QIODevice
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QApplication, QDialog

# constants
DEFAULT_STYLES_BASE_DIR = "styles"


#===
#   Helper functions
#=
def move_dialog_to_screen_center(dialog: QDialog) -> None:
    """Moves dialog widget to screen center."""
    if not isinstance(dialog, QDialog):
        return
    screen = dialog.screen()
    if screen is None:
        screen = QGuiApplication.primaryScreen()
    if screen is None:
        return

    dialog_rect = dialog.frameGeometry()
    dialog_rect.moveCenter(screen.availableGeometry().center())
    dialog.move(dialog_rect.topLeft())

def read_text_resource(path: str, encoding: str = "utf-8") -> str:
    """
    Reads the contents of a text file from the file system **or** from a Qt resource.

    The distinction is made based on the path prefix:

    - ":/..."  -> compiled Qt resource (".qrc" / "_rc.py" file).
    - Any other path -> normal file on disk.

    Args:
        path                : Path to the file or Qt resource (e.g., ":/icons/led.svg").
        encoding            : Codec used to decode the bytes (default "utf-8").

    Returns:
        File contents as a string.

    Raises:
        FileNotFoundError   : If the file on disk does not exist.
        OSError             : If the Qt resource cannot be opened or read.
    """
    if path.startswith(":/"):
        return _read_qt_resource(path, encoding)
    return Path(path).read_text(encoding=encoding)

def _read_qt_resource(resource_path: str, encoding: str) -> str:
    """
    Reads a Qt resource via "QFile".

    Args:
        resource_path       : Path in the form ":/..." registered in ".qrc".
        encoding            : Codec for decoding (e.g., "utf-8").

    Returns:
        Resource content as a string.

    Raises:
        OSError             : If the resource does not exist or is not readable.
    """
    qfile = QFile(resource_path)
    if not qfile.exists():
        raise OSError(f"Qt resource not found: '{resource_path}'")
    if not qfile.open(QIODevice.OpenModeFlag.ReadOnly):
        raise OSError(f"Cannot open Qt resource '{resource_path}': {qfile.errorString()}")
    try:
        raw: QByteArray = qfile.readAll()
    finally:
        qfile.close()
    if raw.isEmpty():
        raise OSError(f"Qt resource is empty: '{resource_path}'")
    return bytes(raw).decode(encoding)


#===
#   QThemeManager
#=
class QThemeManager:
    """
    Manages QSS themes for a PySide6 application.

    Loads a ".qss" file from a base directory and applies it to the current "QApplication" instance.
    The base path can be either a directory on disk or a Qt resource (e.g., ":/styles").

    Args:
        base_dir: base_dir: Directory (or Qt resource prefix) containing the ".qss" files. Default: "styles".

    Example::

        # from file system
        manager = QThemeManager("assets/styles")
        manager.load("dark")

        # from Qt resource  (the .qrc file must declare :/styles/dark.qss)
        manager = QThemeManager(":/styles")
        manager.load("dark")
    """

    def __init__(self, base_dir: str = DEFAULT_STYLES_BASE_DIR) -> None:
        self._base_dir = base_dir.rstrip("/")

    def load(self, theme_name: str) -> None:
        """
        Applies *theme_name* to the current "QApplication".

        Args:
            theme_name          : Name of the theme (without extension).
                                  The file "<base_dir>/<theme_name>.qss" must exist.
        Raises:
            FileNotFoundError   : If the ".qss" file does not exist on disk.
            OSError             : If the Qt resource cannot be read.
            RuntimeError        : If no "QApplication" instance exists.
        """
        app = QApplication.instance()
        if app is None:
            raise RuntimeError("No QApplication instance found.")

        qss_path = f"{self._base_dir}/{theme_name}.qss"
        qss = read_text_resource(qss_path)
        app.setStyleSheet(qss)
