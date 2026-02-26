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
# Created:      26/02/2026
# Copyright:    RosettaCNC (c) 2016-2026
# Licence:      RosettaCNC License 1.0 (RCNC-1.0)
# Coding Style  https://www.python.org/dev/peps/pep-0008/
#-------------------------------------------------------------------------------
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog

from ui_user_media_dialog import Ui_UserMediaDialog
from ui_user_message_dialog import Ui_UserMessageDialog

import cnc_api_client_core as cnc

V_SPACE                 = 10
BUTTON_SPACE            = 10
VERTICAL_BORDER         = 21
VERTICAL_HTML_BORDER    = 8


class UserMediaDialog(QDialog):

    def __init__(
        self, parent=None,
        operator_request : cnc.APIOperatorRequest = None
        ):
        # call qt inherited dialog constructor
        super().__init__(parent)

        # set Qt Designer generated ui
        self.ui = Ui_UserMediaDialog()
        self.ui.setupUi(self)

        self._allow_close = False
        self.operator_request = operator_request

        # set caption and modal mode
        self.setWindowTitle('Media to Operator')
        self.setModal(True)

    def reject(self):
        if self._allow_close:
            super().reject()

    def closeEvent(self, event):
        if self._allow_close:
            event.accept()
        else:
            event.ignore()

    def force_close(self):
        self._allow_close = True
        self.close()


class UserMessageDialog(QDialog):

    def __init__(
        self, parent=None,
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


        # define attribute to allow close/reject activity
        self._allow_close = True

        self._apply_geometry()

        # set modal mode
        self.setModal(True)

    def reject(self):
        if self._allow_close:
            super().reject()

    def closeEvent(self, event):
        if self._allow_close:
            event.accept()
        else:
            event.ignore()

    def force_close(self):
        self._allow_close = True
        self.close()

    # == BEG: non-public attributes
    #
    def _apply_geometry(self):

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
        label.setMargin(VERTICAL_HTML_BORDER)
        label.setWordWrap(False)
        label.setText(html)
        label_size_hint = label.sizeHint()
        dialog_width = max(450, label_size_hint.width())
        label.setGeometry(0, 0, dialog_width, label_size_hint.height())
        label_size = label.size()
        dialog_height = label_size.height() + VERTICAL_HTML_BORDER

        # evaluate edit fields visibility and position
        ort = self.operator_request.type
        if ort == cnc.OPRT_USER_MESSAGE_CONTINUE:
            for elem in self.edit_fields:
                elem["label"].setVisible(False)
                elem["edit"].setVisible(False)

        elif ort == cnc.OPRT_USER_MESSAGE_STOP:
            for elem in self.edit_fields:
                elem["label"].setVisible(False)
                elem["edit"].setVisible(False)

        elif ort == cnc.OPRT_USER_MESSAGE_STOP_CONTINUE:
            for elem in self.edit_fields:
                elem["label"].setVisible(False)
                elem["edit"].setVisible(False)

        elif ort == cnc.OPRT_USER_MESSAGE_VALUE_OR_STOP:
            for elem in self.edit_fields:
                elem["label"].setVisible(False)
                elem["edit"].setVisible(False)
            for i in range(1):
                label = self.edit_fields[i]["label"]
                edit = self.edit_fields[i]["edit"]
                label.setVisible(True)
                edit.setVisible(True)
                left = (dialog_width - (label.size().width() + 10 + edit.size().width())) // 2
                label.move(left, dialog_height)
                left = left + label.size().width() + 10
                edit.move(left, dialog_height)
                dialog_height += edit.size().height() + 4
            dialog_height += (VERTICAL_HTML_BORDER - 4)

        elif ort == cnc.OPRT_USER_MESSAGE_VALUES_OR_STOP:
            for elem in self.edit_fields:
                elem["label"].setVisible(False)
                elem["edit"].setVisible(False)
            for i in range(self.operator_request.data_elements):
                label = self.edit_fields[i]["label"]
                edit = self.edit_fields[i]["edit"]
                label.setVisible(True)
                edit.setVisible(True)
                left = (dialog_width - (label.size().width() + 10 + edit.size().width())) // 2
                label.move(left, dialog_height)
                left = left + label.size().width() + 10
                edit.move(left, dialog_height)
                dialog_height += edit.size().height() + 4
            dialog_height += (VERTICAL_HTML_BORDER - 4)

        else:
            pass # should never happen

        # evaluate buttons visibility and position
        ort = self.operator_request.type
        if ort == cnc.OPRT_USER_MESSAGE_CONTINUE:
            self.ui.stopButton.setVisible(False)
            self.ui.continueButton.setVisible(True)
            left = (dialog_width - self.ui.continueButton.size().width()) / 2
            self.ui.continueButton.move(left, dialog_height)
            self.ui.continueButton.setFocus()

        elif ort == cnc.OPRT_USER_MESSAGE_STOP:
            self.ui.stopButton.setVisible(True)
            self.ui.continueButton.setVisible(False)
            left = (dialog_width - self.ui.continueButton.size().width()) / 2
            self.ui.stopButton.move(left, dialog_height)
            self.ui.stopButton.setFocus()

        elif ort == cnc.OPRT_USER_MESSAGE_STOP_CONTINUE:
            self.ui.stopButton.setVisible(True)
            self.ui.continueButton.setVisible(True)
            left = (dialog_width / 2) - BUTTON_SPACE - self.ui.stopButton.size().width()
            self.ui.stopButton.move(left, dialog_height)
            left = (dialog_width / 2) + BUTTON_SPACE
            self.ui.continueButton.move(left, dialog_height)
            self.ui.continueButton.setFocus()

        elif ort == cnc.OPRT_USER_MESSAGE_VALUE_OR_STOP:
            self.ui.stopButton.setVisible(True)
            self.ui.continueButton.setVisible(True)
            left = (dialog_width / 2) - BUTTON_SPACE - self.ui.stopButton.size().width()
            self.ui.stopButton.move(left, dialog_height)
            left = (dialog_width / 2) + BUTTON_SPACE
            self.ui.continueButton.move(left, dialog_height)
            self.ui.continueButton.setFocus()

        elif ort == cnc.OPRT_USER_MESSAGE_VALUES_OR_STOP:
            self.ui.stopButton.setVisible(True)
            self.ui.continueButton.setVisible(True)
            left = (dialog_width / 2) - BUTTON_SPACE - self.ui.stopButton.size().width()
            self.ui.stopButton.move(left, dialog_height)
            left = (dialog_width / 2) + BUTTON_SPACE
            self.ui.continueButton.move(left, dialog_height)
            self.ui.continueButton.setFocus()

        else:
            pass # should never happen

        dialog_height = dialog_height + self.ui.continueButton.size().height() + V_SPACE
        self.resize(dialog_width, dialog_height)
    #
    # == END: non-public attributes
