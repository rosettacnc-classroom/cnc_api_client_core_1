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
# Created:      12/02/2026
# Copyright:    RosettaCNC (c) 2016-2026
# Licence:      RosettaCNC License 1.0 (RCNC-1.0)
# Coding Style  https://www.python.org/dev/peps/pep-0008/
#-------------------------------------------------------------------------------
# pylint: disable=R0903 -> too-few-public-methods
#-------------------------------------------------------------------------------
from pathlib import Path
from PySide6.QtWidgets import QApplication

class QThemeManager:
    """Xx..."""
    def __init__(self, base_dir: str = 'styles'):
        self.base_dir = Path(base_dir)

    def load(self, theme_name: str) -> None:
        """Xxx..."""
        qss_path = self.base_dir / f'{theme_name}.qss'
        qss = qss_path.read_text(encoding='utf-8')
        QApplication.instance().setStyleSheet(qss)
