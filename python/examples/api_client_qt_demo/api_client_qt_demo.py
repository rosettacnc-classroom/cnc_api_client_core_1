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

from PySide6.QtWidgets import QApplication

from api_client_qt_demo_desktop_view import ApiClientQtDemoDesktopView

def main():
    """Main entry point."""

    # initialize application and enter in main loop
    application = QApplication(sys.argv)
    application.setStyle('Fusion')
    window = ApiClientQtDemoDesktopView()
    window.show()
    sys.exit(application.exec())

if __name__ == '__main__':
    main()
