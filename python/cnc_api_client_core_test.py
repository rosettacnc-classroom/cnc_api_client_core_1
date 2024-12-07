"""CNC API Client Core for RosettaCNC & derivated NC Systems Test."""
#-------------------------------------------------------------------------------
# Name:         cnc_api_client_core_test
#
# Purpose:      CNC API Client Core for RosettaCNC & derivated NC Systems Test
#
# Note          Compatible with API server version 1.5.1
#               1 (on 1.x.y) means interface contract
#               x (on 1.x.y) means version
#               y (on 1.x.y) means release
#
# Note          Checked with Python 3.11.7
#
# Note          Some data values or code are aligned to specified text columns to
#               simplify data identification during the update of the API client
#               to a newer version of the API server.
#
# Note          The use of generic exception raising and catching is intentional.
#               As a client, we are not concerned with logging the specific
#               exceptions that occur. Instead, our focus is on handling these
#               exceptions to maintain the desired execution flow within set
#               parameters.
#
# TO DO         To change the direct dict value recovery j[''][''] with j.get('')
#               to avoid exception when received response do not contains the
#               key:value. This permit to increase compatibility of API.
#
# Author:       support@rosettacnc.com
#
# Created:      29/11/2024
# Copyright:    RosettaCNC (c) 2016-2024
# Licence:      RosettaCNC License 1.0 (RCNC-1.0)
# Coding Style  https://www.python.org/dev/peps/pep-0008/
#-------------------------------------------------------------------------------
# _pylint: disable=C0103 -> invalid-name
# pylint: disable=C0116 -> missing-function-docstring
# pylint: disable=C0301 -> line-too-long
# _pylint: disable=C0302 -> too-many-lines
# _pylint: disable=R0902 -> too-many-instance-attributes
# _pylint: disable=R0903 -> too-few-public-methods
# _pylint: disable=R0904 -> too-many-public-methods
# _pylint: disable=R0911 -> too-many-return-statements
# _pylint: disable=R0912 -> too-many-branches
# _pylint: disable=R0915 -> too-many-statements
# _pylint: disable=W0702 -> bare-except
# _pylint: disable=W0719 -> broad-exception-raised           ## take care when you use that ##
#-------------------------------------------------------------------------------
import sys
import time
from datetime import datetime, timedelta

import numpy as np
import cnc_api_client_core as api

# == BEG: support methods
#

def log_command(command: str):
    print()
    print(command)
    print("=" * len(command))

def format_analog_values(values):
    formatted_lines = []
    for i in range(0, len(values), 8):
        line = ", ".join(f"{value:7.2f}" for value in values[i:i+8])
        formatted_lines.append(line)
    return "\n".join(formatted_lines)

def format_digital_values(values):
    formatted_lines = []
    for i in range(0, len(values), 8):
        line = ", ".join(f"{value:4d}" for value in values[i:i+8])
        formatted_lines.append(line)
    return "\n".join(formatted_lines)

#
# == END: support methods

# == BEG: API Server "cmd" requests
#

def eval_cmd_work_oder_add():
    log_command('CMD: WORK ORDER ADD')
    order_code = 'W_20240618_0001'
    order_data = api.APIWorkOrderDataForAdd()
    order_data.order_locked = False
    order_data.order_priority = api.WO_PR_HIGHEST
    order_data.job_order_code = 'J_00021234'
    order_data.customer_code = 'LABMEC srl'
    order_data.item_code = 'bridge structure'
    order_data.material_code = 'aluminium (H95)'
    order_data.order_notes = 'Use only aluminium tools!'
    order_data.use_deadline_datetime = True
    order_data.deadline_datetime = datetime(2024, 6, 19, 10, 20, 30)
    order_data.files[0].file_name = "W_0001.ngc"
    order_data.files[0].pieces_per_file = 5
    order_data.files[0].requested_pieces = 50
    order_data.files[2].file_name = "W_0003.ngc"
    order_data.files[2].pieces_per_file = 1
    order_data.files[2].requested_pieces = 10
    res = core.work_order_add(order_code, order_data)
    print('ADDED' if res else 'NOT ADDED')

def eval_cmd_work_order_delete():
    log_command('CMD: WORK ORDER DELETE')
    res = core.work_order_delete('W_20240618_0001')
    print('DELETED' if res else 'NOT DELETED')

#
# == END: API Server "cmd" requests

# == BEG: API Server "get" requests
#

def eval_get_analog_inputs():
    log_command('GET: ANALOG INPUTS')
    analog_inputs = core.get_analog_inputs()
    if not analog_inputs.has_data:
        print("No data available")
    else:
        print(format_analog_values(analog_inputs.value))

def eval_get_analog_outputs():
    log_command('GET: ANALOG OUTPUTS')
    analog_outputs = core.get_analog_outputs()
    if not analog_outputs.has_data:
        print("No data available")
    else:
        print(format_analog_values(analog_outputs.value))

def eval_get_axes_info():
    log_command('GET: AXES INFO')
    axes_info = core.get_axes_info()
    if not axes_info.has_data:
        print("No data available")
    else:
        print('joint_position                   =', axes_info.joint_position)
        print('machine_position                 =', axes_info.machine_position)
        print('program_position                 =', axes_info.program_position)
        print('machine_target_position          =', axes_info.machine_target_position)
        print('program_target_position          =', axes_info.program_target_position)
        print('actual_velocity                  =', axes_info.actual_velocity)
        print('working_wcs                      =', axes_info.working_wcs)
        print('working_offset                   =', axes_info.working_offset)
        print('dynamic_offset                   =', axes_info.dynamic_offset)
        print('homing_done                      =', axes_info.homing_done)
        print('homing_done_mask                 =', axes_info.homing_done_mask)

def eval_get_cnc_info():
    log_command('GET: CNC INFO')
    cnc_info = core.get_cnc_info()
    if not cnc_info.has_data:
        print("No data available")
    else:
        print('units_mode                       =', cnc_info.units_mode)
        print('axes_mask                        =', cnc_info.axes_mask)
        print('state_machine                    =', cnc_info.state_machine)
        print('gcode_line                       =', cnc_info.gcode_line)
        print('worked_time                      =', cnc_info.worked_time)
        print('hud_user_message                 =', cnc_info.hud_user_message)
        print('coolant_mist                     =', cnc_info.coolant_mist)
        print('coolant_flood                    =', cnc_info.coolant_flood)
        print('lube_axis_cycles_made            =', cnc_info.lube_axis_cycles_made)
        print('lube_axis_time_to_next_cycle     =', cnc_info.lube_axis_time_to_next_cycle)
        print('lube_spindle_cycles_made         =', cnc_info.lube_spindle_cycles_made)
        print('lube_spindle_time_to_next_cycle  =', cnc_info.lube_spindle_time_to_next_cycle)
        print('feed_programmed                  =', cnc_info.feed_programmed)
        print('feed_target                      =', cnc_info.feed_target)
        print('feed_reference                   =', cnc_info.feed_reference)
        print('spindle_programmed               =', cnc_info.spindle_programmed)
        print('spindle_target                   =', cnc_info.spindle_target)
        print('spindle_actual                   =', cnc_info.spindle_actual)
        print('spindle_load                     =', cnc_info.spindle_load)
        print('spindle_torque                   =', cnc_info.spindle_torque)
        print('spindle_direction                =', cnc_info.spindle_direction)
        print('spindle_not_ready                =', cnc_info.spindle_not_ready)
        print('spindle_shaft                    =', cnc_info.spindle_shaft)
        print('spindle_status                   =', cnc_info.spindle_status)
        print('spindle_voltage                  =', cnc_info.spindle_voltage)
        print('override_jog                     =', cnc_info.override_jog)
        print('override_jog_min                 =', cnc_info.override_jog_min)
        print('override_jog_max                 =', cnc_info.override_jog_max)
        print('override_jog_enabled             =', cnc_info.override_jog_enabled)
        print('override_jog_locked              =', cnc_info.override_jog_locked)
        print('override_spindle                 =', cnc_info.override_spindle)
        print('override_spindle_min             =', cnc_info.override_spindle_min)
        print('override_spindle_max             =', cnc_info.override_spindle_max)
        print('override_spindle_enabled         =', cnc_info.override_spindle_enabled)
        print('override_spindle_locked          =', cnc_info.override_spindle_locked)
        print('override_fast                    =', cnc_info.override_fast)
        print('override_fast_min                =', cnc_info.override_fast_min)
        print('override_fast_max                =', cnc_info.override_fast_max)
        print('override_fast_enabled            =', cnc_info.override_fast_enabled)
        print('override_fast_locked             =', cnc_info.override_fast_locked)
        print('override_feed                    =', cnc_info.override_feed)
        print('override_feed_min                =', cnc_info.override_feed_min)
        print('override_feed_max                =', cnc_info.override_feed_max)
        print('override_feed_enabled            =', cnc_info.override_feed_enabled)
        print('override_feed_locked             =', cnc_info.override_feed_locked)
        print('override_feed_custom_1           =', cnc_info.override_feed_custom_1)
        print('override_feed_custom_1_min       =', cnc_info.override_feed_custom_1_min)
        print('override_feed_custom_1_max       =', cnc_info.override_feed_custom_1_max)
        print('override_feed_custom_1_enabled   =', cnc_info.override_feed_custom_1_enabled)
        print('override_feed_custom_1_locked    =', cnc_info.override_feed_custom_1_locked)
        print('override_feed_custom_2           =', cnc_info.override_feed_custom_2)
        print('override_feed_custom_2_min       =', cnc_info.override_feed_custom_2_min)
        print('override_feed_custom_2_max       =', cnc_info.override_feed_custom_2_max)
        print('override_feed_custom_2_enabled   =', cnc_info.override_feed_custom_2_enabled)
        print('override_feed_custom_2_locked    =', cnc_info.override_feed_custom_2_locked)
        print('override_plasma_power            =', cnc_info.override_plasma_power)
        print('override_plasma_power_min        =', cnc_info.override_plasma_power_min)
        print('override_plasma_power_max        =', cnc_info.override_plasma_power_max)
        print('override_plasma_power_enabled    =', cnc_info.override_plasma_power_enabled)
        print('override_plasma_power_locked     =', cnc_info.override_plasma_power_locked)
        print('override_plasma_voltage          =', cnc_info.override_plasma_voltage)
        print('override_plasma_voltage_min      =', cnc_info.override_plasma_voltage_min)
        print('override_plasma_voltage_max      =', cnc_info.override_plasma_voltage_max)
        print('override_plasma_voltage_enabled  =', cnc_info.override_plasma_voltage_enabled)
        print('override_plasma_voltage_locked   =', cnc_info.override_plasma_voltage_locked)
        print('tool_id                          =', cnc_info.tool_id)
        print('tool_slot                        =', cnc_info.tool_slot)
        print('tool_slot_enabled                =', cnc_info.tool_slot_enabled)
        print('tool_type                        =', cnc_info.tool_type)
        print('tool_diameter                    =', cnc_info.tool_diameter)
        print('tool_offset_x                    =', cnc_info.tool_offset_x)
        print('tool_offset_y                    =', cnc_info.tool_offset_y)
        print('tool_offset_z                    =', cnc_info.tool_offset_z)
        print('tool_param_1                     =', cnc_info.tool_param_1)
        print('tool_param_2                     =', cnc_info.tool_param_2)
        print('tool_param_3                     =', cnc_info.tool_param_3)
        print('tool_description                 =', cnc_info.tool_description)

def eval_get_cnc_parameters():
    cnc_parameters = core.get_cnc_parameters(4000, 21)
    if not cnc_parameters.has_data:
        print("No data available")
    else:
        for i in range(len(cnc_parameters.values)):
            print(f'[{i}] = {cnc_parameters.values[i]:12.6f} : {cnc_parameters.descriptions[i]}')

def eval_get_compile_info():
    log_command('GET: COMPILE INFO')
    compile_info = core.get_compile_info()
    if not compile_info.has_data:
        print("No data available")
    else:
        print('code                             =', compile_info.code)
        print('code_line                        =', compile_info.code_line)
        print('file_line                        =', compile_info.file_line)
        print('file_name                        =', compile_info.file_name)
        print('message                          =', compile_info.message)
        print('state                            =', compile_info.state)

def eval_get_digital_inputs():
    log_command('GET: DIGITAL INPUTS')
    digital_inputs = core.get_digital_inputs()
    if not digital_inputs.has_data:
        print("No data available")
    else:
        print(format_digital_values(digital_inputs.value))

def eval_get_digital_outputs():
    log_command('GET: DIGITAL OUTPUTS')
    digital_outputs = core.get_digital_outputs()
    if not digital_outputs.has_data:
        print("No data available")
    else:
        print(format_digital_values(digital_outputs.value))

def eval_get_enabled_commands():
    log_command('GET: ENABLED COMMANDS')
    enabled_commands = core.get_enabled_commands()
    if not enabled_commands.has_data:
        print("No data available")
    else:
        print('cnc_continue                     =', enabled_commands.cnc_continue)
        print('cnc_homing                       =', enabled_commands.cnc_homing)
        print('cnc_jog_command                  =', enabled_commands.cnc_jog_command)
        print('cnc_mdi_command                  =', enabled_commands.cnc_mdi_command)
        print('cnc_parameters                   =', enabled_commands.cnc_parameters)
        print('cnc_pause                        =', enabled_commands.cnc_pause)
        print('cnc_resume                       =', enabled_commands.cnc_resume)
        print('cnc_resume_from_line             =', enabled_commands.cnc_resume_from_line)
        print('cnc_resume_from_point            =', enabled_commands.cnc_resume_from_point)
        print('cnc_start                        =', enabled_commands.cnc_start)
        print('cnc_start_from_line              =', enabled_commands.cnc_start_from_line)
        print('cnc_start_from_point             =', enabled_commands.cnc_start_from_point)
        print('cnc_stop                         =', enabled_commands.cnc_stop)
        print('program_analysis                 =', enabled_commands.program_analysis)
        print('program_analysis_abort           =', enabled_commands.program_analysis_abort)
        print('program_gcode_add_text           =', enabled_commands.program_gcode_add_text)
        print('program_gcode_clear              =', enabled_commands.program_gcode_clear)
        print('program_gcode_set_text           =', enabled_commands.program_gcode_set_text)
        print('program_load                     =', enabled_commands.program_load)
        print('program_new                      =', enabled_commands.program_new)
        print('program_save                     =', enabled_commands.program_save)
        print('program_save_as                  =', enabled_commands.program_save_as)
        print('reset_alarms                     =', enabled_commands.reset_alarms)
        print('reset_alarms_history             =', enabled_commands.reset_alarms_history)
        print('reset_warnings                   =', enabled_commands.reset_warnings)
        print('reset_warnings_history           =', enabled_commands.reset_warnings_history)
        print('set_program_position             =', enabled_commands.set_program_position)

def eval_get_machine_settings():
    log_command('GET: MACHINE SETTINGS')
    machine_settings = core.get_machine_settings()
    if not machine_settings.has_data:
        print("No data available")
    else:
        print(f'axis_machine_type       : {machine_settings.axis_machine_type}')
        print(f'axis_kinematics_model   : {machine_settings.axis_kinematics_model}')
        print(f'axis_x_type             : {machine_settings.axis_x_type}')
        print(f'axis_x_max_vel          : {machine_settings.axis_x_max_vel}')
        print(f'axis_x_acc              : {machine_settings.axis_x_acc}')
        print(f'axis_x_min_lim          : {machine_settings.axis_x_min_lim}')
        print(f'axis_x_max_lim          : {machine_settings.axis_x_max_lim}')
        print(f'axis_y_type             : {machine_settings.axis_y_type}')
        print(f'axis_y_max_vel          : {machine_settings.axis_y_max_vel}')
        print(f'axis_y_acc              : {machine_settings.axis_y_acc}')
        print(f'axis_y_min_lim          : {machine_settings.axis_y_min_lim}')
        print(f'axis_y_max_lim          : {machine_settings.axis_y_max_lim}')
        print(f'axis_z_type             : {machine_settings.axis_z_type}')
        print(f'axis_z_max_vel          : {machine_settings.axis_z_max_vel}')
        print(f'axis_z_acc              : {machine_settings.axis_z_acc}')
        print(f'axis_z_min_lim          : {machine_settings.axis_z_min_lim}')
        print(f'axis_z_max_lim          : {machine_settings.axis_z_max_lim}')
        print(f'axis_a_type             : {machine_settings.axis_a_type}')
        print(f'axis_a_max_vel          : {machine_settings.axis_a_max_vel}')
        print(f'axis_a_acc              : {machine_settings.axis_a_acc}')
        print(f'axis_a_min_lim          : {machine_settings.axis_a_min_lim}')
        print(f'axis_a_max_lim          : {machine_settings.axis_a_max_lim}')
        print(f'axis_b_type             : {machine_settings.axis_b_type}')
        print(f'axis_b_max_vel          : {machine_settings.axis_b_max_vel}')
        print(f'axis_b_acc              : {machine_settings.axis_b_acc}')
        print(f'axis_b_min_lim          : {machine_settings.axis_b_min_lim}')
        print(f'axis_b_max_lim          : {machine_settings.axis_b_max_lim}')
        print(f'axis_c_type             : {machine_settings.axis_c_type}')
        print(f'axis_c_max_vel          : {machine_settings.axis_c_max_vel}')
        print(f'axis_c_acc              : {machine_settings.axis_c_acc}')
        print(f'axis_c_min_lim          : {machine_settings.axis_c_min_lim}')
        print(f'axis_c_max_lim          : {machine_settings.axis_c_max_lim}')
        print(f'kinematics_h_x          : {machine_settings.kinematics_h_x}')
        print(f'kinematics_h_y          : {machine_settings.kinematics_h_y}')
        print(f'kinematics_h_z          : {machine_settings.kinematics_h_z}')
        print(f'kinematics_j_x          : {machine_settings.kinematics_j_x}')
        print(f'kinematics_j_y          : {machine_settings.kinematics_j_y}')
        print(f'kinematics_j_z          : {machine_settings.kinematics_j_z}')

def eval_get_machining_info():
    log_command('GET: MACHINING INFO')
    machining_info = core.get_machining_info()
    if not machining_info.has_data:
        print("No data available")
    else:
        print('tool_path_in_fast                =', machining_info.tool_path_in_fast)
        print('tool_path_in_feed                =', machining_info.tool_path_in_feed)
        print('total_path                       =', machining_info.total_path)
        print('planned_time                     =', machining_info.planned_time)
        if not machining_info.used_tool:
            print('used_tool                        =', machining_info.used_tool)
        else:
            for i in range(len(machining_info.used_tool)):
                used_tool_info = machining_info.used_tool[i]
                print(f'used_tool[{i}].tool_id             =', used_tool_info.tool_id)
                print(f'used_tool[{i}].in_fast             =', used_tool_info.in_fast)
                print(f'used_tool[{i}].in_feed             =', used_tool_info.in_feed)
        print('tcp_extents_in_fast_min_x        =', machining_info.tcp_extents_in_fast_min_x)
        print('tcp_extents_in_fast_min_y        =', machining_info.tcp_extents_in_fast_min_y)
        print('tcp_extents_in_fast_min_z        =', machining_info.tcp_extents_in_fast_min_z)
        print('tcp_extents_in_fast_max_x        =', machining_info.tcp_extents_in_fast_max_x)
        print('tcp_extents_in_fast_max_y        =', machining_info.tcp_extents_in_fast_max_y)
        print('tcp_extents_in_fast_max_z        =', machining_info.tcp_extents_in_fast_max_z)
        print('tcp_extents_in_fast_length_x     =', machining_info.tcp_extents_in_fast_length_x)
        print('tcp_extents_in_fast_length_y     =', machining_info.tcp_extents_in_fast_length_y)
        print('tcp_extents_in_fast_length_z     =', machining_info.tcp_extents_in_fast_length_z)
        print('tcp_extents_in_feed_min_x        =', machining_info.tcp_extents_in_feed_min_x)
        print('tcp_extents_in_feed_min_y        =', machining_info.tcp_extents_in_feed_min_y)
        print('tcp_extents_in_feed_min_z        =', machining_info.tcp_extents_in_feed_min_z)
        print('tcp_extents_in_feed_max_x        =', machining_info.tcp_extents_in_feed_max_x)
        print('tcp_extents_in_feed_max_y        =', machining_info.tcp_extents_in_feed_max_y)
        print('tcp_extents_in_feed_max_z        =', machining_info.tcp_extents_in_feed_max_z)
        print('tcp_extents_in_feed_length_x     =', machining_info.tcp_extents_in_feed_length_x)
        print('tcp_extents_in_feed_length_y     =', machining_info.tcp_extents_in_feed_length_y)
        print('tcp_extents_in_feed_length_z     =', machining_info.tcp_extents_in_feed_length_z)
        print('joints_in_fast_min_x             =', machining_info.joints_in_fast_min_x)
        print('joints_in_fast_min_y             =', machining_info.joints_in_fast_min_y)
        print('joints_in_fast_min_z             =', machining_info.joints_in_fast_min_z)
        print('joints_in_fast_min_a             =', machining_info.joints_in_fast_min_a)
        print('joints_in_fast_min_b             =', machining_info.joints_in_fast_min_b)
        print('joints_in_fast_min_c             =', machining_info.joints_in_fast_min_c)
        print('joints_in_fast_max_x             =', machining_info.joints_in_fast_max_x)
        print('joints_in_fast_max_y             =', machining_info.joints_in_fast_max_y)
        print('joints_in_fast_max_z             =', machining_info.joints_in_fast_max_z)
        print('joints_in_fast_max_a             =', machining_info.joints_in_fast_max_a)
        print('joints_in_fast_max_b             =', machining_info.joints_in_fast_max_b)
        print('joints_in_fast_max_c             =', machining_info.joints_in_fast_max_c)
        print('joints_in_fast_length_x          =', machining_info.joints_in_fast_length_x)
        print('joints_in_fast_length_y          =', machining_info.joints_in_fast_length_y)
        print('joints_in_fast_length_z          =', machining_info.joints_in_fast_length_z)
        print('joints_in_fast_length_a          =', machining_info.joints_in_fast_length_a)
        print('joints_in_fast_length_b          =', machining_info.joints_in_fast_length_b)
        print('joints_in_fast_length_c          =', machining_info.joints_in_fast_length_c)
        print('joints_in_feed_min_x             =', machining_info.joints_in_feed_min_x)
        print('joints_in_feed_min_y             =', machining_info.joints_in_feed_min_y)
        print('joints_in_feed_min_z             =', machining_info.joints_in_feed_min_z)
        print('joints_in_feed_min_a             =', machining_info.joints_in_feed_min_a)
        print('joints_in_feed_min_b             =', machining_info.joints_in_feed_min_b)
        print('joints_in_feed_min_c             =', machining_info.joints_in_feed_min_c)
        print('joints_in_feed_max_x             =', machining_info.joints_in_feed_max_x)
        print('joints_in_feed_max_y             =', machining_info.joints_in_feed_max_y)
        print('joints_in_feed_max_z             =', machining_info.joints_in_feed_max_z)
        print('joints_in_feed_max_a             =', machining_info.joints_in_feed_max_a)
        print('joints_in_feed_max_b             =', machining_info.joints_in_feed_max_b)
        print('joints_in_feed_max_c             =', machining_info.joints_in_feed_max_c)
        print('joints_in_feed_length_x          =', machining_info.joints_in_feed_length_x)
        print('joints_in_feed_length_y          =', machining_info.joints_in_feed_length_y)
        print('joints_in_feed_length_z          =', machining_info.joints_in_feed_length_z)
        print('joints_in_feed_length_a          =', machining_info.joints_in_feed_length_a)
        print('joints_in_feed_length_b          =', machining_info.joints_in_feed_length_b)
        print('joints_in_feed_length_c          =', machining_info.joints_in_feed_length_c)

def eval_get_programmed_points():
    log_command('GET: PROGRAMMED POINTS')
    programmed_points = core.get_programmed_points()
    if not programmed_points.has_data:
        print("No data available")
    else:
        print(programmed_points.points)

def eval_get_scanning_laser_info():
    log_command('GET: SCANNING LASER INFO')
    scaning_laser_info = core.get_scanning_laser_info()
    if not scaning_laser_info.has_data:
        print("No data available")
    else:
        print('laser_out_bit                    =', scaning_laser_info.laser_out_bit)
        print('laser_out_umf                    =', scaning_laser_info.laser_out_umf)
        print('laser_h_measure                  =', scaning_laser_info.laser_h_measure)
        print('laser_mcs_x_position             =', scaning_laser_info.laser_mcs_x_position)
        print('laser_mcs_y_position             =', scaning_laser_info.laser_mcs_y_position)
        print('laser_mcs_z_position             =', scaning_laser_info.laser_mcs_z_position)

def eval_get_system_info():
    log_command('GET: SYSTEM INFO')
    system_info = core.get_system_info()
    if not system_info.has_data:
        print("No data available")
    else:
        print('machine_name                     =', system_info.machine_name)
        print('control_software_version         =', system_info.control_software_version)
        print('core_version                     =', system_info.core_version)
        print('api_server_version               =', system_info.api_server_version)
        print('firmware_version                 =', system_info.firmware_version)
        print('firmware_version_tag             =', system_info.firmware_version_tag)
        print('firmware_interface_level         =', system_info.firmware_interface_level)
        print('order_code                       =', system_info.order_code)
        print('customer_id                      =', system_info.customer_id)
        print('serial_number                    =', system_info.serial_number)
        print('part_number                      =', system_info.part_number)
        print('customization_number             =', system_info.customization_number)
        print('hardware_version                 =', system_info.hardware_version)
        print('operative_system                 =', system_info.operative_system)
        print('operative_system_crc             =', system_info.operative_system_crc)
        print('pld_version                      =', system_info.pld_version)

def eval_get_tools_info():
    log_command('GET: TOOLS INFO')
    tools_info = core.get_tools_info()
    if not tools_info.has_data:
        print("No data available")
    else:
        print('slot_enabled                     =', tools_info.slot_enabled)
        print('tools                            =', len(tools_info.data))
        if tools_info.data:
            print('  --------------------------------')
            for tool_info in tools_info.data:
                print('  tool_id                        =', tool_info.tool_id)
                print('  tool_slot                      =', tool_info.tool_slot)
                print('  tool_type                      =', tool_info.tool_type)
                print('  tool_diameter                  =', tool_info.tool_diameter)
                print('  tool_offset_x                  =', tool_info.tool_offset_x)
                print('  tool_offset_y                  =', tool_info.tool_offset_y)
                print('  tool_offset_z                  =', tool_info.tool_offset_z)
                print('  tool_param_1                   =', tool_info.tool_param_1)
                print('  tool_param_2                   =', tool_info.tool_param_2)
                print('  tool_param_3                   =', tool_info.tool_param_3)
                print('  tool_param_4                   =', tool_info.tool_param_4)
                print('  tool_param_5                   =', tool_info.tool_param_5)
                print('  tool_param_6                   =', tool_info.tool_param_6)
                print('  tool_param_7                   =', tool_info.tool_param_7)
                print('  tool_param_8                   =', tool_info.tool_param_8)
                print('  tool_param_9                   =', tool_info.tool_param_9)
                print('  tool_param_10                  =', tool_info.tool_param_10)
                print('  tool_param_51                  =', tool_info.tool_param_51)
                print('  tool_param_52                  =', tool_info.tool_param_52)
                print('  tool_param_53                  =', tool_info.tool_param_53)
                print('  tool_param_54                  =', tool_info.tool_param_54)
                print('  tool_param_55                  =', tool_info.tool_param_55)
                print('  tool_param_56                  =', tool_info.tool_param_56)
                print('  tool_param_57                  =', tool_info.tool_param_57)
                print('  tool_param_58                  =', tool_info.tool_param_58)
                print('  tool_param_59                  =', tool_info.tool_param_59)
                print('  tool_param_60                  =', tool_info.tool_param_60)
                print('  tool_description               =', tool_info.tool_description)
                print('  --------------------------------')


"""

log_command('GET: GEOMETRY INFO')
geometry_info = core.get_vm_geometry_info(['f-y-screw', 'x-structure'])
if not geometry_info:
    print("No data available")
else:
    for i in range(len(geometry_info)):
        info = geometry_info[i]
        j = f'{i:3d}'
        print(f'  [{j}].name                     =', info.name)
        print(f'  [{j}].x                        =', info.x)
        print(f'  [{j}].y                        =', info.y)
        print(f'  [{j}].z                        =', info.z)
        print(f'  [{j}].color                    =', info.color)
        print(f'  [{j}].scale                    =', info.scale)
        print(f'  [{j}].visible                  =', info.visible)
        print(f'  [{j}].edge_angle               =', info.edges_angle)
        print(f'  [{j}].edges_visible            =', info.edges_visible)
        print('  --------------------------------')
"""

def eval_get_work_info():
    log_command('GET: WORK INFO')
    work_info = core.get_work_info()
    if not work_info.has_data:
        print("No data available")
    else:
        print('work_mode                        =', work_info.work_mode)
        print('active_work_order_code           =', work_info.active_work_order_code)
        print('active_work_order_file_index     =', work_info.active_work_order_file_index)
        print('file_name                        =', work_info.file_name)
        print('planned_time                     =', work_info.planned_time)
        print('worked_time                      =', work_info.worked_time)

def eval_get_work_order_code_list():
    log_command('GET: WORK ORDER CODE LIST')
    work_order_code = ''
    work_order_code_list = core.get_work_order_code_list()
    if work_order_code_list.has_data:
        for i in range(len(work_order_code_list.data)):
            if i == 0:
                work_order_code = work_order_code_list.data[i].order_code
            print('work order #', i + 1)
            print('  order_code                     =', work_order_code_list.data[i].order_code)
            print('  order_state                    =', work_order_code_list.data[i].order_state)
            print('  revision_number                =', work_order_code_list.data[i].revision_number)

def eval_get_work_order_data():
    log_command('GET: WORK ORDER DATA (FIRST IN THE LIST)')
    work_order_code_list = core.get_work_order_code_list()
    if not work_order_code_list.has_data:
        return
    if len(work_order_code_list.data) == 0:
        return
    work_order_code = work_order_code_list.data[0].order_code
    work_order_data = core.get_work_order_data(work_order_code, 0)
    if work_order_data.has_data:
        print('revision_number                  =', work_order_data.revision_number)
        print('order_state                      =', work_order_data.order_state)
        print('order_locked                     =', work_order_data.order_locked)
        print('order_code                       =', work_order_data.order_code)
        print('order_priority                   =', work_order_data.order_priority)
        print('job_order_code                   =', work_order_data.job_order_code)
        print('customer_code                    =', work_order_data.customer_code)
        print('item_code                        =', work_order_data.item_code)
        print('material_code                    =', work_order_data.material_code)
        print('order_notes                      =', work_order_data.order_notes)
        for i in range(8):
            print('file', i + 1)
            print('  file_name                      =', work_order_data.files[i].file_name)
            print('  file_state                     =', work_order_data.files[i].file_state)
            print('  pieces per file                =', work_order_data.files[i].pieces_per_file)
            print('  requested_pieces               =', work_order_data.files[i].requested_pieces)
            print('  produced_pieces                =', work_order_data.files[i].produced_pieces)
            print('  discarded_pieces               =', work_order_data.files[i].discarded_pieces)
        print('use_deadline_datetime            =', work_order_data.use_deadline_datetime)
        print('creation_datetime                =', work_order_data.creation_datetime)
        print('deadline_datetime                =', work_order_data.deadline_datetime)
        print('reception_datetime               =', work_order_data.reception_datetime)
        print('acceptance_datetime              =', work_order_data.acceptance_datetime)
        print('begin_datetime                   =', work_order_data.begin_datetime)
        print('end_datetime                     =', work_order_data.end_datetime)
        print('archived_datetime                =', work_order_data.archived_datetime)
        print('time_for_setup                   =', work_order_data.time_for_setup)
        print('time_for_idle                    =', work_order_data.time_for_idle)
        print('time_for_work                    =', work_order_data.time_for_work)
        print('time_total                       =', work_order_data.time_total)
        print('operator_notes                   =', work_order_data.operator_notes)
        for i in range(len(work_order_data.log_items)):
            print('log item', i + 1)
            print('  log_id                         =', work_order_data.log_items[i].log_id)
            print('  log_datetime                   =', work_order_data.log_items[i].log_datetime)
            print('  log_info_1                     =', work_order_data.log_items[i].log_info_1)
            print('  log_info_2                     =', work_order_data.log_items[i].log_info_2)

def eval_get_work_order_file_list():
    log_command('GET: WORK ORDER FILE LIST')
    work_order_file_list = core.get_work_order_file_list(path="backup", file_filter="")
    if not work_order_file_list.has_data:
        print("No data available")
    else:
        print('file founds                      =', len(work_order_file_list.files))
        for i in range(len(work_order_file_list.files)):
            print('file #', i + 1)
            print('  type                           =', work_order_file_list.files[i].type)
            print('  name                           =', work_order_file_list.files[i].name)
            print('  size                           =', work_order_file_list.files[i].size)
            print('  creation_datetime              =', work_order_file_list.files[i].creation_datetime)
            print('  last_access_datetime           =', work_order_file_list.files[i].last_access_datetime)
            print('  last_write_datetime            =', work_order_file_list.files[i].last_write_datetime)

#
# == END: API Server "get" requests

# == BEG: API Server "set" requests
#

def eval_set_cnc_parameters():
    log_command('GET: CNC PARAMETERS')
    values = [
        0,
        0,
        3,
        30,
        30,
        165,
        40,
        190,
        158.651,
        0,
        0,
        36.188,
        40.018,
        152.029,
        78.186,
        150.021,
        175.905,
        0,
        0,
        1,
        24
    ]
    descriptions    = [
        'VISION CAMERA: Camera Offset from Spindle X',
        'VISION CAMERA: Camera Offset from Spindle Y',
        'VISION CAMERA: Marker Mode',
        'VISION CAMERA: Marker Position 01 X',
        'VISION CAMERA: Marker Position 01 Y',
        'VISION CAMERA: Marker Position 02 X',
        'VISION CAMERA: Marker Position 02 Y',
        'VISION CAMERA: Marker Position 03 X',
        'VISION CAMERA: Marker Position 03 Y',
        'VISION CAMERA: Marker Position 04 X',
        'VISION CAMERA: Marker Position 04 Y',
        'VISION CAMERA: Actual Marker Position 01 X',
        'VISION CAMERA: Actual Marker Position 01 Y',
        'VISION CAMERA: Actual Marker Position 02 X',
        'VISION CAMERA: Actual Marker Position 02 Y',
        'VISION CAMERA: Actual Marker Position 03 X',
        'VISION CAMERA: Actual Marker Position 03 Y',
        'VISION CAMERA: Actual Marker Position 04 X',
        'VISION CAMERA: Actual Marker Position 04 Y',
        'VISION CAMERA: Enable GCode Scaling Compensation',
        'VISION CAMERA: Find Markers Acquiring ID'
    ]
    res = core.set_cnc_parameters(4000, values, descriptions)
    print(f'set = {res}')

def eval_set_override():
    log_command('SET: OVERRIDE')
    cnc_info = core.get_cnc_info()
    if not cnc_info.has_data:
        print("No data available")
    else:
        def check_override_range_by_name(name: str, delay:int = 0.01):
            """This check iterate all values from min to max with an extra value before min and max to verify limits."""
            print(f'- check {name}')
            ovr_min = getattr(cnc_info, f'override_{name}_min')
            ovr_max = getattr(cnc_info, f'override_{name}_max')
            call_m = getattr(core, f'set_override_{name}', None)
            for value in range(ovr_min - 1, ovr_max + 2):
                res = call_m(value)
                print(f'   {value:3} = {res}')
                time.sleep(delay)

        check_override_range_by_name('jog')
        check_override_range_by_name('spindle')
        check_override_range_by_name('fast')
        check_override_range_by_name('feed')
        check_override_range_by_name('feed_custom_1')
        check_override_range_by_name('feed_custom_2')
        check_override_range_by_name('plasma_power')
        check_override_range_by_name('plasma_voltage')

def eval_set_program_position():
    log_command('SET: POSITION')
    machine_settings = core.get_machine_settings()
    if not machine_settings.has_data:
        print("No data available")
    else:
        def check_set_position_by_name(name: str, delay:int = 0.1):
            """This check iterate some values from min to max."""
            print(f'- check set_program_position_{name}')
            axis_type = getattr(machine_settings, f'axis_{name}_type')
            if axis_type not in [api.AT_LINEAR, api.AT_ROTARY_FREE, api.AT_ROTARY_HEAD, api.AT_ROTARY_TABLE]:
                print('   axis not enabled to request')
                return
            axis_min_lim = getattr(machine_settings, f'axis_{name}_min_lim')
            axis_max_lim = getattr(machine_settings, f'axis_{name}_max_lim')
            call_m = getattr(core, f'set_program_position_{name}', None)
            steps = np.linspace(axis_min_lim, axis_max_lim, 10)
            for value in steps:
                res = call_m(value)
                print(f'   {value:12.4f} = {res}')
                time.sleep(delay)

        check_set_position_by_name('x')
        check_set_position_by_name('y')
        check_set_position_by_name('z')
        check_set_position_by_name('a')
        check_set_position_by_name('b')
        check_set_position_by_name('c')

def eval_set_work_order_data():
    log_command('SET: WORK ORDER DATA')
    data = api.APIWorkOrderDataForSet()
    #data.order_state = api.WO_ST_RELEASED
    data.order_locked = True
    data.order_priority = api.WO_PR_HIGH
    data.job_order_code = 'job order code'
    data.customer_code = 'customer code'
    data.item_code = 'item code'
    data.material_code = 'material code'
    data.order_notes = 'order notes'
    data.files[0].file_name = 'W_0001.ngc'
    data.files[0].requested_pieces = 2
    data.files[0].pieces_per_file = 1
    data.files[1].file_name = 'W_0002.ngc'
    data.files[1].requested_pieces = 4
    data.files[1].pieces_per_file = 2
    data.files[2].file_name = 'W_0003.ngc'
    data.files[2].requested_pieces = 8
    data.files[2].pieces_per_file = 4
    data.files[3].file_name = 'W_0004.ngc'
    data.files[3].requested_pieces = 10
    data.files[3].pieces_per_file = 5
    data.files[4].file_name = 'W_0005.ngc'
    data.files[4].requested_pieces = 12
    data.files[4].pieces_per_file = 6
    data.files[5].file_name = 'W_0006.ngc'
    data.files[5].requested_pieces = 14
    data.files[5].pieces_per_file = 7
    data.files[6].file_name = 'W_0007.ngc'
    data.files[6].requested_pieces = 16
    data.files[6].pieces_per_file = 8
    data.files[7].file_name = 'W_0008.ngc'
    data.files[7].requested_pieces = 18
    data.files[7].pieces_per_file = 9

    res = core.work_order_delete("test")
    print(f' deletion of work order test: {res}')
    time.sleep(4)
    res = core.work_order_add("test")
    print(f' creation of work order test: {res}')
    time.sleep(4)
    res = core.set_work_order_data("test", data)
    print(f' set data of work order test: {res}')


#
# == BEG: API Server "set" requests

# get and check connection with API Server
core = api.CncAPIClientCore()
core.connect('127.0.0.1', 8000)
if not core.is_connected:
    print("No connection with API Server")
    sys.exit()

eval_cmd_work_oder_add()
time.sleep(2)
eval_cmd_work_order_delete()

eval_get_analog_inputs()
eval_get_analog_outputs()
eval_get_axes_info()
eval_get_cnc_info()
eval_get_cnc_parameters()
eval_get_compile_info()
eval_get_digital_inputs()
eval_get_digital_outputs()
eval_get_enabled_commands()
eval_get_machine_settings()
eval_get_machining_info()
eval_get_programmed_points()
eval_get_scanning_laser_info()
eval_get_system_info()
eval_get_tools_info()
eval_get_work_info()
eval_get_work_order_code_list()
eval_get_work_order_data()
eval_get_work_order_file_list()

eval_set_cnc_parameters()
eval_set_override()
eval_set_program_position()
eval_set_work_order_data()
