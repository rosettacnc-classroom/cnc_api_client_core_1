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
# Created:      02/02/2026
# Copyright:    RosettaCNC (c) 2016-2026
# Licence:      RosettaCNC License 1.0 (RCNC-1.0)
# Coding Style  https://www.python.org/dev/peps/pep-0008/
#-------------------------------------------------------------------------------
# pylint: disable=C0103 -> invalid-name
# pylint: disable=C0301 -> line-too-long
# pylint: disable=C0302 -> too-many-lines
# pylint: disable=R0902 -> too-many-instance-attributes
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
from statistics import median
from collections import namedtuple

import cnc_api_client_core as cnc
from utils import DecimalsTrimMode, format_float, is_in_str_list_range

from PySide6.QtCore import QTimer
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QFileDialog, QLabel, QLineEdit, QMainWindow, QPushButton

from ui_desktop_view import Ui_DesktopView

from cnc_memento import CncMemento

# define here the version number to show in view caption
VERSION = '1.0.1'

# == application info
APP_TITLE                   = f'API Client Demo with Qt PySide6 UI - {VERSION}'

# == default constants
DEF_API_SERVER_HOST         = '127.0.0.1'
DEF_API_SERVER_PORT         = 8000
DEF_API_SERVER_USE_TLS      = False
DEF_STAY_ON_TOP             = False

# == settings file name
SETTINGS_FILE_NAME          = 'settings.xml'

DEF_LOAD_PROGRAM_FILE_NAME  = 'D:\\gcode-repository\\_test_\\heavy\\2.8-milions.ngc'
DEF_SAVE_PROGRAM_FILE_NAME  = 'D:\\gcode-repository\\_test_\\heavy\\2.8-milions_new.ngc'

# == debug settings
DBG_UPD_TICK_TIME           = False

# == program constants
OVERRIDE_SEATTLE_TIME       = 500

# == api server connection state
ASCS_DISCONNECTED           = 0
ASCS_CONNECTED              = 1
ASCS_ERROR                  = 2

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
VK_RETURN                   = 0x0D

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

        # set current persistable save version
        self.__persistable_save_version = 1

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
        self.ui.StatusBar.addPermanentWidget(self.StateMachineLabel)
        self.ui.StatusBar.addPermanentWidget(self.APIServerConnectionStateLabel, 1)

        # declare class public attributes (for pylint check)
        self.api = None
        self.ctx = None
        self.api_server_connection_state = None
        self.api_server_host = None
        self.api_server_port = None
        self.api_server_use_tls = None
        self.stay_on_top = None
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
        self.program_load_file_name = None
        self.program_save_file_name = None
        self.set_program_position_a = None
        self.set_program_position_b = None
        self.set_program_position_c = None
        self.set_program_position_x = None
        self.set_program_position_y = None
        self.set_program_position_z = None
        self.units_mode = None
        self.system_info_in_use = None

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

        # events for commands
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

        # events for tab program
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

        # events for tab jog
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

        # events for tab ui dialogs
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

        # events for connection with API Server
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
            else:
                pass # !!! SHOULD NEVER HAPPEN !!!

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

        # update server connect/disconnect button
        self.ui.ServerConnectDisconnectButton.setEnabled(True)
        if self.api_server_connection_state == ASCS_CONNECTED:
            self.ui.ServerConnectDisconnectButton.setText('Disconnect')
        else:
            self.ui.ServerConnectDisconnectButton.setText('Connect')

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

        sender = self.sender()
        value = sender.text().strip()

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

        self.__update_editable_fields()

    def __on_form_close(self):
        # save settings on memento
        self.__memento_save()

        # disable and unlink update timer
        self.tmrUpdate.stop()

    def __on_form_show(self):
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
        self.program_load_file_name = ''
        self.program_save_file_name = ''
        self.set_program_position_a = 0.0
        self.set_program_position_b = 0.0
        self.set_program_position_c = 0.0
        self.set_program_position_x = 0.0
        self.set_program_position_y = 0.0
        self.set_program_position_z = 0.0
        #FToolInfoLabel: THtmlLabel
        self.units_mode = cnc.UM_METRIC
        self.system_info_in_use = None

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
            um = '{:.3f}' if self.units_mode == cnc.UM_METRIC else '{:.4f}'
            self.ui.programLoadFileNameEdit.setText(self.program_load_file_name)
            self.ui.programSaveFileAsFileNameEdit.setText(self.program_save_file_name)
            """
            self.CNCResumeAfterStopFromLineEdit.Text = str(self.cnc_resume_after_stop_from_line)
            self.CNCStartFromLineEdit.Text = str(self.cnc_start_from_line)
            """
            self.ui.setProgramPositionXEdit.setText(um.format(self.set_program_position_x))
            self.ui.setProgramPositionYEdit.setText(um.format(self.set_program_position_y))
            self.ui.setProgramPositionZEdit.setText(um.format(self.set_program_position_z))
            self.ui.setProgramPositionAEdit.setText(um.format(self.set_program_position_a))
            self.ui.setProgramPositionBEdit.setText(um.format(self.set_program_position_b))
            self.ui.setProgramPositionCEdit.setText(um.format(self.set_program_position_c))
            """
            self.APIServerHostEdit.Text = self.api_server_host
            self.APIServerPortEdit.Text = str(self.api_server_port)
            self.UseTLSCheckBox.IsChecked = self.api_server_use_tls
            self.StayOnTopCheckBox.IsChecked = self.stay_on_top
            """
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

        # update tab program values
        if self.ui.tabWidget.currentWidget() == self.ui.tabProgram:
            self.ui.programLoadFileNameEdit.setEnabled(enabled_commands.program_load)
            self.ui.programSaveFileAsFileNameEdit.setEnabled(enabled_commands.program_load)

        # update tab g-code values
        if self.ui.tabWidget.currentWidget() == self.ui.tabGCode:
            pass

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
            """
            self.SpindleStatusLabel.Enabled = False
            self.SpindleStatusValue.Enabled = False
            self.CoolantMistLabel.Enabled = False
            self.CoolantMistValue.Enabled = False
            self.CoolantFloodLabel.Enabled = False
            self.CoolantFloodValue.Enabled = False
            self.GCodeLineLabel.Enabled = False
            self.GCodeLineValue.Enabled = False
            self.WorkedTimeLabel.Enabled = False
            self.WorkedTimeValue.Enabled = False
            self.PlannedTimeLabel.Enabled = False
            self.PlannedTimeValue.Enabled = False
            self.ProgramLoadFileNameEdit.Enabled = False
            self.ProgramSaveFileNameEdit.Enabled = False
            self.ProgramGCodeSetTextMemo.Enabled = False
            self.ProgramGCodeAddTextEdit.Enabled = False
            self.CNCStartFromLineEdit.Enabled = False
            self.CNCResumeAfterStopFromLineEdit.Enabled = False
            self.CNCMDICommandMemo.Enabled = False
            """
            self.ui.setProgramPositionXEdit.setEnabled(False)
            self.ui.setProgramPositionYEdit.setEnabled(False)
            self.ui.setProgramPositionZEdit.setEnabled(False)
            self.ui.setProgramPositionAEdit.setEnabled(False)
            self.ui.setProgramPositionBEdit.setEnabled(False)
            self.ui.setProgramPositionCEdit.setEnabled(False)
            """
            self.APIServerHostEdit.Enabled = True
            self.APIServerPortEdit.Enabled = True
            self.UseTLSCheckBox.Enabled = True
            """
        else:
            """
            self.SpindleStatusLabel.Enabled = True
            self.SpindleStatusValue.Enabled = True
            self.CoolantMistLabel.Enabled = True
            self.CoolantMistValue.Enabled = True
            self.CoolantFloodLabel.Enabled = True
            self.CoolantFloodValue.Enabled = True
            self.GCodeLineLabel.Enabled = True
            self.GCodeLineValue.Enabled = True
            self.WorkedTimeLabel.Enabled = True
            self.WorkedTimeValue.Enabled = True
            self.PlannedTimeLabel.Enabled = True
            self.PlannedTimeValue.Enabled = True
            self.ProgramLoadFileNameEdit.Enabled = self.ctx.enabled_commands.program_load
            self.ProgramSaveFileNameEdit.Enabled = self.ctx.enabled_commands.program_save
            self.ProgramGCodeSetTextMemo.Enabled = self.ctx.enabled_commands.program_gcode_set_text
            self.ProgramGCodeAddTextEdit.Enabled = self.ctx.enabled_commands.program_gcode_add_text
            self.CNCStartFromLineEdit.Enabled = self.ctx.enabled_commands.cnc_start_from_line
            self.CNCResumeAfterStopFromLineEdit.Enabled = self.ctx.enabled_commands.cnc_resume
            self.CNCMDICommandMemo.Enabled = self.ctx.enabled_commands.cnc_mdi_command
            """

            set_program_position = self.ctx.enabled_commands.set_program_position
            self.ui.setProgramPositionXEdit.setEnabled((set_program_position & cnc.X_AXIS_MASK) > 0)
            self.ui.setProgramPositionYEdit.setEnabled((set_program_position & cnc.Y_AXIS_MASK) > 0)
            self.ui.setProgramPositionZEdit.setEnabled((set_program_position & cnc.Z_AXIS_MASK) > 0)
            self.ui.setProgramPositionAEdit.setEnabled((set_program_position & cnc.A_AXIS_MASK) > 0)
            self.ui.setProgramPositionBEdit.setEnabled((set_program_position & cnc.B_AXIS_MASK) > 0)
            self.ui.setProgramPositionCEdit.setEnabled((set_program_position & cnc.C_AXIS_MASK) > 0)
            """
            self.APIServerHostEdit.Enabled = False
            self.APIServerPortEdit.Enabled = False
            self.UseTLSCheckBox.Enabled = False
            """
    #
    # == END: update methods
