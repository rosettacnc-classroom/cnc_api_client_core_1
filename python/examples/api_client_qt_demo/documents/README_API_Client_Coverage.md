# API Client Coverage

## Project files analyzed

- `cnc_api_client_core.py`
- `api_client_qt_demo.py`
- `api_client_qt_demo_desktop_view.py`
- `qt_alarms_warnings_dialog.py`
- `qt_user_dialogs.py`

## Scope of this document

This document reports how much of the public interface of class `CncAPIClientCore`
(in `cnc_api_client_core.py`) is currently covered by the demo files loaded for analysis.

### Important note

- **Direct usage** = the method is called explicitly in the analyzed files.
- **Indirect usage** = the method is not called directly by the UI logic, but is used through helper/context objects created and used by the demo.
- In particular, `api_client_qt_demo_desktop_view.py` creates `CncAPIInfoContext(self.api)`, whose `update()` method uses some additional API methods.

## Summary

| Item | Value |
|---|---:|
| Total public methods in `CncAPIClientCore` | 96 |
| Methods used directly in the analyzed demo files | 58 |
| Methods used including indirect usage via `CncAPIInfoContext.update()` | 61 |
| Methods not yet covered in the demo | 35 |
| Estimated demo coverage | 63.5% |

## Methods used in the demo

### Directly used methods

- `connect`
- `close`
- `cnc_change_function_state_mode`
- `cnc_connection_close`
- `cnc_connection_open`
- `cnc_continue`
- `cnc_homing`
- `cnc_jog_command`
- `cnc_mdi_command`
- `cnc_pause`
- `cnc_resume`
- `cnc_resume_from_line`
- `cnc_start`
- `cnc_start_from_line`
- `cnc_stop`
- `program_analysis`
- `program_analysis_abort`
- `program_gcode_add_text`
- `program_gcode_set_text`
- `program_load`
- `program_new`
- `program_save`
- `program_save_as`
- `get_program_info`
- `set_program_position_x`
- `set_program_position_y`
- `set_program_position_z`
- `set_program_position_a`
- `set_program_position_b`
- `set_program_position_c`
- `set_wcs_info`
- `set_program_position_x_with_laser_reference`
- `set_program_position_y_with_laser_reference`
- `set_program_position_z_with_laser_reference`
- `show_ui_dialog`
- `get_cnc_info`
- `get_coordinate_systems_info`
- `get_machining_info`
- `get_operator_request`
- `get_scanning_laser_info`
- `get_system_info`
- `set_override_jog`
- `set_override_spindle`
- `set_override_fast`
- `set_override_feed`
- `set_override_feed_custom_1`
- `set_override_feed_custom_2`
- `set_override_plasma_power`
- `set_override_plasma_voltage`
- `reset_alarms`
- `reset_alarms_history`
- `reset_warnings`
- `reset_warnings_history`
- `get_alarms_current_list`
- `get_alarms_history_list`
- `get_warnings_current_list`
- `get_warnings_history_list`
- `set_operator_response`

### Indirectly used methods

Used via `CncAPIInfoContext.update()`:

- `get_axes_info`
- `get_compile_info`
- `get_enabled_commands`

## Methods not yet covered in the demo

### Connection / startup

- `connect_direct`

### Advanced start / resume

- `cnc_resume_from_point`
- `cnc_start_from_point`

### Logging

- `log_add`

### G-code management

- `program_gcode_clear`

### Tools library

- `tools_lib_add`
- `tools_lib_clear`
- `tools_lib_delete`
- `tools_lib_insert`
- `get_tools_lib_count`
- `get_tools_lib_info`
- `get_tools_lib_infos`
- `get_tools_lib_tool_index_from_id`
- `set_tools_lib_info`

### Work / work order

- `work_order_add`
- `work_order_delete`
- `get_work_info`
- `get_work_order_code_list`
- `get_work_order_data`
- `get_work_order_file_list`
- `set_work_order_data`

### Inputs / outputs / CNC parameters

- `get_analog_inputs`
- `get_analog_outputs`
- `get_digital_inputs`
- `get_digital_outputs`
- `get_cnc_parameters`
- `set_cnc_parameters`

### Localization / machine / geometry

- `get_localization_info`
- `set_localization`
- `get_machine_settings`
- `get_vm_geometry_info`
- `set_vm_geometry_info`

### Additional program data

- `get_programmed_points`

### Public utility methods currently not used

- `create_compact_json_request`
- `datetime_to_filetime`

## Recommended interpretation

The current demo already covers the most visible and useful areas for a first API showcase:

- connection base flow
- main CNC commands
- jog and homing
- load/save program
- G-code editing
- program analysis
- overrides
- WCS handling
- alarms and warnings
- operator dialogs
- several status/info reads

The main areas still missing from the demo are:

- tools library management
- work order management
- digital/analog I/O visualization
- CNC parameters and localization
- direct connection mode
- advanced start/resume from point
- VM geometry related functions

## Suggested next priorities for the demo

### 1. Essential next additions

- `get_digital_inputs`
- `get_digital_outputs`
- `get_analog_inputs`
- `get_analog_outputs`
- `get_cnc_parameters`
- `set_cnc_parameters`

### 2. Useful functional additions

- `get_tools_lib_count`
- `get_tools_lib_info`
- `get_tools_lib_infos`
- `set_tools_lib_info`
- `tools_lib_add`
- `tools_lib_delete`
- `tools_lib_insert`
- `tools_lib_clear`

### 3. Advanced / completeness additions

- `get_work_info`
- `get_work_order_code_list`
- `get_work_order_data`
- `get_work_order_file_list`
- `set_work_order_data`
- `work_order_add`
- `work_order_delete`
- `connect_direct`
- `cnc_start_from_point`
- `cnc_resume_from_point`
- `get_vm_geometry_info`
- `set_vm_geometry_info`
- `get_localization_info`
- `set_localization`
- `get_machine_settings`
- `get_programmed_points`
- `log_add`
- `program_gcode_clear`
