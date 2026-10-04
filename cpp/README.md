# RosettaCNC API Client - C++ Implementation

## Description

This project contains a partial C++ port of the RosettaCNC API client implemented in `../python/cnc_api_client_core.py` (API Server v1.5.3). The client enables communication with a RosettaCNC CNC server via TCP/IP sockets with optional SSL/TLS 1.2 support.

### Key Features:
- TCP/IP socket communication with SSL support (Schannel)
- Native JSON parser for handling nested responses
- API data structures for the currently implemented C++ methods
- Test program for the currently implemented subset
- Windows x64 support with Visual Studio 2019

## Project Files

- `cnc_api_client_core.h` - C++ declarations and API data structures
- `cnc_api_client_core.cpp` - C++ client implementation
- `main.cpp` - Test program for the implemented subset
- `CncAPIClient.vcxproj` - Visual Studio 2019 project

## Implementation Status

### 📊 Overall Summary
- **GET Methods**: 27/36 ✅ (75%)
- **SET Methods**: 16/32 ✅ (50%)
- **CMD Methods**: 3/56 ✅ (5%)

The totals above are based on the public synchronous methods currently exposed by
`../python/cnc_api_client_core.py`. The 10 Python convenience wrappers whose names end
in `_threaded` are reported separately and are not included in the CMD total.

---

## ✅ Implemented GET Methods (27/36 - 75%)

The following GET methods have a C++ implementation:

1. ✅ `get_axes_info()` - Axes information (positions, velocities, homing)
2. ✅ `get_cnc_info()` - Complete CNC information (state, alarms, tool, spindle)
3. ✅ `get_compile_info()` - Compiler state and errors
4. ✅ `get_enabled_commands()` - Available commands
5. ✅ `get_digital_inputs()` - 128 digital inputs
6. ✅ `get_digital_outputs()` - 128 digital outputs
7. ✅ `get_alarms_current_list()` - Current alarms list
8. ✅ `get_alarms_history_list()` - Alarms history
9. ✅ `get_warnings_current_list()` - Current warnings list
10. ✅ `get_warnings_history_list()` - Warnings history
11. ✅ `get_system_info()` - System information (versions, serial)
12. ✅ `get_analog_inputs()` - 16 analog inputs
13. ✅ `get_analog_outputs()` - 16 analog outputs
14. ✅ `get_machining_info()` - Machining information (paths, times)
15. ✅ `get_work_info()` - Work information (mode, file, times)
16. ✅ `get_tools_lib_info(int index)` - Single tool information
17. ✅ `get_tools_lib_infos()` - All tools information
18. ✅ `get_tools_lib_count()` - Tool library count
19. ✅ `get_tools_lib_tool_index_from_id(int tool_id)` - Tool index from ID
20. ✅ `get_machine_settings()` - Machine settings
21. ✅ `get_localization_info()` - Localization information
22. ✅ `get_scanning_laser_info()` - Scanning laser information
23. ✅ `get_work_order_code_list()` - Work order code list
24. ✅ `get_work_order_data(order_code, mode)` - Work order data
25. ✅ `get_work_order_file_list(path, filter)` - Work order file list
26. ✅ `get_programmed_points()` - Programmed points
27. ✅ `get_cnc_parameters(address, elements)` - CNC parameters

### ❌ GET Methods To Implement (9)

- ❌ `get_compiler_settings()`
- ❌ `get_coordinate_systems_info()`
- ❌ `get_mru_programs_list()`
- ❌ `get_operator_request()`
- ❌ `get_program_info()`
- ❌ `get_runtime_data()`
- ❌ `get_simulator_data(data_type)`
- ❌ `get_toolpath_data(mode)`
- ❌ `get_vm_geometry_info(names)` — declared in the C++ header, but not defined in the C++ source

---

## ✅ Implemented SET Methods (16/32 - 50%)

### Override (8/8) ✅
1. ✅ `set_override_jog(int value)` - Jog speed override
2. ✅ `set_override_fast(int value)` - Rapid speed override
3. ✅ `set_override_feed(int value)` - Feed rate override
4. ✅ `set_override_feed_custom_1(int value)` - Custom feed override 1
5. ✅ `set_override_feed_custom_2(int value)` - Custom feed override 2
6. ✅ `set_override_plasma_power(int value)` - Plasma power override
7. ✅ `set_override_plasma_voltage(int value)` - Plasma voltage override
8. ✅ `set_override_spindle(int value)` - Spindle override

### Program Positions (6/6) ✅
9. ✅ `set_program_position_x(double value)` - Set X position
10. ✅ `set_program_position_y(double value)` - Set Y position
11. ✅ `set_program_position_z(double value)` - Set Z position
12. ✅ `set_program_position_a(double value)` - Set A position
13. ✅ `set_program_position_b(double value)` - Set B position
14. ✅ `set_program_position_c(double value)` - Set C position

### Other SET (2/18) ✅
15. ✅ `set_cnc_parameters(address, values, descriptions)` - Set CNC parameters
16. ✅ `set_localization(units_mode, locale_name)` - Set localization (units and locale)

### ❌ SET Methods To Implement (16)

- ❌ `set_compiler_settings(data)`
- ❌ `set_dynamic_offset_x(value)`
- ❌ `set_dynamic_offset_y(value)`
- ❌ `set_dynamic_offset_z(value)`
- ❌ `set_dynamic_offsets(x, y, z)`
- ❌ `set_kinematics()`
- ❌ `set_operator_response(response)`
- ❌ `set_program_position_x_with_laser_reference(value)`
- ❌ `set_program_position_y_with_laser_reference(value)`
- ❌ `set_program_position_z_with_laser_reference(value, sample_count)`
- ❌ `set_simulator_current_time_ms(value)`
- ❌ `set_simulator_speed_track(value)`
- ❌ `set_tools_lib_info(info)`
- ❌ `set_wcs_info(wcs, offset, activate)`
- ❌ `set_vm_geometry_info(values)`
- ❌ `set_work_order_data(order_code, data)`

---

## ✅ Implemented CMD Methods (3/56 - 5%)

### Execution Control (2/5) ✅
1. ✅ `cnc_start()` - Start program execution
2. ✅ `cnc_stop()` - Stop execution

### Program Management (1/10) ✅
3. ✅ `program_load(const std::string& file_name)` - Load program

### ⚠️ Partial/Stub CMD Methods (4)

These methods have a C++ body, but their request names or signatures do not match the
current Python implementation and therefore are not counted as implemented:

- ⚠️ `cnc_pause()` — sends `cnc_pause` instead of `cnc.pause`
- ⚠️ `cnc_resume(int line)` — sends `cnc_resume` instead of `cnc.resume`; the Python signature uses `force_sync` and `timeout`
- ⚠️ `cnc_jog_command(int command)` — sends `cnc_jog_command` instead of `cnc.jog.command`
- ⚠️ `reset_alarms()` — sends `reset_alarms` instead of `reset.alarms`

### ❌ CMD Methods To Implement (49)

#### Execution Control
- ❌ `cnc_continue()` - Continue execution

#### Start/Resume from Specific Point (4)
- ❌ `cnc_start_from_line(int line)` - Start from line
- ❌ `cnc_start_from_point(int point)` - Start from point
- ❌ `cnc_resume_from_line(int line)` - Resume from line
- ❌ `cnc_resume_from_point(int point)` - Resume from point

#### Connection and Configuration (3)
- ❌ `cnc_connection_open(...)` - Open CNC connection
- ❌ `cnc_connection_close()` - Close CNC connection
- ❌ `cnc_change_function_state_mode(int name, int mode)` - Change function state mode

#### Movement and Homing
- ❌ `cnc_homing(int axes_mask)` - Execute axes homing

#### MDI Commands
- ❌ `cnc_mdi_command(const std::string& command)` - Execute MDI command

#### File Import and Export
- ❌ `file_export_cpf(file_name)`
- ❌ `file_export_csf(file_name)`
- ❌ `file_export_ctf(file_name)`
- ❌ `file_export_msg(file_name)`
- ❌ `file_export_psf(file_name)`
- ❌ `file_import_cpf(file_name)`
- ❌ `file_import_csf(file_name)`
- ❌ `file_import_ctf(file_name)`
- ❌ `file_import_msg(file_name)`
- ❌ `file_import_psf(file_name)`

#### Most Recently Used Programs
- ❌ `mru_programs_list_clear()`
- ❌ `mru_programs_list_remove_item(index)`

#### Program Management
- ❌ `program_new()` - New program
- ❌ `program_save()` - Save program
- ❌ `program_save_as(const std::string& file_name)` - Save program as
- ❌ `program_gcode_add_text(const std::string& text)` - Add GCode text
- ❌ `program_gcode_clear()` - Clear GCode
- ❌ `program_gcode_modified()` - Notify that GCode was modified
- ❌ `program_gcode_set_text(const std::string& text)` - Set GCode text
- ❌ `program_analysis(int mode)` - Analyze program
- ❌ `program_analysis_abort()` - Abort analysis

#### Reset and Alarm Management
- ❌ `reset_alarms_history()` - Reset alarms history
- ❌ `reset_warnings()` - Reset warnings
- ❌ `reset_warnings_history()` - Reset warnings history

#### Simulator
- ❌ `simulator_continue()`
- ❌ `simulator_pause()`
- ❌ `simulator_place_and_pause_to_line(line)`
- ❌ `simulator_start()`
- ❌ `simulator_step_backward()`
- ❌ `simulator_step_forward()`
- ❌ `simulator_stop()`

#### Tool Library
- ❌ `tools_lib_add(const APIToolsLibInfoForSet* info)` - Add tool
- ❌ `tools_lib_clear()` - Clear tool library
- ❌ `tools_lib_delete(int index)` - Delete tool
- ❌ `tools_lib_insert(const APIToolsLibInfoForSet* info)` - Insert tool

#### Work Orders
- ❌ `work_order_add(order_code, data)` - Add work order
- ❌ `work_order_delete(const std::string& order_code)` - Delete work order

#### Other Commands
- ❌ `log_add(const std::string& text)` - Add log entry
- ❌ `show_ui_dialog(int uid_id)` - Show UI dialog

### ❌ Threaded Convenience Methods To Implement (10, excluded from CMD total)

- ❌ `cnc_resume_threaded(...)`
- ❌ `cnc_resume_from_line_threaded(...)`
- ❌ `cnc_resume_from_point_threaded(...)`
- ❌ `cnc_start_threaded(...)`
- ❌ `cnc_start_from_line_threaded(...)`
- ❌ `cnc_start_from_point_threaded(...)`
- ❌ `program_analysis_threaded(...)`
- ❌ `program_load_threaded(...)`
- ❌ `program_save_threaded(...)`
- ❌ `program_save_as_threaded(...)`

---

## 🔨 Build

Requirements:
- Visual Studio 2019 or later
- Windows 10 x64
- Platform Toolset v142

Build with MSBuild:
```bash
msbuild CncAPIClient.vcxproj /p:Configuration=Debug /p:Platform=x64 /t:Build
```

Or open the `.vcxproj` file in Visual Studio and build (F7).

## 🧪 Testing

The `main.cpp` program includes tests for the currently implemented subset:

1. **GET Methods Test** - Automatic tests for all 27 GET methods
2. **Real-time Monitoring** - 10 seconds of real-time CNC monitoring
3. **SET Methods Test** (interactive) - Tests for all 16 implemented SET methods
4. **CMD Methods Test** (interactive) - Test program_load, cnc_start/stop

Run:
```bash
.\x64\Debug\CncAPIClient.exe
```

## 📄 License

This is a C++ port of the original RosettaCNC Python API (v1.5.3).
