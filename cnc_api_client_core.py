"""CNC API Client Core for RosettaCNC & derivated Control Software."""
#-------------------------------------------------------------------------------
# Name:         cnc_api_client_core
#
# Purpose:      CNC API Client Core for RosettaCNC & derivated Control Software
#
# Note          Compatible with API server version 1.4
#               1 (on 1.x) means interface contract
#               x (on 1.x) means release version
#
# Note          Checked with Python 3.11.3
#
# Author:       support@rosettacnc.com
#
# Created:      10/05/2023
# Copyright:    RosettaCNC (c) 2016-2023
# Licence:      RosettaCNC License 1.0 (RCNC-1.0)
# Coding Style  https://www.python.org/dev/peps/pep-0008/
#-------------------------------------------------------------------------------
# pylint: disable=C0103 -> invalid-name
# pylint: disable=C0302 -> too-many-lines
# pylint: disable=R0902 -> too-many-instance-attributes
# pylint: disable=R0903 -> too-few-public-methods
# pylint: disable=R0904 -> too-many-public-methods
# pylint: disable=R0915 -> too-many-statements
# pylint: disable=W0702 -> bare-except
#-------------------------------------------------------------------------------
import json
import socket

# module version
__version__ = '1.4.1'                           # module version

# analysis mode
ANALYSIS_MT                         = 'mt'      # model path with tools colors
ANALYSIS_RT                         = 'rt'      # real path with tools colors
ANALYSIS_RF                         = 'rf'      # real path with colors related to the feed
ANALYSIS_RV                         = 'rv'      # real path with colors related to the velocity
ANALYSIS_RZ                         = 'rz'      # raal path with colors realted to the feed Z level

# axis mask
X_AXIS_MASK                         = 0x0001    # X axis mask
Y_AXIS_MASK                         = 0x0002    # Y axis mask
Z_AXIS_MASK                         = 0x0004    # Z axis mask
A_AXIS_MASK                         = 0x0008    # A axis mask
B_AXIS_MASK                         = 0x0010    # B axis mask
C_AXIS_MASK                         = 0x0020    # C axis mask
U_AXIS_MASK                         = 0x0040    # A axis mask
V_AXIS_MASK                         = 0x0080    # B axis mask
W_AXIS_MASK                         = 0x0100    # C axis mask

# axis mask
X2Z_AXIS_MASK                       = 0x0007    # X to Z axis mask
X2C_AXIS_MASK                       = 0x003F    # X to C axis mask
X2W_AXIS_MASK                       = 0x01FF    # X to W axis mask

# compile state
CS_INIT                             = 0         # compiler xxx
CS_READY                            = 1         # compiler xxx
CS_ERROR                            = 2         # compiler xxx
CS_FIRST_STEP                       = 3         # compiler xxx
CS_FIRST_STEP_RUNNING               = 4         # compiler xxx
CS_WAITING_FOR_DATA                 = 5         # compiler xxx
CS_WAITING_FOR_DATA_RUNNING         = 6         # compiler xxx
CS_FINISHED                         = 7         # compiler xxx

# jog command
JC_NONE                             = 0         # none jog movement
JC_X_BW                             = 1         # jog x axis backward
JC_X_FW                             = 2         # jog x axis forward
JC_Y_BW                             = 3         # jog y axis backward
JC_Y_FW                             = 4         # jog y axis forward
JC_Z_BW                             = 5         # jog z axis backward
JC_Z_FW                             = 6         # jog Z axis forward
JC_A_BW                             = 7         # jog a axis backward
JC_A_FW                             = 8         # jog a axis forward
JC_B_BW                             = 9         # jog b axis backward
JC_B_FW                             = 10        # jog b axis forward
JC_C_BW                             = 11        # jog c axis backward
JC_C_FW                             = 12        # jog c axis forward

# state machine
SM_DISCONNECTED                     = 0         # Control Software state: internal state : DISCONNECTED
SM_SIMULATOR                        = 1         # Control Software state: internal state : SIMULATOR
SM_INIT                             = 2         # CNC Board: SM_INIT                     : INIT
SM_INIT_FIELD_BUS                   = 3         # CNC Board: SM_INIT_FIELDBUS            : INIT FIELD BUS
SM_ALARM                            = 4         # CNC Board: ST_MACH.SM_ALARM            : ALARM
SM_IDLE                             = 5         # CNC Board: ST_MACH.SM_IDLE             : IDLE
SM_HOMING                           = 6         # CNC Board: ST_MACH.SM_HOMING           : HOMING
SM_JOG                              = 7         # CNC Board: ST_MACH.SM_JOG              : JOG
SM_RUN                              = 8         # CNC Board: ST_MACH.SM_RUN              : RUN
SM_PAUSE                            = 9         # CNC Board: ST_MACH.SM_PAUSE            : PAUSE
SM_LIMIT                            = 10        # CNC Board: ST_MACH.SM_LIMIT            : LIMIT
SM_MEASURE_TOOL                     = 11        # CNC Board: ST_MACH.SM_MEASURE_TOOL     : MEASURE TOOL
SM_SCAN_3D                          = 12        # CNC Board: ST_MACH.SM_SCAN3D           : SCANNING
SM_SAFETY_IDLE                      = 13        # CNC Board: ST_MACH.SM_SAFETY_IDLE      : SAFETY JOG
SM_CHANGE_TOOL                      = 14        # CNC Board: ST_MACH.SM_CHANGE_TOOL      : CHANGE TOOL
SM_SAFETY                           = 15        # CNC Board: ST_MACH.SM_SAFETY           : SAFETY
SM_WAIT_MAIN_POWER                  = 16        # CNC Board: ST_MACH.SM_WAIT_MAIN_POWER  : WAIT MAIN POWER
SM_RETRACT                          = 17        # CNC Board: ST_MACH.SM_RETRACT          : RETRACT

# spindle status
SS_OFF                              = 1         # spindle status: OFF
SS_CW                               = 2         # spindle status: CLOCKWISE
SS_CCW                              = 3         # spindle status: COUNTERCLOCKWISE

# tool type
TT_GENERIC                          = 0         # tool Type: generic
TT_FLAT_END_MILL                    = 1         # tool Type: flat end mill
TT_BALL_NOSE_END_MILL               = 2         # tool Type: ball nose end mill
TT_DRILL                            = 3         # tool Type: drill
TT_PROBE                            = 4         # tool Type: probe
TT_SAW                              = 5         # tool Type: saw
TT_PLASMA                           = 6         # tool Type: plasma
TT_DRAG_KNIFE                       = 7         # tool Type: drag knife
TT_LATHE                            = 8         # tool Type: lathe
TT_LASER                            = 9         # tool Type: laser
TT_WATER_JET                        = 10        # tool Type: water jet

# units mode
UM_METRIC                           = 0         # units mode: metric (mm)
UM_IMPERIAL                         = 1         # units mode: imperial (in)

class APIAnalogInputs:
    """API data structure for analog inputs."""
    has_data                        = False
    value                           = [0.0]*16

class APIAnalogOutputs:
    """API data structure for analog outputs."""
    has_data                        = False
    value                           = [0.0]*16

class APIAxesInfo:
    """API data structure for axes info."""
    has_data                        = False
    joint_position                  = [0.0]*6
    machine_position                = [0.0]*6
    program_position                = [0.0]*6
    machine_target_position         = [0.0]*6
    program_target_position         = [0.0]*6
    actual_velocity                 = [0]*6
    working_wcs                     = 0
    working_offset                  = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    dynamic_offset                  = [0.0, 0.0, 0.0]
    homing_done                     = 0
    homing_done_mask                = 0

class APICncInfo:
    """API data structure for cnc info."""
    has_data                        = False
    units_mode                      = UM_METRIC
    axes_mask                       = 0
    state_machine                   = 0
    gcode_line                      = 0
    worked_time                     = '00:00:00'
    coolant_mist                    = False
    coolant_flood                   = False
    lube_axis_cycles_made           = 0
    lube_axis_time_to_next_cycle    = 0
    lube_spindle_cycles_made        = 0
    lube_spindle_time_to_next_cycle = 0
    feed_programmed                 = 0
    feed_target                     = 0
    feed_reference                  = 0
    spindle_programmed              = 0
    spindle_target                  = 0
    spindle_actual                  = 0
    spindle_load                    = 0
    spindle_torque                  = 0
    spindle_status                  = 0
    override_jog                    = 0
    override_jog_min                = 0
    override_jog_max                = 100
    override_jog_enabled            = False
    override_jog_locked             = False
    override_spindle                = 0
    override_spindle_min            = 0
    override_spindle_max            = 100
    override_spindle_enabled        = False
    override_spindle_locked         = False
    override_fast                   = 0
    override_fast_min               = 0
    override_fast_max               = 100
    override_fast_enabled           = False
    override_fast_locked            = False
    override_feed                   = 0
    override_feed_min               = 0
    override_feed_max               = 100
    override_feed_enabled           = False
    override_feed_locked            = False
    override_feed_custom_1          = 0
    override_feed_custom_1_min      = 0
    override_feed_custom_1_max      = 100
    override_feed_custom_1_enabled  = False
    override_feed_custom_1_locked   = False
    override_feed_custom_2          = 0
    override_feed_custom_2_min      = 0
    override_feed_custom_2_max      = 100
    override_feed_custom_2_enabled  = False
    override_feed_custom_2_locked   = False
    plasma_power                    = 0
    plasma_power_min                = 0
    plasma_power_max                = 100
    plasma_power_enabled            = False
    plasma_power_locked             = False
    plasma_voltage                  = 0
    plasma_voltage_min              = 0
    plasma_voltage_max              = 100
    plasma_voltage_enabled          = False
    plasma_voltage_locked           = False
    tool_id                         = 0
    tool_slot                       = False
    tool_type                       = TT_GENERIC
    tool_diameter                   = 0.0
    tool_offset_x                   = 0.0
    tool_offset_y                   = 0.0
    tool_offset_z                   = 0.0
    tool_param_1                    = 0.0
    tool_param_2                    = 0.0
    tool_param_3                    = 0.0

class APICncParameters:
    """API data structure for cnc parameters."""
    has_data                        = False
    address                         = 0
    parameters                      = []

class APICompileInfo:
    """API data structure for compile info."""
    has_data                        = False
    code                            = 0
    code_line                       = 0
    file_line                       = 0
    file_name                       = ''
    message                         = ''
    state                           = 0

class APIDigitalInputs:
    """API data structure for digital inputs."""
    has_data                        = False
    value                           = [0]*128

class APIDigitalOutputs:
    """API data structure for digital outputs."""
    has_data                        = False
    value                           = [0]*128

class APIEnabledCommands:
    """API data structure for enabled commands."""
    has_data                        = False
    cnc_continue                    = False
    cnc_homing                      = 0
    cnc_jog_command                 = 0
    cnc_mdi_command                 = False
    cnc_parameters                  = False
    cnc_pause                       = False
    cnc_resume                      = False
    cnc_resume_from_line            = False
    cnc_resume_from_point           = False
    cnc_start                       = False
    cnc_start_from_line             = False
    cnc_start_from_point            = False
    cnc_stop                        = False
    program_analysis                = False
    program_analysis_abort          = False
    program_gcode_add_text          = False
    program_gcode_clear             = False
    program_gcode_set_text          = False
    program_load                    = False
    program_new                     = False
    program_save                    = False
    set_program_position            = 0

class APIMachiningInfoUsedTool:
    """API data structure with used tool info."""
    tool_id                         = 0
    in_fast                         = 0.0
    in_feed                         = 0.0

class APIMachiningInfo:
    """API data structure for machining info."""
    has_data                        = False
    tool_path_in_fast               = 0.0
    tool_path_in_feed               = 0.0
    total_path                      = 0.0
    estimated_time                  = '00:00:00'
    used_tool                       = []
    tcp_extents_in_fast_min_x       = 0.0
    tcp_extents_in_fast_min_y       = 0.0
    tcp_extents_in_fast_min_z       = 0.0
    tcp_extents_in_fast_max_x       = 0.0
    tcp_extents_in_fast_max_y       = 0.0
    tcp_extents_in_fast_max_z       = 0.0
    tcp_extents_in_fast_length_x    = 0.0
    tcp_extents_in_fast_length_y    = 0.0
    tcp_extents_in_fast_length_z    = 0.0
    tcp_extents_in_feed_min_x       = 0.0
    tcp_extents_in_feed_min_y       = 0.0
    tcp_extents_in_feed_min_z       = 0.0
    tcp_extents_in_feed_max_x       = 0.0
    tcp_extents_in_feed_max_y       = 0.0
    tcp_extents_in_feed_max_z       = 0.0
    tcp_extents_in_feed_length_x    = 0.0
    tcp_extents_in_feed_length_y    = 0.0
    tcp_extents_in_feed_length_z    = 0.0
    joints_in_fast_min_x            = 0.0
    joints_in_fast_min_y            = 0.0
    joints_in_fast_min_z            = 0.0
    joints_in_fast_min_a            = 0.0
    joints_in_fast_min_b            = 0.0
    joints_in_fast_min_c            = 0.0
    joints_in_fast_max_x            = 0.0
    joints_in_fast_max_y            = 0.0
    joints_in_fast_max_z            = 0.0
    joints_in_fast_max_a            = 0.0
    joints_in_fast_max_b            = 0.0
    joints_in_fast_max_c            = 0.0
    joints_in_fast_length_x         = 0.0
    joints_in_fast_length_y         = 0.0
    joints_in_fast_length_z         = 0.0
    joints_in_fast_length_a         = 0.0
    joints_in_fast_length_b         = 0.0
    joints_in_fast_length_c         = 0.0
    joints_in_feed_min_x            = 0.0
    joints_in_feed_min_y            = 0.0
    joints_in_feed_min_z            = 0.0
    joints_in_feed_min_a            = 0.0
    joints_in_feed_min_b            = 0.0
    joints_in_feed_min_c            = 0.0
    joints_in_feed_max_x            = 0.0
    joints_in_feed_max_y            = 0.0
    joints_in_feed_max_z            = 0.0
    joints_in_feed_max_a            = 0.0
    joints_in_feed_max_b            = 0.0
    joints_in_feed_max_c            = 0.0
    joints_in_feed_length_x         = 0.0
    joints_in_feed_length_y         = 0.0
    joints_in_feed_length_z         = 0.0
    joints_in_feed_length_a         = 0.0
    joints_in_feed_length_b         = 0.0
    joints_in_fast_length_c         = 0.0

class APIProgrammedPoints:
    """API data structure for programmed points."""
    has_data                        = False
    points                          = []

class APIScan3DInfo:
    """API data structure for scan3d info."""
    has_data                        = False
    analog_out_bit                  = 0
    analog_out_umf                  = 0.0
    analog_measure                  = 0.0

class APISystemInfo:
    """API data structure for system info."""
    has_data                        = False
    cnc_control_software            = ''
    cnc_core_version                = ''
    api_server_version              = ''
    firmware_version                = ''
    firmware_version_tag            = ''
    firmware_interface_level        = ''
    order_code                      = ''
    customer_id                     = ''
    serial_number                   = ''
    part_number                     = ''
    customization_number            = ''
    hardware_version                = ''
    operative_system                = ''
    operative_system_crc            = ''
    pld_version                     = ''

class APIVMGeometryInfo:
    """API data structure for virtual machine geometry info."""
    has_data                        = False
    name                            = ''
    x                               = 0.0
    y                               = 0.0
    z                               = 0.0
    color                           = 0
    scale                           = 0.0
    visible                         = False
    edges_angle                     = 0.0
    edges_visible                   = False

class CncAPIClientCore:
    """
    Class with API client core implementation.

    An instance of this class reaches a single API Server.
    If you have several CNC to reach you need to instance this class for each server.
    """

    def __init__(self):
        self.ipc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.is_connected = False
        self.i = 0

    # == BEG: public attributes
    #

    def connect(self, host: str, port: int) -> bool:
        """
        Opens the connection with the specified API server host/port.

        host        The server host address to connect to (eg.'192.168.0.220').
        port        The server host port to connect to (valid range 0..65535).
        return      True if the connection with the API server has been established.
        """
        if self.is_connected:
            return False
        try:
            ipc_server_address = (host, port)
            self.ipc.connect(ipc_server_address)
        except:
            return False
        self.is_connected = True
        return True

    def close(self) -> bool:
        """
        Closes the current connection with the API server

        return      True if the client is connected to an API server and connection is closed successfully.
        """
        if self.is_connected:
            try:
                self.ipc.close()
                self.is_connected = False
                return True
            except:
                return False
        return False

    def close_cnc_control_software(self):
        """Not implemented yet!"""

    def cnc_continue(self):
        """Xxx..."""
        return self.__execute_request('{"cmd":"cnc.continue"}')

    def cnc_homing(self, axes_mask: int) -> bool:
        """
        Requires Homing for specified axes

        axes_mask   Mask with axes affected by the command.
        return      True if the request was successful.
        """
        return self.__execute_request('{"cmd":"cnc.homing","axes.mask":' + str(axes_mask) + '}')

    def cnc_jog_command(self, command: int):
        """
        Requires a JOG Command

        command     Jog command. Available commands are in JC_xxx constants.
        return      True if the request was successful.
        """
        if not command in range(JC_NONE, JC_C_FW + 1):
            return False
        return self.__execute_request('{"cmd":"cnc.jog.command","command":' + str(command) + '}')

    def cnc_mdi_command(self, command: str):
        """Xxx..."""
        command = json.dumps(command)
        return self.__execute_request('{"cmd":"cnc.mdi.command","command":' + command + '}')

    def cnc_pause(self):
        """Xxx..."""
        return self.__execute_request('{"cmd":"cnc.pause"}')

    def cnc_resume(self, line: int):
        """Xxx..."""
        if line > 0:
            request = '{"cmd":"cnc.resume", "line":' + str(line) + '}'
        else:
            request = '{"cmd":"cnc.resume"}'
        return self.__execute_request(request)

    def cnc_resume_from_line(self, line: int):
        """Xxx..."""
        request = '{"cmd":"cnc.resume.from.line", "line":' + str(line) + '}'
        return self.__execute_request(request)

    def cnc_resume_from_point(self, point: int):
        """Xxx..."""
        request = '{"cmd":"cnc.resume.from.point", "point":' + str(point) + '}'
        return self.__execute_request(request)

    def cnc_start(self):
        """Xxx..."""
        return self.__execute_request('{"cmd":"cnc.start"}')

    def cnc_start_from_line(self, line: int):
        """Xxx..."""
        return self.__execute_request('{"cmd":"cnc.start.from.line", "line":' + str(line) + '}')

    def cnc_start_from_point(self, point: int):
        """Xxx..."""
        return self.__execute_request('{"cmd":"cnc.start.from.point", "point":' + str(point) + '}')

    def cnc_stop(self):
        """Xxx..."""
        return self.__execute_request('{"cmd":"cnc.stop"}')

    def program_analysis(self, mode: str):
        """Xxx..."""
        mode = json.dumps(mode)
        return self.__execute_request('{"cmd":"program.analysis","mode":' + mode + '}')

    def program_analysis_abort(self):
        """Xxx..."""
        return self.__execute_request('{"cmd":"program.analysis.abort"}')

    def program_gcode_add_text(self, text: str):
        """Xxx..."""
        text = json.dumps(text)
        return self.__execute_request('{"cmd":"program.gcode.add.text","text":' + text + '}')

    def program_gcode_clear(self):
        """Xxx..."""
        return self.__execute_request('{"cmd":"program.gcode.clear"}')

    def program_gcode_set_text(self, text: str):
        """Xxx..."""
        text = json.dumps(text)
        return self.__execute_request('{"cmd":"program.gcode.set.text","text":' + text + '}')

    def program_new(self):
        """Xxx..."""
        return self.__execute_request('{"cmd":"program.new"}')

    def program_load(self, file_name):
        """Xxx..."""
        file_name = json.dumps(file_name)
        return self.__execute_request('{"cmd":"program.load","name":' + file_name + '}')

    def program_save(self, file_name: str):
        """Xxx..."""
        file_name = json.dumps(file_name)
        return self.__execute_request('{"cmd":"program.save","name":' + file_name + '}')

    def get_analog_inputs(self):
        """Xxx..."""
        try:
            if self.is_connected is False:
                raise Exception()
            data = APIAnalogInputs()
            request = '{"get":"analog.inputs"}'
            response = self.__send_command(request)
            if response != "":
                j = json.loads(response)
                data.value                          = j['res']['value']
                data.has_data                       = True
            return data
        except:
            return APIAnalogInputs()

    def get_analog_outputs(self):
        """Xxx..."""
        try:
            if self.is_connected is False:
                raise Exception()
            data = APIAnalogOutputs()
            request = '{"get":"analog.outputs"}'
            response = self.__send_command(request)
            if response != "":
                j = json.loads(response)
                data.value                          = j['res']['value']
                data.has_data                       = True
            return data
        except:
            return APIAnalogOutputs()

    def get_axes_info(self):
        """Xxx..."""
        try:
            if self.is_connected is False:
                raise Exception()
            data = APIAxesInfo()
            request = '{"get":"axes.info"}'
            response = self.__send_command(request)
            if response != "":
                j = json.loads(response)
                data.joint_position                 = j['res']['joint.position']
                data.machine_position               = j['res']['machine.position']
                data.program_position               = j['res']['program.position']
                data.machine_target_position        = j['res']['machine.target.position']
                data.program_target_position        = j['res']['program.target.position']
                data.actual_velocity                = j['res']['actual.velocity']
                data.working_wcs                    = j['res']['working.wcs']
                data.working_offset                 = j['res']['working.offset']
                data.dynamic_offset                 = j['res']['dynamic.offset']
                data.homing_done                    = j['res']['homing.done']
                data.homing_done_mask               = j['res']['homing.done.mask']
                data.has_data                       = True
            return data
        except:
            return APIAxesInfo()

    def get_cnc_info(self):
        """Xxx..."""
        try:
            if self.is_connected is False:
                raise Exception()
            data = APICncInfo()
            request = '{"get":"cnc.info"}'
            response = self.__send_command(request)
            if response != "":
                j = json.loads(response)
                data.units_mode                         = j['res']['units.mode']
                data.axes_mask                          = j['res']['axes.mask']
                data.state_machine                      = j['res']['state.machine']
                data.gcode_line                         = j['res']['gcode.line']
                data.worked_time                        = j['res']['worked.time']
                data.coolant_mist                       = j['res']['coolant']['mist']
                data.coolant_flood                      = j['res']['coolant']['flood']
                data.lube_axis_cycles_made              = j['res']['lube']['axis.cycles.made']
                data.lube_axis_time_to_next_cycle       = j['res']['lube']['axis.time.to.next.cycle']
                data.lube_spindle_cycles_made           = j['res']['lube']['spindle.cycles.made']
                data.lube_spindle_time_to_next_cycle    = j['res']['lube']['spindle.time.to.next.cycle']
                data.feed_programmed                    = j['res']['feed']['programmed']
                data.feed_target                        = j['res']['feed']['target']
                data.feed_reference                     = j['res']['feed']['reference']
                data.spindle_programmed                 = j['res']['spindle']['programmed']
                data.spindle_target                     = j['res']['spindle']['target']
                data.spindle_actual                     = j['res']['spindle']['actual']
                data.spindle_load                       = j['res']['spindle']['load']
                data.spindle_torque                     = j['res']['spindle']['torque']
                data.spindle_status                     = j['res']['spindle']['status']
                data.override_jog                       = j['res']['override']['jog']
                data.override_jog_min                   = j['res']['override']['jog.min']
                data.override_jog_max                   = j['res']['override']['jog.max']
                data.override_jog_enabled               = j['res']['override']['jog.enabled']
                data.override_jog_locked                = j['res']['override']['jog.locked']
                data.override_spindle                   = j['res']['override']['spindle']
                data.override_spindle_min               = j['res']['override']['spindle.min']
                data.override_spindle_max               = j['res']['override']['spindle.max']
                data.override_spindle_enabled           = j['res']['override']['spindle.enabled']
                data.override_spindle_locked            = j['res']['override']['spindle.locked']
                data.override_fast                      = j['res']['override']['fast']
                data.override_fast_min                  = j['res']['override']['fast.min']
                data.override_fast_max                  = j['res']['override']['fast.max']
                data.override_fast_enabled              = j['res']['override']['fast.enabled']
                data.override_fast_locked               = j['res']['override']['fast.locked']
                data.override_feed                      = j['res']['override']['feed']
                data.override_feed_min                  = j['res']['override']['feed.min']
                data.override_feed_max                  = j['res']['override']['feed.max']
                data.override_feed_enabled              = j['res']['override']['feed.enabled']
                data.override_feed_locked               = j['res']['override']['feed.locked']
                data.override_feed_custom_1             = j['res']['override']['feed.custom.1']
                data.override_feed_custom_1_min         = j['res']['override']['feed.custom.1.min']
                data.override_feed_custom_1_max         = j['res']['override']['feed.custom.1.max']
                data.override_feed_custom_1_enabled     = j['res']['override']['feed.custom.1.enabled']
                data.override_feed_custom_1_locked      = j['res']['override']['feed.custom.1.locked']
                data.override_feed_custom_2             = j['res']['override']['feed.custom.2']
                data.override_feed_custom_2_min         = j['res']['override']['feed.custom.2.min']
                data.override_feed_custom_2_max         = j['res']['override']['feed.custom.2.max']
                data.override_feed_custom_2_enabled     = j['res']['override']['feed.custom.2.enabled']
                data.override_feed_custom_2_locked      = j['res']['override']['feed.custom.2.locked']
                data.plasma_power                       = j['res']['override']['plasma.power']
                data.plasma_power_min                   = j['res']['override']['plasma.power.min']
                data.plasma_power_max                   = j['res']['override']['plasma.power.max']
                data.plasma_power_enabled               = j['res']['override']['plasma.power.enabled']
                data.plasma_power_locked                = j['res']['override']['plasma.power.locked']
                data.plasma_voltage                     = j['res']['override']['plasma.voltage']
                data.plasma_voltage_min                 = j['res']['override']['plasma.voltage.min']
                data.plasma_voltage_max                 = j['res']['override']['plasma.voltage.max']
                data.plasma_voltage_enabled             = j['res']['override']['plasma.voltage.enabled']
                data.plasma_voltage_locked              = j['res']['override']['plasma.voltage.locked']
                data.tool_id                            = j['res']['tool']['id']
                data.tool_slot                          = j['res']['tool']['slot']
                data.tool_type                          = j['res']['tool']['type']
                data.tool_diameter                      = j['res']['tool']['diameter']
                data.tool_offset_x                      = j['res']['tool']['offset.x']
                data.tool_offset_y                      = j['res']['tool']['offset.y']
                data.tool_offset_z                      = j['res']['tool']['offset.z']
                data.tool_param_1                       = j['res']['tool']['param.1']
                data.tool_param_2                       = j['res']['tool']['param.2']
                data.tool_param_3                       = j['res']['tool']['param.3']
                data.has_data = True
            return data
        except:
            return APICncInfo()

    def get_cnc_parameters(self, address: int, elements: int):
        """Xxx..."""
        try:
            if self.is_connected is False:
                raise Exception()
            data = APICncParameters()
            request = '{"get":"cnc.parameters", "address":' + str(address) + ', "elements":' + str(elements) + '}'
            response = self.__send_command(request)
            if response != "":
                j = json.loads(response)
                data.parameters                     = j['res']['parameters']
                data.has_data = True
            return data
        except:
            return APICncParameters()

    def get_compile_info(self):
        """Xxx..."""
        try:
            if self.is_connected is False:
                raise Exception()
            data = APICompileInfo()
            request = '{"get":"compile.info"}'
            response = self.__send_command(request)
            if response != "":
                j = json.loads(response)
                data.code                           = j['res']['code']
                data.code_line                      = j['res']['code.line']
                data.file_line                      = j['res']['file.line']
                data.file_name                      = j['res']['file.name']
                data.message                        = j['res']['message']
                data.state                          = j['res']['state']
                data.has_data = True
            return data
        except:
            return APICompileInfo()

    def get_digital_inputs(self):
        """Xxx..."""
        try:
            if self.is_connected is False:
                raise Exception()
            data = APIDigitalInputs()
            request = '{"get":"digital.inputs"}'
            response = self.__send_command(request)
            if response != "":
                j = json.loads(response)
                data.value                          = j['res']['value']
                data.has_data                       = True
            return data
        except:
            return APIDigitalInputs()

    def get_digital_outputs(self):
        """Xxx..."""
        try:
            if self.is_connected is False:
                raise Exception()
            data = APIDigitalOutputs()
            request = '{"get":"digital.outputs"}'
            response = self.__send_command(request)
            if response != "":
                j = json.loads(response)
                data.value                          = j['res']['value']
                data.has_data                       = True
            return data
        except:
            return APIDigitalOutputs()

    def get_enabled_commands(self):
        """Xxx..."""
        try:
            if self.is_connected is False:
                raise Exception()
            data = APIEnabledCommands()
            request = '{"get":"enabled.commands"}'
            response = self.__send_command(request)
            if response != "":
                j = json.loads(response)
                data.cnc_continue                   = j['res']['cnc.continue']
                data.cnc_homing                     = j['res']['cnc.homing']
                data.cnc_jog_command                = j['res']['cnc.jog.command']
                data.cnc_mdi_command                = j['res']['cnc.mdi.command']
                data.cnc_parameters                 = j['res']['cnc.parameters']
                data.cnc_pause                      = j['res']['cnc.pause']
                data.cnc_resume                     = j['res']['cnc.resume']
                data.cnc_resume_from_line           = j['res']['cnc.resume.from.line']
                data.cnc_resume_from_point          = j['res']['cnc.resume.from.point']
                data.cnc_start                      = j['res']['cnc.start']
                data.cnc_start_from_line            = j['res']['cnc.start.from.line']
                data.cnc_start_from_point           = j['res']['cnc.start.from.point']
                data.cnc_stop                       = j['res']['cnc.stop']
                data.program_analysis               = j['res']['program.analysis']
                data.program_analysis_abort         = j['res']['program.analysis.abort']
                data.program_gcode_add_text         = j['res']['program.gcode.add.text']
                data.program_gcode_clear            = j['res']['program.gcode.clear']
                data.program_gcode_set_text         = j['res']['program.gcode.set.text']
                data.program_load                   = j['res']['program.load']
                data.program_new                    = j['res']['program.new']
                data.program_save                   = j['res']['program.save']
                data.set_program_position           = j['res']['set.program.position']
                data.has_data                       = True
            return data
        except:
            return APIEnabledCommands()

    def get_machining_info(self):
        """Xxx..."""

        def get_machining_info_used_tool(j):
            l = len(j['res']['tool.path']['used.tool'])
            if l == 0:
                return []
            ret = []
            for i in range(l):
                elem = APIMachiningInfoUsedTool()
                elem.tool_id = j['res']['tool.path']['used.tool'][i]['id']
                elem.in_fast = j['res']['tool.path']['used.tool'][i]['in.fast']
                elem.in_feed = j['res']['tool.path']['used.tool'][i]['in.feed']
                ret.append(elem)
            return ret

        try:
            if self.is_connected is False:
                raise Exception()
            data = APIMachiningInfo()
            request = '{"get":"machining.info"}'
            response = self.__send_command(request)
            if response != "":
                j = json.loads(response)
                data.tool_path_in_fast              = j['res']['tool.path']['in.fast']
                data.tool_path_in_feed              = j['res']['tool.path']['in.feed']
                data.total_path                     = j['res']['tool.path']['total.path']
                data.estimated_time                 = j['res']['tool.path']['estimated.time']
                data.used_tool = get_machining_info_used_tool(j)
                data.tcp_extents_in_fast_min_x      = j['res']['tcp.extents.in.fast']['min.x']
                data.tcp_extents_in_fast_min_y      = j['res']['tcp.extents.in.fast']['min.y']
                data.tcp_extents_in_fast_min_z      = j['res']['tcp.extents.in.fast']['min.z']
                data.tcp_extents_in_fast_max_x      = j['res']['tcp.extents.in.fast']['max.x']
                data.tcp_extents_in_fast_max_y      = j['res']['tcp.extents.in.fast']['max.y']
                data.tcp_extents_in_fast_max_z      = j['res']['tcp.extents.in.fast']['max.z']
                data.tcp_extents_in_fast_length_x   = j['res']['tcp.extents.in.fast']['length.x']
                data.tcp_extents_in_fast_length_y   = j['res']['tcp.extents.in.fast']['length.y']
                data.tcp_extents_in_fast_length_z   = j['res']['tcp.extents.in.fast']['length.z']
                data.tcp_extents_in_feed_min_x      = j['res']['tcp.extents.in.feed']['min.x']
                data.tcp_extents_in_feed_min_y      = j['res']['tcp.extents.in.feed']['min.y']
                data.tcp_extents_in_feed_min_z      = j['res']['tcp.extents.in.feed']['min.z']
                data.tcp_extents_in_feed_max_x      = j['res']['tcp.extents.in.feed']['max.x']
                data.tcp_extents_in_feed_max_y      = j['res']['tcp.extents.in.feed']['max.y']
                data.tcp_extents_in_feed_max_z      = j['res']['tcp.extents.in.feed']['max.z']
                data.tcp_extents_in_feed_length_x   = j['res']['tcp.extents.in.feed']['length.x']
                data.tcp_extents_in_feed_length_y   = j['res']['tcp.extents.in.feed']['length.y']
                data.tcp_extents_in_feed_length_z   = j['res']['tcp.extents.in.feed']['length.z']
                data.joints_in_fast_min_x           = j['res']['joints.in.fast']['min.x']
                data.joints_in_fast_min_y           = j['res']['joints.in.fast']['min.y']
                data.joints_in_fast_min_z           = j['res']['joints.in.fast']['min.z']
                data.joints_in_fast_min_a           = j['res']['joints.in.fast']['min.a']
                data.joints_in_fast_min_b           = j['res']['joints.in.fast']['min.b']
                data.joints_in_fast_min_c           = j['res']['joints.in.fast']['min.c']
                data.joints_in_fast_max_x           = j['res']['joints.in.fast']['max.x']
                data.joints_in_fast_max_y           = j['res']['joints.in.fast']['max.y']
                data.joints_in_fast_max_z           = j['res']['joints.in.fast']['max.z']
                data.joints_in_fast_max_a           = j['res']['joints.in.fast']['max.a']
                data.joints_in_fast_max_b           = j['res']['joints.in.fast']['max.b']
                data.joints_in_fast_max_c           = j['res']['joints.in.fast']['max.c']
                data.joints_in_fast_length_x        = j['res']['joints.in.fast']['length.x']
                data.joints_in_fast_length_y        = j['res']['joints.in.fast']['length.y']
                data.joints_in_fast_length_z        = j['res']['joints.in.fast']['length.z']
                data.joints_in_fast_length_a        = j['res']['joints.in.fast']['length.a']
                data.joints_in_fast_length_b        = j['res']['joints.in.fast']['length.b']
                data.joints_in_fast_length_c        = j['res']['joints.in.fast']['length.c']
                data.joints_in_feed_min_x           = j['res']['joints.in.feed']['min.x']
                data.joints_in_feed_min_y           = j['res']['joints.in.feed']['min.y']
                data.joints_in_feed_min_z           = j['res']['joints.in.feed']['min.z']
                data.joints_in_feed_min_a           = j['res']['joints.in.feed']['min.a']
                data.joints_in_feed_min_b           = j['res']['joints.in.feed']['min.b']
                data.joints_in_feed_min_c           = j['res']['joints.in.feed']['min.c']
                data.joints_in_feed_max_x           = j['res']['joints.in.feed']['max.x']
                data.joints_in_feed_max_y           = j['res']['joints.in.feed']['max.y']
                data.joints_in_feed_max_z           = j['res']['joints.in.feed']['max.z']
                data.joints_in_feed_max_a           = j['res']['joints.in.feed']['max.a']
                data.joints_in_feed_max_b           = j['res']['joints.in.feed']['max.b']
                data.joints_in_feed_max_c           = j['res']['joints.in.feed']['max.c']
                data.joints_in_feed_length_x        = j['res']['joints.in.feed']['length.x']
                data.joints_in_feed_length_y        = j['res']['joints.in.feed']['length.y']
                data.joints_in_feed_length_z        = j['res']['joints.in.feed']['length.z']
                data.joints_in_feed_length_a        = j['res']['joints.in.feed']['length.a']
                data.joints_in_feed_length_b        = j['res']['joints.in.feed']['length.b']
                data.joints_in_fast_length_c        = j['res']['joints.in.feed']['length.c']
                data.has_data = True
            return data
        except:
            return APIMachiningInfo()

    def get_programmed_points(self):
        """Xxx..."""
        try:
            if self.is_connected is False:
                raise Exception()
            data = APIProgrammedPoints()
            request = '{"get":"programmed.points"}'
            response = self.__send_command(request)
            if response != "":
                j = json.loads(response)
                data.points                         = j['res']['points']
                data.has_data = True
            return data
        except:
            return APIProgrammedPoints()

    def get_scan3d_info(self):
        """Xxx..."""
        try:
            if self.is_connected is False:
                raise Exception()
            data = APIScan3DInfo()
            request = '{"get":"scan3d.info"}'
            response = self.__send_command(request)
            if response != "":
                j = json.loads(response)
                data.analog_out_bit                 = j['res']['analog.out.bit']
                data.analog_out_umf                 = j['res']['analog.out.umf']
                data.analog_measure                 = j['res']['analog.measure']
                data.has_data = True
            return data
        except:
            return APIScan3DInfo()

    def get_system_info(self):
        """Xxx..."""
        try:
            if self.is_connected is False:
                raise Exception()
            data = APISystemInfo()
            request = '{"get":"system.info"}'
            response = self.__send_command(request)
            if response != "":
                j = json.loads(response)
                data.cnc_control_software           = j['res']['cnc.control.software']
                data.cnc_core_version               = j['res']['cnc.core.version']
                data.api_server_version             = j['res']['api.server.version']
                data.firmware_version               = j['res']['firmware.version']
                data.firmware_version_tag           = j['res']['firmware.version.tag']
                data.firmware_interface_level       = j['res']['firmware.interface.level']
                data.order_code                     = j['res']['order.code']
                data.customer_id                    = j['res']['customer.id']
                data.serial_number                  = j['res']['serial.number']
                data.part_number                    = j['res']['part.number']
                data.customization_number           = j['res']['customization.number']
                data.hardware_version               = j['res']['hardware.version']
                data.operative_system               = j['res']['operative.system']
                data.operative_system_crc           = j['res']['operative.system.crc']
                data.pld_version                    = j['res']['pld.version']
                data.has_data = True
            return data
        except:
            return APISystemInfo()

    def get_vm_geometry_info(self, names: list):
        """Xxx..."""
        try:
            names_count = len(names)
            if names_count == 0:
                return None
            data = [APIVMGeometryInfo() for i in range(names_count)]
            request = '{"get":"vm.geometry.info", "name":['
            for i in range(names_count):
                name = names[i]
                if not isinstance(name, str):
                    return None
                request = request + '"' + name + '"'
                if i < (names_count - 1):
                    request = request + ','
            request = request + ']}'
            response = self.__send_command(request)
            if response != "":
                j = json.loads(response)
                for i in range(names_count):
                    data[i].name                    = j['res'][i]['name']
                    data[i].x                       = j['res'][i]['x']
                    data[i].y                       = j['res'][i]['y']
                    data[i].z                       = j['res'][i]['z']
                    data[i].color                   = j['res'][i]['color']
                    data[i].scale                   = j['res'][i]['scale']
                    data[i].visible                 = j['res'][i]['visible']
                    data[i].edges_angle             = j['res'][i]['edges.angle']
                    data[i].edges_visible           = j['res'][i]['edges.visible']
                    data[i].has_data = data[i].name != ''
            return data
        except:
            return None

    def set_cnc_parameters(self, address: int, values: list):
        """Xxx..."""
        try:
            if len(values) == 0:
                return False
            request = '{"set":"cnc.parameters", "address":' + str(address) + ', "parameters":['
            for idx, value in enumerate(values):
                if not (isinstance(value, int) or isinstance(value, float)):
                    return False
                request = request + str(value)
                if idx < (len(values) - 1):
                    request = request + ','
            request = request + ']}'
            return self.__execute_request(request)
        except:
            return False

    def set_override_fast(self, value: int):
        """Xxx..."""
        return self.__execute_request('{"set":"override", "name":"fast", "value":' + str(int(value)) + '}')

    def set_override_feed(self, value: int):
        """Xxx..."""
        return self.__execute_request('{"set":"override", "name":"feed", "value":' + str(int(value)) + '}')

    def set_override_feed_custom_1(self, value: int):
        """Xxx..."""
        return self.__execute_request('{"set":"override", "name":"feed.custom.1", "value":' + str(int(value)) + '}')

    def set_override_feed_custom_2(self, value: int):
        """Xxx..."""
        return self.__execute_request('{"set":"override", "name":"feed.custom.2", "value":' + str(int(value)) + '}')

    def set_override_jog(self, value: int):
        """Xxx..."""
        return self.__execute_request('{"set":"override", "name":"jog", "value":' + str(int(value)) + '}')

    def set_override_plasma_power(self, value: int):
        """Xxx..."""
        return self.__execute_request('{"set":"override", "name":"plasma.power", "value":' + str(int(value)) + '}')

    def set_override_plasma_voltage(self, value: int):
        """Xxx..."""
        return self.__execute_request('{"set":"override", "name":"plasma.voltage", "value":' + str(int(value)) + '}')

    def set_override_spindle(self, value: int):
        """Xxx..."""
        return self.__execute_request('{"set":"override", "name":"spindle", "value":' + str(int(value)) + '}')

    def set_program_position_a(self, value: float):
        """Xxx..."""
        return self.__execute_request('{"set":"program.position", "data":{"a":' + str(value) + '}}')

    def set_program_position_b(self, value: float):
        """Xxx..."""
        return self.__execute_request('{"set":"program.position", "data":{"b":' + str(value) + '}}')

    def set_program_position_c(self, value: float):
        """Xxx..."""
        return self.__execute_request('{"set":"program.position", "data":{"c":' + str(value) + '}}')

    def set_program_position_x(self, value: float):
        """Xxx..."""
        return self.__execute_request('{"set":"program.position", "data":{"x":' + str(value) + '}}')

    def set_program_position_y(self, value: float):
        """Xxx..."""
        return self.__execute_request('{"set":"program.position", "data":{"y":' + str(value) + '}}')

    def set_program_position_z(self, value: float):
        """Xxx..."""
        return self.__execute_request('{"set":"program.position", "data":{"z":' + str(value) + '}}')

    def set_vm_geometry_info(self, values: list):
        """Xxx..."""
        try:
            if len(values) == 0:
                return False
            request = '{"set":"vm.geometry.info", "data":['
            for idx, value in enumerate(values):
                if not isinstance(value, APIVMGeometryInfo):
                    return False
                request = request + '{'
                request = request + '"name":"' + value.name + '",'
                request = request + '"x":' + str(value.x) + ','
                request = request + '"y":' + str(value.y) + ','
                request = request + '"z":' + str(value.z) + ','
                request = request + '"color":' + str(value.color) + ','
                request = request + '"scale":' + str(value.scale) + ','
                request = request + '"visible":' + str(value.visible).lower() + ','
                request = request + '"edges.angle":' + str(value.edges_angle) + ','
                request = request + '"edges.visible":' + str(value.edges_visible).lower()
                if idx < (len(values) - 1):
                    request = request + '},'
                else:
                    request = request + '}'
            request = request + ']}'
            return self.__execute_request(request)
        except:
            return False

    #
    # == END: public attributes

    # == BEG: non-public attributes
    #

    @staticmethod
    def __evaluate_response(response: str):
        try:
            if len(response) == 0:
                return False
            j = json.loads(response)
            if str(j['res']).lower() == 'true':
                return True
            return False
        except:
            return False

    def __execute_request(self, request: str):
        try:
            if self.is_connected is False:
                return False
            response = self.__send_command(request)
            return self.__evaluate_response(response)
        except:
            return False

    def __send_command(self, request: str):

        def __flush_receiving_buffer():
            try:
                self.ipc.settimeout(0.0)
                self.ipc.recv(1024)
            except:
                pass

        try:
            if self.is_connected is False:
                return ''
            l = len(request)
            if l == 0:
                return ''
            if request[l - 1] != b'\n':
                request = request + '\n'
            __flush_receiving_buffer()
            self.ipc.sendall(request.encode())
            self.ipc.settimeout(5)
            response = ''
            while True:
                data = self.ipc.recv(1)
                self.ipc.settimeout(1)
                if data in [b'\n']:
                    break
                response = response + str(data.decode())
            return response
        except socket.error:
            self.is_connected = False
            return ''

    #
    # == END: non-public attributes

class CncAPIInfoContext:
    """Service class for cnc api info context"""
    axes_info           = APIAxesInfo()
    cnc_info            = APICncInfo()
    compile_info        = APICompileInfo()
    enabled_commands    = APIEnabledCommands()

    def __init__(self, api):
        self.__api = api

    # == BEG: public attributes
    #

    def update(self) -> bool:
        """
        Update cnc api info context.

        :return                 False when the is no connection with the API server
        :rtype                  (bool)
        """
        if self.__api.is_connected is True:
            self.axes_info = self.__api.get_axes_info()
            self.cnc_info = self.__api.get_cnc_info()
            self.compile_info = self.__api.get_compile_info()
            self.enabled_commands = self.__api.get_enabled_commands()
            return True
        return False

    #
    # == END: public attributes
