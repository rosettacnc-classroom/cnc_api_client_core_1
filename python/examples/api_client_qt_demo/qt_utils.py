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
# Created:      18/02/2026
# Copyright:    RosettaCNC (c) 2016-2026
# Licence:      RosettaCNC License 1.0 (RCNC-1.0)
# Coding Style  https://www.python.org/dev/peps/pep-0008/
#-------------------------------------------------------------------------------
# pylint: disable=R0903 -> too-few-public-methods
#-------------------------------------------------------------------------------
import time
import random
from pathlib import Path

from PySide6.QtCore import Qt, QByteArray, QFile, QIODevice, QSize
from PySide6.QtGui import QPixmap, QPainter
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QApplication, QLabel


# constants
DEFAULT_LED_SIZE        = 16
DEFAULT_LED_COLOR_ON    = "#21c45a"
DEFAULT_LED_COLOR_OFF   = "#b0b0b0"
DEFAULT_LED_SVG_PATH    = "images/circular-led.svg"   # può essere anche ":/images/circular-led.svg"
DEFAULT_STYLES_BASE_DIR = "styles"

_BLINK_MIN_INTERVAL_S   = 0.01


#===
#   Helper functions
#=
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


#===
#   QLedWidget
#=
_CacheKey = tuple[int, int, float]


class QLedWidget(QLabel):
    """
    LED indicator widget rendered from an SVG template.

    Supports both **file system** paths and **Qt resources** (".qrc").

    The widget pre-renders two "QPixmap" (ON / OFF) and stores them in
    cache, so state changes only require a "setPixmap" without
    re-rendering the SVG.  The cache is automatically invalidated when
    resizing, changing DPI, or changing colors.

    SVG Contract
    -------------
    The SVG file must contain the placeholder "{{COLOR}}" exactly once
    it will be replaced with the hex color string before rendering.

    Args:
        parent          : Parent widget (optional).
        size            : Fixed width and height in logical pixels.
        resource_name   : Path to the SVG template. Examples:
                          - "images/circular-led.svg" -> file on disk
                          - ":/images/circular-led.svg" -> Qt resource
        color_on        : CSS color when the LED is on.
        color_off       : CSS color when the LED is off.

    Example::

        # file on disk
        led = QLedWidget(parent=self, size=24)

        # Qt resource (requires import of the _rc module generated by pyside6-rcc)
        import resources_rc  # noqa: F401
        led = QLedWidget(parent=self, size=24, resource_name=":/images/circular-led.svg")

        led.setState(True)
    """

    def __init__(
        self,
        parent=None,
        size: int = DEFAULT_LED_SIZE,
        resource_name: str = DEFAULT_LED_SVG_PATH,
        color_on: str = DEFAULT_LED_COLOR_ON,
        color_off: str = DEFAULT_LED_COLOR_OFF,
    ) -> None:
        super().__init__(parent)

        self._state: bool = False
        self._blink_next_toggle: float | None = None

        self._color_on = color_on
        self._color_off = color_off

        # <- single reading point: manages both files and Qt resources
        self._svg_template: str = read_text_resource(resource_name)

        self._pix_on: QPixmap | None = None
        self._pix_off: QPixmap | None = None
        self._cache_key: _CacheKey | None = None

        self.setAlignment(Qt.AlignCenter)
        self.setFixedSize(size, size)

        self._rebuild_cache(force=True)
        self._apply_pixmap()


    # == BEG: public getters/setters
    #
    @property
    def state(self) -> bool:
        """Current LED status ("True" = on, "False" = off)."""
        return self._state
    #
    # == END: public getters/setters


    # == BEG: public attributes
    #
    def getState(self) -> bool:
        """Returns the current state. Prefer the :attr:"state" property."""
        return self._state

    def setState(
        self,
        state: bool,
        random_blink_interval: float = 0.0,
    ) -> None:
        """
        Set the LED state, with optional random flashing.

        Call periodically from a "QTimer" for blinking.

        Behavior:

        - "state=False"                             -> LED forced **off**.
        - "state=True", "random_blink_interval<=0"  -> LED forced **on**.
        - "state=True", "random_blink_interval>0"   -> Random blinking:
          alternates between ON and OFF at random intervals between
          data:"_BLINK_MIN_INTERVAL_S" and *random_blink_interval* seconds.

        Args:
            state                   : Desired logical state.
            random_blink_interval   : Upper limit of the blinking interval (seconds).
                                      "0" disables blinking.
        """
        if not state:
            self._blink_next_toggle = None
            self._set_state(False)
            return

        if random_blink_interval <= 0.0:
            self._blink_next_toggle = None
            self._set_state(True)
            return

        now = time.perf_counter()

        if self._blink_next_toggle is None:
            self._set_state(True)
            self._blink_next_toggle = now + self._random_interval(random_blink_interval)
            return

        if now >= self._blink_next_toggle:
            self._set_state(not self._state)
            self._blink_next_toggle = now + self._random_interval(random_blink_interval)

    def setColors(self, color_on: str, color_off: str) -> None:
        """
        Changes the LED colors and rebuilds the pixmap cache.

        Args:
            color_on    : CSS color for the ON state (e.g., "#21c45a").
            color_off   : CSS color for the OFF state (e.g., "#b0b0b0").
        """
        if color_on == self._color_on and color_off == self._color_off:
            return
        self._color_on = color_on
        self._color_off = color_off
        self._rebuild_cache(force=True)
        self._apply_pixmap()

    def sizeHint(self) -> QSize:
        return QSize(self.width(), self.height())
    #
    # == END: public attributes


    # == BEG: Qt event overrides
    #
    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._rebuild_cache()
        self._apply_pixmap()
    #
    # == END: Qt event overrides


    # == BEG: non-public attributes
    #
    def _apply_pixmap(self) -> None:
        self._rebuild_cache()
        self.setPixmap(self._pix_on if self._state else self._pix_off)
        self.update()

    def _cache_key_now(self) -> _CacheKey:
        return (max(1, self.width()), max(1, self.height()), self._current_dpr())

    def _current_dpr(self) -> float:
        win = self.windowHandle()
        if win is not None and win.screen() is not None:
            return float(win.screen().devicePixelRatio())
        return 1.0

    @staticmethod
    def _random_interval(upper: float) -> float:
        return random.uniform(_BLINK_MIN_INTERVAL_S, max(upper, _BLINK_MIN_INTERVAL_S))

    def _rebuild_cache(self, force: bool = False) -> None:
        key = self._cache_key_now()
        if (
            not force
            and self._cache_key == key
            and self._pix_on is not None
            and self._pix_off is not None
        ):
            return
        w, h, dpr = key
        self._pix_on  = self._render_svg(w, h, dpr, self._color_on)
        self._pix_off = self._render_svg(w, h, dpr, self._color_off)
        self._cache_key = key

    def _render_svg(self, w: int, h: int, dpr: float, color: str) -> QPixmap:
        svg_data = self._svg_template.replace("{{COLOR}}", color)
        renderer = QSvgRenderer(QByteArray(svg_data.encode("utf-8")))

        pw = max(1, round(w * dpr))
        ph = max(1, round(h * dpr))

        pixmap = QPixmap(pw, ph)
        pixmap.setDevicePixelRatio(dpr)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()

        return pixmap

    def _set_state(self, state: bool) -> None:
        if self._state == state:
            return
        self._state = state
        self._apply_pixmap()
    #
    # == END: non-public attributes
