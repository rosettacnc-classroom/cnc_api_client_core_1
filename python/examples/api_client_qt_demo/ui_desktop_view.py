# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'desktop_viewWgdSla.ui'
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
        DesktopView.resize(941, 776)
        font = QFont()
        font.setFamilies([u"Tahoma"])
        font.setPointSize(8)
        DesktopView.setFont(font)
        DesktopView.setLocale(QLocale(QLocale.English, QLocale.UnitedStates))
        self.centralwidget = QWidget(DesktopView)
        self.centralwidget.setObjectName(u"centralwidget")
        self.tabWidget = QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tabWidget.setGeometry(QRect(8, 309, 837, 393))
        self.tab_program = QWidget()
        self.tab_program.setObjectName(u"tab_program")
        self.new_program = QPushButton(self.tab_program)
        self.new_program.setObjectName(u"new_program")
        self.new_program.setGeometry(QRect(16, 41, 120, 24))
        self.ProgramLoadButton = QPushButton(self.tab_program)
        self.ProgramLoadButton.setObjectName(u"ProgramLoadButton")
        self.ProgramLoadButton.setGeometry(QRect(16, 90, 120, 24))
        self.ProgramSaveButton = QPushButton(self.tab_program)
        self.ProgramSaveButton.setObjectName(u"ProgramSaveButton")
        self.ProgramSaveButton.setGeometry(QRect(16, 130, 120, 24))
        self.ProgramSaveAsButton = QPushButton(self.tab_program)
        self.ProgramSaveAsButton.setObjectName(u"ProgramSaveAsButton")
        self.ProgramSaveAsButton.setGeometry(QRect(16, 170, 120, 24))
        self.lineEdit = QLineEdit(self.tab_program)
        self.lineEdit.setObjectName(u"lineEdit")
        self.lineEdit.setGeometry(QRect(190, 130, 113, 22))
        self.lineEdit_2 = QLineEdit(self.tab_program)
        self.lineEdit_2.setObjectName(u"lineEdit_2")
        self.lineEdit_2.setGeometry(QRect(190, 160, 113, 22))
        self.label = QLabel(self.tab_program)
        self.label.setObjectName(u"label")
        self.label.setGeometry(QRect(16, 16, 137, 16))
        self.line = QFrame(self.tab_program)
        self.line.setObjectName(u"line")
        self.line.setGeometry(QRect(16, 33, 806, 2))
        self.line.setFrameShadow(QFrame.Shadow.Plain)
        self.line.setFrameShape(QFrame.Shape.HLine)
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
        self.MCSTitleLabel = QLabel(self.centralwidget)
        self.MCSTitleLabel.setObjectName(u"MCSTitleLabel")
        self.MCSTitleLabel.setGeometry(QRect(16, 13, 145, 17))
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.MCSTitleLabel.sizePolicy().hasHeightForWidth())
        self.MCSTitleLabel.setSizePolicy(sizePolicy)
        font1 = QFont()
        font1.setFamilies([u"Tahoma"])
        font1.setPointSize(8)
        font1.setBold(True)
        self.MCSTitleLabel.setFont(font1)
        self.MCSTitleLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.PRPTitleLabel = QLabel(self.centralwidget)
        self.PRPTitleLabel.setObjectName(u"PRPTitleLabel")
        self.PRPTitleLabel.setGeometry(QRect(184, 13, 145, 17))
        sizePolicy.setHeightForWidth(self.PRPTitleLabel.sizePolicy().hasHeightForWidth())
        self.PRPTitleLabel.setSizePolicy(sizePolicy)
        self.PRPTitleLabel.setFont(font1)
        self.PRPTitleLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.AVLTitleLabel = QLabel(self.centralwidget)
        self.AVLTitleLabel.setObjectName(u"AVLTitleLabel")
        self.AVLTitleLabel.setGeometry(QRect(352, 13, 145, 17))
        sizePolicy.setHeightForWidth(self.AVLTitleLabel.sizePolicy().hasHeightForWidth())
        self.AVLTitleLabel.setSizePolicy(sizePolicy)
        self.AVLTitleLabel.setFont(font1)
        self.AVLTitleLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.WOFTitleLabel = QLabel(self.centralwidget)
        self.WOFTitleLabel.setObjectName(u"WOFTitleLabel")
        self.WOFTitleLabel.setGeometry(QRect(517, 13, 145, 17))
        sizePolicy.setHeightForWidth(self.WOFTitleLabel.sizePolicy().hasHeightForWidth())
        self.WOFTitleLabel.setSizePolicy(sizePolicy)
        self.WOFTitleLabel.setFont(font1)
        self.WOFTitleLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.MTPTitleLabel = QLabel(self.centralwidget)
        self.MTPTitleLabel.setObjectName(u"MTPTitleLabel")
        self.MTPTitleLabel.setGeometry(QRect(16, 149, 145, 17))
        sizePolicy.setHeightForWidth(self.MTPTitleLabel.sizePolicy().hasHeightForWidth())
        self.MTPTitleLabel.setSizePolicy(sizePolicy)
        self.MTPTitleLabel.setFont(font1)
        self.MTPTitleLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.PTPTitleLabel = QLabel(self.centralwidget)
        self.PTPTitleLabel.setObjectName(u"PTPTitleLabel")
        self.PTPTitleLabel.setGeometry(QRect(184, 149, 145, 17))
        sizePolicy.setHeightForWidth(self.PTPTitleLabel.sizePolicy().hasHeightForWidth())
        self.PTPTitleLabel.setSizePolicy(sizePolicy)
        self.PTPTitleLabel.setFont(font1)
        self.PTPTitleLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.JOPTitleLabel = QLabel(self.centralwidget)
        self.JOPTitleLabel.setObjectName(u"JOPTitleLabel")
        self.JOPTitleLabel.setGeometry(QRect(352, 149, 145, 17))
        sizePolicy.setHeightForWidth(self.JOPTitleLabel.sizePolicy().hasHeightForWidth())
        self.JOPTitleLabel.setSizePolicy(sizePolicy)
        self.JOPTitleLabel.setFont(font1)
        self.JOPTitleLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.MachineInfoLabel = QLabel(self.centralwidget)
        self.MachineInfoLabel.setObjectName(u"MachineInfoLabel")
        self.MachineInfoLabel.setGeometry(QRect(520, 149, 145, 17))
        sizePolicy.setHeightForWidth(self.MachineInfoLabel.sizePolicy().hasHeightForWidth())
        self.MachineInfoLabel.setSizePolicy(sizePolicy)
        self.MachineInfoLabel.setFont(font1)
        self.MachineInfoLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.ToolInfoPanel = QFrame(self.centralwidget)
        self.ToolInfoPanel.setObjectName(u"ToolInfoPanel")
        self.ToolInfoPanel.setGeometry(QRect(8, 275, 837, 25))
        self.ToolInfoPanel.setFrameShape(QFrame.Shape.StyledPanel)
        self.ToolInfoPanel.setFrameShadow(QFrame.Shadow.Plain)
        self.TBCNCContinueButton = QFrame(self.centralwidget)
        self.TBCNCContinueButton.setObjectName(u"TBCNCContinueButton")
        self.TBCNCContinueButton.setGeometry(QRect(853, 8, 80, 723))
        self.TBCNCContinueButton.setFrameShape(QFrame.Shape.StyledPanel)
        self.TBCNCContinueButton.setFrameShadow(QFrame.Shadow.Plain)
        self.CommandsLabel = QLabel(self.TBCNCContinueButton)
        self.CommandsLabel.setObjectName(u"CommandsLabel")
        self.CommandsLabel.setGeometry(QRect(0, 0, 80, 17))
        sizePolicy.setHeightForWidth(self.CommandsLabel.sizePolicy().hasHeightForWidth())
        self.CommandsLabel.setSizePolicy(sizePolicy)
        self.CommandsLabel.setFont(font1)
        self.CommandsLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.TBCNCStartButton = QPushButton(self.TBCNCContinueButton)
        self.TBCNCStartButton.setObjectName(u"TBCNCStartButton")
        self.TBCNCStartButton.setGeometry(QRect(8, 25, 64, 54))
        self.TBCNCStopButton = QPushButton(self.TBCNCContinueButton)
        self.TBCNCStopButton.setObjectName(u"TBCNCStopButton")
        self.TBCNCStopButton.setGeometry(QRect(8, 87, 64, 54))
        self.TBCNCPauseButton = QPushButton(self.TBCNCContinueButton)
        self.TBCNCPauseButton.setObjectName(u"TBCNCPauseButton")
        self.TBCNCPauseButton.setGeometry(QRect(8, 149, 64, 54))
        self.TBCNCContinueButton_2 = QPushButton(self.TBCNCContinueButton)
        self.TBCNCContinueButton_2.setObjectName(u"TBCNCContinueButton_2")
        self.TBCNCContinueButton_2.setGeometry(QRect(8, 211, 64, 54))
        self.TBCNCResumeAfterStopButton = QPushButton(self.TBCNCContinueButton)
        self.TBCNCResumeAfterStopButton.setObjectName(u"TBCNCResumeAfterStopButton")
        self.TBCNCResumeAfterStopButton.setGeometry(QRect(8, 273, 64, 54))
        self.ResetAlarmsButton = QPushButton(self.TBCNCContinueButton)
        self.ResetAlarmsButton.setObjectName(u"ResetAlarmsButton")
        self.ResetAlarmsButton.setGeometry(QRect(8, 475, 64, 54))
        self.ResetAlarmsHistoryButton = QPushButton(self.TBCNCContinueButton)
        self.ResetAlarmsHistoryButton.setObjectName(u"ResetAlarmsHistoryButton")
        self.ResetAlarmsHistoryButton.setGeometry(QRect(8, 537, 64, 54))
        self.ResetWarningsButton = QPushButton(self.TBCNCContinueButton)
        self.ResetWarningsButton.setObjectName(u"ResetWarningsButton")
        self.ResetWarningsButton.setGeometry(QRect(8, 599, 64, 54))
        self.ResetWarningsHistoryButton = QPushButton(self.TBCNCContinueButton)
        self.ResetWarningsHistoryButton.setObjectName(u"ResetWarningsHistoryButton")
        self.ResetWarningsHistoryButton.setGeometry(QRect(8, 661, 64, 54))
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
        self.ProgramLoadButton.setText(QCoreApplication.translate("DesktopView", u"Load Program", None))
        self.ProgramSaveButton.setText(QCoreApplication.translate("DesktopView", u"Save Program", None))
        self.ProgramSaveAsButton.setText(QCoreApplication.translate("DesktopView", u"Save Program As", None))
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
        self.MCSTitleLabel.setText(QCoreApplication.translate("DesktopView", u"MACHINE POSITIONS", None))
        self.PRPTitleLabel.setText(QCoreApplication.translate("DesktopView", u"PROGRAM POSITIONS", None))
        self.AVLTitleLabel.setText(QCoreApplication.translate("DesktopView", u"ACTUAL VELOCITIES", None))
        self.WOFTitleLabel.setText(QCoreApplication.translate("DesktopView", u"WORKING OFFSETS", None))
        self.MTPTitleLabel.setText(QCoreApplication.translate("DesktopView", u"MAC SET POSITIONS", None))
        self.PTPTitleLabel.setText(QCoreApplication.translate("DesktopView", u"PRG SET POSITIONS", None))
        self.JOPTitleLabel.setText(QCoreApplication.translate("DesktopView", u"JOINT POSITIONS", None))
        self.MachineInfoLabel.setText(QCoreApplication.translate("DesktopView", u"MACHINE INFO", None))
        self.CommandsLabel.setText(QCoreApplication.translate("DesktopView", u"COMMANDS", None))
        self.TBCNCStartButton.setText(QCoreApplication.translate("DesktopView", u"Start", None))
        self.TBCNCStopButton.setText(QCoreApplication.translate("DesktopView", u"Stop", None))
        self.TBCNCPauseButton.setText(QCoreApplication.translate("DesktopView", u"Pause", None))
        self.TBCNCContinueButton_2.setText(QCoreApplication.translate("DesktopView", u"Continue", None))
        self.TBCNCResumeAfterStopButton.setText(QCoreApplication.translate("DesktopView", u"Resume\n"
"after Stop", None))
        self.ResetAlarmsButton.setText(QCoreApplication.translate("DesktopView", u"Reset\n"
"Alarms", None))
        self.ResetAlarmsHistoryButton.setText(QCoreApplication.translate("DesktopView", u"Reset\n"
"Alarms\n"
"History", None))
        self.ResetWarningsButton.setText(QCoreApplication.translate("DesktopView", u"Reset\n"
"Warnings", None))
        self.ResetWarningsHistoryButton.setText(QCoreApplication.translate("DesktopView", u"Reset\n"
"Warnings", None))
    # retranslateUi

