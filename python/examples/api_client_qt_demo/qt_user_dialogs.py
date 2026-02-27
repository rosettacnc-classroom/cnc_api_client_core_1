"""QT User Dialogs."""
#-------------------------------------------------------------------------------
# Name:         qt_user_dialogs
#
# Purpose:      QT User Dialogs
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
# Created:      27/02/2026
# Copyright:    RosettaCNC (c) 2016-2026
# Licence:      RosettaCNC License 1.0 (RCNC-1.0)
# Coding Style  https://www.python.org/dev/peps/pep-0008/
#-------------------------------------------------------------------------------
# pylint: disable=C0116 -> missing-function-docstring
# pylint: disable=R0912 -> too-many-branches
# pylint: disable=R0915 -> too-many-statements
#-------------------------------------------------------------------------------
import math

from PySide6.QtCore import Qt, QEvent, QObject, QTimer
from PySide6.QtWidgets import QDialog, QLineEdit, QPushButton

from ui_user_media_dialog import Ui_UserMediaDialog
from ui_user_message_dialog import Ui_UserMessageDialog

import cnc_api_client_core as cnc
from utils import DecimalsTrimMode, format_float

# == digits in float
FLOAT_USE_DIGITS                    = 6

# define ui geometry constants
DIALOG_FRAME_WIDTH                  = 2
DIALOG_FRAME_COLOR                  = [120, 120, 120]

DIALOG_WIDTH_MIN                    = 450
DIALOG_BOTTOM_BORDER                = 16

HTML_BORDER_LEFT                    = 20
HTML_BORDER_TOP                     = DIALOG_BOTTOM_BORDER
HTML_BORDER_RIGHT                   = 20
HTML_BORDER_BOTTOM                  = 16

OBJECTS_VERTICAL_SPACE              = 8

LABEL_EDIT_VERTICAL_SPACE           = 4
LABEL_EDIT_HORIZONTAL_SPACE         = 10

BUTTON_HORIZONTAL_SPACE             = 10


class QLineEditSelectAllOnFocusFilter(QObject):
    """Adds automatic select all when a QLineEdit get focus."""
    def eventFilter(self, obj, event):
        if event.type() == QEvent.FocusIn:
            QTimer.singleShot(0, obj.selectAll)
        return super().eventFilter(obj, event)


class UserMediaDialog(QDialog):
    """Implements User Message Dialog for Operator Request from M120 command."""

    def __init__(
        self, parent=None,
        api_client_core : cnc.CncAPIClientCore = None,
        operator_request : cnc.APIOperatorRequest = None
        ):
        # call qt inherited dialog constructor
        super().__init__(parent)

        # set Qt Designer generated ui
        self.ui = Ui_UserMediaDialog()
        self.ui.setupUi(self)

        # TODO : I will implement later when I will have specifications

        # set modal mode
        self.setModal(True)


class UserMessageDialog(QDialog):
    """Implements User Message Dialog for Operator Request from M109 command."""

    def __init__(
        self, parent=None,
        api_client_core : cnc.CncAPIClientCore = None,
        operator_request : cnc.APIOperatorRequest = None
        ):

        # call qt inherited dialog constructor
        super().__init__(parent)

        # set Qt Designer generated ui
        self.ui = Ui_UserMessageDialog()
        self.ui.setupUi(self)

        # set to be frameless
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)

        # save arguments
        self.api_client_core = api_client_core
        self.operator_request = operator_request

        # create edifield handler
        self.edit_fields = [
            {"label" : self.ui.requestLabel01, "edit" : self.ui.requestEdit01},
            {"label" : self.ui.requestLabel02, "edit" : self.ui.requestEdit02},
            {"label" : self.ui.requestLabel03, "edit" : self.ui.requestEdit03},
            {"label" : self.ui.requestLabel04, "edit" : self.ui.requestEdit04},
            {"label" : self.ui.requestLabel05, "edit" : self.ui.requestEdit05},
            {"label" : self.ui.requestLabel06, "edit" : self.ui.requestEdit06},
            {"label" : self.ui.requestLabel07, "edit" : self.ui.requestEdit07},
            {"label" : self.ui.requestLabel08, "edit" : self.ui.requestEdit08},
            {"label" : self.ui.requestLabel09, "edit" : self.ui.requestEdit09},
            {"label" : self.ui.requestLabel10, "edit" : self.ui.requestEdit10},
        ]

        # define non-public attributes
        self.__allow_close = True
        self.__in_update = False

        # link actions to all buttons
        for obj in self.findChildren(QPushButton):
            obj.clicked.connect(self.__on_action_main_execute)

        # link actions to all edits
        for obj in self.findChildren(QLineEdit):
            obj.editingFinished.connect(self.__on_editing_finished)

        # add select all on focus filter to all edits
        self.__edit_select_all_filter = QLineEditSelectAllOnFocusFilter()
        for obj in self.findChildren(QLineEdit):
            obj.installEventFilter(self.__edit_select_all_filter)

        # apply geometry
        self.__apply_geometry()

        # set modal mode
        self.setModal(True)


    # == BEG: relink of native events from inherited Qt PySide6 UI design
    #
    def reject(self):
        if self.__allow_close:
            super().reject()
    def closeEvent(self, event):
        if self.__allow_close:
            event.accept()
        else:
            event.ignore()
    def showEvent(self, event):
        super().showEvent(event)
        self.__on_form_show()
    #
    # == END: relink of native events from inherited Qt PySide6 UI design


    # == BEG: events implementation
    #
    def __on_action_main_execute(self):
        sender = self.sender()

        if sender == self.ui.continueButton:
            response = cnc.APIOperatorResponse()
            response.id = self.operator_request.id
            response.type = cnc.ORPT_CONTINUE
            response.copy_data_from_request(self.operator_request)
            self.api_client_core.set_operator_response(response)

        if sender == self.ui.stopButton:
            response = cnc.APIOperatorResponse()
            response.id = self.operator_request.id
            response.type = cnc.ORPT_STOP
            self.api_client_core.set_operator_response(response)

    def __on_editing_finished(self):

        def str_2_float_with_none_as_nan(value: str, default: float | None) -> float | None:
            txt = value.strip()
            if txt.upper() == "NAN":
                return None
            try:
                num = float(txt)
                if math.isnan(num):
                    return None
                return num
            except Exception:
                return default

        sender = self.sender()
        if sender is None:
            return

        value = sender.text().strip()

        # evaluate editable field
        for idx in range(self.operator_request.data_elements):
            edit = self.edit_fields[idx]["edit"]
            if sender == edit:
                act_val = getattr(self.operator_request, f'data_d{(idx + 1):02}')
                new_val = str_2_float_with_none_as_nan(value, act_val)
                setattr(self.operator_request, f'data_d{(idx + 1):02}', new_val)
                break

        # updated editable fields
        self.__update_editable_fields()

    def __on_form_show(self):
        self.__in_update = False

        # update editable fields
        self.__update_editable_fields()
    #
    # == END: events implementation

    # == BEG: public attributes
    #
    def force_close(self):
        self.__allow_close = True
        self.close()
    #
    # == END: public attributes


    # == BEG: non-public attributes
    #
    def __apply_geometry(self):

        # set frame to be transparent to events and ser border size and color
        self.ui.dialogFrame.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.ui.dialogFrame.setLineWidth(DIALOG_FRAME_WIDTH)
        self.ui.dialogFrame.setStyleSheet(
            f"color:rgb({DIALOG_FRAME_COLOR[0]},{DIALOG_FRAME_COLOR[1]},{DIALOG_FRAME_COLOR[2]})"
        )

        # create html content
        html = (
            '<p align="center">' +
            '<span style="font-family:Tahoma; font-size:20pt;">' +
            self.operator_request.message +
            '</span>' +
            '</p>'
        )

        # set label with html content and set it's geometry
        label = self.ui.requestLabel
        label.setTextFormat(Qt.RichText)
        label.setAlignment(Qt.AlignCenter)
        label.setContentsMargins(
            HTML_BORDER_LEFT,
            HTML_BORDER_TOP,
            HTML_BORDER_RIGHT,
            HTML_BORDER_BOTTOM
        )
        label.setWordWrap(False)
        label.setText(html)
        label_size_hint = label.sizeHint()
        dialog_width = max(DIALOG_WIDTH_MIN, label_size_hint.width())
        label.setGeometry(0, 0, dialog_width, label_size_hint.height())
        label_size = label.size()
        dialog_height = label_size.height()

        # evaluate edit fields visibility and position
        ort = self.operator_request.type
        if ort == cnc.ORQT_USER_MESSAGE_CONTINUE:
            for elem in self.edit_fields:
                elem["label"].setVisible(False)
                elem["edit"].setVisible(False)

        elif ort == cnc.ORQT_USER_MESSAGE_STOP:
            for elem in self.edit_fields:
                elem["label"].setVisible(False)
                elem["edit"].setVisible(False)

        elif ort == cnc.ORQT_USER_MESSAGE_STOP_CONTINUE:
            for elem in self.edit_fields:
                elem["label"].setVisible(False)
                elem["edit"].setVisible(False)

        elif ort == cnc.ORQT_USER_MESSAGE_VALUE_OR_STOP:
            for elem in self.edit_fields:
                elem["label"].setVisible(False)
                elem["edit"].setVisible(False)
            for i in range(1):
                label = self.edit_fields[i]["label"]
                edit = self.edit_fields[i]["edit"]
                label.setVisible(False)
                edit.setVisible(True)
                left = (dialog_width - edit.size().width()) // 2
                edit.move(left, dialog_height)
                dialog_height += edit.size().height() + LABEL_EDIT_VERTICAL_SPACE
            dialog_height += (OBJECTS_VERTICAL_SPACE - LABEL_EDIT_VERTICAL_SPACE)

        elif ort == cnc.ORQT_USER_MESSAGE_VALUES_OR_STOP:
            for elem in self.edit_fields:
                elem["label"].setVisible(False)
                elem["edit"].setVisible(False)
            for i in range(self.operator_request.data_elements):
                label = self.edit_fields[i]["label"]
                edit = self.edit_fields[i]["edit"]
                label.setVisible(True)
                edit.setVisible(True)
                left = (dialog_width - (label.size().width() + LABEL_EDIT_HORIZONTAL_SPACE + edit.size().width())) // 2
                label.move(left, dialog_height)
                left = left + label.size().width() + LABEL_EDIT_HORIZONTAL_SPACE
                edit.move(left, dialog_height)
                dialog_height += edit.size().height() + LABEL_EDIT_VERTICAL_SPACE
            dialog_height += (OBJECTS_VERTICAL_SPACE - LABEL_EDIT_VERTICAL_SPACE)

        else:
            pass # should never happen

        # evaluate buttons visibility and position
        ort = self.operator_request.type
        if ort == cnc.ORQT_USER_MESSAGE_CONTINUE:
            self.ui.stopButton.setVisible(False)
            self.ui.continueButton.setVisible(True)
            left = (dialog_width - self.ui.continueButton.size().width()) // 2
            self.ui.continueButton.move(left, dialog_height)
            self.ui.continueButton.setFocus()

        elif ort == cnc.ORQT_USER_MESSAGE_STOP:
            self.ui.stopButton.setVisible(True)
            self.ui.continueButton.setVisible(False)
            left = (dialog_width - self.ui.continueButton.size().width()) // 2
            self.ui.stopButton.move(left, dialog_height)
            self.ui.stopButton.setFocus()

        elif ort == cnc.ORQT_USER_MESSAGE_STOP_CONTINUE:
            self.ui.stopButton.setVisible(True)
            self.ui.continueButton.setVisible(True)
            left = (dialog_width / 2) - BUTTON_HORIZONTAL_SPACE - self.ui.stopButton.size().width()
            self.ui.stopButton.move(left, dialog_height)
            left = (dialog_width / 2) + BUTTON_HORIZONTAL_SPACE
            self.ui.continueButton.move(left, dialog_height)
            self.ui.continueButton.setFocus()

        elif ort == cnc.ORQT_USER_MESSAGE_VALUE_OR_STOP:
            self.ui.stopButton.setVisible(True)
            self.ui.continueButton.setVisible(True)
            left = (dialog_width / 2) - BUTTON_HORIZONTAL_SPACE - self.ui.stopButton.size().width()
            self.ui.stopButton.move(left, dialog_height)
            left = (dialog_width / 2) + BUTTON_HORIZONTAL_SPACE
            self.ui.continueButton.move(left, dialog_height)
            self.ui.continueButton.setFocus()

        elif ort == cnc.ORQT_USER_MESSAGE_VALUES_OR_STOP:
            self.ui.stopButton.setVisible(True)
            self.ui.continueButton.setVisible(True)
            left = (dialog_width / 2) - BUTTON_HORIZONTAL_SPACE - self.ui.stopButton.size().width()
            self.ui.stopButton.move(left, dialog_height)
            left = (dialog_width / 2) + BUTTON_HORIZONTAL_SPACE
            self.ui.continueButton.move(left, dialog_height)
            self.ui.continueButton.setFocus()

        else:
            pass # should never happen

        dialog_height += self.ui.continueButton.size().height() + DIALOG_BOTTOM_BORDER
        self.ui.dialogFrame.resize(dialog_width, dialog_height)
        self.resize(dialog_width, dialog_height)

    def __update_editable_fields(self):
        """Updates editable fields with related data."""
        if self.__in_update:
            return
        self.__in_update = True
        try:
            for i in range(self.operator_request.data_elements):
                edit = self.edit_fields[i]["edit"]
                value = getattr(self.operator_request, f'data_d{(i+1):02}')
                if value is None or not isinstance(value, (int, float)):
                    edit.setText('NAN')
                else:
                    edit.setText(format_float(value, FLOAT_USE_DIGITS, DecimalsTrimMode.FULL))
        finally:
            self.__in_update = False
    #
    # == END: non-public attributes
