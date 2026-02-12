"""API Client Demo using Qt PySide6 UI."""
#-------------------------------------------------------------------------------
# Name:         api_client_qt_demo_desktop_view
#
# Purpose:      API Client Qt Demo Desktop View
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
# Created:      11/02/2026
# Copyright:    RosettaCNC (c) 2016-2026
# Licence:      RosettaCNC License 1.0 (RCNC-1.0)
# Coding Style  https://www.python.org/dev/peps/pep-0008/
#-------------------------------------------------------------------------------
# pylint: disable=C0103 -> invalid-name
# pylint: disable=C0123 -> unidiomatic-typecheck
# pylint: disable=C0301 -> line-too-long
# pylint: disable=C0302 -> too-many-lines
# pylint: disable=R0902 -> too-many-instance-attributes
# pylint: disable=R0911 -> too-many-return-statements
# pylint: disable=R0912 -> too-many-branches
# pylint: disable=R0914 -> too-many-locals
# pylint: disable=R0915 -> too-many-statements
# pylint: disable=W0105 -> pointless-string-statement
# pylint: disable=W0201 -> attribute-defined-outside-init   ## take care when you use that ##
# pylint: disable=W0238 -> unused-private-member
# pylint: disable=W0612 -> unused-variable
# pylint: disable=W0718 -> broad-exception-caught           ## take care when you use that ##
#-------------------------------------------------------------------------------
import os
import time
import ipaddress
from statistics import median
from collections import namedtuple

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QFileDialog,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QTableWidgetItem
)

from qt_gcode_highlighter import GCodeHighlighter

from ui_desktop_view import Ui_DesktopView

from utils import DecimalsTrimMode, format_float, is_in_str_list_range

import cnc_api_client_core as cnc
from cnc_memento import CncMemento

# define here the version number to show in view caption
VERSION = '1.0.1'

# == application info
APP_TITLE                           = f'API Client Demo with Qt PySide6 UI - {VERSION}'

# == default constants
DEF_API_SERVER_HOST                 = '127.0.0.1'
DEF_API_SERVER_PORT                 = 8000
DEF_API_SERVER_USE_TLS              = False
DEF_STAY_ON_TOP                     = False

# == settings file name
SETTINGS_FILE_NAME                  = 'settings.xml'

DEF_LOAD_PROGRAM_FILE_NAME          = 'D:\\gcode-repository\\_test_\\heavy\\2.8-milions.ngc'
DEF_SAVE_PROGRAM_FILE_NAME          = 'D:\\gcode-repository\\_test_\\heavy\\2.8-milions_new.ngc'

# == debug settings
DBG_UPD_TICK_TIME                   = True

# == program constants
OVERRIDE_SEATTLE_TIME               = 500

# == digits in float
OFFSET_USE_DIGITS                   = 6

# == api server connection state
ASCS_DISCONNECTED                   = 0
ASCS_CONNECTED                      = 1
ASCS_ERROR                          = 2

# == api server connection state texts (english)
ASCS_TEXTS = [
    'DISCONNECTED',
    'CONNECTED',
    'ERROR'
]

# == compile state texts (english)
CS_TEXTS = [
    'INIT',
    'READY',
    'ERROR',
    'FIRST STEP',
    'FIRST STEP RUNNING',
    'WAITING FOR DATA',
    'WAITING FOR DATA RUNNING',
    'FINISHED'
]

# == state machine texts (english)
SM_TEXTS = [
    'DISCONNECTED',
    'SIMULATOR',
    'INIT',
    'INIT FIELDBUS',
    'ALARM',
    'IDLE',
    'HOMING',
    'JOG',
    'RUN',
    'PAUSE',
    'LIMIT',
    'MEASURE TOOL',
    'SCAN 3D',
    'SAFETY JOG',
    'CHANGE TOOL',
    'SAFETY',
    'WAIT MAIN POWER',
    'RETRACT'
]

# == spindle status texts (english)
SS_TEXTS = ['OFF', 'CW', 'CCW']

# keyboard constants
VK_RETURN                           = 0x0D

# == apply wcs change mode
AWCM_ACTIVATE_WCS_ONLY              = 0         # apply wcs changes mode: activate wcs only
AWCM_SET_WCS_OFFSET_ONLY            = 1         # apply wcs changes mode: set wcs offset only
AWCM_SET_WCS_OFFSET_AND_ACTIVATE    = 2         # apply wcs changes mode: set wcs offset and activate

AxisControls = namedtuple('AxisControls', ['label', 'value'])

class ApiClientQtDemoDesktopView(QMainWindow):
    """Xxx..."""

    def __init__(self):
        # call qt inherited view constructor
        super().__init__()

        # set main ui
        self.ui = Ui_DesktopView()
        self.ui.setupUi(self)

        # set caption
        self.setWindowTitle(APP_TITLE)

        # set window ui to fixed size
        self.setFixedSize(self.size())

        # set current persistable save version
        self.__persistable_save_version = 1

        # apply and set gcode editor highlighter
        self.highlighter = GCodeHighlighter(self.ui.gcodeProgramEdit.document())
        self.ui.gcodeProgramEdit.setStyleSheet(
        """
            QPlainTextEdit {
                background-color: #1E1E1E;
                color: #F8F8F2;
                border: 1px solid #44475A;
                selection-background-color: #44475A;
                selection-color: #F8F8F2;
                padding: 10px;
            }
        """
        )

        # create and set update timer
        self.tmrUpdate = QTimer(self)
        self.tmrUpdate.setInterval(1)
        self.tmrUpdate.timeout.connect(self.__on_timer_update)
        self.tmrUpdate.setSingleShot(False)

        # create labels for status bar
        self.StateMachineLabel = QLabel("")
        self.StateMachineLabel.setMinimumWidth(629)
        self.StateMachineLabel.setMaximumWidth(629)
        self.APIServerConnectionStateLabel = QLabel("")
        self.APIServerConnectionStateLabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.ui.StatusBar.setContentsMargins(6, 0, 0, 0)
        self.ui.StatusBar.addPermanentWidget(self.StateMachineLabel)
        self.ui.StatusBar.addPermanentWidget(self.APIServerConnectionStateLabel, 1)

        # lock tables header resize
        self.ui.csOffsetsTable.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.ui.csOffsetsTable.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)

        # declare class public attributes (for pylint check)
        self.api = None
        self.ctx = None
        self.api_server_connection_state = None
        self.stay_on_top_changed = None
        self.axes_mask_enablings_in_use = None
        self.cnc_resume_after_stop_from_line = None
        self.cnc_start_from_line = None
        self.connection_with_cnc = None
        # FDIOImageBitmap: TBitmap
        self.in_update = None
        # FMachiningInfoImageBitmap: TBitmap
        # FOverrideFastWatch: TStopWatch
        # FOverrideFeedCustom1Watch: TStopWatch
        # FOverrideFeedCustom2Watch: TStopWatch
        # FOverrideFeedWatch: TStopWatch
        # FOverrideJogWatch: TStopWatch
        # FOverrideSpindleWatch: TStopWatch

        # declare editable fields support attributes
        self.api_server_host = None
        self.api_server_port = None
        self.api_server_use_tls = None
        self.stay_on_top = None
        self.program_load_file_name = ''
        self.program_save_file_name = ''
        self.set_program_position_a = 0.0
        self.set_program_position_b = 0.0
        self.set_program_position_c = 0.0
        self.set_program_position_x = 0.0
        self.set_program_position_y = 0.0
        self.set_program_position_z = 0.0
        self.set_wcs = 1
        self.set_wcs_x = 0.0
        self.set_wcs_y = 0.0
        self.set_wcs_z = 0.0
        self.set_wcs_a = 0.0
        self.set_wcs_b = 0.0
        self.set_wcs_c = 0.0
        self.apply_wcs_changes_mode = AWCM_SET_WCS_OFFSET_ONLY
        self.units_mode = cnc.UM_METRIC

        # in use cached variables to reduce UI update time
        self.system_info_in_use = None
        self.coordinates_system_info_in_use = None

        # create an action to manage all event executions
        self.on_action_main_execute = QAction("", self)
        self.on_action_main_execute.triggered.connect(self.__on_action_main_execute)

        # link actions to all edit
        for obj in self.findChildren(QLineEdit):
            obj.editingFinished.connect(self.__on_editing_finished)

        # link actions to all buttons
        for obj in self.findChildren(QPushButton):
            name = obj.objectName()
            if name.startswith('cncJogCommand'):
                obj.pressed.connect(self.__on_cnc_jog_command_mouse_down)
                obj.released.connect(self.__on_cnc_jog_command_mouse_up)
            else:
                obj.clicked.connect(self.__on_action_main_execute)

        # link actions to all radio button
        self.apply_wcs_mode_group = QButtonGroup(self)
        self.apply_wcs_mode_group.addButton(self.ui.csActivateWCSOnlyRadioButton, 0)
        self.apply_wcs_mode_group.addButton(self.ui.csSetWCSOffsetOnlyRadioButton, 1)
        self.apply_wcs_mode_group.addButton(self.ui.csSetWCSOffsetAndActivateRadioButton, 2)
        self.apply_wcs_mode_group.idClicked.connect(self.__on_button_group_clicked)

        # link actions to all checkbox
        for obj in self.findChildren(QCheckBox):
            obj.clicked.connect(self.__on_check_box_clicked)

        # create array of axis related objects [ helper attributes ]
        self.axes = ['X', 'Y', 'Z', 'A', 'B', 'C']
        self.axis_masks = [
            cnc.X_AXIS_MASK,
            cnc.Y_AXIS_MASK,
            cnc.Z_AXIS_MASK,
            cnc.A_AXIS_MASK,
            cnc.B_AXIS_MASK,
            cnc.C_AXIS_MASK,
        ]
        def create_axis_controls(prefix):
            return [
                AxisControls(
                    label=getattr(self.ui, f'{prefix}{axis}Label'),
                    value=getattr(self.ui, f'{prefix}{axis}Value')
                )
                for axis in self.axes
            ]
        self.axis_mcs = create_axis_controls('mcs')
        self.axis_wcs = create_axis_controls('wcs')
        self.axis_avl = create_axis_controls('avl')
        self.axis_wof = create_axis_controls('wof')
        self.axis_mtp = create_axis_controls('mtp')
        self.axis_ptp = create_axis_controls('ptp')
        self.axis_jop = create_axis_controls('jop')
        self.all_axis_controls = [
            self.axis_mcs,
            self.axis_wcs,
            self.axis_avl,
            self.axis_wof,
            self.axis_mtp,
            self.axis_ptp,
            self.axis_jop,
        ]
        self.axis_data_mapping = [
            (self.axis_mcs, 'machine_position', False),
            (self.axis_wcs, 'program_position', False),
            (self.axis_avl, 'actual_velocity', True),
            (self.axis_wof, 'working_offset', False),
            (self.axis_mtp, 'machine_target_position', False),
            (self.axis_ptp, 'program_target_position', False),
            (self.axis_jop, 'joint_position', False),
        ]


    # == BEG: relink of native events from inherited Qt PySide6 UI design
    #
    def closeEvent(self, event):
        self.__on_form_close()
        super().closeEvent(event)
    def showEvent(self, event):
        super().showEvent(event)
        self.__on_form_show()
    #
    # == BEG: relink of native events from inherited Qt PySide6 UI design


    # == BEG: events implementation
    #
    def __on_action_main_execute(self):
        sender = self.sender()

        # event main view
        if sender == self.ui.ServerConnectDisconnectButton:
            if self.api_server_connection_state == ASCS_DISCONNECTED:
                if self.api.connect(self.api_server_host, self.api_server_port, self.api_server_use_tls):
                    self.api_server_connection_state = ASCS_CONNECTED
                else:
                    self.api.close()
                    self.api_server_connection_state = ASCS_ERROR
            elif self.api_server_connection_state == ASCS_CONNECTED:
                if self.api.is_connected:
                    if not self.api.close():
                        self.api_server_connection_state = ASCS_ERROR
                        return
                self.api_server_connection_state = ASCS_DISCONNECTED
            elif self.api_server_connection_state == ASCS_ERROR:
                if self.api.connect(self.api_server_host, self.api_server_port, self.api_server_use_tls):
                    self.api_server_connection_state = ASCS_CONNECTED
                else:
                    self.api.close()
                    self.api_server_connection_state = ASCS_ERROR

        # event commands
        if sender == self.ui.CNCConnectionOpenButton:
            self.api.cnc_connection_open(use_ui=True)
        if sender == self.ui.CNCConnectionCloseButton:
            self.api.cnc_connection_close()

        if sender == self.ui.cncStartButton:
            self.api.cnc_start()
        if sender == self.ui.cncStopButton:
            self.api.cnc_stop()
        if sender == self.ui.cncPauseButton:
            self.api.cnc_pause()
        if sender == self.ui.cncContinueButton:
            self.api.cnc_continue()
        if sender == self.ui.cncResumeAfterStopButton:
            self.api.cnc_resume(0)

        if sender == self.ui.resetAlarmsButton:
            self.api.reset_alarms()
        if sender == self.ui.resetAlarmsHistoryButton:
            self.api.reset_alarms_history()
        if sender == self.ui.resetWarningsButton:
            self.api.reset_warnings()
        if sender == self.ui.resetWarningsHistoryButton:
            self.api.reset_warnings_history()

        # event tab program
        if sender == self.ui.programNewButton:
            self.api.program_new()
        if sender == self.ui.programLoadSelectFileButton:
            file_path, selected_filter = QFileDialog.getOpenFileName(
                self,
                "Select a file",
                "",  # start directory, e.g. "C:/"
                "All files (*.*);;Text files (*.txt);;Images (*.png *.jpg *.jpeg)"
            )
            if file_path:
                self.program_load_file_name = file_path
                self.__update_editable_fields()
        if sender == self.ui.programLoadButton:
            self.api.program_load(self.program_load_file_name)
        if sender == self.ui.programSaveButton:
            self.api.program_save()
        if sender == self.ui.programSaveAsButton:
            self.api.program_save_as(self.program_save_file_name)

        # event tab g-code
        if sender == self.ui.gcodeGetProgramTextButton:
            data = self.api.get_program_info()
            if data.has_data:
                self.ui.gcodeProgramEdit.setPlainText(data.code)
        if sender == self.ui.gcodeSetProgramTextButton:
            self.api.program_gcode_set_text(self.ui.gcodeProgramEdit.toPlainText())
        if sender == self.ui.gcodeAddProgramTextButton:
            self.api.program_gcode_add_text(self.ui.gcodeAddProgramTextEdit.text())
        if sender == self.ui.gcodeClearProgramButton:
            self.api.program_new()
            self.ui.gcodeProgramEdit.setPlainText('')
            self.ui.gcodeAddProgramTextEdit.setText('')

        # event tab wcs
        if sender == self.ui.csApplyWCSChangesButton:
            wcs = self.set_wcs
            offset = [None, None, None, None, None, None]
            if self.apply_wcs_changes_mode in [AWCM_SET_WCS_OFFSET_ONLY, AWCM_SET_WCS_OFFSET_AND_ACTIVATE]:
                if self.ui.csSetWCSXCheckBox.isChecked():
                    offset[0] = self.set_wcs_x
                if self.ui.csSetWCSYCheckBox.isChecked():
                    offset[1] = self.set_wcs_y
                if self.ui.csSetWCSZCheckBox.isChecked():
                    offset[2] = self.set_wcs_z
                if self.ui.csSetWCSACheckBox.isChecked():
                    offset[3] = self.set_wcs_a
                if self.ui.csSetWCSBCheckBox.isChecked():
                    offset[4] = self.set_wcs_b
                if self.ui.csSetWCSCCheckBox.isChecked():
                    offset[5] = self.set_wcs_c
            activate = self.apply_wcs_changes_mode in [AWCM_ACTIVATE_WCS_ONLY, AWCM_SET_WCS_OFFSET_AND_ACTIVATE]
            self.api.set_wcs_info(wcs, offset, activate=activate)
            print(f'{wcs} | {offset} | {activate}')

        # event tab cnc
        if sender == self.ui.cncProgramAnalysisMTButton:
            pass
        if sender == self.ui.cncProgramAnalysisRTButton:
            pass
        if sender == self.ui.cncProgramAnalysisRFButton:
            pass
        if sender == self.ui.cncProgramAnalysisRVButton:
            pass
        if sender == self.ui.cncProgramAnalysisRZButton:
            pass
        if sender == self.ui.cncProgramAnalysisAbortButton:
            pass
        if sender == self.ui.cncStartButton:
            pass
        if sender == self.ui.cncStopButton:
            pass
        if sender == self.ui.cncPauseButton:
            pass
        if sender == self.ui.cncContinueButton:
            pass
        if sender == self.ui.cncStartFromLineButton:
            pass
        if sender == self.ui.cncResumeAfterStopButton:
            pass
        if sender == self.ui.cncResumeAfterStopFromLineButton:
            pass

        # event tab jog
        if sender == self.ui.setProgramPositionXButton:
            self.api.set_program_position_x(self.set_program_position_x)
        if sender == self.ui.setProgramPositionYButton:
            self.api.set_program_position_y(self.set_program_position_y)
        if sender == self.ui.setProgramPositionZButton:
            self.api.set_program_position_z(self.set_program_position_z)
        if sender == self.ui.setProgramPositionAButton:
            self.api.set_program_position_a(self.set_program_position_a)
        if sender == self.ui.setProgramPositionBButton:
            self.api.set_program_position_b(self.set_program_position_b)
        if sender == self.ui.setProgramPositionCButton:
            self.api.set_program_position_c(self.set_program_position_c)

        if sender == self.ui.jogSTOPButton:
            self.api.cnc_stop()

        # event tab overrides
        # event tab homing
        # event tab mdi
        # event tab d i/o
        # event tab a i/o
        # event tab scanning laser
        # event tab machining info

        # event tab ui dialogs
        if sender == self.ui.uidAboutButton:
            self.api.show_ui_dialog(cnc.UID_ABOUT)
        if sender == self.ui.uidATCManagementButton:
            self.api.show_ui_dialog(cnc.UID_ATC_MANAGEMENT)
        if sender == self.ui.uidBoardEtherCATMonitorButton:
            self.api.show_ui_dialog(cnc.UID_BOARD_ETHERCAT_MONITOR)
        if sender == self.ui.uidBoardFirmwareManagerButton:
            self.api.show_ui_dialog(cnc.UID_BOARD_FIRMWARE_MANAGER)
        if sender == self.ui.uidBoardMonitorButton:
            self.api.show_ui_dialog(cnc.UID_BOARD_MONITOR)
        if sender == self.ui.uidBoardSettingsButton:
            self.api.show_ui_dialog(cnc.UID_BOARD_SETTINGS)
        if sender == self.ui.uidChangeBoardIPButton:
            self.api.show_ui_dialog(cnc.UID_CHANGE_BOARD_IP)
        if sender == self.ui.uidMacrosManagementButton:
            self.api.show_ui_dialog(cnc.UID_MACROS_MANAGEMENT)
        if sender == self.ui.uidParametersLibraryButton:
            self.api.show_ui_dialog(cnc.UID_PARAMETERS_LIBRARY)
        if sender == self.ui.uidProgramSettingsButton:
            self.api.show_ui_dialog(cnc.UID_PROGRAM_SETTINGS)
        if sender == self.ui.uidToolsLibraryButton:
            self.api.show_ui_dialog(cnc.UID_TOOLS_LIBRARY)
        if sender == self.ui.uidWorkCoordinatesButton:
            self.api.show_ui_dialog(cnc.UID_WORK_COORDINATES)

        # event system info

    def __on_action_main_update(self):
        if self.api_server_connection_state in [ASCS_DISCONNECTED, ASCS_ERROR]:

            # update commands
            self.ui.CNCConnectionCloseButton.setEnabled(False)
            self.ui.CNCConnectionOpenButton.setEnabled(False)

            self.ui.cncStartButton.setEnabled(False)
            self.ui.cncStopButton.setEnabled(False)
            self.ui.cncPauseButton.setEnabled(False)
            self.ui.cncContinueButton.setEnabled(False)
            self.ui.cncResumeAfterStopButton.setEnabled(False)

            self.ui.resetAlarmsButton.setEnabled(False)
            self.ui.resetAlarmsHistoryButton.setEnabled(False)
            self.ui.resetWarningsButton.setEnabled(False)
            self.ui.resetWarningsHistoryButton.setEnabled(False)

            # update tab program
            self.ui.programNewButton.setEnabled(False)
            self.ui.programLoadSelectFileButton.setEnabled(False)
            self.ui.programLoadButton.setEnabled(False)
            self.ui.programSaveButton.setEnabled(False)
            self.ui.programSaveAsButton.setEnabled(False)

            # update tab g-code
            self.ui.gcodeGetProgramTextButton.setEnabled(False)
            self.ui.gcodeSetProgramTextButton.setEnabled(False)
            self.ui.gcodeAddProgramTextButton.setEnabled(False)
            self.ui.gcodeClearProgramButton.setEnabled(False)

            # update tab wcs
            self.ui.csApplyWCSChangesButton.setEnabled(False)

            # update tab jog
            self.ui.cncJogCommandXMButton.setEnabled(False)
            self.ui.cncJogCommandXPButton.setEnabled(False)
            self.ui.cncJogCommandYMButton.setEnabled(False)
            self.ui.cncJogCommandYPButton.setEnabled(False)
            self.ui.cncJogCommandZMButton.setEnabled(False)
            self.ui.cncJogCommandZPButton.setEnabled(False)
            self.ui.cncJogCommandAMButton.setEnabled(False)
            self.ui.cncJogCommandAPButton.setEnabled(False)
            self.ui.cncJogCommandBMButton.setEnabled(False)
            self.ui.cncJogCommandBPButton.setEnabled(False)
            self.ui.cncJogCommandCMButton.setEnabled(False)
            self.ui.cncJogCommandCPButton.setEnabled(False)

            self.ui.jogSTOPButton.setEnabled(False)

            self.ui.setProgramPositionXButton.setEnabled(False)
            self.ui.setProgramPositionYButton.setEnabled(False)
            self.ui.setProgramPositionZButton.setEnabled(False)
            self.ui.setProgramPositionAButton.setEnabled(False)
            self.ui.setProgramPositionBButton.setEnabled(False)
            self.ui.setProgramPositionCButton.setEnabled(False)

            # update tab overrides
            # update tab homing
            # update tab mdi
            # update tab d i/o
            # update tab a i/o
            # update tab scanning laser
            # update tab machining info

            # update tab ui dialogs
            self.ui.uidAboutButton.setEnabled(False)
            self.ui.uidATCManagementButton.setEnabled(False)
            self.ui.uidBoardEtherCATMonitorButton.setEnabled(False)
            self.ui.uidBoardFirmwareManagerButton.setEnabled(False)
            self.ui.uidBoardMonitorButton.setEnabled(False)
            self.ui.uidBoardSettingsButton.setEnabled(False)
            self.ui.uidChangeBoardIPButton.setEnabled(False)
            self.ui.uidMacrosManagementButton.setEnabled(False)
            self.ui.uidParametersLibraryButton.setEnabled(False)
            self.ui.uidProgramSettingsButton.setEnabled(False)
            self.ui.uidToolsLibraryButton.setEnabled(False)
            self.ui.uidWorkCoordinatesButton.setEnabled(False)

            # update tab system info
        else:
            connected = self.ctx.cnc_info.state_machine != cnc.SM_DISCONNECTED
            enabled_commands = self.ctx.enabled_commands

            # update commands
            self.ui.CNCConnectionCloseButton.setEnabled(connected)
            self.ui.CNCConnectionOpenButton.setEnabled(not connected)

            self.ui.cncStartButton.setEnabled(enabled_commands.cnc_start)
            self.ui.cncStopButton.setEnabled(enabled_commands.cnc_stop)
            self.ui.cncPauseButton.setEnabled(enabled_commands.cnc_pause)
            self.ui.cncContinueButton.setEnabled(enabled_commands.cnc_continue)
            self.ui.cncResumeAfterStopButton.setEnabled(enabled_commands.cnc_resume)

            self.ui.resetAlarmsButton.setEnabled(enabled_commands.reset_alarms)
            self.ui.resetAlarmsHistoryButton.setEnabled(enabled_commands.reset_alarms_history)
            self.ui.resetWarningsButton.setEnabled(enabled_commands.reset_warnings)
            self.ui.resetWarningsHistoryButton.setEnabled(enabled_commands.reset_warnings_history)

            # update tab program
            self.ui.programNewButton.setEnabled(enabled_commands.program_new)
            self.ui.programLoadSelectFileButton.setEnabled(enabled_commands.program_load)
            self.ui.programLoadButton.setEnabled(enabled_commands.program_load)
            self.ui.programSaveButton.setEnabled(enabled_commands.program_save)
            self.ui.programSaveAsButton.setEnabled(enabled_commands.program_save_as)

            # update tab g-code
            self.ui.gcodeGetProgramTextButton.setEnabled(enabled_commands.has_data)
            self.ui.gcodeSetProgramTextButton.setEnabled(enabled_commands.program_gcode_set_text)
            self.ui.gcodeAddProgramTextButton.setEnabled(enabled_commands.program_gcode_add_text)
            self.ui.gcodeClearProgramButton.setEnabled(enabled_commands.program_gcode_set_text)

            # update tab wcs
            enabled = False
            has_offset = (
                self.ui.csSetWCSXCheckBox.isChecked() or
                self.ui.csSetWCSYCheckBox.isChecked() or
                self.ui.csSetWCSZCheckBox.isChecked() or
                self.ui.csSetWCSACheckBox.isChecked() or
                self.ui.csSetWCSBCheckBox.isChecked() or
                self.ui.csSetWCSCCheckBox.isChecked()
            )
            if enabled_commands.cnc_parameters:
                if self.apply_wcs_changes_mode == AWCM_ACTIVATE_WCS_ONLY:
                    enabled = connected
                elif self.apply_wcs_changes_mode == AWCM_SET_WCS_OFFSET_ONLY:
                    enabled = has_offset
                elif self.apply_wcs_changes_mode == AWCM_SET_WCS_OFFSET_AND_ACTIVATE:
                    enabled = connected and has_offset
            self.ui.csApplyWCSChangesButton.setEnabled(enabled)

            # update tab cnc

            # update tab jog
            cnc_jog_command = self.ctx.enabled_commands.cnc_jog_command
            self.ui.cncJogCommandXMButton.setEnabled((cnc_jog_command & cnc.X_AXIS_MASK) > 0)
            self.ui.cncJogCommandXPButton.setEnabled((cnc_jog_command & cnc.X_AXIS_MASK) > 0)
            self.ui.cncJogCommandYMButton.setEnabled((cnc_jog_command & cnc.Y_AXIS_MASK) > 0)
            self.ui.cncJogCommandYPButton.setEnabled((cnc_jog_command & cnc.Y_AXIS_MASK) > 0)
            self.ui.cncJogCommandZMButton.setEnabled((cnc_jog_command & cnc.Z_AXIS_MASK) > 0)
            self.ui.cncJogCommandZPButton.setEnabled((cnc_jog_command & cnc.Z_AXIS_MASK) > 0)
            self.ui.cncJogCommandAMButton.setEnabled((cnc_jog_command & cnc.A_AXIS_MASK) > 0)
            self.ui.cncJogCommandAPButton.setEnabled((cnc_jog_command & cnc.A_AXIS_MASK) > 0)
            self.ui.cncJogCommandBMButton.setEnabled((cnc_jog_command & cnc.B_AXIS_MASK) > 0)
            self.ui.cncJogCommandBPButton.setEnabled((cnc_jog_command & cnc.B_AXIS_MASK) > 0)
            self.ui.cncJogCommandCMButton.setEnabled((cnc_jog_command & cnc.C_AXIS_MASK) > 0)
            self.ui.cncJogCommandCPButton.setEnabled((cnc_jog_command & cnc.C_AXIS_MASK) > 0)

            self.ui.jogSTOPButton.setEnabled(self.ctx.enabled_commands.cnc_stop)

            set_program_position = self.ctx.enabled_commands.set_program_position
            self.ui.setProgramPositionXButton.setEnabled((set_program_position & cnc.X_AXIS_MASK) > 0)
            self.ui.setProgramPositionYButton.setEnabled((set_program_position & cnc.Y_AXIS_MASK) > 0)
            self.ui.setProgramPositionZButton.setEnabled((set_program_position & cnc.Z_AXIS_MASK) > 0)
            self.ui.setProgramPositionAButton.setEnabled((set_program_position & cnc.A_AXIS_MASK) > 0)
            self.ui.setProgramPositionBButton.setEnabled((set_program_position & cnc.B_AXIS_MASK) > 0)
            self.ui.setProgramPositionCButton.setEnabled((set_program_position & cnc.C_AXIS_MASK) > 0)

            # update tab overrides
            # update tab homing
            # update tab mdi
            # update tab d i/o
            # update tab a i/o
            # update tab scanning laser
            # update tab machining info

            # update tab ui dialogs
            uid_available = self.ctx.enabled_commands.show_ui_dialog
            self.ui.uidAboutButton.setEnabled(uid_available)
            self.ui.uidATCManagementButton.setEnabled(uid_available)
            self.ui.uidBoardEtherCATMonitorButton.setEnabled(uid_available)
            self.ui.uidBoardFirmwareManagerButton.setEnabled(uid_available)
            self.ui.uidBoardMonitorButton.setEnabled(uid_available)
            self.ui.uidBoardSettingsButton.setEnabled(uid_available)
            self.ui.uidChangeBoardIPButton.setEnabled(uid_available)
            self.ui.uidMacrosManagementButton.setEnabled(uid_available)
            self.ui.uidParametersLibraryButton.setEnabled(uid_available)
            self.ui.uidProgramSettingsButton.setEnabled(uid_available)
            self.ui.uidToolsLibraryButton.setEnabled(uid_available)
            self.ui.uidWorkCoordinatesButton.setEnabled(uid_available)

            # update tab system info

        # update server connect/disconnect button
        self.ui.ServerConnectDisconnectButton.setEnabled(True)
        if self.api_server_connection_state == ASCS_CONNECTED:
            self.ui.ServerConnectDisconnectButton.setText('Disconnect')
        else:
            self.ui.ServerConnectDisconnectButton.setText('Connect')

    def __on_button_group_clicked(self, button_id: int):
        sender = self.sender()

        if sender == self.apply_wcs_mode_group:
            self.apply_wcs_changes_mode = button_id
            self.__update_editable_fields()

    def __on_check_box_clicked(self):
        if self.in_update:
            return

        sender = self.sender()
        value = sender.isChecked()

        if sender == self.ui.useTLSCheckBox:
            self.api_server_use_tls = value

        if sender == self.ui.stayOnTopCheckBox:
            self.stay_on_top = value
            self.stay_on_top_changed = True

    def __on_cnc_jog_command_mouse_down(self):
        sender = self.sender()

        self.api.cnc_jog_command(cnc.JC_NONE)

        if sender == self.ui.cncJogCommandXMButton:
            self.api.cnc_jog_command(cnc.JC_X_BW)
        if sender == self.ui.cncJogCommandXPButton:
            self.api.cnc_jog_command(cnc.JC_X_FW)

        if sender == self.ui.cncJogCommandYMButton:
            self.api.cnc_jog_command(cnc.JC_Y_BW)
        if sender == self.ui.cncJogCommandYPButton:
            self.api.cnc_jog_command(cnc.JC_Y_FW)

        if sender == self.ui.cncJogCommandZMButton:
            self.api.cnc_jog_command(cnc.JC_Z_BW)
        if sender == self.ui.cncJogCommandZPButton:
            self.api.cnc_jog_command(cnc.JC_Z_FW)

        if sender == self.ui.cncJogCommandAMButton:
            self.api.cnc_jog_command(cnc.JC_A_BW)
        if sender == self.ui.cncJogCommandAPButton:
            self.api.cnc_jog_command(cnc.JC_A_FW)

        if sender == self.ui.cncJogCommandBMButton:
            self.api.cnc_jog_command(cnc.JC_B_BW)
        if sender == self.ui.cncJogCommandBPButton:
            self.api.cnc_jog_command(cnc.JC_B_FW)

        if sender == self.ui.cncJogCommandCMButton:
            self.api.cnc_jog_command(cnc.JC_C_BW)
        if sender == self.ui.cncJogCommandCPButton:
            self.api.cnc_jog_command(cnc.JC_C_FW)

    def __on_cnc_jog_command_mouse_up(self):
        self.api.cnc_jog_command(cnc.JC_NONE)

    def __on_editing_finished(self):

        def try_str_2_float(dest_attr_name: str) -> bool:
            try:
                val = float(value)
                setattr(self, dest_attr_name, val)
                return True
            except Exception:
                return False

        def try_str_2_int(dest_attr_name: str, min_val: int | None, max_val: int | None) -> bool:
            try:
                val = int(value)

                # disallow bool-like input explicitly (e.g., value is True/False)
                if type(value) is bool:
                    return False

                # validate min/max types (allow None or int)
                if min_val is not None and type(min_val) is not int:
                    return False
                if max_val is not None and type(max_val) is not int:
                    return False

                # range checks
                if min_val is not None and val < min_val:
                    return False
                if max_val is not None and val > max_val:
                    return False

                setattr(self, dest_attr_name, val)
                return True
            except Exception:
                return False

        def try_str_2_ipv4(dest_attr_name: str) -> bool:
            try:
                ipaddress.IPv4Address(value)
                setattr(self, dest_attr_name, value)
                return True
            except ValueError:
                return False

        sender = self.sender()
        value = sender.text().strip()

        # event from main view
        if sender == self.ui.apiServerHostEdit:
            try_str_2_ipv4('api_server_host')
        if sender == self.ui.apiServerPortEdit:
            try_str_2_int('api_server_port', 1, 65535)

        # event from tab program
        # event from tab g-code

        # event from tab wcs
        if sender == self.ui.csSetWCSEdit:
            try_str_2_int('set_wcs', 1, 9)
        if sender == self.ui.csSetWCSXEdit:
            try_str_2_float('set_wcs_x')
        if sender == self.ui.csSetWCSYEdit:
            try_str_2_float('set_wcs_y')
        if sender == self.ui.csSetWCSZEdit:
            try_str_2_float('set_wcs_z')
        if sender == self.ui.csSetWCSAEdit:
            try_str_2_float('set_wcs_a')
        if sender == self.ui.csSetWCSBEdit:
            try_str_2_float('set_wcs_b')
        if sender == self.ui.csSetWCSCEdit:
            try_str_2_float('set_wcs_c')

        # event from tab cnc

        # event from tab jog
        if sender == self.ui.setProgramPositionXEdit:
            try_str_2_float('set_program_position_x')
        if sender == self.ui.setProgramPositionYEdit:
            try_str_2_float('set_program_position_y')
        if sender == self.ui.setProgramPositionZEdit:
            try_str_2_float('set_program_position_z')
        if sender == self.ui.setProgramPositionAEdit:
            try_str_2_float('set_program_position_a')
        if sender == self.ui.setProgramPositionBEdit:
            try_str_2_float('set_program_position_b')
        if sender == self.ui.setProgramPositionCEdit:
            try_str_2_float('set_program_position_c')

        # event from tab overrides
        # event from tab homing
        # event from tab mdi
        # event from tab d i/o
        # event from tab a i/o
        # event from tab scanning laser
        # event from tab machining info
        # event from tab ui dialogs
        # event from tab system info

        self.__update_editable_fields()

    def __on_form_close(self):
        # save settings on memento
        self.__memento_save()

        # disable and unlink update timer
        self.tmrUpdate.stop()

    def __on_form_show(self):
        # avoid event for stay on top chaning
        if self.stay_on_top_changed is not None:
            return
        self.first_show_event = False

        # set default attributes values
        self.api = None
        self.ctx = None
        self.api_server_connection_state = ASCS_DISCONNECTED
        self.stay_on_top_changed = False
        self.axes_mask_enablings_in_use = -1
        self.cnc_resume_after_stop_from_line = 0
        self.cnc_start_from_line = 0
        # FDIOImageBitmap: TBitmap
        self.in_update = False
        # FMachiningInfoImageBitmap: TBitmap
        # FOverrideFastWatch: TStopWatch
        # FOverrideFeedCustom1Watch: TStopWatch
        # FOverrideFeedCustom2Watch: TStopWatch
        # FOverrideFeedWatch: TStopWatch
        # FOverrideJogWatch: TStopWatch
        # FOverrideSpindleWatch: TStopWatch
        #FToolInfoLabel: THtmlLabel

        # load settings from memento
        self.__memento_load()

        # create and set api client
        self.api = cnc.CncAPIClientCore()

        # create a module api info context
        self.ctx = cnc.CncAPIInfoContext(self.api)

        # update main actions
        ###self.__on_action_main_update(None)

        # enable update timer and call first update NOW
        self.tmrUpdate.start()
        self.__on_timer_update()

        # update editable fields
        self.__update_editable_fields()

        # enable first stay on top update
        self.stay_on_top_changed = True

    def __on_timer_update(self):
        # update non editable objects with related data
        self.__updated_objects()

        # update action main linked objects enablings
        self.__on_action_main_update()

        # update stay on top mode
        if self.stay_on_top_changed:
            self.__set_stay_on_top(self.stay_on_top)
            self.stay_on_top_changed = False
    #
    # == END: events implementation


    # == BEG: memento section
    #
    def __memento_load(self) -> bool:
        try:
            # set default settings values
            self.api_server_host = DEF_API_SERVER_HOST
            self.api_server_port = DEF_API_SERVER_PORT
            self.api_server_use_tls = DEF_API_SERVER_USE_TLS
            self.stay_on_top = DEF_STAY_ON_TOP

            # load memento from file
            file_path = os.path.dirname(__file__) + '\\'
            memento = CncMemento.create_read_root(file_path + SETTINGS_FILE_NAME, 'root')
            if memento is None:
                return False

            # get settings from memento (based on version)
            version = memento.get('version', self.__persistable_save_version)
            if version == 1:
                self.api_server_host = memento.get('api_server_host', DEF_API_SERVER_HOST)
                self.api_server_port = memento.get('api_server_port', DEF_API_SERVER_PORT)
                self.api_server_use_tls = memento.get('api_server_use_tls', DEF_API_SERVER_USE_TLS)
                self.stay_on_top = memento.get('stay_on_top', DEF_STAY_ON_TOP)
                self.program_load_file_name = memento.get('program_load_file_name', '')
                self.program_save_file_name = memento.get('program_save_file_name', '')
                return True
            return False
        except Exception:
            return False

    def __memento_save(self) -> bool:
        try:
            # create memento
            memento = CncMemento.create_write_root('root')

            # set setting to memento
            memento.set('version', 1)
            memento.set('api_server_host', self.api_server_host)
            memento.set('api_server_port', self.api_server_port)
            memento.set('api_server_use_tls', self.api_server_use_tls)
            memento.set('stay_on_top', self.stay_on_top)
            memento.set('program_load_file_name', self.program_load_file_name)
            memento.set('program_save_file_name', self.program_save_file_name)

            # save memento to file
            file_path = os.path.dirname(__file__) + '\\'
            return memento.save_to_file(file_path + SETTINGS_FILE_NAME, indent=4)
        except Exception:
            return False
    #
    # == END: memento section


    # == BEG: generic methods
    #
    def __set_stay_on_top(self, enabled: bool) -> None:
        flags = self.windowFlags()
        is_on_top = bool(flags & Qt.WindowStaysOnTopHint)
        if enabled == is_on_top:
            return
        self.setWindowFlag(Qt.WindowStaysOnTopHint, enabled)
        self.show()
    #
    # == END: generic methods

    # == BEG: laser methods
    #
    def __laser_zero_x_axis(self) -> bool:
        """X-axis zeroing via MCS position returned by scanning laser info."""
        try:
            # get active wcs number
            axes_info = self.api.get_axes_info()
            if not axes_info.has_data:
                return False

            # get scanning laser info
            scanning_laser_info = self.api.get_scanning_laser_info()
            if not scanning_laser_info.has_data:
                return False

            # evaluate new wcs offset
            wcs_offset = scanning_laser_info.laser_mcs_x_position

            # mdi command to set new wcs offst
            command = f'G10 L2 P{axes_info.working_wcs} X{wcs_offset}'
            return self.api.cnc_mdi_command(command)
        except Exception:
            return False

    def __laser_zero_y_axis(self) -> bool:
        """Y-axis zeroing via MCS position returned by scanning laser info."""
        try:
            # get active wcs number
            axes_info = self.api.get_axes_info()
            if not axes_info.has_data:
                return False

            # get scanning laser info
            scanning_laser_info = self.api.get_scanning_laser_info()
            if not scanning_laser_info.has_data:
                return False

            # evaluate new wcs offset
            wcs_offset = scanning_laser_info.laser_mcs_y_position

            # mdi command to set new wcs offst
            command = f'G10 L2 P{axes_info.working_wcs} Y{wcs_offset}'
            return self.api.cnc_mdi_command(command)
        except Exception:
            return False

    def __laser_zero_z_axis(self) -> bool:
        """Z-axis zeroing via MCS position returned by scanning laser info applying median filtering."""
        try:
            # get active wcs number
            axes_info = self.api.get_axes_info()
            if not axes_info.has_data:
                return False

            # get median laser MCS.Z position value as median of LASER_MEDIAN values
            LASER_MEDIAN = 3
            laser_mcs_positions = []
            for m in range(LASER_MEDIAN):
                scanning_laser_info = self.api.get_scanning_laser_info()
                if not scanning_laser_info.has_data:
                    return False
                laser_mcs_positions.append(scanning_laser_info.laser_mcs_z_position)
                time.sleep(0.2)

            # evaluate new wcs offset
            wcs_offset = median(laser_mcs_positions)

            # mdi command to set new wcs offst
            command = f'G10 L2 P{axes_info.working_wcs} Z{wcs_offset}'
            return self.api.cnc_mdi_command(command)
        except Exception:
            return False
    #
    # == END: laser methods


    # == BEG: update methods
    #
    def __update_editable_fields(self):
        """Updates editable fields with related data."""
        if self.in_update:
            return
        self.in_update = True
        try:
            pos_um = '{:.3f}' if self.units_mode == cnc.UM_METRIC else '{:.4f}'

            # update main view
            self.ui.apiServerHostEdit.setText(self.api_server_host)
            self.ui.apiServerPortEdit.setText(str(self.api_server_port))
            self.ui.useTLSCheckBox.setChecked(self.api_server_use_tls)
            self.ui.stayOnTopCheckBox.setChecked(self.stay_on_top)

            # update tab program
            self.ui.programLoadFileNameEdit.setText(self.program_load_file_name)
            self.ui.programSaveFileAsFileNameEdit.setText(self.program_save_file_name)

            # update tab g-code

            # update tab wcs
            if self.apply_wcs_changes_mode == AWCM_ACTIVATE_WCS_ONLY:
                self.ui.csActivateWCSOnlyRadioButton.setChecked(True)
            elif self.apply_wcs_changes_mode == AWCM_SET_WCS_OFFSET_ONLY:
                self.ui.csSetWCSOffsetOnlyRadioButton.setChecked(True)
            elif self.apply_wcs_changes_mode == AWCM_SET_WCS_OFFSET_AND_ACTIVATE:
                self.ui.csSetWCSOffsetAndActivateRadioButton.setChecked(True)
            else:
                self.apply_wcs_changes_mode = AWCM_SET_WCS_OFFSET_ONLY
                self.ui.csSetWCSOffsetOnlyRadioButton.setChecked(True)

            self.ui.csSetWCSEdit.setText(str(self.set_wcs))
            self.ui.csSetWCSXEdit.setText(format_float(self.set_wcs_x, OFFSET_USE_DIGITS, DecimalsTrimMode.FIT))
            self.ui.csSetWCSYEdit.setText(format_float(self.set_wcs_y, OFFSET_USE_DIGITS, DecimalsTrimMode.FIT))
            self.ui.csSetWCSZEdit.setText(format_float(self.set_wcs_z, OFFSET_USE_DIGITS, DecimalsTrimMode.FIT))
            self.ui.csSetWCSAEdit.setText(format_float(self.set_wcs_a, OFFSET_USE_DIGITS, DecimalsTrimMode.FIT))
            self.ui.csSetWCSBEdit.setText(format_float(self.set_wcs_b, OFFSET_USE_DIGITS, DecimalsTrimMode.FIT))
            self.ui.csSetWCSCEdit.setText(format_float(self.set_wcs_c, OFFSET_USE_DIGITS, DecimalsTrimMode.FIT))

            # update tab cnc

            # update tab jog
            self.ui.setProgramPositionXEdit.setText(pos_um.format(self.set_program_position_x))
            self.ui.setProgramPositionYEdit.setText(pos_um.format(self.set_program_position_y))
            self.ui.setProgramPositionZEdit.setText(pos_um.format(self.set_program_position_z))
            self.ui.setProgramPositionAEdit.setText(pos_um.format(self.set_program_position_a))
            self.ui.setProgramPositionBEdit.setText(pos_um.format(self.set_program_position_b))
            self.ui.setProgramPositionCEdit.setText(pos_um.format(self.set_program_position_c))

            # update tab overrides
            # update tab homing
            # update tab mdi
            # update tab d i/o
            # update tab a i/o
            # update tab scanning laser
            # update tab machine info
            # update tab ui dialogs
            # update tab system info
        finally:
            self.in_update = False

    def __updated_objects(self):
        """Updates non editable objects with related data."""

        def debug_update_tick_time():
            # DEBUG: track update ticks at second
            check_time = 5.0
            if not hasattr(self, "tick_time"):
                self.tick_time = time.perf_counter()
                self.tick_count = 0
            else:
                self.tick_count += 1
                t = time.perf_counter() - self.tick_time
                if t > check_time:
                    v = self.tick_count / t
                    self.setWindowTitle(f'{APP_TITLE} - [ {v:8.3f} Update Ticks per Second ]')
                    self.tick_count = 0
                    self.tick_time = time.perf_counter()

        # debug update tick time
        if DBG_UPD_TICK_TIME:
            debug_update_tick_time()

        # evaluate when connection move from connected to error (disconnection of server or wrong server)
        if (self.api_server_connection_state == ASCS_CONNECTED) and not self.api.is_connected:
            self.api_server_connection_state = ASCS_ERROR

        # update api info context
        self.ctx.update()

        # create shortcuts
        cnc_info = self.ctx.cnc_info
        axes_info = self.ctx.axes_info
        enabled_commands = self.ctx.enabled_commands
        work_info = self.api.get_work_info()

        # get connection with cnc state and related changed state
        connection_with_cnc = cnc_info.state_machine != cnc.SM_DISCONNECTED
        connection_with_cnc_changed = self.connection_with_cnc != connection_with_cnc
        self.connection_with_cnc = connection_with_cnc

        # check if units mode changed
        if self.units_mode != cnc_info.units_mode:
            self.units_mode = cnc_info.units_mode
            self.__update_editable_fields()

        # evaluate units mode for formating fields
        um_spc_lf = '{:12.3f} mm' if self.units_mode == cnc.UM_METRIC else '{:12.4f} in'
        um_spc_rf = '{:12.3f} dg' if self.units_mode == cnc.UM_METRIC else '{:12.4f} dg'
        um_vel_lf = '{:7.0f} mm/min' if self.units_mode == cnc.UM_METRIC else '{:7.0f} in/min'
        um_vel_rf = '{:7.0f} dg/min' if self.units_mode == cnc.UM_METRIC else '{:7.0f} dg/min'
        um_decimals = 3 if self.units_mode == cnc.UM_METRIC else 4

        # update axes info
        for axis_group, attr_name, is_velocity in self.axis_data_mapping:
            data = getattr(axes_info, attr_name)
            for i, axis in enumerate(axis_group):
                fmt = (um_vel_lf if i < 3 else um_vel_rf) if is_velocity else (um_spc_lf if i < 3 else um_spc_rf)
                axis.value.setText(fmt.format(data[i]))
        self.ui.wofTitleLabel.setText(f'WORKING OFFSETS {axes_info.working_wcs}')

        # update tool info
        text = ''
        if cnc_info.tool_slot == 0:
            text = f'T{cnc_info.tool_id:d} -'
        else:
            text = f'T{cnc_info.tool_id:d} Slot:{cnc_info.tool_slot:d} -'
        text = text + ' X:' + format_float(cnc_info.tool_offset_x, um_decimals, DecimalsTrimMode.FULL)
        text = text + ' Y:' + format_float(cnc_info.tool_offset_y, um_decimals, DecimalsTrimMode.FULL)
        text = text + ' Z:' + format_float(cnc_info.tool_offset_z, um_decimals, DecimalsTrimMode.FULL)
        self.ui.toolInfoLabel.setText(text)

        # update tab program
        if self.ui.tabWidget.currentWidget() == self.ui.tabProgram:
            self.ui.programLoadFileNameEdit.setEnabled(enabled_commands.program_load)
            self.ui.programSaveFileAsFileNameEdit.setEnabled(enabled_commands.program_load)

        # update tab g-code values
        if self.ui.tabWidget.currentWidget() == self.ui.tabGCode:
            self.ui.gcodeProgramEdit.setEnabled(enabled_commands.program_gcode_set_text)
            self.ui.gcodeAddProgramTextEdit.setEnabled(enabled_commands.program_gcode_add_text)

        # update tab coordinate system
        if self.ui.tabWidget.currentWidget() == self.ui.tabWCS:
            csi = self.api.get_coordinate_systems_info()
            if not csi.is_equal(self.coordinates_system_info_in_use):
                self.coordinates_system_info_in_use = csi

                def set_active_wcs_header_bold(table, working_wcs: int):
                    active_row = int(working_wcs)
                    if active_row < 1 or active_row > 9:
                        active_row = -1
                    for r in range(table.rowCount()):
                        hdr = table.verticalHeaderItem(r)
                        if hdr is None:
                            hdr = QTableWidgetItem(table.verticalHeaderItem(r).text() if table.verticalHeaderItem(r) else "")
                            table.setVerticalHeaderItem(r, hdr)
                        f = hdr.font()
                        f.setBold(r == active_row)
                        hdr.setFont(f)

                wcs_names = ['G54', 'G55', 'G56', 'G57', 'G58', 'G59', 'G59.1', 'G59.2', 'G59.3']
                if 1 <= csi.working_wcs <= 9:
                    wcs_name = wcs_names[csi.working_wcs - 1]
                    self.ui.csWorkingWCS.setText(f"Working WCS.{csi.working_wcs:d} - [ {wcs_name} ]")
                else:
                    self.ui.csWorkingWCS.setText("Unavailable working WCS")
                set_active_wcs_header_bold(self.ui.csOffsetsTable, csi.working_wcs)
                for r in range(self.ui.csOffsetsTable.rowCount()):
                    if r == 0:
                        offsets = csi.working_offset
                    else:
                        offsets = getattr(csi, f"wcs_{r}")
                    for c in range(self.ui.csOffsetsTable.columnCount()):
                        item = self.ui.csOffsetsTable.item(r, c)
                        if item is None:
                            item = QTableWidgetItem()
                            item.setTextAlignment(Qt.AlignCenter)
                            self.ui.csOffsetsTable.setItem(r, c, item)
                        if csi.has_data:
                            item.setText(format_float(offsets[c], OFFSET_USE_DIGITS, DecimalsTrimMode.FIT))
                        else:
                            item.setText('- - -')

            if self.api_server_connection_state in [ASCS_DISCONNECTED, ASCS_ERROR] or not enabled_commands.cnc_parameters:
                self.ui.csWorkingWCS.setEnabled(False)
                self.ui.csOffsetsTable.setEnabled(False)
                self.ui.csActivateWCSOnlyRadioButton.setEnabled(False)
                self.ui.csSetWCSOffsetOnlyRadioButton.setEnabled(False)
                self.ui.csSetWCSOffsetAndActivateRadioButton.setEnabled(False)
                self.ui.csSetWCSLabel.setEnabled(False)
                self.ui.csSetWCSEdit.setEnabled(False)
                self.ui.csSetWCSXCheckBox.setEnabled(False)
                self.ui.csSetWCSXEdit.setEnabled(False)
                self.ui.csSetWCSYCheckBox.setEnabled(False)
                self.ui.csSetWCSYEdit.setEnabled(False)
                self.ui.csSetWCSZCheckBox.setEnabled(False)
                self.ui.csSetWCSZEdit.setEnabled(False)
                self.ui.csSetWCSACheckBox.setEnabled(False)
                self.ui.csSetWCSAEdit.setEnabled(False)
                self.ui.csSetWCSBCheckBox.setEnabled(False)
                self.ui.csSetWCSBEdit.setEnabled(False)
                self.ui.csSetWCSCCheckBox.setEnabled(False)
                self.ui.csSetWCSCEdit.setEnabled(False)
            else:
                self.ui.csWorkingWCS.setEnabled(True)
                self.ui.csOffsetsTable.setEnabled(True)
                self.ui.csActivateWCSOnlyRadioButton.setEnabled(True)
                self.ui.csSetWCSOffsetOnlyRadioButton.setEnabled(True)
                self.ui.csSetWCSOffsetAndActivateRadioButton.setEnabled(True)
                self.ui.csSetWCSLabel.setEnabled(True)
                self.ui.csSetWCSEdit.setEnabled(True)

                enabled = self.apply_wcs_changes_mode in [AWCM_SET_WCS_OFFSET_ONLY, AWCM_SET_WCS_OFFSET_AND_ACTIVATE]
                self.ui.csSetWCSXCheckBox.setEnabled(enabled)
                self.ui.csSetWCSXEdit.setEnabled(enabled and self.ui.csSetWCSXCheckBox.isChecked())
                self.ui.csSetWCSYCheckBox.setEnabled(enabled)
                self.ui.csSetWCSYEdit.setEnabled(enabled and self.ui.csSetWCSYCheckBox.isChecked())
                self.ui.csSetWCSZCheckBox.setEnabled(enabled)
                self.ui.csSetWCSZEdit.setEnabled(enabled and self.ui.csSetWCSZCheckBox.isChecked())
                self.ui.csSetWCSACheckBox.setEnabled(enabled)
                self.ui.csSetWCSAEdit.setEnabled(enabled and self.ui.csSetWCSACheckBox.isChecked())
                self.ui.csSetWCSBCheckBox.setEnabled(enabled)
                self.ui.csSetWCSBEdit.setEnabled(enabled and self.ui.csSetWCSBCheckBox.isChecked())
                self.ui.csSetWCSCCheckBox.setEnabled(enabled)
                self.ui.csSetWCSCEdit.setEnabled(enabled and self.ui.csSetWCSCCheckBox.isChecked())

        # update tab cnc values
        if self.ui.tabWidget.currentWidget() == self.ui.tabCNC:
            pass

        # update tab jog values
        if self.ui.tabWidget.currentWidget() == self.ui.tabJOG:
            pass

        # update tab overrides values
        if self.ui.tabWidget.currentWidget() == self.ui.tabOverrides:
            pass

        # update tab homing values
        if self.ui.tabWidget.currentWidget() == self.ui.tabHoming:
            pass

        # update tab mdi values
        if self.ui.tabWidget.currentWidget() == self.ui.tabMDI:
            pass

        # update tab d(igital) i/o values
        if self.ui.tabWidget.currentWidget() == self.ui.tabDIO:
            pass

        # update tab a(nalog) i/o values
        if self.ui.tabWidget.currentWidget() == self.ui.tabAIO:
            pass

        # update tab scanning laser values
        if self.ui.tabWidget.currentWidget() == self.ui.tabScanningLaser:
            pass

        # update tab machining info values
        if self.ui.tabWidget.currentWidget() == self.ui.tabMachiningInfo:
            pass

        # update tab ui dialogs
        if self.ui.tabWidget.currentWidget() == self.ui.tabUIDialogs:
            pass

        # update tab system info values
        if self.ui.tabWidget.currentWidget() == self.ui.tabSystemInfo:
            system_info = self.api.get_system_info()
            if not cnc.APISystemInfo.are_equal(self.system_info_in_use, system_info):
                self.system_info_in_use = system_info
                self.ui.systemInfoEdit.clear()
                self.ui.systemInfoEdit.append('')
                self.ui.systemInfoEdit.append('  Machine Name               : ' + system_info.machine_name)
                self.ui.systemInfoEdit.append('  Control Software Version   : ' + system_info.control_software_version)
                self.ui.systemInfoEdit.append('  Core Version               : ' + system_info.core_version)
                self.ui.systemInfoEdit.append('  API Server Version         : ' + system_info.api_server_version)
                self.ui.systemInfoEdit.append('  Firmware Version           : ' + system_info.firmware_version)
                self.ui.systemInfoEdit.append('  Firmware Version Tag       : ' + system_info.firmware_version_tag)
                self.ui.systemInfoEdit.append('  Firmware Interface Level   : ' + system_info.firmware_interface_level)
                self.ui.systemInfoEdit.append('  Order Code                 : ' + system_info.order_code)
                self.ui.systemInfoEdit.append('  Customer Id                : ' + system_info.customer_id)
                self.ui.systemInfoEdit.append('  Serial Number              : ' + system_info.serial_number)
                self.ui.systemInfoEdit.append('  Part Number                : ' + system_info.part_number)
                self.ui.systemInfoEdit.append('  Customization Number       : ' + system_info.customization_number)
                self.ui.systemInfoEdit.append('  Hardware Version           : ' + system_info.hardware_version)
                self.ui.systemInfoEdit.append('  Operative System           : ' + system_info.operative_system)
                self.ui.systemInfoEdit.append('  Operative System CRC       : ' + system_info.operative_system_crc)
                self.ui.systemInfoEdit.append('  PLD Version                : ' + system_info.pld_version)

        # update status bar
        text = 'UNKNOWN'
        if is_in_str_list_range(SM_TEXTS, cnc_info.state_machine):
            text = SM_TEXTS[cnc_info.state_machine]
        self.StateMachineLabel.setText('Machine State : ' + text)
        text = 'UNKNOWN'
        if is_in_str_list_range(ASCS_TEXTS, self.api_server_connection_state):
            text = ASCS_TEXTS[self.api_server_connection_state]
        if not self.api_server_use_tls:
            self.APIServerConnectionStateLabel.setText('Connection with Server : ' + text)
        else:
            self.APIServerConnectionStateLabel.setText('Connection with Server [TLS] : ' + text)

        # update axis enablings
        if (self.axes_mask_enablings_in_use != cnc_info.axes_mask) or connection_with_cnc_changed:
            self.axes_mask_enablings_in_use = cnc_info.axes_mask
            for axis_group in self.all_axis_controls:
                for axis, mask in zip(axis_group, self.axis_masks):
                    enabled = connection_with_cnc and ((self.axes_mask_enablings_in_use & mask) != 0)
                    axis.label.setEnabled(enabled)
                    axis.value.setEnabled(enabled)

        # update general objects enabling
        if self.api_server_connection_state in [ASCS_DISCONNECTED, ASCS_ERROR]:
            # update main view
            self.ui.apiServerHostEdit.setEnabled(True)
            self.ui.apiServerPortEdit.setEnabled(True)
            self.ui.useTLSCheckBox.setEnabled(True)

            # update tab jog
            self.ui.setProgramPositionXEdit.setEnabled(False)
            self.ui.setProgramPositionYEdit.setEnabled(False)
            self.ui.setProgramPositionZEdit.setEnabled(False)
            self.ui.setProgramPositionAEdit.setEnabled(False)
            self.ui.setProgramPositionBEdit.setEnabled(False)
            self.ui.setProgramPositionCEdit.setEnabled(False)
        else:
            # update main view
            self.ui.apiServerHostEdit.setEnabled(False)
            self.ui.apiServerPortEdit.setEnabled(False)
            self.ui.useTLSCheckBox.setEnabled(False)

            # update tab jog
            set_program_position = self.ctx.enabled_commands.set_program_position
            self.ui.setProgramPositionXEdit.setEnabled((set_program_position & cnc.X_AXIS_MASK) > 0)
            self.ui.setProgramPositionYEdit.setEnabled((set_program_position & cnc.Y_AXIS_MASK) > 0)
            self.ui.setProgramPositionZEdit.setEnabled((set_program_position & cnc.Z_AXIS_MASK) > 0)
            self.ui.setProgramPositionAEdit.setEnabled((set_program_position & cnc.A_AXIS_MASK) > 0)
            self.ui.setProgramPositionBEdit.setEnabled((set_program_position & cnc.B_AXIS_MASK) > 0)
            self.ui.setProgramPositionCEdit.setEnabled((set_program_position & cnc.C_AXIS_MASK) > 0)
    #
    # == END: update methods
