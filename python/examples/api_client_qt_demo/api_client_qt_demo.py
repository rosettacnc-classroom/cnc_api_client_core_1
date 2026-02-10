"""API Client Demo using Qt PySide6 UI."""
#-------------------------------------------------------------------------------
# Name:         api_client_qt_demo
#
# Purpose:      API Client Demo with Qt PySide6 UI
#               https://pypi.org/project/PySide6/
#
# Note          Compatible with API server version 1.5.1
#               1 (on 1.x.y) means interface contract
#               x (on 1.x.y) means version
#               y (on 1.x.y) means release
#
# Note          Checked with Python 3.11.9
#
# Author:       rosettacnc-classroom@gmail.com
#
# Created:      07/12/2024
# Copyright:    RosettaCNC (c) 2016-2024
# Licence:      RosettaCNC License 1.0 (RCNC-1.0)
# Coding Style  https://www.python.org/dev/peps/pep-0008/
#               With cnc_vision_vcl/fmx objects is used Delphi coding style
#-------------------------------------------------------------------------------
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QGuiApplication, Qt, QIcon

from utils_qt import QThemeManager
from api_client_qt_demo_desktop_view import ApiClientQtDemoDesktopView

def main():
    """Main entry point."""

    # initialize application and apply style and theme
    application = QApplication(sys.argv)
    application.setStyle('Fusion')
    QGuiApplication.styleHints().setColorScheme(Qt.ColorScheme.Light)
    #theme = QThemeManager("styles")
    #theme.load("Light")

    # set global application icon
    base_dir = Path(__file__).resolve().parent
    icon_path = base_dir / 'images' / 'rosettacnc.ico'
    application.setWindowIcon(QIcon(str(icon_path)))

    # create main view and enter in main loop
    window = ApiClientQtDemoDesktopView()
    window.show()
    sys.exit(application.exec())

if __name__ == '__main__':
    main()
