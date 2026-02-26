# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'user_media_dialogPwjQAr.ui'
##
## Created by: Qt User Interface Compiler version 6.10.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QAbstractButton, QApplication, QDialog, QDialogButtonBox,
    QSizePolicy, QWidget)

class Ui_UserMediaDialog(object):
    def setupUi(self, UserMediaDialog):
        if not UserMediaDialog.objectName():
            UserMediaDialog.setObjectName(u"UserMediaDialog")
        UserMediaDialog.resize(400, 300)
        self.buttonBox = QDialogButtonBox(UserMediaDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setGeometry(QRect(30, 240, 341, 32))
        self.buttonBox.setOrientation(Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Ok)

        self.retranslateUi(UserMediaDialog)
        self.buttonBox.accepted.connect(UserMediaDialog.accept)
        self.buttonBox.rejected.connect(UserMediaDialog.reject)

        QMetaObject.connectSlotsByName(UserMediaDialog)
    # setupUi

    def retranslateUi(self, UserMediaDialog):
        UserMediaDialog.setWindowTitle(QCoreApplication.translate("UserMediaDialog", u"Dialog", None))
    # retranslateUi

