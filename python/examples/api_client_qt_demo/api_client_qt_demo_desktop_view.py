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
# Created:      12/03/2026
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
# pylint: disable=R1702 -> too-many-nested-blocks
# pylint: disable=W0105 -> pointless-string-statement
# pylint: disable=W0201 -> attribute-defined-outside-init   ## take care when you use that ##
# pylint: disable=W0238 -> unused-private-member
# pylint: disable=W0612 -> unused-variable
# pylint: disable=W0718 -> broad-exception-caught           ## take care when you use that ##
#-------------------------------------------------------------------------------
import time
import ipaddress
from pathlib import Path
from collections import namedtuple

from PySide6.QtCore import Qt, QEvent, QTimer, QSize
from PySide6.QtGui import QAction, QFont, QIcon
from PySide6.QtWidgets import (
    QAbstractSlider,
    QButtonGroup,
    QCheckBox,
    QDialog,
    QFileDialog,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QRadioButton,
    QSlider,
    QTableWidgetItem
)

from qt_gcode_highlighter import GCodeHighlighter
from qt_alarms_warnings_dialog import AlarmsWarningsDialog, AlarmsWarningsMode
from qt_user_dialogs import UserMediaDialog, UserMessageDialog
from qt_realtime_scope import QRealTimeScope
from qt_extra_widgets import QLedWidget

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

# == api server connection led colors
ASCL_DISCONNECTED                   = "#b0b0b0"
ASCL_CONNECTED                      = "#21c45a"
ASCL_ERROR                          = "#ff7259"

# == api server connection state
ASCS_DISCONNECTED                   = 0
ASCS_CONNECTED                      = 1
ASCS_ERROR                          = 2

# == api server connection state texts (english)
ASCS_TEXTS = [
    'DISCONNECTED',
    'CONNECTED',
    'DISCONNECTED AFTER AN ERROR'
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

# settle times to sync api get values after an api set value
SETTLE_TIME_SLIDER                  = 0.4

AxisControls = namedtuple('AxisControls', ['label', 'value'])

class ApiClientQtDemoDesktopView(QMainWindow):
    """Xxx..."""

    def __init__(self):
        # call qt inherited view constructor
        super().__init__()

        # set Qt Designer generated ui
        self.ui = Ui_DesktopView()
        self.ui.setupUi(self)

        # set caption
        self.setWindowTitle(APP_TITLE)

        # set window ui to fixed size
        self.setFixedSize(self.size())

        # set current persistable save version
        self.__persistable_save_version = 1

        # set realtime scope to plot axes positions
        self.realtime_scope = QRealTimeScope(self.ui.axesPositionsPlot, 6, 4000)

        # set laser scope to plot laser values
        self.laser_scope = QRealTimeScope(self.ui.laserPlot, 1, 4000)
        self.ui.laserPlot.enableAutoRange('y', False)
        self.ui.laserPlot.setYRange(0, 4095, padding=0.05)
        self.ui.laserPlot.getPlotItem().getAxis('left').setWidth(30)

        # create a mono font object for code editors
        mono_font = QFont("Consolas")               # Windows
        if not QFont(mono_font).exactMatch():
            mono_font = QFont("Monaco")             # macOS
        if not QFont(mono_font).exactMatch():
            mono_font = QFont("DejaVu Sans Mono")   # Linux
        if not QFont(mono_font).exactMatch():
            mono_font = QFont("Courier New")        # Fallback universale
        mono_font.setStyleHint(QFont.Monospace)
        mono_font.setPointSize(9)

        # create light style sheet
        self.sytlesheet_light = (
        """
            /* style for horizontal lines */
            QFrame[isHLine="true"] {
                color: #B9B9B9;
            }

            /* style for g-code editors */
            QPlainTextEdit {
                background-color: #1E1E1E;
                color: #F8F8F2;
                border: 1px solid #44475A;
                selection-background-color: #44475A;
                selection-color: #F8F8F2;
                padding: 0px;
            }

            /* style for common buttons */
            QPushButton:pressed {
                background-color: #C3E3FD;
            }

            QPushButton:hover {
                background-color: #DCEFFE;
            }

            /* style for special buttons */
            QPushButton[isSpecial="true"] {
                border: 2px solid #B9B9B9;
                border-radius: 6px;
                background-color: white;
            }

            QPushButton[isSpecial="true"]:pressed {
                border: 2px solid #54B7FF;
                background-color: #e0e0e0;
            }
        """
        )

        # apply light style sheet
        self.setStyleSheet(self.sytlesheet_light)

        # apply and set gcode editor highlighter
        self.highlighter = GCodeHighlighter(self.ui.gcodeProgramEdit.document())
        self.ui.gcodeProgramEdit.setFont(mono_font)

        # apply and set mdi command editor highlighter
        self.highlighter = GCodeHighlighter(self.ui.mdiCommandEdit.document())
        self.ui.mdiCommandEdit.setFont(mono_font)

        # create and set update timer
        self.tmr_update = QTimer(self)
        self.tmr_update.setInterval(1)
        self.tmr_update.timeout.connect(self.__on_timer_update)
        self.tmr_update.setSingleShot(False)

        # create labels for status bar
        self.StateMachineLabel = QLabel("")
        self.StateMachineLabel.setMinimumWidth(500)
        self.StateMachineLabel.setMaximumWidth(500)
        self.APIServerConnectionStateLabel = QLabel("")
        self.APIServerConnectionStateLabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.APIServerConnectionStateLed = QLedWidget(
            self.ui.statusBar,
            self.ui.statusBar.contentsRect().height() - 16,
            ':/images/images/circular-led.svg',
            color_on=ASCL_CONNECTED,
            color_off=ASCL_DISCONNECTED
        )
        self.ui.statusBar.setContentsMargins(6, 0, 0, 0)
        self.ui.statusBar.addPermanentWidget(self.StateMachineLabel)
        self.ui.statusBar.addPermanentWidget(self.APIServerConnectionStateLabel, 1)
        self.ui.statusBar.addPermanentWidget(self.APIServerConnectionStateLed)

        # lock tables header resize
        self.ui.csOffsetsTable.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.ui.csOffsetsTable.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)

        # set cooler states status push buttons
        self.ui.cfsmCoolantMistButton.setStatusIcons(
            icon_disabled=":/images/images/cooler_mist_disabled.svg",
            icon_off=":/images/images/cooler_mist_off.svg",
            icon_on=":/images/images/cooler_mist_on.svg",
            icon_size=QSize(50, 50)
        )
        self.ui.cfsmCoolantFloodButton.setStatusIcons(
            icon_disabled=":/images/images/cooler_flood_disabled.svg",
            icon_off=":/images/images/cooler_flood_off.svg",
            icon_on=":/images/images/cooler_flood_on.svg",
            icon_size=QSize(50, 50)
        )
        self.ui.cfsmAUX01Button.setStatusIcons(
            icon_disabled="images\\aux_01_disabled.svg",
            icon_off="images\\aux_01_enabled_1.svg",
            icon_on="images\\aux_01_enabled_2.svg",
            icon_size=QSize(28, 28)
        )
        self.ui.cfsmAUX02Button.setStatusIcons(
            icon_disabled="images\\aux_02_disabled.svg",
            icon_off="images\\aux_02_enabled_1.svg",
            icon_on="images\\aux_02_enabled_2.svg",
            icon_size=QSize(28, 28)
        )
        self.ui.cfsmAUX03Button.setStatusIcons(
            icon_disabled="images\\aux_03_disabled.svg",
            icon_off="images\\aux_03_enabled_1.svg",
            icon_on="images\\aux_03_enabled_2.svg",
            icon_size=QSize(28, 28)
        )
        self.ui.cfsmAUX04Button.setStatusIcons(
            icon_disabled="images\\aux_04_disabled.svg",
            icon_off="images\\aux_04_enabled_1.svg",
            icon_on="images\\aux_04_enabled_2.svg",
            icon_size=QSize(28, 28)
        )
        self.ui.cfsmAUX05Button.setStatusIcons(
            icon_disabled="images\\aux_05_disabled.svg",
            icon_off="images\\aux_05_enabled_1.svg",
            icon_on="images\\aux_05_enabled_2.svg",
            icon_size=QSize(28, 28)
        )

        # declare class public attributes (for pylint check)
        self.api = None
        self.ctx = None
        self.api_server_connection_state = None
        self.axes_mask_enablings_in_use = None
        self.cnc_resume_after_stop_from_line = None
        self.cnc_start_from_line = None
        self.connection_with_cnc = None
        self.in_update = None
        self.slider_update_inhibition_until = 0.0
        self.stay_on_top_changed = None

        # declare active operator request attributes
        self.active_operator_request = None
        self.active_operator_request_dialog = None

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
        self.machining_info_in_use = None
        self.system_info_in_use = None
        self.coordinates_system_info_in_use = None

        # create an action to manage all event executions
        self.on_action_main_execute = QAction("", self)
        self.on_action_main_execute.triggered.connect(self.__on_action_main_execute)

        # create and set apply wcs mode group
        self.apply_wcs_mode_group = QButtonGroup(self)
        self.apply_wcs_mode_group.addButton(self.ui.csActivateWCSOnlyRadioButton, 0)
        self.apply_wcs_mode_group.addButton(self.ui.csSetWCSOffsetOnlyRadioButton, 1)
        self.apply_wcs_mode_group.addButton(self.ui.csSetWCSOffsetAndActivateRadioButton, 2)
        self.apply_wcs_mode_group.idClicked.connect(self.__on_button_group_clicked)

        # link actions to all edits
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

        # link actions to all checkbox
        for obj in self.findChildren(QCheckBox):
            obj.clicked.connect(self.__on_check_box_clicked)

        # link actions to all radio button
        for obj in self.findChildren(QRadioButton):
            obj.clicked.connect(self.__on_radio_button_clicked)

        # link actions to override value labels enabled to double-click
        self.override_value_labels = {
            self.ui.ovrJogValue             : "jog",
            self.ui.ovrSpindleValue         : "spindle",
            self.ui.ovrFastValue            : "fast",
            self.ui.ovrFeedValue            : "feed",
            self.ui.ovrFeedCSM1Value        : "feed_custom_1",
            self.ui.ovrFeedCSM2Value        : "feed_custom_2",
            self.ui.ovrPlasmaVoltageValue   : "plasma_voltage",
            self.ui.ovrPlasmaPowerValue     : "plasma_power",
        }
        for label in self.override_value_labels:
            label.installEventFilter(self)

        # link actions to all sliders
        for obj in self.findChildren(QSlider):
            obj.actionTriggered.connect(self.__on_slider_action)

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
    def eventFilter(self, obj, event):
        """Handles double-clicks on all QLabels."""
        if isinstance(obj, QLabel) and event.type() == QEvent.MouseButtonDblClick:
            self.__on_label_double_click(obj)
            return True
        return super().eventFilter(obj, event)
    def showEvent(self, event):
        super().showEvent(event)
        self.__on_form_show()
    #
    # == BEG: relink of native events from inherited Qt PySide6 UI design


    # == BEG: events implementation
    #
    def __on_action_main_execute(self):
        sender = self.sender()

        # events main view
        if sender == self.ui.apiServerConnectionButton:
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

        # events commands
        if sender == self.ui.cmdsConnectionOpenButton:
            self.api.cnc_connection_open(use_ui=False, use_fast_mode=False, skip_firmware_check=True, overwrite_cnc_settings=True)
        if sender == self.ui.cmdsConnectionCloseButton:
            self.api.cnc_connection_close()

        if sender == self.ui.cmdsStartButton:
            self.api.cnc_start()
        if sender == self.ui.cmdsStopButton:
            self.api.cnc_stop()
        if sender == self.ui.cmdsPauseButton:
            self.api.cnc_pause()
        if sender == self.ui.cmdsContinueButton:
            self.api.cnc_continue()
        if sender == self.ui.cmdsResumeAfterStopButton:
            self.api.cnc_resume(0)

        # evensts show
        if sender == self.ui.showAlarmsButton:
            self.__alarms_warnings_dialog(AlarmsWarningsMode.ALARMS_CURRENT)
        if sender == self.ui.showAlarmsHistoryButton:
            self.__alarms_warnings_dialog(AlarmsWarningsMode.ALARMS_HISTORY)
        if sender == self.ui.showWarningsButton:
            self.__alarms_warnings_dialog(AlarmsWarningsMode.WARNINGS_CURRENT)
        if sender == self.ui.showWarningsHistoryButton:
            self.__alarms_warnings_dialog(AlarmsWarningsMode.WARNINGS_HISTORY)

        # events tab general
        if sender == self.ui.cfsmSpindleCWButton and not self.ctx.cnc_info.spindle_not_ready:
            self.api.cnc_change_function_state_mode(cnc.FS_NM_SPINDLE_CW, cnc.FS_MD_TOGGLE)
        if sender == self.ui.cfsmSpindleCCWButton and not self.ctx.cnc_info.spindle_not_ready:
            self.api.cnc_change_function_state_mode(cnc.FS_NM_SPINDLE_CCW, cnc.FS_MD_TOGGLE)
        if sender == self.ui.cfsmCoolantMistButton:
            self.api.cnc_change_function_state_mode(cnc.FS_NM_MIST, cnc.FS_MD_TOGGLE)
        if sender == self.ui.cfsmCoolantFloodButton:
            self.api.cnc_change_function_state_mode(cnc.FS_NM_FLOOD, cnc.FS_MD_TOGGLE)
        if sender == self.ui.cfsmAUX01Button:
            self.api.cnc_change_function_state_mode(cnc.FS_NM_AUX_01, cnc.FS_MD_TOGGLE)
        if sender == self.ui.cfsmAUX02Button:
            self.api.cnc_change_function_state_mode(cnc.FS_NM_AUX_02, cnc.FS_MD_TOGGLE)
        if sender == self.ui.cfsmAUX03Button:
            self.api.cnc_change_function_state_mode(cnc.FS_NM_AUX_03, cnc.FS_MD_TOGGLE)
        if sender == self.ui.cfsmAUX04Button:
            self.api.cnc_change_function_state_mode(cnc.FS_NM_AUX_04, cnc.FS_MD_TOGGLE)
        if sender == self.ui.cfsmAUX05Button:
            self.api.cnc_change_function_state_mode(cnc.FS_NM_AUX_05, cnc.FS_MD_TOGGLE)

        # events tab axes position plot

        # events tab program
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

        # events tab g-code
        if sender == self.ui.gcodeGetProgramTextButton:
            data = self.api.get_program_info()
            if data.has_data:
                self.ui.gcodeProgramEdit.setPlainText(data.code)
        if sender == self.ui.gcodeSetProgramTextButton:
            self.api.program_gcode_set_text(self.ui.gcodeProgramEdit.toPlainText())
        if sender == self.ui.gcodeAddProgramTextButton:
            self.api.program_gcode_add_text(self.ui.gcodeAddProgramTextEdit.text())
        if sender == self.ui.gcodeClearProgramTextButton:
            self.api.program_gcode_set_text('')
            self.ui.gcodeProgramEdit.setPlainText('')
            self.ui.gcodeAddProgramTextEdit.setText('')

        # events tab mdi
        if sender == self.ui.mdiCommandExecuteButton:
            mdi_command = self.ui.mdiCommandEdit.toPlainText()
            self.api.cnc_mdi_command(mdi_command)

        # events tab cnc
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
        if sender == self.ui.cncStartButton: # ???
            pass
        if sender == self.ui.cncStopButton: # ???
            pass
        if sender == self.ui.cncPauseButton: # ???
            pass
        if sender == self.ui.cncContinueButton: # ???
            pass
        if sender == self.ui.cncStartFromLineButton: # ???
            pass
        if sender == self.ui.cncResumeAfterStopButton: # ???
            pass
        if sender == self.ui.cncResumeAfterStopFromLineButton: # ???
            pass

        # events tab jog
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

        # events tab overrides
        # events tab homing

        # events tab wcs
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

        # events tab d i/o
        # events tab a i/o
        # events tab scanning laser
        if sender == self.ui.laserZeroXAxisButton:
            self.api.set_program_position_x_with_laser_reference()
        if sender == self.ui.laserZeroYAxisButton:
            self.api.set_program_position_y_with_laser_reference()
        if sender == self.ui.laserZeroZAxisButton:
            self.api.set_program_position_z_with_laser_reference()

        # events tab machining info

        # events tab ui dialogs
        if sender == self.ui.uidAboutButton:
            self.api.show_ui_dialog(cnc.UID_ID_ABOUT)
        if sender == self.ui.uidATCManagementButton:
            self.api.show_ui_dialog(cnc.UID_ID_ATC_MANAGEMENT)
        if sender == self.ui.uidBoardEtherCATMonitorButton:
            self.api.show_ui_dialog(cnc.UID_ID_BOARD_ETHERCAT_MONITOR)
        if sender == self.ui.uidBoardFirmwareManagerButton:
            self.api.show_ui_dialog(cnc.UID_ID_BOARD_FIRMWARE_MANAGER)
        if sender == self.ui.uidBoardMonitorButton:
            self.api.show_ui_dialog(cnc.UID_ID_BOARD_MONITOR)
        if sender == self.ui.uidBoardSettingsButton:
            self.api.show_ui_dialog(cnc.UID_ID_BOARD_SETTINGS)
        if sender == self.ui.uidChangeBoardIPButton:
            self.api.show_ui_dialog(cnc.UID_ID_CHANGE_BOARD_IP)
        if sender == self.ui.uidMacrosManagementButton:
            self.api.show_ui_dialog(cnc.UID_ID_MACROS_MANAGEMENT)
        if sender == self.ui.uidParametersLibraryButton:
            self.api.show_ui_dialog(cnc.UID_ID_PARAMETERS_LIBRARY)
        if sender == self.ui.uidProgramSettingsButton:
            self.api.show_ui_dialog(cnc.UID_ID_PROGRAM_SETTINGS)
        if sender == self.ui.uidToolsLibraryButton:
            self.api.show_ui_dialog(cnc.UID_ID_TOOLS_LIBRARY)
        if sender == self.ui.uidWorkCoordinatesButton:
            self.api.show_ui_dialog(cnc.UID_ID_WORK_COORDINATES)

        # events system info

    def __on_action_main_update(self):
        if self.api_server_connection_state in [ASCS_DISCONNECTED, ASCS_ERROR]:

            # updates main view

            # updates commands
            self.ui.cmdsConnectionOpenButton.setEnabled(False)
            self.ui.cmdsConnectionCloseButton.setEnabled(False)

            self.ui.cmdsStartButton.setEnabled(False)
            self.ui.cmdsStopButton.setEnabled(False)
            self.ui.cmdsPauseButton.setEnabled(False)
            self.ui.cmdsContinueButton.setEnabled(False)
            self.ui.cmdsResumeAfterStopButton.setEnabled(False)

            # updates show
            self.ui.showAlarmsButton.setEnabled(False)
            self.ui.showAlarmsHistoryButton.setEnabled(False)
            self.ui.showWarningsButton.setEnabled(False)
            self.ui.showWarningsHistoryButton.setEnabled(False)

            # updates tab general
            self.ui.cfsmSpindleCWButton.setEnabled(False)
            self.ui.cfsmSpindleCCWButton.setEnabled(False)
            self.ui.cfsmCoolantMistButton.setEnabled(False)
            self.ui.cfsmCoolantFloodButton.setEnabled(False)
            self.ui.cfsmAUX01Button.setEnabled(False)
            self.ui.cfsmAUX02Button.setEnabled(False)
            self.ui.cfsmAUX03Button.setEnabled(False)
            self.ui.cfsmAUX04Button.setEnabled(False)
            self.ui.cfsmAUX05Button.setEnabled(False)

            # updates tab axes position plot

            # updates tab program
            self.ui.programNewButton.setEnabled(False)
            self.ui.programLoadSelectFileButton.setEnabled(False)
            self.ui.programLoadButton.setEnabled(False)
            self.ui.programSaveButton.setEnabled(False)
            self.ui.programSaveAsButton.setEnabled(False)

            # updates tab g-code
            self.ui.gcodeGetProgramTextButton.setEnabled(False)
            self.ui.gcodeSetProgramTextButton.setEnabled(False)
            self.ui.gcodeAddProgramTextButton.setEnabled(False)
            self.ui.gcodeClearProgramTextButton.setEnabled(False)

            # updates tab mdi
            # updates tab cnc

            # updates tab jog
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

            # updates tab overrides
            # updates tab homing

            # updates tab wcs
            self.ui.csApplyWCSChangesButton.setEnabled(False)

            # updates tab d i/o
            # updates tab a i/o
            # updates tab scanning laser
            self.ui.laserZeroXAxisButton.setEnabled(False)
            self.ui.laserZeroYAxisButton.setEnabled(False)
            self.ui.laserZeroZAxisButton.setEnabled(False)

            # updates tab machining info

            # updates tab ui dialogs
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

            # updates tab system info
        else:
            connected = self.ctx.cnc_info.state_machine != cnc.SM_DISCONNECTED
            enabled_commands = self.ctx.enabled_commands

            # updates main view

            # updates commands
            self.ui.cmdsConnectionOpenButton.setEnabled(enabled_commands.cnc_connection_open)
            self.ui.cmdsConnectionCloseButton.setEnabled(enabled_commands.cnc_connection_close)

            self.ui.cmdsStartButton.setEnabled(enabled_commands.cnc_start)
            self.ui.cmdsStopButton.setEnabled(enabled_commands.cnc_stop)
            self.ui.cmdsPauseButton.setEnabled(enabled_commands.cnc_pause)
            self.ui.cmdsContinueButton.setEnabled(enabled_commands.cnc_continue)
            self.ui.cmdsResumeAfterStopButton.setEnabled(enabled_commands.cnc_resume)

            # updates show
            self.ui.showAlarmsButton.setEnabled(True)
            self.ui.showAlarmsHistoryButton.setEnabled(True)
            self.ui.showWarningsButton.setEnabled(True)
            self.ui.showWarningsHistoryButton.setEnabled(True)

            # updates tab general
            if self.ctx.cnc_info.spindle_not_ready:
                # keep button enabled to permits colored icon with spindle_not_ready (command will however ignored)
                spindle_cw_enabled = True
                spindle_ccw_enabled = True
            else:
                spindle_cw_enabled = enabled_commands.cnc_csfm_spindle_cw
                spindle_ccw_enabled = enabled_commands.cnc_csfm_spindle_ccw
            self.ui.cfsmSpindleCWButton.setEnabled(spindle_cw_enabled)
            self.ui.cfsmSpindleCCWButton.setEnabled(spindle_ccw_enabled)
            self.ui.cfsmCoolantMistButton.setEnabled(enabled_commands.cnc_csfm_cooler_flood)
            self.ui.cfsmCoolantFloodButton.setEnabled(enabled_commands.cnc_csfm_cooler_mist)
            self.ui.cfsmAUX01Button.setEnabled(enabled_commands.cnc_csfm_aux & 0x0001)
            self.ui.cfsmAUX02Button.setEnabled(enabled_commands.cnc_csfm_aux & 0x0002)
            self.ui.cfsmAUX03Button.setEnabled(enabled_commands.cnc_csfm_aux & 0x0004)
            self.ui.cfsmAUX04Button.setEnabled(enabled_commands.cnc_csfm_aux & 0x0008)
            self.ui.cfsmAUX05Button.setEnabled(enabled_commands.cnc_csfm_aux & 0x0010)

            # updates tab axes position plot

            # updates tab program
            self.ui.programNewButton.setEnabled(enabled_commands.program_new)
            self.ui.programLoadSelectFileButton.setEnabled(enabled_commands.program_load)
            self.ui.programLoadButton.setEnabled(enabled_commands.program_load)
            self.ui.programSaveButton.setEnabled(enabled_commands.program_save)
            self.ui.programSaveAsButton.setEnabled(enabled_commands.program_save_as)

            # updates tab g-code
            self.ui.gcodeGetProgramTextButton.setEnabled(enabled_commands.has_data)
            self.ui.gcodeSetProgramTextButton.setEnabled(enabled_commands.program_gcode_set_text)
            self.ui.gcodeAddProgramTextButton.setEnabled(enabled_commands.program_gcode_add_text)
            self.ui.gcodeClearProgramTextButton.setEnabled(enabled_commands.program_gcode_set_text)

            # updates tab mdi
            self.ui.mdiCommandExecuteButton.setEnabled(enabled_commands.cnc_mdi_command)

            # updates tab cnc

            # updates tab jog
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

            # updates tab overrides
            # updates tab homing

            # updates tab wcs
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

            # updates tab d i/o
            # updates tab a i/o
            # updates tab scanning laser
            self.ui.laserZeroXAxisButton.setEnabled(enabled_commands.cnc_mdi_command)
            self.ui.laserZeroYAxisButton.setEnabled(enabled_commands.cnc_mdi_command)
            self.ui.laserZeroZAxisButton.setEnabled(enabled_commands.cnc_mdi_command)

            # updates tab machining info

            # updates tab ui dialogs
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

            # updates tab system info

        # updates server connection button
        self.ui.apiServerConnectionButton.setEnabled(True)
        if self.api_server_connection_state == ASCS_CONNECTED:
            self.ui.apiServerConnectionButton.setText('Disconnect')
        else:
            self.ui.apiServerConnectionButton.setText('Connect')

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

        if sender == self.ui.apiServerUseTLSCheckBox:
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
        if sender is None:
            return
        value = sender.text().strip()

        # events main view
        if sender == self.ui.apiServerHostEdit:
            try_str_2_ipv4('api_server_host')
        if sender == self.ui.apiServerPortEdit:
            try_str_2_int('api_server_port', 1, 65535)

        # events commands
        # events tab general
        # events tab axes position plot
        # events tab program
        # evenst tab g-code
        # events tab mdi
        # events tab cnc

        # events tab jog
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

        # events tab overrides
        # events tab homing

        # events tab wcs
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

        # events tab d i/o
        # events tab a i/o
        # events tab scanning laser
        # events tab machining info
        # events tab ui dialogs
        # events tab system info

        # update editable fields
        self.__update_editable_fields()

    def __on_form_close(self):
        # save settings on memento
        self.__memento_save()

        # disable and unlink update timer
        self.tmr_update.stop()

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
        self.in_update = False

        # load settings from memento
        self.__memento_load()

        # create and set api client
        self.api = cnc.CncAPIClientCore()

        # create a module api info context
        self.ctx = cnc.CncAPIInfoContext(self.api)

        # update main actions
        ###self.__on_action_main_update(None)

        # enable update timer and call first update NOW
        self.tmr_update.start()
        self.__on_timer_update()

        # update editable fields
        self.__update_editable_fields()

        # enable first stay on top update
        self.stay_on_top_changed = True

    def __on_label_double_click(self, sender: QLabel):
        # check if sender in override value labels dict
        name = self.override_value_labels.get(sender)
        if name is not None:
            # get cnc info
            cnc_info = self.api.get_cnc_info()
            if not cnc_info.has_data:
                return
            enabled = getattr(cnc_info, f'override_{name}_enabled')
            locked = getattr(cnc_info, f'override_{name}_locked')
            if enabled and not locked:
                # set related ovveride value
                value = min(100, getattr(cnc_info, f'override_{name}_max'))
                method = getattr(self.api, f'set_override_{name}')
                method(value)
                # start slide update inhibition until timer
                self.slider_update_inhibition_until = time.perf_counter() + SETTLE_TIME_SLIDER
                return

    def __on_radio_button_clicked(self):
        sender = self.sender()
        if sender in [
            self.ui.minfoTCPExtentsInfoRadioButton,
            self.ui.minfoJointsInfoRadioButton,
            self.ui.minfoUsedToolInfoRadioButton,
        ]:
            self.machining_info_in_use = None
            self.__updated_objects()

    def __on_slider_action(self, action_value: int):
        sender: QSlider = self.sender()
        action =  QAbstractSlider.SliderAction(action_value)

        # evaluate action to get predicted value
        v = sender.value()
        if action == QAbstractSlider.SliderSingleStepAdd:
            value = min(v + sender.singleStep(), sender.maximum())
        elif action == QAbstractSlider.SliderSingleStepSub:
            value = max(v - sender.singleStep(), sender.minimum())
        elif action == QAbstractSlider.SliderPageStepAdd:
            value = min(v + sender.pageStep(), sender.maximum())
        elif action == QAbstractSlider.SliderPageStepSub:
            value = max(v - sender.pageStep(), sender.minimum())
        elif action == QAbstractSlider.SliderToMinimum:
            value = sender.minimum()
        elif action == QAbstractSlider.SliderToMaximum:
            value = sender.maximum()
        elif action == QAbstractSlider.SliderMove:
            value = sender.sliderPosition()
        else:
            return

        # write new ovverride value
        if sender == self.ui.ovrJogSlider:
            self.api.set_override_jog(value)
        if sender == self.ui.ovrSpindleSlider:
            self.api.set_override_spindle(value)
        if sender == self.ui.ovrFastSlider:
            self.api.set_override_fast(value)
        if sender == self.ui.ovrFeedSlider:
            self.api.set_override_feed(value)
        if sender == self.ui.ovrFeedCSM1Slider:
            self.api.set_override_feed_custom_1(value)
        if sender == self.ui.ovrFeedCSM2Slider:
            self.api.set_override_feed_custom_2(value)
        if sender == self.ui.ovrPlasmaPowerSlider:
            self.api.set_override_plasma_power(value)
        if sender == self.ui.ovrPlasmaVoltageSlider:
            self.api.set_override_plasma_voltage(value)

        # start slide update inhibition until timer
        self.slider_update_inhibition_until = time.perf_counter() + SETTLE_TIME_SLIDER

    def __on_timer_update(self):
        # update non editable objects with related data
        self.__updated_objects()

        # update action main linked objects enablings
        self.__on_action_main_update()

        # check operator request
        self.__operator_request_check()

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
            base_path = Path(__file__).resolve().parent
            memento_path = base_path / SETTINGS_FILE_NAME
            memento = CncMemento.create_read_root(str(memento_path), 'root')
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
            base_path = Path(__file__).resolve().parent
            memento_path = base_path / SETTINGS_FILE_NAME
            return memento.save_to_file(str(memento_path), indent=4)
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


    # == BEG: update methods
    #
    def __update_editable_fields(self):
        """Updates editable fields with related data."""
        if self.in_update:
            return
        self.in_update = True
        try:
            pos_um = '{:.3f}' if self.units_mode == cnc.UM_METRIC else '{:.4f}'

            # updates main view
            self.ui.apiServerHostEdit.setText(self.api_server_host)
            self.ui.apiServerPortEdit.setText(str(self.api_server_port))
            self.ui.apiServerUseTLSCheckBox.setChecked(self.api_server_use_tls)
            self.ui.stayOnTopCheckBox.setChecked(self.stay_on_top)

            # updates commands
            # updates tab general
            # updates tab axes position plot

            # updates tab program
            self.ui.programLoadFileNameEdit.setText(self.program_load_file_name)
            self.ui.programSaveFileAsFileNameEdit.setText(self.program_save_file_name)

            # updates tab g-code
            # updates tab mdi
            # updates tab cnc

            # updates tab jog
            self.ui.setProgramPositionXEdit.setText(pos_um.format(self.set_program_position_x))
            self.ui.setProgramPositionYEdit.setText(pos_um.format(self.set_program_position_y))
            self.ui.setProgramPositionZEdit.setText(pos_um.format(self.set_program_position_z))
            self.ui.setProgramPositionAEdit.setText(pos_um.format(self.set_program_position_a))
            self.ui.setProgramPositionBEdit.setText(pos_um.format(self.set_program_position_b))
            self.ui.setProgramPositionCEdit.setText(pos_um.format(self.set_program_position_c))

            # updates tab overrides
            # updates tab homing

            # updates tab wcs
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

            # updates tab d i/o
            # updates tab a i/o
            # updates tab scanning laser
            # updates tab machine info
            # updates tab ui dialogs
            # updates tab system info
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

        # updates tab general
        if self.ui.tabWidgetMain.currentWidget() == self.ui.tabGeneral:
            # update axes info
            for axis_group, attr_name, is_velocity in self.axis_data_mapping:
                data = getattr(axes_info, attr_name)
                for i, axis in enumerate(axis_group):
                    fmt = (um_vel_lf if i < 3 else um_vel_rf) if is_velocity else (um_spc_lf if i < 3 else um_spc_rf)
                    axis.value.setText(fmt.format(data[i]))
            self.ui.wofTitleLabel.setText(f'WORKING OFFSETS {axes_info.working_wcs}')

            # update spindles buttons
            self.__update_spindle_buttons()
            self.ui.cfsmCoolantMistButton.setStatus(cnc_info.coolant_mist)
            self.ui.cfsmCoolantFloodButton.setStatus(cnc_info.coolant_flood)
            self.ui.cfsmAUX01Button.setStatus(cnc_info.aux_outputs & 0x0001)
            self.ui.cfsmAUX02Button.setStatus(cnc_info.aux_outputs & 0x0002)
            self.ui.cfsmAUX03Button.setStatus(cnc_info.aux_outputs & 0x0004)
            self.ui.cfsmAUX04Button.setStatus(cnc_info.aux_outputs & 0x0008)
            self.ui.cfsmAUX05Button.setStatus(cnc_info.aux_outputs & 0x0010)

            # update machine info
            # spindleStatusValue -> QLabel
            self.ui.coolantMistValue.setText('ON' if cnc_info.coolant_mist else 'OFF')
            self.ui.coolantFloodValue.setText('ON' if cnc_info.coolant_flood else 'OFF')
            # gcodeLineValue -> QLabel
            self.ui.workedTimeValue.setText(cnc_info.worked_time)
            self.ui.plannedTimeValue.setText(cnc_info.planned_time)

            # update tool info
            text = ''
            if cnc_info.tool_slot == 0:
                text = f'T{cnc_info.tool_id:d} -'
            else:
                text = f'T{cnc_info.tool_id:d} Slot:{cnc_info.tool_slot:d} -'
            tx = ' X:' + format_float(cnc_info.tool_offset_x, um_decimals, DecimalsTrimMode.FULL)
            ty = ' Y:' + format_float(cnc_info.tool_offset_y, um_decimals, DecimalsTrimMode.FULL)
            tz = ' Z:' + format_float(cnc_info.tool_offset_z, um_decimals, DecimalsTrimMode.FULL)
            if cnc_info.tool_offset_x != 0:
                tx = f'<b>{tx}</b>'
            if cnc_info.tool_offset_y != 0:
                ty = f'<b>{ty}</b>'
            if cnc_info.tool_offset_z != 0:
                tz = f'<B>{tz}</B>'
            description = f'{cnc_info.tool_description}'
            if description != '':
                description = f' - {description}'
            self.ui.toolInfoLabel.setText(f'{text}{tx}{ty}{tz}{description}')

        # updates tab axes position plot
        if self.ui.tabWidgetMain.currentWidget() == self.ui.tabAxesPositionPlot:
            if axes_info.has_data:
                self.realtime_scope.push(axes_info.program_position)

        # updates tab program
        if self.ui.tabWidget.currentWidget() == self.ui.tabProgram:
            self.ui.programLoadFileNameEdit.setEnabled(enabled_commands.program_load)
            self.ui.programSaveFileAsFileNameEdit.setEnabled(enabled_commands.program_load)

        # updates tab g-code
        if self.ui.tabWidget.currentWidget() == self.ui.tabGCode:
            self.ui.gcodeProgramEdit.setEnabled(enabled_commands.has_data)
            self.ui.gcodeAddProgramTextEdit.setEnabled(enabled_commands.program_gcode_add_text)

        # updates tab mdi
        if self.ui.tabWidget.currentWidget() == self.ui.tabMDI:
            self.ui.mdiCommandEdit.setEnabled(enabled_commands.cnc_mdi_command)

        # updates tab cnc
        if self.ui.tabWidget.currentWidget() == self.ui.tabCNC:
            pass

        # updates tab jog
        if self.ui.tabWidget.currentWidget() == self.ui.tabJOG:
            pass

        # updates tab overrides
        if self.ui.tabWidget.currentWidget() == self.ui.tabOverrides:

            # update override sliders limits
            self.ui.ovrJogSlider.setRange(cnc_info.override_jog_min, cnc_info.override_jog_max)
            self.ui.ovrSpindleSlider.setRange(cnc_info.override_spindle_min, cnc_info.override_spindle_max)
            self.ui.ovrFastSlider.setRange(cnc_info.override_fast_min, cnc_info.override_fast_max)
            self.ui.ovrFeedSlider.setRange(cnc_info.override_feed_min, cnc_info.override_feed_max)
            self.ui.ovrFeedCSM1Slider.setRange(cnc_info.override_feed_custom_1_min, cnc_info.override_feed_custom_1_max)
            self.ui.ovrFeedCSM2Slider.setRange(cnc_info.override_feed_custom_2_min, cnc_info.override_feed_custom_2_max)
            self.ui.ovrPlasmaPowerSlider.setRange(cnc_info.override_plasma_power_min, cnc_info.override_plasma_power_max)
            self.ui.ovrPlasmaVoltageSlider.setRange(cnc_info.override_plasma_voltage_min, cnc_info.override_plasma_voltage_max)

            # update override sliders values
            if time.perf_counter() > self.slider_update_inhibition_until:
                self.slider_update_inhibition_until = 0.0
                self.ui.ovrJogSlider.setValue(cnc_info.override_jog)
                self.ui.ovrSpindleSlider.setValue(cnc_info.override_spindle)
                self.ui.ovrFastSlider.setValue(cnc_info.override_fast)
                self.ui.ovrFeedSlider.setValue(cnc_info.override_feed)
                self.ui.ovrFeedCSM1Slider.setValue(cnc_info.override_feed_custom_1)
                self.ui.ovrFeedCSM2Slider.setValue(cnc_info.override_feed_custom_2)
                self.ui.ovrPlasmaPowerSlider.setValue(cnc_info.override_plasma_power)
                self.ui.ovrPlasmaVoltageSlider.setValue(cnc_info.override_plasma_voltage)

            # update override labels value
            self.ui.ovrJogValue.setText(str(cnc_info.override_jog))
            self.ui.ovrSpindleValue.setText(str(cnc_info.override_spindle))
            self.ui.ovrFastValue.setText(str(cnc_info.override_fast))
            self.ui.ovrFeedValue.setText(str(cnc_info.override_feed))
            self.ui.ovrFeedCSM1Value.setText(str(cnc_info.override_feed_custom_1))
            self.ui.ovrFeedCSM2Value.setText(str(cnc_info.override_feed_custom_2))
            self.ui.ovrPlasmaPowerValue.setText(str(cnc_info.override_plasma_power))
            self.ui.ovrPlasmaVoltageValue.setText(str(cnc_info.override_plasma_voltage))

        # updates tab homing
        if self.ui.tabWidget.currentWidget() == self.ui.tabHoming:
            pass

        # updates tab wcs
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

        # updates tab d i/o
        if self.ui.tabWidget.currentWidget() == self.ui.tabDIO:
            pass

        # updates tab a i/o
        if self.ui.tabWidget.currentWidget() == self.ui.tabAIO:
            pass

        # updates tab scanning laser
        if self.ui.tabWidget.currentWidget() == self.ui.tabScanningLaser:
            laser_info = self.api.get_scanning_laser_info()
            if not laser_info.has_data:
                self.ui.laserOutBitValue.setText('- - -')
                self.ui.laserOutUmfValue.setText('- - -')
                self.ui.laserHMeasureValue.setText('- - -')
                self.ui.laserMCSXPositionValue.setText('- - -')
                self.ui.laserMCSYPositionValue.setText('- - -')
                self.ui.laserMCSZPositionValue.setText('- - -')
                self.laser_scope.clear()
            else:
                self.ui.laserOutBitValue.setText(f'{laser_info.laser_out_bit}')
                self.ui.laserOutUmfValue.setText(f'{laser_info.laser_out_umf}')
                h_mes = format_float(laser_info.laser_h_measure, um_decimals, DecimalsTrimMode.NONE)
                mcs_x = format_float(laser_info.laser_mcs_x_position, um_decimals, DecimalsTrimMode.NONE)
                mcs_y = format_float(laser_info.laser_mcs_y_position, um_decimals, DecimalsTrimMode.NONE)
                mcs_z = format_float(laser_info.laser_mcs_z_position, um_decimals, DecimalsTrimMode.NONE)
                self.ui.laserHMeasureValue.setText(h_mes)
                self.ui.laserMCSXPositionValue.setText(mcs_x)
                self.ui.laserMCSYPositionValue.setText(mcs_y)
                self.ui.laserMCSZPositionValue.setText(mcs_z)
                if self.ui.laserShowOutBitPlotCheckBox.isChecked():
                    self.laser_scope.push([laser_info.laser_out_bit])
                else:
                    self.laser_scope.clear()

        # updates tab machining info
        if self.ui.tabWidget.currentWidget() == self.ui.tabMachiningInfo:
            machining_info = self.api.get_machining_info()
            if not cnc.APIMachiningInfo.are_equal(self.machining_info_in_use, machining_info):
                self.machining_info_in_use = machining_info
                m = machining_info
                lf = um_spc_lf.format
                rf = um_spc_rf.format
                if self.ui.minfoTCPExtentsInfoRadioButton.isChecked():
                    text = (
                        'TOOL PATH\n'
                        '=========\n'
                        'IN FAST    {}\n'
                        'IN FEED    {}\n'
                        'TOTAL PATH {}\n'
                        'PLANNED TIME      {}\n'
                        '\n'
                        '\n'
                        'TCP EXTENTS IN FAST               TCP EXTENTS IN FEED\n'
                        '===================               ===================\n'
                        'MIN X      {}        MIN X       {}\n'
                        'MIN Y      {}        MIN Y       {}\n'
                        'MIN Z      {}        MIN Z       {}\n'
                        'MAX X      {}        MAX X       {}\n'
                        'MAX Y      {}        MAX Y       {}\n'
                        'MAX Z      {}        MAX Z       {}\n'
                        'LENGTH X   {}        LENGTH X    {}\n'
                        'LENGTH Y   {}        LENGTH Y    {}\n'
                        'LENTGH Z   {}        LENTGH Z    {}\n'
                    ).format(
                        lf(m.tool_path_in_fast),
                        lf(m.tool_path_in_feed),
                        lf(m.total_path),
                        m.planned_time,
                        lf(m.tcp_extents_in_fast_min_x), lf(m.tcp_extents_in_feed_min_x),
                        lf(m.tcp_extents_in_fast_min_y), lf(m.tcp_extents_in_feed_min_y),
                        lf(m.tcp_extents_in_fast_min_z), lf(m.tcp_extents_in_feed_min_z),
                        lf(m.tcp_extents_in_fast_max_x), lf(m.tcp_extents_in_feed_max_x),
                        lf(m.tcp_extents_in_fast_max_y), lf(m.tcp_extents_in_feed_max_y),
                        lf(m.tcp_extents_in_fast_max_z), lf(m.tcp_extents_in_feed_max_z),
                        lf(m.tcp_extents_in_fast_length_x), lf(m.tcp_extents_in_feed_length_x),
                        lf(m.tcp_extents_in_fast_length_y), lf(m.tcp_extents_in_feed_length_y),
                        lf(m.tcp_extents_in_fast_length_z), lf(m.tcp_extents_in_feed_length_z),
                    )
                elif self.ui.minfoJointsInfoRadioButton.isChecked():
                    text = (
                        'JOINTS IN FAST                    JOINTS IN FEED\n'
                        '==============                    ==============\n'
                        'MIN X      {}        MIN X       {}\n'
                        'MIN Y      {}        MIN Y       {}\n'
                        'MIN Z      {}        MIN Z       {}\n'
                        'MIN A      {}        MIN A       {}\n'
                        'MIN B      {}        MIN B       {}\n'
                        'MIN C      {}        MIN C       {}\n'
                        'MAX X      {}        MAX X       {}\n'
                        'MAX Y      {}        MAX Y       {}\n'
                        'MAX Z      {}        MAX Z       {}\n'
                        'MAX A      {}        MAX A       {}\n'
                        'MAX B      {}        MAX B       {}\n'
                        'MAX C      {}        MAX C       {}\n'
                        'LENGTH X   {}        LENGTH X    {}\n'
                        'LENGTH Y   {}        LENGTH Y    {}\n'
                        'LENGTH Z   {}        LENGTH Z    {}\n'
                        'LENGTH A   {}        LENGTH A    {}\n'
                        'LENGTH B   {}        LENGTH B    {}\n'
                        'LENGTH C   {}        LENGTH C    {}\n'
                    ).format(
                        lf(m.joints_in_fast_min_x), lf(m.joints_in_feed_min_x),
                        lf(m.joints_in_fast_min_y), lf(m.joints_in_feed_min_y),
                        lf(m.joints_in_fast_min_z), lf(m.joints_in_feed_min_z),
                        rf(m.joints_in_fast_min_a), rf(m.joints_in_feed_min_a),
                        rf(m.joints_in_fast_min_b), rf(m.joints_in_feed_min_b),
                        rf(m.joints_in_fast_min_c), rf(m.joints_in_feed_min_c),
                        lf(m.joints_in_fast_max_x), lf(m.joints_in_feed_max_x),
                        lf(m.joints_in_fast_max_y), lf(m.joints_in_feed_max_y),
                        lf(m.joints_in_fast_max_z), lf(m.joints_in_feed_max_z),
                        rf(m.joints_in_fast_max_a), rf(m.joints_in_feed_max_a),
                        rf(m.joints_in_fast_max_b), rf(m.joints_in_feed_max_b),
                        rf(m.joints_in_fast_max_c), rf(m.joints_in_feed_max_c),
                        lf(m.joints_in_fast_length_x), lf(m.joints_in_feed_length_x),
                        lf(m.joints_in_fast_length_y), lf(m.joints_in_feed_length_y),
                        lf(m.joints_in_fast_length_z), lf(m.joints_in_feed_length_z),
                        rf(m.joints_in_fast_length_a), rf(m.joints_in_feed_length_a),
                        rf(m.joints_in_fast_length_b), rf(m.joints_in_feed_length_b),
                        rf(m.joints_in_fast_length_c), rf(m.joints_in_feed_length_c),
                    )
                elif self.ui.minfoUsedToolInfoRadioButton.isChecked():
                    TEXT_LINES_FOR_USED_TOOL = 5
                    MAX_VISIBLE_USED_TOOL_COLS = 4
                    MAX_VISIBLE_USED_TOOL_ROWS = 4
                    COLUMN_WIDTH = 30

                    tools = len(m.used_tool)
                    capacity = MAX_VISIBLE_USED_TOOL_COLS * MAX_VISIBLE_USED_TOOL_ROWS

                    if tools == 0:
                        text = 'USED TOOL INFO EMPTY'
                    else:
                        lines = [''] * (MAX_VISIBLE_USED_TOOL_ROWS * TEXT_LINES_FOR_USED_TOOL)
                        visible_tools = min(tools, capacity)

                        for tool_index in range(visible_tools):
                            row = tool_index % MAX_VISIBLE_USED_TOOL_ROWS
                            line_index = row * TEXT_LINES_FOR_USED_TOOL
                            tool = m.used_tool[tool_index]

                            lines[line_index + 0] += f'TOOL {tool.tool_id:3d}'
                            lines[line_index + 1] += '========'
                            lines[line_index + 2] += f'In Fast{lf(tool.in_fast)}'
                            lines[line_index + 3] += f'In Feed{lf(tool.in_feed)}'

                            is_last_in_column = (
                                row == MAX_VISIBLE_USED_TOOL_ROWS - 1 or
                                tool_index == visible_tools - 1
                            )
                            if is_last_in_column:
                                for i, line in enumerate(lines):
                                    pad = (-len(line)) % COLUMN_WIDTH
                                    lines[i] += ' ' * pad

                        text = '\n'.join(lines)

                        if tools > capacity:
                            text += (
                                f'\nPS: Used tools are {tools}, '
                                f'but here we have space to view only {capacity} of them'
                            )
                else:
                    text = 'UNKNOWN FEATURE'
                self.ui.minfoDataEdit.setText(text)

        # updates tab ui dialogs
        if self.ui.tabWidget.currentWidget() == self.ui.tabUIDialogs:
            pass

        # updates tab system info
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
                if not system_info.has_data:
                    self.ui.systemInfoEdit.append('  Licensed Features          : ')
                else:
                    lf_01 = '*' if system_info.licensed_feature_panel_pc else ' '
                    lf_02 = '*' if system_info.licensed_feature_panel_pc_demo else ' '
                    lf_03 = '*' if system_info.licensed_feature_work_orders else ' '
                    lf_04 = '*' if system_info.licensed_feature_opc_ua_server else ' '
                    lf_05 = '*' if system_info.licensed_feature_probe_sdk_g1 else ' '
                    lf_06 = '*' if system_info.licensed_feature_probe_sdk_g2 else ' '
                    lf_07 = '*' if system_info.licensed_feature_probe_sdk_g3 else ' '
                    lf_08 = '*' if system_info.licensed_feature_probe_sdk_g4 else ' '
                    lf_09 = '*' if system_info.licensed_feature_probe_sdk_g5 else ' '

                    self.ui.systemInfoEdit.append(f'  Licensed Features          : [ {lf_01} ] PanelPC')
                    self.ui.systemInfoEdit.append(f'                               [ {lf_02} ] PanelPC Demo')
                    self.ui.systemInfoEdit.append(f'                               [ {lf_03} ] Work Orders')
                    self.ui.systemInfoEdit.append(f'                               [ {lf_04} ] OPC UA Server')
                    self.ui.systemInfoEdit.append(f'                               [ {lf_05} ] Probe SDK Group 1')
                    self.ui.systemInfoEdit.append(f'                               [ {lf_06} ] Probe SDK Group 2')
                    self.ui.systemInfoEdit.append(f'                               [ {lf_07} ] Probe SDK Group 3')
                    self.ui.systemInfoEdit.append(f'                               [ {lf_08} ] Probe SDK Group 4')
                    self.ui.systemInfoEdit.append(f'                               [ {lf_09} ] Probe SDK Group 5')

        # update status bar
        text = 'UNKNOWN'
        if is_in_str_list_range(SM_TEXTS, cnc_info.state_machine):
            text = SM_TEXTS[cnc_info.state_machine]
        if cnc_info.state_machine == cnc.SM_ALARM:
            text = f'<b><font color="#FF0000">{text} - {cnc_info.current_alarm_text}</font></b>'
            self.StateMachineLabel.setToolTip(cnc_info.current_alarm_text)
        else:
            if cnc_info.current_warning_code != 0:
                text = f'{text} - <b><font color="#FF6A00">{cnc_info.current_warning_text}</font></b>'
                self.StateMachineLabel.setToolTip(cnc_info.current_warning_text)
            else:
                self.StateMachineLabel.setToolTip('')
        self.StateMachineLabel.setText('Machine State : ' + text)
        text = 'UNKNOWN'
        if is_in_str_list_range(ASCS_TEXTS, self.api_server_connection_state):
            text = ASCS_TEXTS[self.api_server_connection_state]
        if not self.api_server_use_tls:
            self.APIServerConnectionStateLabel.setText('Connection with Server : ' + text)
        else:
            if self.api.socket_ssl_info:
                text = f'Connection with Server [ {self.api.socket_ssl_info} ] : {text}'
            else:
                text = f'Connection with Server [ TLS ] : {text}'
            self.APIServerConnectionStateLabel.setText(text)
        if self.api_server_connection_state in [None, ASCS_DISCONNECTED]:
            self.APIServerConnectionStateLed.setColors(ASCL_CONNECTED, ASCL_DISCONNECTED)
            self.APIServerConnectionStateLed.setState(False)
        elif self.api_server_connection_state == ASCS_ERROR:
            self.APIServerConnectionStateLed.setColors(ASCL_CONNECTED, ASCL_ERROR)
            self.APIServerConnectionStateLed.setState(False)
        else:
            self.APIServerConnectionStateLed.setColors(ASCL_CONNECTED, ASCL_DISCONNECTED)
            self.APIServerConnectionStateLed.setState(True, 0.3)

        # update axis enablings
        if (self.axes_mask_enablings_in_use != cnc_info.axes_mask) or connection_with_cnc_changed:
            self.axes_mask_enablings_in_use = cnc_info.axes_mask
            for axis_group in self.all_axis_controls:
                for axis, mask in zip(axis_group, self.axis_masks):
                    enabled = connection_with_cnc and ((self.axes_mask_enablings_in_use & mask) != 0)
                    axis.label.setEnabled(enabled)
                    axis.value.setEnabled(enabled)

        # update objects enablings
        #
        # TAKE CARE
        # =========
        # Buttons widgets enablings are managed by self.__on_action_main_update()
        #
        if self.api_server_connection_state in [ASCS_DISCONNECTED, ASCS_ERROR]:
            # enablings main view
            self.ui.apiServerHostEdit.setEnabled(True)
            self.ui.apiServerPortEdit.setEnabled(True)
            self.ui.apiServerUseTLSCheckBox.setEnabled(True)

            # enablings commands

            # enablings tab general
            self.ui.mcsTitleLabel.setEnabled(False)
            self.ui.prpTitleLabel.setEnabled(False)
            self.ui.avlTitleLabel.setEnabled(False)
            self.ui.wofTitleLabel.setEnabled(False)
            self.ui.mtpTitleLabel.setEnabled(False)
            self.ui.ptpTitleLabel.setEnabled(False)
            self.ui.jopTitleLabel.setEnabled(False)
            self.ui.machineInfoLabel.setEnabled(False)
            self.ui.spindleStatusLabel.setEnabled(False)
            self.ui.spindleStatusValue.setEnabled(False)
            self.ui.coolantMistLabel.setEnabled(False)
            self.ui.coolantMistValue.setEnabled(False)
            self.ui.coolantFloodLabel.setEnabled(False)
            self.ui.coolantFloodValue.setEnabled(False)
            self.ui.gcodeLineLabel.setEnabled(False)
            self.ui.gcodeLineValue.setEnabled(False)
            self.ui.workedTimeLabel.setEnabled(False)
            self.ui.workedTimeValue.setEnabled(False)
            self.ui.plannedTimeLabel.setEnabled(False)
            self.ui.plannedTimeValue.setEnabled(False)

            # enablings tab axes position plot
            # enablings tab program
            # enablings tab g-code
            # enablings tab mdi
            # enablings tab cnc

            # enablings tab jog
            self.ui.setProgramPositionXEdit.setEnabled(False)
            self.ui.setProgramPositionYEdit.setEnabled(False)
            self.ui.setProgramPositionZEdit.setEnabled(False)
            self.ui.setProgramPositionAEdit.setEnabled(False)
            self.ui.setProgramPositionBEdit.setEnabled(False)
            self.ui.setProgramPositionCEdit.setEnabled(False)

            # enablings tab overrides
            self.ui.ovrJogLabel.setEnabled(False)
            self.ui.ovrJogSlider.setEnabled(False)
            self.ui.ovrJogValue.setEnabled(False)
            self.ui.ovrSpindleLabel.setEnabled(False)
            self.ui.ovrSpindleSlider.setEnabled(False)
            self.ui.ovrSpindleValue.setEnabled(False)
            self.ui.ovrFastLabel.setEnabled(False)
            self.ui.ovrFastSlider.setEnabled(False)
            self.ui.ovrFastValue.setEnabled(False)
            self.ui.ovrFeedLabel.setEnabled(False)
            self.ui.ovrFeedSlider.setEnabled(False)
            self.ui.ovrFeedValue.setEnabled(False)
            self.ui.ovrFeedCSM1Label.setEnabled(False)
            self.ui.ovrFeedCSM1Slider.setEnabled(False)
            self.ui.ovrFeedCSM1Value.setEnabled(False)
            self.ui.ovrFeedCSM2Label.setEnabled(False)
            self.ui.ovrFeedCSM2Slider.setEnabled(False)
            self.ui.ovrFeedCSM2Value.setEnabled(False)
            self.ui.ovrPlasmaPowerLabel.setEnabled(False)
            self.ui.ovrPlasmaPowerSlider.setEnabled(False)
            self.ui.ovrPlasmaPowerValue.setEnabled(False)
            self.ui.ovrPlasmaVoltageLabel.setEnabled(False)
            self.ui.ovrPlasmaVoltageSlider.setEnabled(False)
            self.ui.ovrPlasmaVoltageValue.setEnabled(False)
            self.ui.toolInfoLabel.setEnabled(False)

            # enablings tab homing
            # enablings tab wcs
            # enablings tab d i/o
            # enablings tab a i/o
            # enablings tab scanning laser
            # enablings tab machining info
            # enablings tab ui dialogs
            # enablings tab system info
        else:
            # enablings main view
            self.ui.apiServerHostEdit.setEnabled(False)
            self.ui.apiServerPortEdit.setEnabled(False)
            self.ui.apiServerUseTLSCheckBox.setEnabled(False)

            # enablings commands

            # enablings tab general
            self.ui.mcsTitleLabel.setEnabled(True)
            self.ui.prpTitleLabel.setEnabled(True)
            self.ui.avlTitleLabel.setEnabled(True)
            self.ui.wofTitleLabel.setEnabled(True)
            self.ui.mtpTitleLabel.setEnabled(True)
            self.ui.ptpTitleLabel.setEnabled(True)
            self.ui.jopTitleLabel.setEnabled(True)
            self.ui.machineInfoLabel.setEnabled(True)
            self.ui.spindleStatusLabel.setEnabled(True)
            self.ui.spindleStatusValue.setEnabled(True)
            self.ui.coolantMistLabel.setEnabled(True)
            self.ui.coolantMistValue.setEnabled(True)
            self.ui.coolantFloodLabel.setEnabled(True)
            self.ui.coolantFloodValue.setEnabled(True)
            self.ui.gcodeLineLabel.setEnabled(True)
            self.ui.gcodeLineValue.setEnabled(True)
            self.ui.workedTimeLabel.setEnabled(True)
            self.ui.workedTimeValue.setEnabled(True)
            self.ui.plannedTimeLabel.setEnabled(True)
            self.ui.plannedTimeValue.setEnabled(True)
            self.ui.toolInfoLabel.setEnabled(True)

            # enablings tab axes position plot
            # enablings tab program
            # enablings tab g-code
            # enablings tab mdi
            # enablings tab cnc

            # enablings tab jog
            set_program_position = enabled_commands.set_program_position
            self.ui.setProgramPositionXEdit.setEnabled((set_program_position & cnc.X_AXIS_MASK) > 0)
            self.ui.setProgramPositionYEdit.setEnabled((set_program_position & cnc.Y_AXIS_MASK) > 0)
            self.ui.setProgramPositionZEdit.setEnabled((set_program_position & cnc.Z_AXIS_MASK) > 0)
            self.ui.setProgramPositionAEdit.setEnabled((set_program_position & cnc.A_AXIS_MASK) > 0)
            self.ui.setProgramPositionBEdit.setEnabled((set_program_position & cnc.B_AXIS_MASK) > 0)
            self.ui.setProgramPositionCEdit.setEnabled((set_program_position & cnc.C_AXIS_MASK) > 0)

            # enablings tab overrides
            self.ui.ovrJogLabel.setEnabled(cnc_info.override_jog_enabled)
            self.ui.ovrJogSlider.setEnabled(
                cnc_info.override_jog_enabled and not cnc_info.override_jog_locked)
            self.ui.ovrJogValue.setEnabled(cnc_info.override_jog_enabled)
            self.ui.ovrSpindleLabel.setEnabled(cnc_info.override_spindle_enabled)
            self.ui.ovrSpindleSlider.setEnabled(
                cnc_info.override_spindle_enabled and not cnc_info.override_spindle_locked)
            self.ui.ovrSpindleValue.setEnabled(cnc_info.override_spindle_enabled)
            self.ui.ovrFastLabel.setEnabled(cnc_info.override_fast_enabled)
            self.ui.ovrFastSlider.setEnabled(
                cnc_info.override_fast_enabled and not cnc_info.override_fast_locked)
            self.ui.ovrFastValue.setEnabled(cnc_info.override_fast_enabled)
            self.ui.ovrFeedLabel.setEnabled(cnc_info.override_feed_enabled)
            self.ui.ovrFeedSlider.setEnabled(
                cnc_info.override_feed_enabled and not cnc_info.override_feed_locked)
            self.ui.ovrFeedValue.setEnabled(cnc_info.override_feed_enabled)
            self.ui.ovrFeedCSM1Label.setEnabled(cnc_info.override_feed_custom_1_enabled)
            self.ui.ovrFeedCSM1Slider.setEnabled(
                cnc_info.override_feed_custom_1_enabled and not cnc_info.override_feed_custom_1_locked)
            self.ui.ovrFeedCSM1Value.setEnabled(cnc_info.override_feed_custom_1_enabled)
            self.ui.ovrFeedCSM2Label.setEnabled(cnc_info.override_feed_custom_2_enabled)
            self.ui.ovrFeedCSM2Slider.setEnabled(
                cnc_info.override_feed_custom_2_enabled and not cnc_info.override_feed_custom_2_locked)
            self.ui.ovrFeedCSM2Value.setEnabled(cnc_info.override_feed_custom_2_enabled)
            self.ui.ovrPlasmaPowerLabel.setEnabled(cnc_info.override_plasma_power_enabled)
            self.ui.ovrPlasmaPowerSlider.setEnabled(
                cnc_info.override_plasma_power_enabled and not cnc_info.override_plasma_power_locked)
            self.ui.ovrPlasmaPowerValue.setEnabled(cnc_info.override_plasma_power_enabled)
            self.ui.ovrPlasmaVoltageLabel.setEnabled(cnc_info.override_plasma_voltage_enabled)
            self.ui.ovrPlasmaVoltageSlider.setEnabled(
                cnc_info.override_plasma_voltage_enabled and not cnc_info.override_plasma_voltage_locked)
            self.ui.ovrPlasmaVoltageValue.setEnabled(cnc_info.override_plasma_voltage_enabled)

            # enablings tab homing
            # enablings tab wcs
            # enablings tab d i/o
            # enablings tab a i/o
            # enablings tab scanning laser
            # enablings tab machining info
            # enablings tab ui dialogs
            # enablings tab system info

    def __update_spindle_buttons(self):

        SPINDLE_CW_DISABLED         = 0
        SPINDLE_CW_ENABLED_01       = 1
        SPINDLE_CW_ENABLED_02       = 2
        SPINDLE_CW_ENABLED_03       = 3

        SPINDLE_CCW_DISABLED        = 4
        SPINDLE_CCW_ENABLED_01      = 5
        SPINDLE_CCW_ENABLED_02      = 6
        SPINDLE_CCW_ENABLED_03      = 7

        icons = [
            ":/images/images/spindle_cw_disabled.svg",
            ":/images/images/spindle_cw_enabled_1.svg",
            ":/images/images/spindle_cw_enabled_2.svg",
            ":/images/images/spindle_cw_enabled_3.svg",
            ":/images/images/spindle_ccw_disabled.svg",
            ":/images/images/spindle_ccw_enabled_1.svg",
            ":/images/images/spindle_ccw_enabled_2.svg",
            ":/images/images/spindle_ccw_enabled_3.svg",
        ]

        def update_button_icon(button: QPushButton, icon_id: int, force_update: bool = False):
            current_icon_id = button.property("icon_id")
            if not force_update and current_icon_id == icon_id:
                return
            button.setProperty("icon_id", icon_id)
            icon_name = icons[icon_id]
            icon = QIcon(icon_name)
            button.setIcon(icon)
            size_hint = button.size()
            icon_size = QSize(size_hint.width() - 10, size_hint.height() - 10)
            button.setIconSize(icon_size)

        # create shortcuts
        cnc_info = self.ctx.cnc_info
        btn_cw = self.ui.cfsmSpindleCWButton
        btn_ccw = self.ui.cfsmSpindleCCWButton

        #
        if cnc_info.state_machine in [cnc.SM_DISCONNECTED, cnc.SM_SIMULATOR, cnc.SM_ALARM]:
            update_button_icon(btn_cw, SPINDLE_CW_DISABLED)
            update_button_icon(btn_ccw, SPINDLE_CCW_DISABLED)
        else:
            if cnc_info.spindle_not_ready:
                update_button_icon(btn_cw, SPINDLE_CW_ENABLED_03)
                update_button_icon(btn_ccw, SPINDLE_CCW_ENABLED_03)
            else:
                blink_state = (int(time.perf_counter() * 1000) % 700) >= 350
                if cnc_info.spindle_direction == cnc.SD_CW:
                    update_button_icon(btn_ccw, SPINDLE_CCW_ENABLED_01)
                    update_button_icon(btn_cw, SPINDLE_CW_ENABLED_01 if blink_state else SPINDLE_CW_ENABLED_02)
                elif cnc_info.spindle_direction == cnc.SD_CCW:
                    update_button_icon(btn_cw, SPINDLE_CW_ENABLED_01)
                    update_button_icon(btn_ccw, SPINDLE_CCW_ENABLED_01 if blink_state else SPINDLE_CCW_ENABLED_02)
                else:
                    update_button_icon(btn_cw, SPINDLE_CW_ENABLED_01)
                    update_button_icon(btn_ccw, SPINDLE_CCW_ENABLED_01)
    #
    # == END: update methods

    # == BEG: user dialogs methods
    #
    def __alarms_warnings_dialog(self, mode: AlarmsWarningsMode):
        dialog = AlarmsWarningsDialog(self, self.api, mode)
        dialog.open()

    def __operator_request_check(self):

        def kill_active_operator_request():
            if isinstance(self.active_operator_request_dialog, QDialog):
                self.active_operator_request_dialog.force_close()
            self.active_operator_request_dialog = None
            self.active_operator_request = None

        cnc_info = self.ctx.cnc_info

        # check if we do not have connection e/o data
        if not cnc_info.has_data:
            kill_active_operator_request()
            return

        # check if we do not have a pending operator request id (empty string or None)
        if not cnc_info.operator_request_id_pending:
            kill_active_operator_request()
            return

        # check if operator request id is already managed by a dialog
        if (
            self.active_operator_request is not None and
            self.active_operator_request.id == cnc_info.operator_request_id_pending
        ):
            return

        # new request: close any previous dialog and download the payload
        kill_active_operator_request()

        # get operator request
        operator_request = self.api.get_operator_request()
        if not operator_request.has_data:
            return

        if operator_request.type in [
            cnc.ORQT_USER_MEDIA_CONTINUE,
            cnc.ORQT_USER_MEDIA_STOP,
            cnc.ORQT_USER_MEDIA_STOP_CONTINUE,
            cnc.ORQT_USER_MEDIA_VALUE_OR_STOP,
            cnc.ORQT_USER_MEDIA_VALUES_OR_STOP,
        ]:
            self.__operator_request_show_user_media_dialog(operator_request)
        elif operator_request.type in [
            cnc.ORQT_USER_MESSAGE_CONTINUE,
            cnc.ORQT_USER_MESSAGE_STOP,
            cnc.ORQT_USER_MESSAGE_STOP_CONTINUE,
            cnc.ORQT_USER_MESSAGE_VALUE_OR_STOP,
            cnc.ORQT_USER_MESSAGE_VALUES_OR_STOP,
        ]:
            self.__operator_request_show_user_message_dialog(operator_request)
        else:
            kill_active_operator_request()

    def __operator_request_show_user_media_dialog(self, operator_request: cnc.APIOperatorRequest):
        self.active_operator_request = operator_request
        self.active_operator_request_dialog = UserMediaDialog(
            parent=self,
            api_client_core=self.api,
            operator_request=operator_request
        )
        self.active_operator_request_dialog.open()

    def __operator_request_show_user_message_dialog(self, operator_request: cnc.APIOperatorRequest):
        self.active_operator_request = operator_request
        self.active_operator_request_dialog = UserMessageDialog(
            parent=self,
            api_client_core=self.api,
            operator_request=operator_request
        )
        self.active_operator_request_dialog.open()
    #
    # == END: user dialogs methods
