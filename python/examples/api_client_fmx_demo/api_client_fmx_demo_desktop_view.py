"""API Client Demo using Embarcadero FMX UI."""
#-------------------------------------------------------------------------------
# Name:         api_client_fmx_demo_desktop_view
#
# Purpose:      API Client Demo Desktop View
#
# Note          Compatible with API server version 1.5.1
#               1 (on 1.x.y) means interface contract
#               x (on 1.x.y) means version
#               y (on 1.x.y) means release
#
# Note          Checked with Python 3.11.9
#
# Author:       rosettacnc-classroom@gmail.com
#
# Created:      07/12/2024
# Copyright:    RosettaCNC (c) 2016-2024
# Licence:      RosettaCNC License 1.0 (RCNC-1.0)
# Coding Style  https://www.python.org/dev/peps/pep-0008/
#               With cnc_vision_vcl/fmx objects is used Delphi coding style
#-------------------------------------------------------------------------------
# pylint: disable=C0103 -> invalid-name
# pylint: disable=C0115 -> missing-class-docstring
# pylint: disable=C0116 -> missing-function-docstring
# pylint: disable=C0209 -> consider-using-f-string
# pylint: disable=C0301 -> line-too-long
# pylint: disable=C0302 -> too-many-lines
# pylint: disable=C0321 -> multiple-statements              ## works but not suggested way to code ##
# pylint: disable=E0602 -> undefined-variable               ## take care when you use that ##
# pylint: disable=R0902 -> too-many-instance-attributes
# pylint: disable=R0903 -> too-few-public-methods
# pylint: disable=R0912 -> too-many-branches
# pylint: disable=R0913 -> too-many-arguments
# pylint: disable=R0914 -> too-many-locals
# pylint: disable=R0915 -> too-many-statements
# pylint: disable=R1716 -> chained-comparison
# pylint: disable=W0201 -> attribute-defined-outside-init   ## take care when you use that ##
# pylint: disable=W0401 -> wildcard-import
# pylint: disable=W0613 -> unused-argument
# pylint: disable=W0614 -> unused-wildcard-import
# pylint: disable=W0702 -> bare-except
#-------------------------------------------------------------------------------
import os
import time
from statistics import median

import cnc_api_client_core as cnc

from delphifmx import *
from osDesktopView import DesktopView

from cnc_memento import CncMemento

# define here the version number to show in view caption
VERSION = '1.0.1'

# == default constants
DEF_API_SERVER_HOST         = '127.0.0.1'
DEF_API_SERVER_PORT         = 8000
DEF_API_SERVER_USE_TLS      = False
DEF_STAY_ON_TOP             = False

# settings file name
SETTINGS_FILE_NAME          = 'settings.xml'

DEF_CLA_HOMING_DONE         = 0xFFFFFFFF    # claWhite
DEF_CLA_HOMING_TODO         = 0xFFFFFF00    # claYellow
DEF_CLA_HOMING_OFF          = 0xFF808080    #

DEF_LOAD_PROGRAM_FILE_NAME  = 'D:\\gcode-repository\\_test_\\heavy\\2.8-milions.ngc'
DEF_SAVE_PROGRAM_FILE_NAME  = 'D:\\gcode-repository\\_test_\\heavy\\2.8-milions_new.ngc'

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

# == decimals trim mode
DTMD_NONE                   = 0
DTMD_FIT                    = 1
DTMD_DOT                    = 2
DTMD_FULL                   = 3

def format_float(value, decimals, trim_mode):
    try:
        fmt = '{:.' + str(decimals) + 'f}'
        ret = fmt.format(value)
        return ret
        """
          try
            S := '%.' + IntToStr(Decimals) + 'f';
            Result := Format(S, [Value]);
            if TrimMode = dtmdNone then Exit;
            for I := Length(Result) downto 2 do
            begin
              if Result[I] <> '0' then
              begin
                if Result[I] = '.' then
                begin
                  case TrimMode of
                    dtmdFit:
                      Result := Copy(Result, 1, I + 1);
                    dtmdDot:
                      Result := Copy(Result, 1, I);
                    dtmdFull:
                      Result := Copy(Result, 1, I - 1);
                  end;
                  Exit;
                end
                else
                  Result := Copy(Result, 1, I);
                Exit;
              end;
            end;
          except
            Result := '';
          end;
        """
    except:
        return ''

class ApiClientFmxDemoDesktopView(DesktopView):
    "Xxx..."

    def __init__(self, owner):
        # call vcl inherited view constructor
        super().__init__(owner)

        # set caption
        self.Caption = "API Client Demo with Embarcadero FMX UI " + VERSION

        # set main form events handlers
        self.OnClose = self.__on_form_close
        self.OnShow = self.__on_form_show

        # set current persistable save version
        self.__persistable_save_version = 1

        # create and set update timer
        self.tmrUpdate = Timer(self)
        self.tmrUpdate.Interval = 1
        self.tmrUpdate.Enabled = False
        self.tmrUpdate.OnTimer = self.__on_timer_update

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


    # == BEG: relink of native events from inherited FMX UI design
    #
    def ActionMainExecute(self, Sender):
        self.__on_action_main_execute(Sender)
    def ActionMainUpdate(self, Sender):
        self.__on_action_main_update(Sender)
    def CheckBoxChange(self, Sender):
        self.__on_checkbox_change(Sender)
    def CNCJogCommandMouseDown(self, Sender, Button, Shift, X, Y):
        self.__on_cnc_jog_command_mouse_down(Sender, Button, Shift, X, Y)
    def CNCJogCommandMouseUp(self, Sender, Button, Shift, X, Y):
        self.__on_cnc_jog_command_mouse_up(Sender, Button, Shift, X, Y)
    def EditClick(self, Sender):
        self.__on_edit_click(Sender)
    def EditEnter(self, Sender):
        self.__on_edit_enter(Sender)
    def EditExit(self, Sender):
        self.__on_edit_exit(Sender)
    def EditKeyDown(self, Sender, Key, KeyChar, Shift):
        self.__on_edit_key_down(Sender, Key, KeyChar, Shift)
    #
    # == END: relink of native events from inherited FMX UI design


    # == BEG: events implementation
    #
    def __on_action_main_execute(self, Sender):
        if Sender == self.CNCContinueAction:
            self.api.cnc_continue()
        if Sender == self.CNCHomingAAction:
            self.api.cnc_homing(cnc.A_AXIS_MASK)
        if Sender == self.CNCHomingAllAction:
            self.api.cnc_homing(cnc.X2C_AXIS_MASK)
        if Sender == self.CNCHomingBAction:
            self.api.cnc_homing(cnc.B_AXIS_MASK)
        if Sender == self.CNCHomingCAction:
            self.api.cnc_homing(cnc.C_AXIS_MASK)
        if Sender == self.CNCHomingXAction:
            self.api.cnc_homing(cnc.X_AXIS_MASK)
        if Sender == self.CNCHomingYAction:
            self.api.cnc_homing(cnc.Y_AXIS_MASK)
        if Sender == self.CNCHomingZAction:
            self.api.cnc_homing(cnc.Z_AXIS_MASK)
        if Sender == self.CNCMDICommandAction:
            self.api.cnc_mdi_command(self.CNCMDICommandMemo.Text)
        if Sender == self.CNCPauseAction:
            self.api.cnc_pause()
        if Sender == self.CNCResumeAfterStopAction:
            self.api.cnc_resume(0)
        if Sender == self.CNCResumeAfterStopFromLineAction:
            self.api.cnc_resume(self.cnc_resume_after_stop_from_line)
        if Sender == self.CNCStartAction:
            self.api.cnc_start()
        if Sender == self.CNCStartFromLineAction:
            self.api.cnc_start_from_line(self.cnc_start_from_line)
        if Sender == self.CNCStopAction:
            self.api.cnc_stop()
        if Sender == self.LaserZeroXAxisAction:
            self.__laser_zero_x_axis()
        if Sender == self.LaserZeroYAxisAction:
            self.__laser_zero_y_axis()
        if Sender == self.LaserZeroZAxisAction:
            self.__laser_zero_z_axis()
        if Sender == self.ProgramAnalysisAbortAction:
            self.api.program_analysis_abort()
        if Sender == self.ProgramAnalysisMTAction:
            self.api.program_analysis(cnc.ANALYSIS_MT)
        if Sender == self.ProgramAnalysisRFAction:
            self.api.program_analysis(cnc.ANALYSIS_RF)
        if Sender == self.ProgramAnalysisRTAction:
            self.api.program_analysis(cnc.ANALYSIS_RT)
        if Sender == self.ProgramAnalysisRVAction:
            self.api.program_analysis(cnc.ANALYSIS_RV)
        if Sender == self.ProgramAnalysisRZAction:
            self.api.program_analysis(cnc.ANALYSIS_RZ)
        if Sender == self.ProgramGCodeAddTextAction:
            self.api.program_gcode_add_text(self.ProgramGCodeAddTextEdit.Text)
        if Sender == self.ProgramGCodeClearAction:
            self.api.program_gcode_clear()
        if Sender == self.ProgramGCodeSetTextAction:
            self.api.program_gcode_set_text(self.ProgramGCodeSetTextMemo.Text)
        if Sender == self.ProgramLoadAction:
            self.api.program_load(self.program_load_file_name)
        if Sender == self.SelectFileAction:
            # TODO : manage the case of Stay On Top active
            if self.OpenDialog.Execute():
                self.program_load_file_name = self.OpenDialog.FileName
                self.__update_fields()
        if Sender == self.ProgramNewAction:
            self.api.program_new()
        if Sender == self.ProgramSaveAction:
            self.api.program_save(self.program_save_file_name)
        if Sender == self.ResetAlarmsAction:
            self.api.reset_alarms()
        if Sender == self.ResetAlarmsHistoryAction:
            self.api.reset_alarms_history()
        if Sender == self.ResetWarningsAction:
            self.api.reset_warnings()
        if Sender == self.ResetWarningsHistoryAction:
            self.api.reset_warnings_history()
        if Sender == self.ServerConnectDisconnectAction:
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
        if Sender == self.ProgramSaveAction:
            self.api.program_save(self.program_save_file_name)
        if Sender == self.SetProgramPositionXAction:
            self.api.set_program_position_x(self.set_program_position_x)
        if Sender == self.SetProgramPositionYAction:
            self.api.set_program_position_y(self.set_program_position_y)
        if Sender == self.SetProgramPositionZAction:
            self.api.set_program_position_z(self.set_program_position_z)
        if Sender == self.SetProgramPositionAAction:
            self.api.set_program_position_a(self.set_program_position_a)
        if Sender == self.SetProgramPositionBAction:
            self.api.set_program_position_b(self.set_program_position_b)
        if Sender == self.SetProgramPositionCAction:
            self.api.set_program_position_c(self.set_program_position_c)

        # direct action update to avoid delay of cyclic refresh
        self.ctx.update()
        self.__on_action_main_update(None)

    def __on_action_main_update(self, Sender):
        if self.api_server_connection_state in [ASCS_DISCONNECTED, ASCS_ERROR]:
            self.CNCContinueAction.Enabled = False
            self.CNCHomingAAction.Enabled = False
            self.CNCHomingAllAction.Enabled = False
            self.CNCHomingBAction.Enabled = False
            self.CNCHomingCAction.Enabled = False
            self.CNCHomingXAction.Enabled = False
            self.CNCHomingYAction.Enabled = False
            self.CNCHomingZAction.Enabled = False
            self.CNCMDICommandAction.Enabled = False
            self.CNCPauseAction.Enabled = False
            self.CNCResumeAfterStopAction.Enabled = False
            self.CNCResumeAfterStopFromLineAction.Enabled = False
            self.CNCStartAction.Enabled = False
            self.CNCStartFromLineAction.Enabled = False
            self.CNCStopAction.Enabled = False
            self.LaserZeroXAxisAction.Enabled = False
            self.LaserZeroYAxisAction.Enabled = False
            self.LaserZeroZAxisAction.Enabled = False
            self.ProgramAnalysisAbortAction.Enabled = False
            self.ProgramAnalysisMTAction.Enabled = False
            self.ProgramAnalysisRFAction.Enabled = False
            self.ProgramAnalysisRTAction.Enabled = False
            self.ProgramAnalysisRVAction.Enabled = False
            self.ProgramAnalysisRZAction.Enabled = False
            self.ProgramGCodeAddTextAction.Enabled = False
            self.ProgramGCodeClearAction.Enabled = False
            self.ProgramGCodeSetTextAction.Enabled = False
            self.ProgramLoadAction.Enabled = False
            self.ProgramNewAction.Enabled = False
            self.ProgramSaveAction.Enabled = False
            self.ResetAlarmsAction.Enabled = False
            self.ResetAlarmsHistoryAction.Enabled = False
            self.ResetWarningsAction.Enabled = False
            self.ResetWarningsHistoryAction.Enabled = False
            self.SetProgramPositionAAction.Enabled = False
            self.SetProgramPositionBAction.Enabled = False
            self.SetProgramPositionCAction.Enabled = False
            self.SetProgramPositionXAction.Enabled = False
            self.SetProgramPositionYAction.Enabled = False
            self.SetProgramPositionZAction.Enabled = False
        else:
            enabled_commands = self.ctx.enabled_commands
            self.CNCContinueAction.Enabled = enabled_commands.cnc_continue
            self.CNCHomingAAction.Enabled = (enabled_commands.cnc_homing & cnc.A_AXIS_MASK) != 0
            self.CNCHomingAllAction.Enabled = enabled_commands.cnc_homing != 0
            self.CNCHomingBAction.Enabled = (enabled_commands.cnc_homing & cnc.B_AXIS_MASK) != 0
            self.CNCHomingCAction.Enabled = (enabled_commands.cnc_homing & cnc.C_AXIS_MASK) != 0
            self.CNCHomingXAction.Enabled = (enabled_commands.cnc_homing & cnc.X_AXIS_MASK) != 0
            self.CNCHomingYAction.Enabled = (enabled_commands.cnc_homing & cnc.Y_AXIS_MASK) != 0
            self.CNCHomingZAction.Enabled = (enabled_commands.cnc_homing & cnc.Z_AXIS_MASK) != 0
            self.CNCMDICommandAction.Enabled = enabled_commands.cnc_mdi_command
            self.CNCPauseAction.Enabled = enabled_commands.cnc_pause
            self.CNCResumeAfterStopAction.Enabled = enabled_commands.cnc_resume
            self.CNCResumeAfterStopFromLineAction.Enabled = enabled_commands.cnc_resume
            self.CNCStartAction.Enabled = enabled_commands.cnc_start
            self.CNCStartFromLineAction.Enabled = enabled_commands.cnc_start_from_line
            self.CNCStopAction.Enabled = enabled_commands.cnc_stop
            self.LaserZeroXAxisAction.Enabled = enabled_commands.cnc_mdi_command
            self.LaserZeroYAxisAction.Enabled = enabled_commands.cnc_mdi_command
            self.LaserZeroZAxisAction.Enabled = enabled_commands.cnc_mdi_command
            self.ProgramAnalysisAbortAction.Enabled = enabled_commands.program_analysis_abort
            self.ProgramAnalysisMTAction.Enabled = enabled_commands.program_analysis
            self.ProgramAnalysisRFAction.Enabled = enabled_commands.program_analysis
            self.ProgramAnalysisRTAction.Enabled = enabled_commands.program_analysis
            self.ProgramAnalysisRVAction.Enabled = enabled_commands.program_analysis
            self.ProgramAnalysisRZAction.Enabled = enabled_commands.program_analysis
            self.ProgramGCodeAddTextAction.Enabled = enabled_commands.program_gcode_add_text
            self.ProgramGCodeClearAction.Enabled = enabled_commands.program_gcode_clear
            self.ProgramGCodeSetTextAction.Enabled = enabled_commands.program_gcode_set_text
            self.ProgramLoadAction.Enabled = enabled_commands.program_load
            self.ProgramNewAction.Enabled = enabled_commands.program_new
            self.ProgramSaveAction.Enabled = enabled_commands.program_save
            self.ResetAlarmsAction.Enabled = enabled_commands.reset_alarms
            self.ResetAlarmsHistoryAction.Enabled = enabled_commands.reset_alarms_history
            self.ResetWarningsAction.Enabled = enabled_commands.reset_warnings
            self.ResetWarningsHistoryAction.Enabled = enabled_commands.reset_warnings_history
            self.SetProgramPositionAAction.Enabled = (enabled_commands.set_program_position & cnc.A_AXIS_MASK) != 0
            self.SetProgramPositionBAction.Enabled = (enabled_commands.set_program_position & cnc.B_AXIS_MASK) != 0
            self.SetProgramPositionCAction.Enabled = (enabled_commands.set_program_position & cnc.C_AXIS_MASK) != 0
            self.SetProgramPositionXAction.Enabled = (enabled_commands.set_program_position & cnc.X_AXIS_MASK) != 0
            self.SetProgramPositionYAction.Enabled = (enabled_commands.set_program_position & cnc.Y_AXIS_MASK) != 0
            self.SetProgramPositionZAction.Enabled = (enabled_commands.set_program_position & cnc.Z_AXIS_MASK) != 0
        if self.api_server_connection_state == ASCS_CONNECTED:
            self.ServerConnectDisconnectAction.Caption = 'Disconnect'
        else:
            self.ServerConnectDisconnectAction.Caption = 'Connect'

    def __on_checkbox_change(self, Sender):
        if self.in_update:
            return
        if Sender == self.UseTLSCheckBox:
            self.api_server_use_tls = self.UseTLSCheckBox.IsChecked
        if Sender == self.StayOnTopCheckBox:
            self.stay_on_top = self.StayOnTopCheckBox.IsChecked
            self.stay_on_top_changed = True
        self.__update_fields()

    def __on_cnc_jog_command_mouse_down(self, Sender, Button, Shift, X, Y):
        self.api.cnc_jog_command(cnc.JC_NONE)

        if Sender == self.CNCJogCommandXMButton:
            self.api.cnc_jog_command(cnc.JC_X_BW)
        if Sender == self.CNCJogCommandXPButton:
            self.api.cnc_jog_command(cnc.JC_X_FW)

        if Sender == self.CNCJogCommandYMButton:
            self.api.cnc_jog_command(cnc.JC_Y_BW)
        if Sender == self.CNCJogCommandYPButton:
            self.api.cnc_jog_command(cnc.JC_Y_FW)

        if Sender == self.CNCJogCommandZMButton:
            self.api.cnc_jog_command(cnc.JC_Z_BW)
        if Sender == self.CNCJogCommandZPButton:
            self.api.cnc_jog_command(cnc.JC_Z_FW)

        if Sender == self.CNCJogCommandAMButton:
            self.api.cnc_jog_command(cnc.JC_A_BW)
        if Sender == self.CNCJogCommandAPButton:
            self.api.cnc_jog_command(cnc.JC_A_FW)

        if Sender == self.CNCJogCommandBMButton:
            self.api.cnc_jog_command(cnc.JC_B_BW)
        if Sender == self.CNCJogCommandBPButton:
            self.api.cnc_jog_command(cnc.JC_B_FW)

        if Sender == self.CNCJogCommandCMButton:
            self.api.cnc_jog_command(cnc.JC_C_BW)
        if Sender == self.CNCJogCommandCPButton:
            self.api.cnc_jog_command(cnc.JC_C_FW)

    def __on_cnc_jog_command_mouse_up(self, Sender, Button, Shift, X, Y):
        self.api.cnc_jog_command(cnc.JC_NONE)

    def __on_edit_click(self, Sender):
        pass

    def __on_edit_enter(self, Sender):
        # TAKE CARE
        # =========
        # DelphiFMX does not support AutoSelect property.
        # I've tried to force SelectAll on the OnEnter event but seems does not work!
        Sender.SelectAll()
        # Sender.Repaint()
        # self.Caption = f"Sender : {Sender.name} | {Sender.Text} | {Sender.SelStart} | {Sender.SelLength}"
        pass

    def __on_edit_exit(self, Sender):

        def try_str_2_float(dest_attr_name: str) -> bool:
            try:
                val = float(value)
                setattr(self, dest_attr_name, val)
                return True
            except:
                return False

        if self.in_update:
            return
        value = Sender.Text.strip()
        if Sender == self.ProgramLoadFileNameEdit:
            self.program_load_file_name = value
        if Sender == self.ProgramSaveFileNameEdit:
            self.program_save_file_name = value
        if Sender == self.SetProgramPositionXEdit:
            try_str_2_float('set_program_position_x')
        if Sender == self.SetProgramPositionYEdit:
            try_str_2_float('set_program_position_y')
        if Sender == self.SetProgramPositionZEdit:
            try_str_2_float('set_program_position_z')
        if Sender == self.SetProgramPositionAEdit:
            try_str_2_float('set_program_position_a')
        if Sender == self.SetProgramPositionBEdit:
            try_str_2_float('set_program_position_b')
        if Sender == self.SetProgramPositionCEdit:
            try_str_2_float('set_program_position_c')
        self.__update_fields()

    def __on_edit_key_down(self, Sender, Key, KeyChar, Shift):
        if Key == VK_RETURN:
            self.__on_edit_exit(Sender)

    def __on_form_close(self, sender, action):
        # save settings on memento
        self.__memento_save()

        # disable and unlink update timer
        self.tmrUpdate.Enabled = False
        self.tmrUpdate.OnTimer = None

    def __on_form_show(self, owner):
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
        self.__on_action_main_update(None)

        # enable update timer and call first update NOW
        self.tmrUpdate.Enabled = True
        self.__on_timer_update(None)

        # update fields
        self.__update_fields()

        # enable first stay on top update
        self.stay_on_top_changed = True

    def __on_timer_update(self, sender):

        class HomingDomeStateColor:
            x = DEF_CLA_HOMING_DONE
            y = DEF_CLA_HOMING_DONE
            z = DEF_CLA_HOMING_DONE
            a = DEF_CLA_HOMING_DONE
            b = DEF_CLA_HOMING_DONE
            c = DEF_CLA_HOMING_DONE

        def is_in_str_list_range(texts, index):
            """Check if index in range of a list of strings"""
            return index >= 0 and index <= len(texts)

        # update state of form stay on top
        if self.stay_on_top_changed:
            if self.stay_on_top:
                if self.FormStyle != 'StayOnTop':
                    self.FormStyle = 'StayOnTop'
            else:
                if self.FormStyle != 'Normal':
                    self.FormStyle = 'Normal'

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

        # checks if units mode changed
        if self.units_mode != cnc_info.units_mode:
            self.units_mode = cnc_info.units_mode
            self.__update_fields()

        # evaluate units mode for formating fields
        um_spc_lf = '{:12.3f} mm' if self.units_mode == cnc.UM_METRIC else '{:12.4f} in'
        um_spc_rf = '{:12.3f} dg' if self.units_mode == cnc.UM_METRIC else '{:12.4f} dg'
        um_vel_lf = '{:7.0f} mm/min' if self.units_mode == cnc.UM_METRIC else '{:7f.0} in/min'
        um_vel_rf = '{:7.0f} dg/min' if self.units_mode == cnc.UM_METRIC else '{:7f.0} dg/min'
        um_decimals = 3 if self.units_mode == cnc.UM_METRIC else 4

        # get colors depending by cnc axes mask & axes homing done mask
        color = HomingDomeStateColor()
        a_mask = cnc_info.axes_mask
        h_mask = axes_info.homing_done_mask
        if axes_info.has_data:
            color.x = DEF_CLA_HOMING_DONE if (h_mask & cnc.X_AXIS_MASK) > 0 else DEF_CLA_HOMING_TODO
            color.y = DEF_CLA_HOMING_DONE if (h_mask & cnc.Y_AXIS_MASK) > 0 else DEF_CLA_HOMING_TODO
            color.z = DEF_CLA_HOMING_DONE if (h_mask & cnc.Z_AXIS_MASK) > 0 else DEF_CLA_HOMING_TODO
            color.a = DEF_CLA_HOMING_DONE if (h_mask & cnc.A_AXIS_MASK) > 0 else DEF_CLA_HOMING_TODO
            color.b = DEF_CLA_HOMING_DONE if (h_mask & cnc.B_AXIS_MASK) > 0 else DEF_CLA_HOMING_TODO
            color.c = DEF_CLA_HOMING_DONE if (h_mask & cnc.C_AXIS_MASK) > 0 else DEF_CLA_HOMING_TODO
        if (a_mask & cnc.X_AXIS_MASK) == 0: color.x = DEF_CLA_HOMING_DONE
        if (a_mask & cnc.Y_AXIS_MASK) == 0: color.y = DEF_CLA_HOMING_DONE
        if (a_mask & cnc.Z_AXIS_MASK) == 0: color.z = DEF_CLA_HOMING_DONE
        if (a_mask & cnc.A_AXIS_MASK) == 0: color.a = DEF_CLA_HOMING_DONE
        if (a_mask & cnc.B_AXIS_MASK) == 0: color.b = DEF_CLA_HOMING_DONE
        if (a_mask & cnc.C_AXIS_MASK) == 0: color.c = DEF_CLA_HOMING_DONE

        # update axes info - machine positions
        self.MCSXValue.Text = um_spc_lf.format(axes_info.machine_position[0])
        self.MCSYValue.Text = um_spc_lf.format(axes_info.machine_position[1])
        self.MCSZValue.Text = um_spc_lf.format(axes_info.machine_position[2])
        self.MCSAValue.Text = um_spc_rf.format(axes_info.machine_position[3])
        self.MCSBValue.Text = um_spc_rf.format(axes_info.machine_position[4])
        self.MCSCValue.Text = um_spc_rf.format(axes_info.machine_position[5])
        self.MCSXValue.FontColor = color.x
        self.MCSYValue.FontColor = color.y
        self.MCSZValue.FontColor = color.z
        self.MCSAValue.FontColor = color.a
        self.MCSBValue.FontColor = color.b
        self.MCSCValue.FontColor = color.c

        # update axes info - program positions
        self.WCSXValue.Text = um_spc_lf.format(axes_info.program_position[0])
        self.WCSYValue.Text = um_spc_lf.format(axes_info.program_position[1])
        self.WCSZValue.Text = um_spc_lf.format(axes_info.program_position[2])
        self.WCSAValue.Text = um_spc_rf.format(axes_info.program_position[3])
        self.WCSBValue.Text = um_spc_rf.format(axes_info.program_position[4])
        self.WCSCValue.Text = um_spc_rf.format(axes_info.program_position[5])
        self.WCSXValue.FontColor = color.x
        self.WCSYValue.FontColor = color.y
        self.WCSZValue.FontColor = color.z
        self.WCSAValue.FontColor = color.a
        self.WCSBValue.FontColor = color.b
        self.WCSCValue.FontColor = color.c

        # update axes info - actual velocities
        self.AVLXValue.Text = um_vel_lf.format(axes_info.actual_velocity[0])
        self.AVLYValue.Text = um_vel_lf.format(axes_info.actual_velocity[1])
        self.AVLZValue.Text = um_vel_lf.format(axes_info.actual_velocity[2])
        self.AVLAValue.Text = um_vel_rf.format(axes_info.actual_velocity[3])
        self.AVLBValue.Text = um_vel_rf.format(axes_info.actual_velocity[4])
        self.AVLCValue.Text = um_vel_rf.format(axes_info.actual_velocity[5])

        # update axes info - working offsets
        self.WOFTitleLabel.Text = 'WORKING OFFSETS ' + str(axes_info.working_wcs)
        self.WOFXValue.Text = um_spc_lf.format(axes_info.working_offset[0])
        self.WOFYValue.Text = um_spc_lf.format(axes_info.working_offset[1])
        self.WOFZValue.Text = um_spc_lf.format(axes_info.working_offset[2])
        self.WOFAValue.Text = um_spc_rf.format(axes_info.working_offset[3])
        self.WOFBValue.Text = um_spc_rf.format(axes_info.working_offset[4])
        self.WOFCValue.Text = um_spc_rf.format(axes_info.working_offset[5])

        # update axes info - machine target positions
        self.MTPXValue.Text = um_spc_lf.format(axes_info.machine_target_position[0])
        self.MTPYValue.Text = um_spc_lf.format(axes_info.machine_target_position[1])
        self.MTPZValue.Text = um_spc_lf.format(axes_info.machine_target_position[2])
        self.MTPAValue.Text = um_spc_rf.format(axes_info.machine_target_position[3])
        self.MTPBValue.Text = um_spc_rf.format(axes_info.machine_target_position[4])
        self.MTPCValue.Text = um_spc_rf.format(axes_info.machine_target_position[5])

        # update axes info - program target positions
        self.PTPXValue.Text = um_spc_lf.format(axes_info.program_target_position[0])
        self.PTPYValue.Text = um_spc_lf.format(axes_info.program_target_position[1])
        self.PTPZValue.Text = um_spc_lf.format(axes_info.program_target_position[2])
        self.PTPAValue.Text = um_spc_rf.format(axes_info.program_target_position[3])
        self.PTPBValue.Text = um_spc_rf.format(axes_info.program_target_position[4])
        self.PTPCValue.Text = um_spc_rf.format(axes_info.program_target_position[5])

        # update axes info - joint positions
        self.JOPXValue.Text = um_spc_lf.format(axes_info.joint_position[0])
        self.JOPYValue.Text = um_spc_lf.format(axes_info.joint_position[1])
        self.JOPZValue.Text = um_spc_lf.format(axes_info.joint_position[2])
        self.JOPAValue.Text = um_spc_rf.format(axes_info.joint_position[3])
        self.JOPBValue.Text = um_spc_rf.format(axes_info.joint_position[4])
        self.JOPCValue.Text = um_spc_rf.format(axes_info.joint_position[5])

        # update working info
        text = 'OFF'
        if is_in_str_list_range(SM_TEXTS, cnc_info.spindle_status - 1):
            text = SS_TEXTS[cnc_info.spindle_status - 1]
        self.SpindleStatusValue.Text = text
        self.CoolantMistValue.Text = 'ON' if cnc_info.coolant_mist else 'OFF'
        self.CoolantFloodValue.Text = 'ON' if cnc_info.coolant_flood else 'OFF'
        self.GCodeLineValue.Text = str(cnc_info.gcode_line)
        self.WorkedTimeValue.Text = work_info.worked_time
        self.PlannedTimeValue.Text = work_info.planned_time

        # update tool info
        text = ''
        if cnc_info.tool_slot == 0:
            text = 'T{:d} -'.format(cnc_info.tool_id)
        else:
            text = 'T{:d} Slot:{:d} -'.format(cnc_info.tool_id, cnc_info.tool_slot)
        text = text + ' X:' + format_float(cnc_info.tool_offset_x, um_decimals, DTMD_FULL)
        text = text + ' Y:' + format_float(cnc_info.tool_offset_y, um_decimals, DTMD_FULL)
        text = text + ' Z:' + format_float(cnc_info.tool_offset_z, um_decimals, DTMD_FULL)
        self.ToolInfoLabel.Text = text

        # update tab cnc values
        if self.TabControl.ActiveTab == self.TabCNC:
            text = 'UNKNOWN'
            if is_in_str_list_range(CS_TEXTS, self.ctx.compile_info.state):
                text = CS_TEXTS[self.ctx.compile_info.state]
            self.CompilationStateLabel.Text = ' Compilation state : ' + text
            self.CompilationMessageLabel.Text = ' Message : ' + self.ctx.compile_info.message

        # update tab override values:
        if self.TabControl.ActiveTab == self.TabOverrides:

            def update_override(obj, val, name: str):
                obj.Enabled = getattr(cnc_info, f'override_{name}_enabled')
                obj.Max     = getattr(cnc_info, f'override_{name}_max')
                obj.Min     = getattr(cnc_info, f'override_{name}_min')
                value       = getattr(cnc_info, f'override_{name}')
                obj.Value   = value
                val.Text    = f'{value} %'

            update_override(self.OverrideJog, self.OverrideJogValue, 'jog')
            update_override(self.OverrideSpindle, self.OverrideSpindleValue, 'spindle')
            update_override(self.OverrideFast, self.OverrideFastValue, 'fast')
            update_override(self.OverrideFeed, self.OverrideFeedValue, 'feed')
            update_override(self.OverrideFeedCustom1, self.OverrideFeedCustom1Value, 'feed_custom_1')
            update_override(self.OverrideFeedCustom2, self.OverrideFeedCustom2Value, 'feed_custom_2')

        # update tab homing
        if self.TabControl.ActiveTab == self.TabHoming:
            h_mask = axes_info.homing_done_mask

            def set_homing_state_color(target, mask, action):
                if (not axes_info.has_data) or (not enabled_commands.has_data):
                    target.Fill.Color = DEF_CLA_HOMING_OFF
                else:
                    if (enabled_commands.cnc_homing & mask) == 0:
                        target.Fill.Color = DEF_CLA_HOMING_OFF if (h_mask & mask) > 0 else DEF_CLA_HOMING_TODO
                    else:
                        target.Fill.Color = DEF_CLA_HOMING_DONE if (h_mask & mask) > 0 else DEF_CLA_HOMING_TODO

            set_homing_state_color(self.HomingXState, cnc.X_AXIS_MASK, self.CNCHomingXAction)
            set_homing_state_color(self.HomingYState, cnc.Y_AXIS_MASK, self.CNCHomingYAction)
            set_homing_state_color(self.HomingZState, cnc.Z_AXIS_MASK, self.CNCHomingZAction)
            set_homing_state_color(self.HomingAState, cnc.A_AXIS_MASK, self.CNCHomingAAction)
            set_homing_state_color(self.HomingBState, cnc.B_AXIS_MASK, self.CNCHomingBAction)
            set_homing_state_color(self.HomingCState, cnc.C_AXIS_MASK, self.CNCHomingCAction)
            #set_homing_state_color(self.HomingAllState, cnc.C_AXIS_MASK, self.CNCHomingAllAction)


            """
            self.HomingXState.Fill.Color = DEF_CLA_HOMING_DONE if (h_mask & cnc.X_AXIS_MASK) > 0 else DEF_CLA_HOMING_TODO
            self.HomingYState.Fill.Color = DEF_CLA_HOMING_DONE if (h_mask & cnc.Y_AXIS_MASK) > 0 else DEF_CLA_HOMING_TODO
            self.HomingZState.Fill.Color = DEF_CLA_HOMING_DONE if (h_mask & cnc.Z_AXIS_MASK) > 0 else DEF_CLA_HOMING_TODO
            self.HomingAState.Fill.Color = DEF_CLA_HOMING_DONE if (h_mask & cnc.A_AXIS_MASK) > 0 else DEF_CLA_HOMING_TODO
            self.HomingBState.Fill.Color = DEF_CLA_HOMING_DONE if (h_mask & cnc.B_AXIS_MASK) > 0 else DEF_CLA_HOMING_TODO
            self.HomingCState.Fill.Color = DEF_CLA_HOMING_DONE if (h_mask & cnc.C_AXIS_MASK) > 0 else DEF_CLA_HOMING_TODO
            self.HomingAllState.Fill.Color = DEF_CLA_HOMING_DONE if axes_info.homing_done else DEF_CLA_HOMING_TODO
            """

        # update tab digital inputs/outputs values
        if self.TabControl.ActiveTab == self.TabDIO:
            bitmap = self.DIOImage.Bitmap
            bitmap.Width = int(self.DIOImage.Width)
            bitmap.Height = int(self.DIOImage.Height)
            bitmap.Clear(0xFF000000)
            canvas = bitmap.Canvas
            r = RectF(8 + 15, 10, bitmap.Width - 8, bitmap.Height - 10)
            # from delphi FMX documentation
            # procedure FillText(
            #       const ARect: TRectF;
            #       const AText: string;
            #       const WordWrap: Boolean;
            #       const AOpacity: Single;
            #       const Flags: TFillTextFlags;
            #       const ATextAlign: TTextAlign;
            #       const AVTextAlign: TTextAlign = TTextAlign.Center
            #   ); virtual;
            s = 'hello'
            #canvas.FillText(r, s, False, 100.0, 'RightToLeft')
            #canvas.FillText(None, 'hello world', False, 1, [], 0, 0)

        # update tab scanning laser values
        if self.TabControl.ActiveTab == self.TabScanningLaser:
            scanning_info = self.api.get_scanning_laser_info()
            self.LaserOutBitValue.Text = f'{scanning_info.laser_out_bit} bt'
            self.LaserOutUMFValue.Text = f'{scanning_info.laser_out_umf} bt'
            self.LaserHMeasureValue.Text = um_spc_lf.format(scanning_info.laser_h_measure)
            self.LaserMCSXPositionValue.Text = um_spc_lf.format(scanning_info.laser_mcs_x_position)
            self.LaserMCSYPositionValue.Text = um_spc_lf.format(scanning_info.laser_mcs_y_position)
            self.LaserMCSZPositionValue.Text = um_spc_lf.format(scanning_info.laser_mcs_z_position)

        # update tab analog inputs/outputs values
        if self.TabControl.ActiveTab == self.TabAIO:
            analog_inputs = self.api.get_analog_inputs()
            self.ANI01Value.Text = '{:5.2f} %'.format(analog_inputs.value[0])
            self.ANI02Value.Text = '{:5.2f} %'.format(analog_inputs.value[1])
            self.ANI03Value.Text = '{:5.2f} %'.format(analog_inputs.value[2])
            self.ANI04Value.Text = '{:5.2f} %'.format(analog_inputs.value[3])
            self.ANI05Value.Text = '{:5.2f} %'.format(analog_inputs.value[4])
            self.ANI06Value.Text = '{:5.2f} %'.format(analog_inputs.value[5])
            self.ANI07Value.Text = '{:5.2f} %'.format(analog_inputs.value[6])
            self.ANI08Value.Text = '{:5.2f} %'.format(analog_inputs.value[7])
            self.ANI09Value.Text = '{:5.2f} %'.format(analog_inputs.value[8])
            self.ANI10Value.Text = '{:5.2f} %'.format(analog_inputs.value[9])
            self.ANI11Value.Text = '{:5.2f} %'.format(analog_inputs.value[10])
            self.ANI12Value.Text = '{:5.2f} %'.format(analog_inputs.value[11])
            self.ANI13Value.Text = '{:5.2f} %'.format(analog_inputs.value[12])
            self.ANI14Value.Text = '{:5.2f} %'.format(analog_inputs.value[13])
            self.ANI15Value.Text = '{:5.2f} %'.format(analog_inputs.value[14])
            self.ANI16Value.Text = '{:5.2f} %'.format(analog_inputs.value[15])

            analog_outputs = self.api.get_analog_outputs()
            self.ANO01Value.Text = '{:5.2f} %'.format(analog_outputs.value[0])
            self.ANO02Value.Text = '{:5.2f} %'.format(analog_outputs.value[1])
            self.ANO03Value.Text = '{:5.2f} %'.format(analog_outputs.value[2])
            self.ANO04Value.Text = '{:5.2f} %'.format(analog_outputs.value[3])
            self.ANO05Value.Text = '{:5.2f} %'.format(analog_outputs.value[4])
            self.ANO06Value.Text = '{:5.2f} %'.format(analog_outputs.value[5])
            self.ANO07Value.Text = '{:5.2f} %'.format(analog_outputs.value[6])
            self.ANO08Value.Text = '{:5.2f} %'.format(analog_outputs.value[7])
            self.ANO09Value.Text = '{:5.2f} %'.format(analog_outputs.value[8])
            self.ANO10Value.Text = '{:5.2f} %'.format(analog_outputs.value[9])
            self.ANO11Value.Text = '{:5.2f} %'.format(analog_outputs.value[10])
            self.ANO12Value.Text = '{:5.2f} %'.format(analog_outputs.value[11])
            self.ANO13Value.Text = '{:5.2f} %'.format(analog_outputs.value[12])
            self.ANO14Value.Text = '{:5.2f} %'.format(analog_outputs.value[13])
            self.ANO15Value.Text = '{:5.2f} %'.format(analog_outputs.value[14])
            self.ANO16Value.Text = '{:5.2f} %'.format(analog_outputs.value[15])

        # update tab machining info values
        if self.TabControl.ActiveTab == self.TabMachiningInfo:
            pass

        # update tab system info values
        if self.TabControl.ActiveTab == self.TabSystemInfo:
            system_info = self.api.get_system_info()
            if not cnc.APISystemInfo.are_equal(self.system_info_in_use, system_info):
                self.system_info_in_use = system_info
                self.SystemInfoMemo.Lines.Clear()
                self.SystemInfoMemo.Lines.Add('')
                self.SystemInfoMemo.Lines.Add('  Machine Name               : ' + system_info.machine_name)
                self.SystemInfoMemo.Lines.Add('  Control Software Version   : ' + system_info.control_software_version)
                self.SystemInfoMemo.Lines.Add('  Core Version               : ' + system_info.core_version)
                self.SystemInfoMemo.Lines.Add('  API Server Version         : ' + system_info.api_server_version)
                self.SystemInfoMemo.Lines.Add('  Firmware Version           : ' + system_info.firmware_version)
                self.SystemInfoMemo.Lines.Add('  Firmware Version Tag       : ' + system_info.firmware_version_tag)
                self.SystemInfoMemo.Lines.Add('  Firmware Interface Level   : ' + system_info.firmware_interface_level)
                self.SystemInfoMemo.Lines.Add('  Order Code                 : ' + system_info.order_code)
                self.SystemInfoMemo.Lines.Add('  Customer Id                : ' + system_info.customer_id)
                self.SystemInfoMemo.Lines.Add('  Serial Number              : ' + system_info.serial_number)
                self.SystemInfoMemo.Lines.Add('  Part Number                : ' + system_info.part_number)
                self.SystemInfoMemo.Lines.Add('  Customization Number       : ' + system_info.customization_number)
                self.SystemInfoMemo.Lines.Add('  Hardware Version           : ' + system_info.hardware_version)
                self.SystemInfoMemo.Lines.Add('  Operative System           : ' + system_info.operative_system)
                self.SystemInfoMemo.Lines.Add('  Operative System CRC       : ' + system_info.operative_system_crc)
                self.SystemInfoMemo.Lines.Add('  PLD Version                : ' + system_info.pld_version)

        # update status bar
        text = 'UNKNOWN'
        if is_in_str_list_range(SM_TEXTS, cnc_info.state_machine):
            text = SM_TEXTS[cnc_info.state_machine]
        self.StateMachineLabel.Text = 'Machine State : ' + text
        text = 'UNKNOWN'
        if is_in_str_list_range(ASCS_TEXTS, self.api_server_connection_state):
            text = ASCS_TEXTS[self.api_server_connection_state]
        if not self.api_server_use_tls:
            self.APIServerConnectionStateLabel.Text = 'Connection with Server : ' + text
        else:
            self.APIServerConnectionStateLabel.Text = 'Connection with Server [TLS] : ' + text

        # update axis enablings
        if self.axes_mask_enablings_in_use != cnc_info.axes_mask:
            self.axes_mask_enablings_in_use = cnc_info.axes_mask

            x_axis_enabled = (self.axes_mask_enablings_in_use & cnc.X_AXIS_MASK) != 0
            y_axis_enabled = (self.axes_mask_enablings_in_use & cnc.Y_AXIS_MASK) != 0
            z_axis_enabled = (self.axes_mask_enablings_in_use & cnc.Z_AXIS_MASK) != 0
            a_axis_enabled = (self.axes_mask_enablings_in_use & cnc.A_AXIS_MASK) != 0
            b_axis_enabled = (self.axes_mask_enablings_in_use & cnc.B_AXIS_MASK) != 0
            c_axis_enabled = (self.axes_mask_enablings_in_use & cnc.C_AXIS_MASK) != 0

            self.MCSXLabel.Enabled = x_axis_enabled
            self.MCSYLabel.Enabled = y_axis_enabled
            self.MCSZLabel.Enabled = z_axis_enabled
            self.MCSALabel.Enabled = a_axis_enabled
            self.MCSBLabel.Enabled = b_axis_enabled
            self.MCSCLabel.Enabled = c_axis_enabled
            self.MCSXValue.Enabled = x_axis_enabled
            self.MCSYValue.Enabled = y_axis_enabled
            self.MCSZValue.Enabled = z_axis_enabled
            self.MCSAValue.Enabled = a_axis_enabled
            self.MCSBValue.Enabled = b_axis_enabled
            self.MCSCValue.Enabled = c_axis_enabled

            self.WCSXLabel.Enabled = x_axis_enabled
            self.WCSYLabel.Enabled = y_axis_enabled
            self.WCSZLabel.Enabled = z_axis_enabled
            self.WCSALabel.Enabled = a_axis_enabled
            self.WCSBLabel.Enabled = b_axis_enabled
            self.WCSCLabel.Enabled = c_axis_enabled
            self.WCSXValue.Enabled = x_axis_enabled
            self.WCSYValue.Enabled = y_axis_enabled
            self.WCSZValue.Enabled = z_axis_enabled
            self.WCSAValue.Enabled = a_axis_enabled
            self.WCSBValue.Enabled = b_axis_enabled
            self.WCSCValue.Enabled = c_axis_enabled

            self.AVLXLabel.Enabled = x_axis_enabled
            self.AVLYLabel.Enabled = y_axis_enabled
            self.AVLZLabel.Enabled = z_axis_enabled
            self.AVLALabel.Enabled = a_axis_enabled
            self.AVLBLabel.Enabled = b_axis_enabled
            self.AVLCLabel.Enabled = c_axis_enabled
            self.AVLXValue.Enabled = x_axis_enabled
            self.AVLYValue.Enabled = y_axis_enabled
            self.AVLZValue.Enabled = z_axis_enabled
            self.AVLAValue.Enabled = a_axis_enabled
            self.AVLBValue.Enabled = b_axis_enabled
            self.AVLCValue.Enabled = c_axis_enabled

            self.WOFXLabel.Enabled = x_axis_enabled
            self.WOFYLabel.Enabled = y_axis_enabled
            self.WOFZLabel.Enabled = z_axis_enabled
            self.WOFALabel.Enabled = a_axis_enabled
            self.WOFBLabel.Enabled = b_axis_enabled
            self.WOFCLabel.Enabled = c_axis_enabled
            self.WOFXValue.Enabled = x_axis_enabled
            self.WOFYValue.Enabled = y_axis_enabled
            self.WOFZValue.Enabled = z_axis_enabled
            self.WOFAValue.Enabled = a_axis_enabled
            self.WOFBValue.Enabled = b_axis_enabled
            self.WOFCValue.Enabled = c_axis_enabled

            self.MTPXLabel.Enabled = x_axis_enabled
            self.MTPYLabel.Enabled = y_axis_enabled
            self.MTPZLabel.Enabled = z_axis_enabled
            self.MTPALabel.Enabled = a_axis_enabled
            self.MTPBLabel.Enabled = b_axis_enabled
            self.MTPCLabel.Enabled = c_axis_enabled
            self.MTPXValue.Enabled = x_axis_enabled
            self.MTPYValue.Enabled = y_axis_enabled
            self.MTPZValue.Enabled = z_axis_enabled
            self.MTPAValue.Enabled = a_axis_enabled
            self.MTPBValue.Enabled = b_axis_enabled
            self.MTPCValue.Enabled = c_axis_enabled

            self.PTPXLabel.Enabled = x_axis_enabled
            self.PTPYLabel.Enabled = y_axis_enabled
            self.PTPZLabel.Enabled = z_axis_enabled
            self.PTPALabel.Enabled = a_axis_enabled
            self.PTPBLabel.Enabled = b_axis_enabled
            self.PTPCLabel.Enabled = c_axis_enabled
            self.PTPXValue.Enabled = x_axis_enabled
            self.PTPYValue.Enabled = y_axis_enabled
            self.PTPZValue.Enabled = z_axis_enabled
            self.PTPAValue.Enabled = a_axis_enabled
            self.PTPBValue.Enabled = b_axis_enabled
            self.PTPCValue.Enabled = c_axis_enabled

            self.JOPXLabel.Enabled = x_axis_enabled
            self.JOPYLabel.Enabled = y_axis_enabled
            self.JOPZLabel.Enabled = z_axis_enabled
            self.JOPALabel.Enabled = a_axis_enabled
            self.JOPBLabel.Enabled = b_axis_enabled
            self.JOPCLabel.Enabled = c_axis_enabled
            self.JOPXValue.Enabled = x_axis_enabled
            self.JOPYValue.Enabled = y_axis_enabled
            self.JOPZValue.Enabled = z_axis_enabled
            self.JOPAValue.Enabled = a_axis_enabled
            self.JOPBValue.Enabled = b_axis_enabled
            self.JOPCValue.Enabled = c_axis_enabled

        # update general objects enabling
        if self.api_server_connection_state in [ASCS_DISCONNECTED, ASCS_ERROR]:
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
            self.CNCJogCommandXMButton.Enabled = False
            self.CNCJogCommandXPButton.Enabled = False
            self.CNCJogCommandYMButton.Enabled = False
            self.CNCJogCommandYPButton.Enabled = False
            self.CNCJogCommandZMButton.Enabled = False
            self.CNCJogCommandZPButton.Enabled = False
            self.CNCJogCommandAMButton.Enabled = False
            self.CNCJogCommandAPButton.Enabled = False
            self.CNCJogCommandBMButton.Enabled = False
            self.CNCJogCommandBPButton.Enabled = False
            self.CNCJogCommandCMButton.Enabled = False
            self.CNCJogCommandCPButton.Enabled = False
            self.CNCMDICommandMemo.Enabled = False
            self.SetProgramPositionXEdit.Enabled = False
            self.SetProgramPositionYEdit.Enabled = False
            self.SetProgramPositionZEdit.Enabled = False
            self.SetProgramPositionAEdit.Enabled = False
            self.SetProgramPositionBEdit.Enabled = False
            self.SetProgramPositionCEdit.Enabled = False
            self.APIServerHostEdit.Enabled = True
            self.APIServerPortEdit.Enabled = True
            self.UseTLSCheckBox.Enabled = True
        else:
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
            self.CNCJogCommandXMButton.Enabled = (self.ctx.enabled_commands.cnc_jog_command & cnc.X_AXIS_MASK) > 0
            self.CNCJogCommandXPButton.Enabled = (self.ctx.enabled_commands.cnc_jog_command & cnc.X_AXIS_MASK) > 0
            self.CNCJogCommandYMButton.Enabled = (self.ctx.enabled_commands.cnc_jog_command & cnc.Y_AXIS_MASK) > 0
            self.CNCJogCommandYPButton.Enabled = (self.ctx.enabled_commands.cnc_jog_command & cnc.Y_AXIS_MASK) > 0
            self.CNCJogCommandZMButton.Enabled = (self.ctx.enabled_commands.cnc_jog_command & cnc.Z_AXIS_MASK) > 0
            self.CNCJogCommandZPButton.Enabled = (self.ctx.enabled_commands.cnc_jog_command & cnc.Z_AXIS_MASK) > 0
            self.CNCJogCommandAMButton.Enabled = (self.ctx.enabled_commands.cnc_jog_command & cnc.A_AXIS_MASK) > 0
            self.CNCJogCommandAPButton.Enabled = (self.ctx.enabled_commands.cnc_jog_command & cnc.A_AXIS_MASK) > 0
            self.CNCJogCommandBMButton.Enabled = (self.ctx.enabled_commands.cnc_jog_command & cnc.B_AXIS_MASK) > 0
            self.CNCJogCommandBPButton.Enabled = (self.ctx.enabled_commands.cnc_jog_command & cnc.B_AXIS_MASK) > 0
            self.CNCJogCommandCMButton.Enabled = (self.ctx.enabled_commands.cnc_jog_command & cnc.C_AXIS_MASK) > 0
            self.CNCJogCommandCPButton.Enabled = (self.ctx.enabled_commands.cnc_jog_command & cnc.C_AXIS_MASK) > 0
            self.CNCMDICommandMemo.Enabled = self.ctx.enabled_commands.cnc_mdi_command
            self.SetProgramPositionXEdit.Enabled = (self.ctx.enabled_commands.set_program_position & cnc.X_AXIS_MASK) > 0
            self.SetProgramPositionYEdit.Enabled = (self.ctx.enabled_commands.set_program_position & cnc.Y_AXIS_MASK) > 0
            self.SetProgramPositionZEdit.Enabled = (self.ctx.enabled_commands.set_program_position & cnc.Z_AXIS_MASK) > 0
            self.SetProgramPositionAEdit.Enabled = (self.ctx.enabled_commands.set_program_position & cnc.A_AXIS_MASK) > 0
            self.SetProgramPositionBEdit.Enabled = (self.ctx.enabled_commands.set_program_position & cnc.B_AXIS_MASK) > 0
            self.SetProgramPositionCEdit.Enabled = (self.ctx.enabled_commands.set_program_position & cnc.C_AXIS_MASK) > 0
            self.APIServerHostEdit.Enabled = False
            self.APIServerPortEdit.Enabled = False
            self.UseTLSCheckBox.Enabled = False
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
                self.program_safe_file_name = memento.get('program_save_file_name', '')
                return True
            return False
        except:
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
            memento.set('program_save_file_name', self.program_safe_file_name)

            # save memento to file
            file_path = os.path.dirname(__file__) + '\\'
            return memento.save_to_file(file_path + SETTINGS_FILE_NAME, indent=4)
        except:
            return False
    #
    # == END: memento section

    # == BEG: generic methods
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
        except:
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
        except:
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
        except:
            return False

    #
    # == END: generic methods

    def __update_fields(self):
        """Updates editable fields with related data."""
        if self.in_update:
            return
        self.in_update = True
        try:
            um = '{:.3f}' if self.units_mode == cnc.UM_METRIC else '{:.4f}'
            self.ProgramLoadFileNameEdit.Text = self.program_load_file_name
            self.ProgramSaveFileNameEdit.Text = self.program_save_file_name
            self.CNCResumeAfterStopFromLineEdit.Text = str(self.cnc_resume_after_stop_from_line)
            self.CNCStartFromLineEdit.Text = str(self.cnc_start_from_line)
            self.SetProgramPositionXEdit.Text = um.format(self.set_program_position_x)
            self.SetProgramPositionYEdit.Text = um.format(self.set_program_position_y)
            self.SetProgramPositionZEdit.Text = um.format(self.set_program_position_z)
            self.SetProgramPositionAEdit.Text = um.format(self.set_program_position_a)
            self.SetProgramPositionBEdit.Text = um.format(self.set_program_position_b)
            self.SetProgramPositionCEdit.Text = um.format(self.set_program_position_c)
            self.APIServerHostEdit.Text = self.api_server_host
            self.APIServerPortEdit.Text = str(self.api_server_port)
            self.UseTLSCheckBox.IsChecked = self.api_server_use_tls
            self.StayOnTopCheckBox.IsChecked = self.stay_on_top
        finally:
            self.in_update = False
