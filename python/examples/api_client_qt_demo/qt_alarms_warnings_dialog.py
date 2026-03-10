"""QT Alarms & Warnings Dialog."""
#-------------------------------------------------------------------------------
# Name:         qt_alarms_warnings_dialog
#
# Purpose:      QT Alarms & Warnings Dialog
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
# pylint: disable=R0902 -> too-many-instance-attributes
# pylint: disable=R0912 -> too-many-branches
#-------------------------------------------------------------------------------
from enum import IntEnum

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QButtonGroup, QDialog, QHeaderView, QPushButton, QTableWidgetItem

from ui_alarms_warnings_dialog import Ui_AlarmsWarningsDialog

import cnc_api_client_core as cnc
from qt_utils import move_dialog_to_screen_center

# define ui geometry constants
DIALOG_FRAME_WIDTH      = 2


class AlarmsWarningsMode(IntEnum):
    """Alarms and warnings mode enumerations."""
    ALARMS_CURRENT      = 0
    ALARMS_HISTORY      = 1
    WARNINGS_CURRENT    = 2
    WARNINGS_HISTORY    = 3


class AlarmsWarningsDialog(QDialog):
    """Alarms and warnings dialog widget."""

    def __init__(
        self,
        parent=None,
        api: cnc.CncAPIClientCore = None,
        mode: AlarmsWarningsMode | int = AlarmsWarningsMode.ALARMS_CURRENT
        ):
        # call qt inherited dialog constructor
        super().__init__(parent)

        # set Qt Designer generated ui
        self.ui = Ui_AlarmsWarningsDialog()
        self.ui.setupUi(self)

        # set to be frameless
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)

        # create light style sheet
        self.sytlesheet_light = (
        """
            QDialog {
                background-color: rgb(240, 240, 240);
            }

            QFrame#dialogFrame {
                color: #A0A0A4;
            }

            QLabel[alarmMode="alarms_current"] {
                background-color: #FF0000;
                color: white;
                font: 700 18pt "Roboto Bold";
                border: 1px solid rgb(210, 210, 210);
            }
            QLabel[alarmMode="alarms_history"] {
                background-color: #800000;
                color: white;
                font: 700 18pt "Arial";
                border: 1px solid rgb(210, 210, 210);
            }
            QLabel[alarmMode="warnings_current"] {
                background-color: #FFA500;
                color: white;
                font: 700 18pt "Arial";
                border: 1px solid rgb(210, 210, 210);
            }
            QLabel[alarmMode="warnings_history"] {
                background-color: #FF8C00;
                color: white;
                font: 700 18pt "Arial";
                border: 1px solid rgb(210, 210, 210);
            }

            QTableWidget {
                background-color: #FFFFFF;
                alternate-background-color: #F6F6F6;
                gridline-color: rgb(195, 195, 195);
                selection-background-color: #F6DCC6;
                selection-color: rgb(0, 0, 0);
                border: 1px solid rgb(180, 180, 180);
            }
            QHeaderView::section {
                background-color: rgb(55, 55, 55);
                color: rgb(255, 255, 255);
                padding: 6px;
                border: 1px solid rgb(90, 90, 90);
                font: 700 11pt "Roboto Bold";
            }

            /* here you can change the table vertical scrollbar
            QTableWidget QScrollBar:vertical {
                width: 18px;
                margin: 0px;
                background: #f0f0f0;
            }

            QTableWidget QScrollBar::handle:vertical {
                background: #b0b0b0;
                min-height: 20px;
            }

            QTableWidget QScrollBar::add-line:vertical,
            QTableWidget QScrollBar::sub-line:vertical {
                height: 0px;
            }

            QTableWidget QScrollBar::add-page:vertical,
            QTableWidget QScrollBar::sub-page:vertical {
                background: none;
            }
            */

            QPushButton:checked {
                background-color: rgb(215, 215, 215);
                border: 2px solid rgb(120, 120, 120);
            }
        """
        )

        # apply light style sheet
        self.setStyleSheet(self.sytlesheet_light)

        # store argument parameters
        self.api = api
        try:
            self.mode = AlarmsWarningsMode(mode)
        except (ValueError, TypeError):
            self.mode = AlarmsWarningsMode.ALARMS_CURRENT

        # set dialog frame border size
        self.ui.dialogFrame.setLineWidth(DIALOG_FRAME_WIDTH)

        # set mesasge table wiget settings
        self.ui.messagesTableWidget.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.ui.messagesTableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.ui.messagesTableWidget.setColumnWidth(0, 57)
        self.ui.messagesTableWidget.setColumnWidth(1, 140)
        self.ui.messagesTableWidget.setColumnWidth(2, 70)
        self.ui.messagesTableWidget.setColumnWidth(3, 120)
        self.ui.messagesTableWidget.horizontalHeaderItem(3).setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.ui.messagesTableWidget.horizontalHeader().setFixedHeight(37)
        self.ui.messagesTableWidget.verticalHeader().setDefaultSectionSize(31)
        self.ui.messagesTableWidget.setFocusPolicy(Qt.NoFocus)
        self.item_font = QFont("Roboto", 10)

        # sets attributes default values
        self.data = None
        self.data_mode = None

        # create exclusive button group for mode buttons
        self.mode_button_group = QButtonGroup(self)
        self.mode_button_group.setExclusive(True)

        self.mode_buttons = {
            AlarmsWarningsMode.ALARMS_CURRENT: self.ui.modeAlarmsCurrentButton,
            AlarmsWarningsMode.ALARMS_HISTORY: self.ui.modeAlarmsHistoryButton,
            AlarmsWarningsMode.WARNINGS_CURRENT: self.ui.modeWarningsCurrentButton,
            AlarmsWarningsMode.WARNINGS_HISTORY: self.ui.modeWarningsHistoryButtonButton,
        }

        for mode_key, button in self.mode_buttons.items():
            button.setCheckable(True)
            self.mode_button_group.addButton(button, int(mode_key))

        # link actions to all buttons
        for obj in self.findChildren(QPushButton):
            obj.clicked.connect(self.__on_action_main_execute)

        # create and set update timer
        self.tmr_update = QTimer(self)
        self.tmr_update.setInterval(1)
        self.tmr_update.timeout.connect(self.__on_timer_update)
        self.tmr_update.setSingleShot(False)

        # set modal mode
        self.setModal(True)

    # == BEG: relink of native events from inherited Qt PySide6 UI design
    #
    def showEvent(self, event):
        super().showEvent(event)
        self.__on_form_show()
    #
    # == BEG: relink of native events from inherited Qt PySide6 UI design


    # == BEG: events implementation
    #
    def __on_action_main_execute(self):
        sender = self.sender()

        if sender == self.ui.resetButton:
            if self.mode == AlarmsWarningsMode.ALARMS_CURRENT:
                self.api.reset_alarms()
            if self.mode == AlarmsWarningsMode.ALARMS_HISTORY:
                self.api.reset_alarms_history()
            if self.mode == AlarmsWarningsMode.WARNINGS_CURRENT:
                self.api.reset_warnings()
            if self.mode == AlarmsWarningsMode.WARNINGS_HISTORY:
                self.api.reset_warnings_history()

        if sender == self.ui.modeAlarmsCurrentButton:
            self.__set_mode(AlarmsWarningsMode.ALARMS_CURRENT)
        if sender == self.ui.modeAlarmsHistoryButton:
            self.__set_mode(AlarmsWarningsMode.ALARMS_HISTORY)
        if sender == self.ui.modeWarningsCurrentButton:
            self.__set_mode(AlarmsWarningsMode.WARNINGS_CURRENT)
        if sender == self.ui.modeWarningsHistoryButtonButton:
            self.__set_mode(AlarmsWarningsMode.WARNINGS_HISTORY)

        if sender == self.ui.exitButton:
            self.close()

    def __on_action_main_update(self):
        pass

    def __on_form_show(self):
        # move dialog to screen center
        move_dialog_to_screen_center(self)

        # set default attributes values
        self.__set_mode(self.mode)

        # enable update timer and call first update NOW
        self.tmr_update.start()
        self.__on_timer_update()

    def __on_timer_update(self):
        # update non editable objects with related data
        self.__updated_objects()

        # update action main linked objects enablings
        self.__on_action_main_update()
    #
    # == END: events implementation


    # == BEG: generic methods
    #
    def __set_mode(self, mode: AlarmsWarningsMode | int) -> None:
        try:
            self.mode = AlarmsWarningsMode(mode)
        except (ValueError, TypeError):
            return

        match self.mode:
            case AlarmsWarningsMode.ALARMS_CURRENT:
                alarm_mode ='alarms_current'
                text = 'CURRENT ALARMS'
            case AlarmsWarningsMode.ALARMS_HISTORY:
                alarm_mode ='alarms_history'
                text = 'ALARMS HISTORY'
            case AlarmsWarningsMode.WARNINGS_CURRENT:
                alarm_mode ='warnings_current'
                text = 'CURRENT WARNINGS'
            case AlarmsWarningsMode.WARNINGS_HISTORY:
                alarm_mode ='warnings_history'
                text = 'WARNINGS HISTORY'

        self.ui.titleLabel.setProperty("alarmMode", alarm_mode)
        self.ui.titleLabel.setText(text)

        button = self.mode_buttons.get(mode)
        if button is not None:
            button.setChecked(True)

        # refresh stylesheet owner
        self.setStyleSheet(self.styleSheet())
    #
    # == END: generic methods


    # == BEG: update methods
    #
    def __updated_objects(self):
        """Updates non editable objects with related data."""

        def extra_message_text(s: str) -> str:
            if s.startswith('['):
                end_pos = s.find(']', 1)
                if end_pos != -1:
                    return s[end_pos + 1:].strip()
            return s

        data = None

        match self.mode:
            case AlarmsWarningsMode.ALARMS_CURRENT:
                data = self.api.get_alarms_current_list()
            case AlarmsWarningsMode.ALARMS_HISTORY:
                data = self.api.get_alarms_history_list()
            case AlarmsWarningsMode.WARNINGS_CURRENT:
                data = self.api.get_warnings_current_list()
            case AlarmsWarningsMode.WARNINGS_HISTORY:
                data = self.api.get_warnings_history_list()

        if not data.has_data:
            self.close()
            return

        if data.is_equal(self.data) and self.data_mode == self.mode:
            return

        self.data = data
        self.data_mode = self.mode

        match self.mode:
            case AlarmsWarningsMode.ALARMS_CURRENT:
                rows = 20
                code_prefix = 'A'
            case AlarmsWarningsMode.ALARMS_HISTORY:
                rows = 100
                code_prefix = 'A'
            case AlarmsWarningsMode.WARNINGS_CURRENT:
                rows = 20
                code_prefix = 'W'
            case AlarmsWarningsMode.WARNINGS_HISTORY:
                rows = 100
                code_prefix = 'W'

        self.ui.messagesTableWidget.setRowCount(rows)

        data_count = len(data.list)
        for r in range(self.ui.messagesTableWidget.rowCount()):
            if r == 0:
                pass
            else:
                pass
            for c in range(self.ui.messagesTableWidget.columnCount()):
                item = self.ui.messagesTableWidget.item(r, c)
                if item is None:
                    item = QTableWidgetItem()
                    self.ui.messagesTableWidget.setItem(r, c, item)
                item.setFont(self.item_font)
                if (r + 1) > data_count:
                    item.setText('')
                    continue
                match c:
                    case 0:
                        item.setText(f'{r + 1}')
                        item.setTextAlignment(Qt.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                    case 1:
                        item.setText(data.list[r].datetime.strftime("%d/%m/%Y, %H:%M:%S"))
                        item.setTextAlignment(Qt.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                    case 2:
                        item.setText(f'{code_prefix}{data.list[r].code:04d}')
                        item.setTextAlignment(Qt.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                    case 3:
                        item.setText(' ' + extra_message_text(data.list[r].text))
                        item.setTextAlignment(Qt.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    #
    # == END: update methods
