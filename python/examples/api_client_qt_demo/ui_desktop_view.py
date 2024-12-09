# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'desktop_viewnCMWpH.ui'
##
## Created by: Qt User Interface Compiler version 6.8.0
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
from PySide6.QtWidgets import (QApplication, QFrame, QLabel, QLineEdit,
    QMainWindow, QPushButton, QSizePolicy, QStatusBar,
    QTabWidget, QWidget)

class Ui_DesktopView(object):
    def setupUi(self, DesktopView):
        if not DesktopView.objectName():
            DesktopView.setObjectName(u"DesktopView")
        DesktopView.resize(1012, 780)
        font = QFont()
        font.setFamilies([u"Tahoma"])
        font.setPointSize(8)
        DesktopView.setFont(font)
        DesktopView.setLocale(QLocale(QLocale.English, QLocale.UnitedStates))
        self.centralwidget = QWidget(DesktopView)
        self.centralwidget.setObjectName(u"centralwidget")
        self.tabWidget = QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tabWidget.setGeometry(QRect(10, 370, 981, 381))
        self.tab_program = QWidget()
        self.tab_program.setObjectName(u"tab_program")
        self.new_program = QPushButton(self.tab_program)
        self.new_program.setObjectName(u"new_program")
        self.new_program.setGeometry(QRect(20, 50, 101, 24))
        self.pushButton_2 = QPushButton(self.tab_program)
        self.pushButton_2.setObjectName(u"pushButton_2")
        self.pushButton_2.setGeometry(QRect(50, 90, 101, 24))
        self.pushButton_3 = QPushButton(self.tab_program)
        self.pushButton_3.setObjectName(u"pushButton_3")
        self.pushButton_3.setGeometry(QRect(50, 120, 101, 24))
        self.pushButton_4 = QPushButton(self.tab_program)
        self.pushButton_4.setObjectName(u"pushButton_4")
        self.pushButton_4.setGeometry(QRect(50, 150, 101, 24))
        self.lineEdit = QLineEdit(self.tab_program)
        self.lineEdit.setObjectName(u"lineEdit")
        self.lineEdit.setGeometry(QRect(190, 130, 113, 22))
        self.lineEdit_2 = QLineEdit(self.tab_program)
        self.lineEdit_2.setObjectName(u"lineEdit_2")
        self.lineEdit_2.setGeometry(QRect(190, 160, 113, 22))
        self.label = QLabel(self.tab_program)
        self.label.setObjectName(u"label")
        self.label.setGeometry(QRect(20, 20, 121, 16))
        self.line = QFrame(self.tab_program)
        self.line.setObjectName(u"line")
        self.line.setGeometry(QRect(20, 40, 791, 16))
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)
        self.tabWidget.addTab(self.tab_program, "")
        self.tab_gcode = QWidget()
        self.tab_gcode.setObjectName(u"tab_gcode")
        self.tabWidget.addTab(self.tab_gcode, "")
        self.tab_3 = QWidget()
        self.tab_3.setObjectName(u"tab_3")
        self.tabWidget.addTab(self.tab_3, "")
        self.tab_4 = QWidget()
        self.tab_4.setObjectName(u"tab_4")
        self.tabWidget.addTab(self.tab_4, "")
        self.tab_5 = QWidget()
        self.tab_5.setObjectName(u"tab_5")
        self.tabWidget.addTab(self.tab_5, "")
        self.tab_6 = QWidget()
        self.tab_6.setObjectName(u"tab_6")
        self.tabWidget.addTab(self.tab_6, "")
        self.tab_7 = QWidget()
        self.tab_7.setObjectName(u"tab_7")
        self.tabWidget.addTab(self.tab_7, "")
        self.tab_8 = QWidget()
        self.tab_8.setObjectName(u"tab_8")
        self.tabWidget.addTab(self.tab_8, "")
        self.tab_9 = QWidget()
        self.tab_9.setObjectName(u"tab_9")
        self.tabWidget.addTab(self.tab_9, "")
        self.tab_10 = QWidget()
        self.tab_10.setObjectName(u"tab_10")
        self.tabWidget.addTab(self.tab_10, "")
        self.tab_11 = QWidget()
        self.tab_11.setObjectName(u"tab_11")
        self.tabWidget.addTab(self.tab_11, "")
        self.tab_12 = QWidget()
        self.tab_12.setObjectName(u"tab_12")
        self.tabWidget.addTab(self.tab_12, "")
        DesktopView.setCentralWidget(self.centralwidget)
        self.statusbar = QStatusBar(DesktopView)
        self.statusbar.setObjectName(u"statusbar")
        DesktopView.setStatusBar(self.statusbar)

        self.retranslateUi(DesktopView)

        self.tabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(DesktopView)
    # setupUi

    def retranslateUi(self, DesktopView):
        DesktopView.setWindowTitle(QCoreApplication.translate("DesktopView", u"API Client Engine Demo", None))
        self.new_program.setText(QCoreApplication.translate("DesktopView", u"New Program", None))
        self.pushButton_2.setText(QCoreApplication.translate("DesktopView", u"PushButton", None))
        self.pushButton_3.setText(QCoreApplication.translate("DesktopView", u"PushButton", None))
        self.pushButton_4.setText(QCoreApplication.translate("DesktopView", u"PushButton", None))
        self.label.setText(QCoreApplication.translate("DesktopView", u"NEW PROGRAM", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_program), QCoreApplication.translate("DesktopView", u"Program", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_gcode), QCoreApplication.translate("DesktopView", u"G-Code", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_3), QCoreApplication.translate("DesktopView", u"CNC", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_4), QCoreApplication.translate("DesktopView", u"JOG", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_5), QCoreApplication.translate("DesktopView", u"Overrides", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_6), QCoreApplication.translate("DesktopView", u"Homing", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_7), QCoreApplication.translate("DesktopView", u"MDI", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_8), QCoreApplication.translate("DesktopView", u"D I/O", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_9), QCoreApplication.translate("DesktopView", u"A I/O", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_10), QCoreApplication.translate("DesktopView", u"Scanning Laser", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_11), QCoreApplication.translate("DesktopView", u"Machining Info", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_12), QCoreApplication.translate("DesktopView", u"System Info", None))
    # retranslateUi

