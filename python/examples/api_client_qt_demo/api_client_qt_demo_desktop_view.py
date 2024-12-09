"""API Client Demo using Qt PySide6 UI."""
#-------------------------------------------------------------------------------
# Name:         api_client_qt_demo_desktop_view
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
# Created:      08/12/2024
# Copyright:    RosettaCNC (c) 2016-2024
# Licence:      RosettaCNC License 1.0 (RCNC-1.0)
# Coding Style  https://www.python.org/dev/peps/pep-0008/
#               With cnc_vision_vcl/fmx objects is used Delphi coding style
#-------------------------------------------------------------------------------
import os
import time
from statistics import median

import cnc_api_client_core as cnc

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QMainWindow
from ui_desktop_view import Ui_DesktopView

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

class ApiClientQtDemoDesktopView(QMainWindow):
    "Xxx..."

    def __init__(self):
        # call qt inherited view constructor
        super().__init__()

        # set main ui
        self.ui = Ui_DesktopView()
        self.ui.setupUi(self)

        # set caption
        self.setWindowTitle("API Client Demo with Qt PySide6 UI " + VERSION)

        # set main form events handlers
        #self.OnClose = self.__on_form_close
        #self.OnShow = self.__on_form_show

        # set current persistable save version
        self.__persistable_save_version = 1

        # create and set update timer
        self.tmrUpdate = QTimer(self)
        self.tmrUpdate.setInterval(1)
        self.tmrUpdate.timeout.connect(self.__on_timer_update)
        self.tmrUpdate.setSingleShot(False)

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

    # == BEG: relink of native events from inherited Qt PySide6 UI design
    #
    def showEvent(self, event):
        super().showEvent(event)
        self.__on_form_show(event)
    def closeEvent(self, event):
        super().closeEvent(event)
    #
    # == BEG: relink of native events from inherited Qt PySide6 UI design


    # == BEG: events implementation
    #
    def __on_form_show(self, event):
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

        # update fields
        self.__update_fields()

        # enable first stay on top update
        self.stay_on_top_changed = True

    def __on_timer_update(self):
        pass
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
        pass
