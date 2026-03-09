# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'alarms_warnings_dialogEkkWbo.ui'
##
## Created by: Qt User Interface Compiler version 6.8.3
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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QDialog, QHBoxLayout,
    QHeaderView, QLabel, QPushButton, QSizePolicy,
    QSpacerItem, QTableWidget, QTableWidgetItem, QVBoxLayout,
    QWidget)

class Ui_AlarmsWarningsDialog(object):
    def setupUi(self, AlarmsWarningsDialog):
        if not AlarmsWarningsDialog.objectName():
            AlarmsWarningsDialog.setObjectName(u"AlarmsWarningsDialog")
        AlarmsWarningsDialog.resize(930, 637)
        AlarmsWarningsDialog.setStyleSheet(u"QDialog {\n"
"    background-color: rgb(240, 240, 240);\n"
"}\n"
"QLabel#titleLabel {\n"
"    background-color: rgb(243, 164, 0);\n"
"    color: rgb(255, 255, 255);\n"
"    font: 700 18pt \"Arial\";\n"
"    border: 1px solid rgb(210, 210, 210);\n"
"}\n"
"QTableWidget {\n"
"    background-color: rgb(232, 232, 232);\n"
"    gridline-color: rgb(195, 195, 195);\n"
"    selection-background-color: rgb(230, 211, 191);\n"
"    selection-color: rgb(0, 0, 0);\n"
"    border: 1px solid rgb(180, 180, 180);\n"
"}\n"
"QHeaderView::section {\n"
"    background-color: rgb(55, 55, 55);\n"
"    color: rgb(255, 255, 255);\n"
"    padding: 6px;\n"
"    border: 1px solid rgb(90, 90, 90);\n"
"    font: 700 11pt \"Arial\";\n"
"}\n"
"")
        self.mainLayout = QVBoxLayout(AlarmsWarningsDialog)
        self.mainLayout.setSpacing(8)
        self.mainLayout.setObjectName(u"mainLayout")
        self.mainLayout.setContentsMargins(8, 8, 8, 8)
        self.titleLabel = QLabel(AlarmsWarningsDialog)
        self.titleLabel.setObjectName(u"titleLabel")
        self.titleLabel.setMinimumSize(QSize(0, 44))
        self.titleLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.mainLayout.addWidget(self.titleLabel)

        self.messagesTableWidget = QTableWidget(AlarmsWarningsDialog)
        if (self.messagesTableWidget.columnCount() < 4):
            self.messagesTableWidget.setColumnCount(4)
        __qtablewidgetitem = QTableWidgetItem()
        self.messagesTableWidget.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.messagesTableWidget.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        __qtablewidgetitem2 = QTableWidgetItem()
        self.messagesTableWidget.setHorizontalHeaderItem(2, __qtablewidgetitem2)
        __qtablewidgetitem3 = QTableWidgetItem()
        self.messagesTableWidget.setHorizontalHeaderItem(3, __qtablewidgetitem3)
        if (self.messagesTableWidget.rowCount() < 14):
            self.messagesTableWidget.setRowCount(14)
        __qtablewidgetitem4 = QTableWidgetItem()
        __qtablewidgetitem4.setTextAlignment(Qt.AlignCenter);
        self.messagesTableWidget.setItem(0, 0, __qtablewidgetitem4)
        __qtablewidgetitem5 = QTableWidgetItem()
        self.messagesTableWidget.setItem(0, 1, __qtablewidgetitem5)
        __qtablewidgetitem6 = QTableWidgetItem()
        __qtablewidgetitem6.setTextAlignment(Qt.AlignCenter);
        self.messagesTableWidget.setItem(0, 2, __qtablewidgetitem6)
        __qtablewidgetitem7 = QTableWidgetItem()
        self.messagesTableWidget.setItem(0, 3, __qtablewidgetitem7)
        self.messagesTableWidget.setObjectName(u"messagesTableWidget")
        self.messagesTableWidget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.messagesTableWidget.setAlternatingRowColors(False)
        self.messagesTableWidget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.messagesTableWidget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.messagesTableWidget.setShowGrid(True)
        self.messagesTableWidget.setRowCount(14)
        self.messagesTableWidget.setColumnCount(4)
        self.messagesTableWidget.horizontalHeader().setDefaultSectionSize(120)
        self.messagesTableWidget.horizontalHeader().setHighlightSections(False)
        self.messagesTableWidget.horizontalHeader().setStretchLastSection(True)
        self.messagesTableWidget.verticalHeader().setVisible(False)

        self.mainLayout.addWidget(self.messagesTableWidget)

        self.footerLayout = QHBoxLayout()
        self.footerLayout.setSpacing(8)
        self.footerLayout.setObjectName(u"footerLayout")
        self.resetButton = QPushButton(AlarmsWarningsDialog)
        self.resetButton.setObjectName(u"resetButton")
        self.resetButton.setMinimumSize(QSize(0, 0))
        self.resetButton.setAutoDefault(False)

        self.footerLayout.addWidget(self.resetButton)

        self.leftSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.footerLayout.addItem(self.leftSpacer)

        self.centerButtonsLayout = QHBoxLayout()
        self.centerButtonsLayout.setSpacing(8)
        self.centerButtonsLayout.setObjectName(u"centerButtonsLayout")
        self.modeAlarmsCurrentButton = QPushButton(AlarmsWarningsDialog)
        self.modeAlarmsCurrentButton.setObjectName(u"modeAlarmsCurrentButton")
        self.modeAlarmsCurrentButton.setMinimumSize(QSize(146, 74))
        self.modeAlarmsCurrentButton.setAutoDefault(False)

        self.centerButtonsLayout.addWidget(self.modeAlarmsCurrentButton)

        self.modeAlarmsHistoryButton = QPushButton(AlarmsWarningsDialog)
        self.modeAlarmsHistoryButton.setObjectName(u"modeAlarmsHistoryButton")
        self.modeAlarmsHistoryButton.setMinimumSize(QSize(146, 74))
        self.modeAlarmsHistoryButton.setAutoDefault(False)

        self.centerButtonsLayout.addWidget(self.modeAlarmsHistoryButton)

        self.modeWarningsCurrentButton = QPushButton(AlarmsWarningsDialog)
        self.modeWarningsCurrentButton.setObjectName(u"modeWarningsCurrentButton")
        self.modeWarningsCurrentButton.setMinimumSize(QSize(146, 74))
        self.modeWarningsCurrentButton.setAutoDefault(False)

        self.centerButtonsLayout.addWidget(self.modeWarningsCurrentButton)

        self.modeWarningsHistoryButtonButton = QPushButton(AlarmsWarningsDialog)
        self.modeWarningsHistoryButtonButton.setObjectName(u"modeWarningsHistoryButtonButton")
        self.modeWarningsHistoryButtonButton.setMinimumSize(QSize(146, 74))
        self.modeWarningsHistoryButtonButton.setAutoDefault(False)

        self.centerButtonsLayout.addWidget(self.modeWarningsHistoryButtonButton)


        self.footerLayout.addLayout(self.centerButtonsLayout)

        self.rightSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.footerLayout.addItem(self.rightSpacer)

        self.exitButton = QPushButton(AlarmsWarningsDialog)
        self.exitButton.setObjectName(u"exitButton")
        self.exitButton.setMinimumSize(QSize(0, 0))
        self.exitButton.setAutoDefault(False)

        self.footerLayout.addWidget(self.exitButton)


        self.mainLayout.addLayout(self.footerLayout)


        self.retranslateUi(AlarmsWarningsDialog)

        QMetaObject.connectSlotsByName(AlarmsWarningsDialog)
    # setupUi

    def retranslateUi(self, AlarmsWarningsDialog):
        AlarmsWarningsDialog.setWindowTitle(QCoreApplication.translate("AlarmsWarningsDialog", u"Current Warnings", None))
        self.titleLabel.setText(QCoreApplication.translate("AlarmsWarningsDialog", u"CURRENT WARNINGS", None))
        self.titleLabel.setProperty(u"alarmMode", QCoreApplication.translate("AlarmsWarningsDialog", u"alarms_current", None))
        ___qtablewidgetitem = self.messagesTableWidget.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("AlarmsWarningsDialog", u"N.", None));
        ___qtablewidgetitem1 = self.messagesTableWidget.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("AlarmsWarningsDialog", u"Acquisition Date", None));
        ___qtablewidgetitem2 = self.messagesTableWidget.horizontalHeaderItem(2)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("AlarmsWarningsDialog", u"Code", None));
        ___qtablewidgetitem3 = self.messagesTableWidget.horizontalHeaderItem(3)
        ___qtablewidgetitem3.setText(QCoreApplication.translate("AlarmsWarningsDialog", u"Description", None));

        __sortingEnabled = self.messagesTableWidget.isSortingEnabled()
        self.messagesTableWidget.setSortingEnabled(False)
        ___qtablewidgetitem4 = self.messagesTableWidget.item(0, 0)
        ___qtablewidgetitem4.setText(QCoreApplication.translate("AlarmsWarningsDialog", u"1", None));
        ___qtablewidgetitem5 = self.messagesTableWidget.item(0, 1)
        ___qtablewidgetitem5.setText(QCoreApplication.translate("AlarmsWarningsDialog", u"09/03/2026 12:07:22", None));
        ___qtablewidgetitem6 = self.messagesTableWidget.item(0, 2)
        ___qtablewidgetitem6.setText(QCoreApplication.translate("AlarmsWarningsDialog", u"W0002", None));
        ___qtablewidgetitem7 = self.messagesTableWidget.item(0, 3)
        ___qtablewidgetitem7.setText(QCoreApplication.translate("AlarmsWarningsDialog", u"Custom Warning 2 - [From Digital Input ]", None));
        self.messagesTableWidget.setSortingEnabled(__sortingEnabled)

        self.resetButton.setText(QCoreApplication.translate("AlarmsWarningsDialog", u"RESET", None))
        self.modeAlarmsCurrentButton.setText(QCoreApplication.translate("AlarmsWarningsDialog", u"Current\n"
"Alarms", None))
        self.modeAlarmsHistoryButton.setText(QCoreApplication.translate("AlarmsWarningsDialog", u"Alarms\n"
"History", None))
        self.modeWarningsCurrentButton.setText(QCoreApplication.translate("AlarmsWarningsDialog", u"Current\n"
"Warnings", None))
        self.modeWarningsHistoryButtonButton.setText(QCoreApplication.translate("AlarmsWarningsDialog", u"Warning\n"
"History", None))
        self.exitButton.setText(QCoreApplication.translate("AlarmsWarningsDialog", u"EXIT", None))
    # retranslateUi

