# API Client Coverage

Analysis generated from the full Python project (`api_client_qt_demo.zip`).

## Scope

- Source analyzed: all `.py` files in the demo project zip.
- Main focus: `CncAPIClientCore` public methods and `APIxxxx` data structures.
- Indirect usage through `CncAPIInfoContext` is included as project coverage.
- For direct method parameters, coverage means the argument is explicitly supplied in project calls. When a method is called without supplying a parameter that has a default value, it is marked as `no [default]`.
- For `APIxxxx` classes, coverage means a field is actually read from a response object or written into a request object somewhere in the project.

## Summary

- Public methods in `CncAPIClientCore`: **96**
- Methods used in the project: **61**
- Methods not used in the project: **35**
- API data classes found: **35**
- API data classes with at least one covered field: **8**

## Method coverage

| Method | Status | Calls | Parameter coverage | Return type |
|---|---:|---:|---|---|
| `close` | used | 9 | n/a | `bool/other` |
| `cnc_change_function_state_mode` | used | 9 | name=yes(pos); mode=yes(pos) | `bool/other` |
| `cnc_connection_close` | used | 1 | n/a | `bool/other` |
| `cnc_connection_open` | used | 1 | use_ui=yes(kw); use_fast_mode=yes(kw); skip_firmware_check=yes(kw); overwrite_cnc_settings=yes(kw) | `bool/other` |
| `cnc_continue` | used | 2 | n/a | `bool/other` |
| `cnc_homing` | used | 7 | axes_mask=yes(pos) | `bool/other` |
| `cnc_jog_command` | used | 14 | command=yes(pos) | `bool/other` |
| `cnc_mdi_command` | used | 1 | command=yes(pos) | `bool/other` |
| `cnc_pause` | used | 2 | n/a | `bool/other` |
| `cnc_resume` | used | 2 | line=yes(pos) | `bool/other` |
| `cnc_resume_from_line` | used | 1 | line=yes(pos) | `bool/other` |
| `cnc_resume_from_point` | not used | 0 | point=no | `bool/other` |
| `cnc_start` | used | 2 | n/a | `bool/other` |
| `cnc_start_from_line` | used | 1 | line=yes(pos) | `bool/other` |
| `cnc_start_from_point` | not used | 0 | point=no | `bool/other` |
| `cnc_stop` | used | 3 | n/a | `bool/other` |
| `connect` | used | 18 | host=yes(pos); port=yes(pos); use_ssl=yes(pos) | `bool/other` |
| `connect_direct` | not used | 0 | n/a | `bool/other` |
| `create_compact_json_request` | not used | 0 | n/a | `bool/other` |
| `datetime_to_filetime` | not used | 0 | n/a | `bool/other` |
| `get_alarms_current_list` | used | 1 | n/a | `APIAlarmsWarningsList` |
| `get_alarms_history_list` | used | 1 | n/a | `APIAlarmsWarningsList` |
| `get_analog_inputs` | not used | 0 | n/a | `APIAnalogInputs` |
| `get_analog_outputs` | not used | 0 | n/a | `APIAnalogOutputs` |
| `get_axes_info` | used | 2 | n/a | `APIAxesInfo` |
| `get_cnc_info` | used | 3 | n/a | `APICncInfo` |
| `get_cnc_parameters` | not used | 0 | address=no; elements=no | `APICncParameters` |
| `get_compile_info` | used | 2 | n/a | `APICompileInfo` |
| `get_coordinate_systems_info` | used | 1 | n/a | `APICoordinateSystemsInfo` |
| `get_digital_inputs` | not used | 0 | n/a | `APIDigitalInputs` |
| `get_digital_outputs` | not used | 0 | n/a | `APIDigitalOutputs` |
| `get_enabled_commands` | used | 2 | n/a | `APIEnabledCommands` |
| `get_localization_info` | not used | 0 | n/a | `APILocalizationInfo` |
| `get_machine_settings` | not used | 0 | n/a | `APIMachineSettings` |
| `get_machining_info` | used | 1 | n/a | `APIMachiningInfo` |
| `get_operator_request` | used | 1 | n/a | `APIOperatorRequest` |
| `get_program_info` | used | 1 | n/a | `APIProgramInfo` |
| `get_programmed_points` | not used | 0 | n/a | `APIProgrammedPoints` |
| `get_scanning_laser_info` | used | 1 | n/a | `APIScanningLaserInfo` |
| `get_system_info` | used | 1 | n/a | `APISystemInfo` |
| `get_tools_lib_count` | not used | 0 | n/a | `APIToolsLibCount` |
| `get_tools_lib_info` | not used | 0 | index=no | `APIToolsLibInfo` |
| `get_tools_lib_infos` | not used | 0 | n/a | `APIToolsLibInfos` |
| `get_tools_lib_tool_index_from_id` | not used | 0 | tool_id=no | `APIToolsLibToolIndexFromId` |
| `get_vm_geometry_info` | not used | 0 | names=no | `bool/other` |
| `get_warnings_current_list` | used | 1 | n/a | `APIAlarmsWarningsList` |
| `get_warnings_history_list` | used | 1 | n/a | `APIAlarmsWarningsList` |
| `get_work_info` | not used | 0 | n/a | `APIWorkInfo` |
| `get_work_order_code_list` | not used | 0 | n/a | `APIWorkOrderCodeList` |
| `get_work_order_data` | not used | 0 | order_code=no; mode=no | `APIWorkOrderDataForGet` |
| `get_work_order_file_list` | not used | 0 | path=no; file_filter=no | `APIWorkOrderFileList` |
| `log_add` | not used | 0 | text=no | `bool/other` |
| `program_analysis` | used | 5 | mode=yes(pos) | `bool/other` |
| `program_analysis_abort` | used | 1 | n/a | `bool/other` |
| `program_gcode_add_text` | used | 1 | text=yes(pos) | `bool/other` |
| `program_gcode_clear` | not used | 0 | n/a | `bool/other` |
| `program_gcode_set_text` | used | 2 | text=yes(pos) | `bool/other` |
| `program_load` | used | 1 | file_name=yes(pos) | `bool/other` |
| `program_new` | used | 1 | n/a | `bool/other` |
| `program_save` | used | 1 | n/a | `bool/other` |
| `program_save_as` | used | 1 | file_name=yes(pos) | `bool/other` |
| `reset_alarms` | used | 1 | n/a | `bool/other` |
| `reset_alarms_history` | used | 1 | n/a | `bool/other` |
| `reset_warnings` | used | 1 | n/a | `bool/other` |
| `reset_warnings_history` | used | 1 | n/a | `bool/other` |
| `set_cnc_parameters` | not used | 0 | address=no; values=no; descriptions=no | `bool/other` |
| `set_localization` | not used | 0 | units_mode=no; locale_name=no | `bool/other` |
| `set_operator_response` | used | 4 | response=yes(pos) | `bool/other` |
| `set_override_fast` | used | 1 | value=yes(pos) | `bool/other` |
| `set_override_feed` | used | 1 | value=yes(pos) | `bool/other` |
| `set_override_feed_custom_1` | used | 1 | value=yes(pos) | `bool/other` |
| `set_override_feed_custom_2` | used | 1 | value=yes(pos) | `bool/other` |
| `set_override_jog` | used | 1 | value=yes(pos) | `bool/other` |
| `set_override_plasma_power` | used | 1 | value=yes(pos) | `bool/other` |
| `set_override_plasma_voltage` | used | 1 | value=yes(pos) | `bool/other` |
| `set_override_spindle` | used | 1 | value=yes(pos) | `bool/other` |
| `set_program_position_a` | used | 1 | value=yes(pos) | `bool/other` |
| `set_program_position_b` | used | 1 | value=yes(pos) | `bool/other` |
| `set_program_position_c` | used | 1 | value=yes(pos) | `bool/other` |
| `set_program_position_x` | used | 1 | value=yes(pos) | `bool/other` |
| `set_program_position_x_with_laser_reference` | used | 1 | value=no [default] | `bool/other` |
| `set_program_position_y` | used | 1 | value=yes(pos) | `bool/other` |
| `set_program_position_y_with_laser_reference` | used | 1 | value=no [default] | `bool/other` |
| `set_program_position_z` | used | 1 | value=yes(pos) | `bool/other` |
| `set_program_position_z_with_laser_reference` | used | 1 | value=no [default]; sample_count=no [default] | `bool/other` |
| `set_tools_lib_info` | not used | 0 | info=no | `bool/other` |
| `set_vm_geometry_info` | not used | 0 | values=no | `bool/other` |
| `set_wcs_info` | used | 1 | wcs=yes(pos); offset=yes(pos); activate=yes(kw) | `bool/other` |
| `set_work_order_data` | not used | 0 | order_code=no; data=no | `bool/other` |
| `show_ui_dialog` | used | 12 | uid_id=yes(pos) | `bool/other` |
| `tools_lib_add` | not used | 0 | info=no | `bool/other` |
| `tools_lib_clear` | not used | 0 | n/a | `bool/other` |
| `tools_lib_delete` | not used | 0 | index=no | `bool/other` |
| `tools_lib_insert` | not used | 0 | info=no | `bool/other` |
| `work_order_add` | not used | 0 | order_code=no; data=no | `bool/other` |
| `work_order_delete` | not used | 0 | order_code=no | `bool/other` |

## API data structure field coverage

| API class | Fields | Related to | Covered fields | Unused fields |
|---|---:|---|---|---|
| `APIAlarmsWarningsList` | 1 | return of get_alarms_current_list(), return of get_alarms_history_list(), return of get_warnings_current_list(), return of get_warnings_history_list() | list | - |
| `APIAnalogInputs` | 2 | return of get_analog_inputs() | - | has_data, value |
| `APIAnalogOutputs` | 2 | return of get_analog_outputs() | - | has_data, value |
| `APIAxesInfo` | 15 | return of get_axes_info() | - | actual_velocity, dynamic_offset, has_data, homing_correction_space, homing_done, homing_done_mask, homing_running_mask, homing_sensors_mask, joint_position, machine_position, machine_target_position, program_position, program_target_position, working_offset, working_wcs |
| `APICncInfo` | 92 | return of get_cnc_info() | has_data | aux_outputs, axes_mask, coolant_flood, coolant_mist, current_alarm_code, current_alarm_datetime, current_alarm_info1, current_alarm_info2, current_alarm_text, current_warning_code, current_warning_datetime, current_warning_info1, current_warning_info2, current_warning_text, feed_programmed, feed_reference, feed_target, gcode_line, hud_user_message, lube_axis_cycles_made, lube_axis_time_to_next_cycle, lube_spindle_cycles_made, lube_spindle_time_to_next_cycle, operator_request_id_pending, override_fast, override_fast_enabled, override_fast_locked, override_fast_max, override_fast_min, override_feed, override_feed_custom_1, override_feed_custom_1_enabled, override_feed_custom_1_locked, override_feed_custom_1_max, override_feed_custom_1_min, override_feed_custom_2, override_feed_custom_2_enabled, override_feed_custom_2_locked, override_feed_custom_2_max, override_feed_custom_2_min, override_feed_enabled, override_feed_locked, override_feed_max, override_feed_min, override_jog, override_jog_enabled, override_jog_locked, override_jog_max, override_jog_min, override_plasma_power, override_plasma_power_enabled, override_plasma_power_locked, override_plasma_power_max, override_plasma_power_min, override_plasma_voltage, override_plasma_voltage_enabled, override_plasma_voltage_locked, override_plasma_voltage_max, override_plasma_voltage_min, override_spindle, override_spindle_enabled, override_spindle_locked, override_spindle_max, override_spindle_min, planned_time, spindle_actual, spindle_direction, spindle_load, spindle_not_ready, spindle_phase, spindle_programmed, spindle_shaft, spindle_status, spindle_target, spindle_torque, spindle_voltage, state_machine, tool_description, tool_diameter, tool_id, tool_offset_x, tool_offset_y, tool_offset_z, tool_param_1, tool_param_2, tool_param_3, tool_slot, tool_slot_enabled, tool_type, units_mode, worked_time |
| `APICncParameters` | 4 | return of get_cnc_parameters() | - | address, descriptions, has_data, values |
| `APICompileInfo` | 7 | return of get_compile_info() | - | code, code_line, file_line, file_name, has_data, message, state |
| `APICoordinateSystemsInfo` | 12 | return of get_coordinate_systems_info() | has_data, working_offset, working_wcs | wcs_1, wcs_2, wcs_3, wcs_4, wcs_5, wcs_6, wcs_7, wcs_8, wcs_9 |
| `APIDigitalInputs` | 2 | return of get_digital_inputs() | - | has_data, value |
| `APIDigitalOutputs` | 2 | return of get_digital_outputs() | - | has_data, value |
| `APIEnabledCommands` | 41 | return of get_enabled_commands() | - | cnc_connection_close, cnc_connection_open, cnc_continue, cnc_csfm_aux, cnc_csfm_cooler_flood, cnc_csfm_cooler_mist, cnc_csfm_jog_mode, cnc_csfm_spindle_ccw, cnc_csfm_spindle_cw, cnc_csfm_thc_disabled, cnc_csfm_torch, cnc_homing, cnc_jog_command, cnc_mdi_command, cnc_parameters, cnc_pause, cnc_resume, cnc_resume_from_line, cnc_resume_from_point, cnc_start, cnc_start_from_line, cnc_start_from_point, cnc_stop, has_data, program_analysis, program_analysis_abort, program_gcode_add_text, program_gcode_clear, program_gcode_set_text, program_load, program_new, program_save, program_save_as, reset_alarms, reset_alarms_history, reset_warnings, reset_warnings_history, set_kinematics, set_program_position, show_ui_dialog, tools_lib_write |
| `APILocalizationInfo` | 5 | return of get_localization_info() | - | description, has_data, list, locale_name, units_mode |
| `APIMachineSettings` | 39 | return of get_machine_settings() | - | axis_a_acc, axis_a_max_lim, axis_a_max_vel, axis_a_min_lim, axis_a_type, axis_b_acc, axis_b_max_lim, axis_b_max_vel, axis_b_min_lim, axis_b_type, axis_c_acc, axis_c_max_lim, axis_c_max_vel, axis_c_min_lim, axis_c_type, axis_kinematics_model, axis_machine_type, axis_x_acc, axis_x_max_lim, axis_x_max_vel, axis_x_min_lim, axis_x_type, axis_y_acc, axis_y_max_lim, axis_y_max_vel, axis_y_min_lim, axis_y_type, axis_z_acc, axis_z_max_lim, axis_z_max_vel, axis_z_min_lim, axis_z_type, has_data, kinematics_h_x, kinematics_h_y, kinematics_h_z, kinematics_j_x, kinematics_j_y, kinematics_j_z |
| `APIMachiningInfo` | 60 | return of get_machining_info() | - | has_data, joints_in_fast_length_a, joints_in_fast_length_b, joints_in_fast_length_c, joints_in_fast_length_x, joints_in_fast_length_y, joints_in_fast_length_z, joints_in_fast_max_a, joints_in_fast_max_b, joints_in_fast_max_c, joints_in_fast_max_x, joints_in_fast_max_y, joints_in_fast_max_z, joints_in_fast_min_a, joints_in_fast_min_b, joints_in_fast_min_c, joints_in_fast_min_x, joints_in_fast_min_y, joints_in_fast_min_z, joints_in_feed_length_a, joints_in_feed_length_b, joints_in_feed_length_c, joints_in_feed_length_x, joints_in_feed_length_y, joints_in_feed_length_z, joints_in_feed_max_a, joints_in_feed_max_b, joints_in_feed_max_c, joints_in_feed_max_x, joints_in_feed_max_y, joints_in_feed_max_z, joints_in_feed_min_a, joints_in_feed_min_b, joints_in_feed_min_c, joints_in_feed_min_x, joints_in_feed_min_y, joints_in_feed_min_z, planned_time, tcp_extents_in_fast_length_x, tcp_extents_in_fast_length_y, tcp_extents_in_fast_length_z, tcp_extents_in_fast_max_x, tcp_extents_in_fast_max_y, tcp_extents_in_fast_max_z, tcp_extents_in_fast_min_x, tcp_extents_in_fast_min_y, tcp_extents_in_fast_min_z, tcp_extents_in_feed_length_x, tcp_extents_in_feed_length_y, tcp_extents_in_feed_length_z, tcp_extents_in_feed_max_x, tcp_extents_in_feed_max_y, tcp_extents_in_feed_max_z, tcp_extents_in_feed_min_x, tcp_extents_in_feed_min_y, tcp_extents_in_feed_min_z, tool_path_in_fast, tool_path_in_feed, total_path, used_tool |
| `APIMachiningInfoUsedTool` | 3 | - | - | in_fast, in_feed, tool_id |
| `APIOperatorRequest` | 17 | return of get_operator_request() | has_data, type | data_d01, data_d02, data_d03, data_d04, data_d05, data_d06, data_d07, data_d08, data_d09, data_d10, data_elements, external_continue_requested, id, media, message |
| `APIOperatorResponse` | 13 | param response of set_operator_response() | id, type | data_d01, data_d02, data_d03, data_d04, data_d05, data_d06, data_d07, data_d08, data_d09, data_d10, data_elements |
| `APIProgramInfo` | 3 | return of get_program_info() | code, has_data | file_name |
| `APIProgrammedPoints` | 2 | return of get_programmed_points() | - | has_data, points |
| `APIScanningLaserInfo` | 7 | return of get_scanning_laser_info() | has_data, laser_h_measure, laser_mcs_x_position, laser_mcs_y_position, laser_mcs_z_position, laser_out_bit, laser_out_umf | - |
| `APISystemInfo` | 26 | return of get_system_info() | api_server_version, control_software_version, core_version, customer_id, customization_number, firmware_interface_level, firmware_version, firmware_version_tag, hardware_version, has_data, licensed_feature_opc_ua_server, licensed_feature_panel_pc, licensed_feature_panel_pc_demo, licensed_feature_probe_sdk_g1, licensed_feature_probe_sdk_g2, licensed_feature_probe_sdk_g3, licensed_feature_probe_sdk_g4, licensed_feature_probe_sdk_g5, licensed_feature_work_orders, machine_name, operative_system, operative_system_crc, order_code, part_number, pld_version, serial_number | - |
| `APIToolsLibCount` | 2 | return of get_tools_lib_count() | - | count, has_data |
| `APIToolsLibInfo` | 1 | return of get_tools_lib_info() | - | has_data |
| `APIToolsLibInfoForGet` | 29 | - | - | tool_description, tool_diameter, tool_id, tool_index, tool_offset_x, tool_offset_y, tool_offset_z, tool_param_1, tool_param_10, tool_param_2, tool_param_3, tool_param_4, tool_param_5, tool_param_51, tool_param_52, tool_param_53, tool_param_54, tool_param_55, tool_param_56, tool_param_57, tool_param_58, tool_param_59, tool_param_6, tool_param_60, tool_param_7, tool_param_8, tool_param_9, tool_slot, tool_type |
| `APIToolsLibInfoForSet` | 29 | param info of tools_lib_add(), param info of tools_lib_insert(), param info of set_tools_lib_info() | - | tool_description, tool_diameter, tool_id, tool_index, tool_offset_x, tool_offset_y, tool_offset_z, tool_param_1, tool_param_10, tool_param_2, tool_param_3, tool_param_4, tool_param_5, tool_param_51, tool_param_52, tool_param_53, tool_param_54, tool_param_55, tool_param_56, tool_param_57, tool_param_58, tool_param_59, tool_param_6, tool_param_60, tool_param_7, tool_param_8, tool_param_9, tool_slot, tool_type |
| `APIToolsLibInfos` | 2 | return of get_tools_lib_infos() | - | has_data, slot_enabled |
| `APIToolsLibToolIndexFromId` | 2 | return of get_tools_lib_tool_index_from_id() | - | has_data, index |
| `APIVMGeometryInfo` | 10 | - | - | color, edges_angle, edges_visible, has_data, name, scale, visible, x, y, z |
| `APIWorkInfo` | 7 | return of get_work_info() | - | active_work_order_code, active_work_order_file_index, file_name, has_data, planned_time, work_mode, worked_time |
| `APIWorkOrderCodeList` | 2 | return of get_work_order_code_list() | - | data, has_data |
| `APIWorkOrderCodeListData` | 3 | - | - | order_code, order_state, revision_number |
| `APIWorkOrderDataForAdd` | 10 | param data of work_order_add() | - | customer_code, deadline_datetime, files, item_code, job_order_code, material_code, order_locked, order_notes, order_priority, use_deadline_datetime |
| `APIWorkOrderDataForGet` | 26 | return of get_work_order_data() | - | acceptance_datetime, archived_datetime, begin_datetime, creation_datetime, customer_code, deadline_datetime, end_datetime, files, has_data, item_code, job_order_code, log_items, material_code, operator_notes, order_code, order_locked, order_notes, order_priority, order_state, reception_datetime, revision_number, time_for_idle, time_for_setup, time_for_work, time_total, use_deadline_datetime |
| `APIWorkOrderDataForSet` | 11 | param data of set_work_order_data() | - | customer_code, deadline_datetime, files, item_code, job_order_code, material_code, order_locked, order_notes, order_priority, order_state, use_deadline_datetime |
| `APIWorkOrderFileList` | 2 | return of get_work_order_file_list() | - | files, has_data |

## Nested API structures

| Nested class | Fields | Notes |
|---|---|---|
| `APIAlarmsWarningsList.AlarmWarningData` | - | Nested structure defined in API model |
| `APILocalizationInfo.LocalizationData` | - | Nested structure defined in API model |
| `APIWorkOrderCodeList.ListData` | order_code, order_state, revision_number | Nested structure defined in API model |
| `APIWorkOrderDataForAdd.FileData` | file_name, pieces_per_file, requested_pieces | Nested structure defined in API model |
| `APIWorkOrderDataForGet.FileData` | discarded_pieces, file_name, file_state, pieces_per_file, produced_pieces, requested_pieces | Nested structure defined in API model |
| `APIWorkOrderDataForGet.LogItemData` | log_datetime, log_id, log_info_1, log_info_2 | Nested structure defined in API model |
| `APIWorkOrderDataForSet.FileData` | file_name, pieces_per_file, requested_pieces | Nested structure defined in API model |
| `APIWorkOrderFileList.FileData` | creation_datetime, last_access_datetime, last_write_datetime, name, size, type | Nested structure defined in API model |

## Notes

- `set_program_position_z_with_laser_reference()` is called in the project, but both parameters are omitted in the call site, so the demo currently relies on the method defaults (`value=0.0`, `sample_count=3`).
- `APIOperatorResponse` is used only partially in the current demo: only `id` and `type` are written before calling `set_operator_response()`.
- Several response classes are used only minimally. Example: `APICncInfo` currently uses only `has_data`, while `APIProgramInfo` uses `has_data` and `code`.
- Most uncovered API field surface is concentrated in tools library, work order, machine settings, CNC parameters, digital/analog I/O, and localization models.
