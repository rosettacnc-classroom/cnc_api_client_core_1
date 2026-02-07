# RosettaCNC API Client - C++ Implementation

## Description

This project contains the C++ implementation of the RosettaCNC API client, ported from the original Python version (v1.5.3). The client enables communication with a RosettaCNC CNC server via TCP/IP sockets with optional SSL/TLS 1.2 support.

### Key Features:
- TCP/IP socket communication with SSL support (Schannel)
- Native JSON parser for handling nested responses
- Complete API data structures management
- Fully tested with real CNC server
- Windows x64 support with Visual Studio 2019

## Project Files

- `cnc_api_client_core.h` - Header with all declarations (1210 lines)
- `cnc_api_client_core.cpp` - Client implementation (2700+ lines)
- `main.cpp` - Complete test program (720+ lines)
- `CncAPIClient.vcxproj` - Visual Studio 2019 project

## Implementation Status

### 📊 Overall Summary
- **GET Methods**: 27/27 ✅ (100%)
- **SET Methods**: 16/18 ✅ (89%)
- **CMD Methods**: 2/36 ✅ (6%)

---

## ✅ Implemented GET Methods (27/27 - 100%)

All GET methods have been implemented and tested with real CNC server:

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

---

## ✅ Implemented SET Methods (16/18 - 89%)

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

### Other SET (2/4) ✅
15. ✅ `set_cnc_parameters(address, values, descriptions)` - Set CNC parameters
16. ✅ `set_localization(units_mode, locale_name)` - Set localization (units and locale)

### ❌ SET Methods To Implement (2)
17. ❌ `set_tools_lib_info(const APIToolsLibInfoForSet* info)` - Set tool information
18. ❌ `set_vm_geometry_info(const std::vector<APIVMGeometryInfo>& values)` - Set VM geometry info
19. ❌ `set_work_order_data(order_code, data)` - Set work order data

---

## ✅ Implemented CMD Methods (2/36 - 6%)

### Execution Control (2/5) ✅
1. ✅ `cnc_start()` - Start program execution
2. ✅ `cnc_stop()` - Stop execution

### ❌ CMD Methods To Implement (34)

#### Execution Control (3/5)
- ❌ `cnc_pause()` - Pause execution
- ❌ `cnc_resume(int line)` - Resume execution
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

#### Movement and Homing (2)
- ❌ `cnc_homing(int axes_mask)` - Execute axes homing
- ❌ `cnc_jog_command(int command)` - Manual jog commands

#### MDI Commands (1)
- ❌ `cnc_mdi_command(const std::string& command)` - Execute MDI command

#### Program Management (9)
- ❌ `program_load(const std::string& file_name)` - Load program
- ❌ `program_new()` - New program
- ❌ `program_save()` - Save program
- ❌ `program_save_as(const std::string& file_name)` - Save program as
- ❌ `program_gcode_add_text(const std::string& text)` - Add GCode text
- ❌ `program_gcode_clear()` - Clear GCode
- ❌ `program_gcode_set_text(const std::string& text)` - Set GCode text
- ❌ `program_analysis(const std::string& mode)` - Analyze program
- ❌ `program_analysis_abort()` - Abort analysis

#### Reset and Alarm Management (4)
- ❌ `reset_alarms()` - Reset alarms
- ❌ `reset_alarms_history()` - Reset alarms history
- ❌ `reset_warnings()` - Reset warnings
- ❌ `reset_warnings_history()` - Reset warnings history

#### Tool Library (4)
- ❌ `tools_lib_add(const APIToolsLibInfoForSet* info)` - Add tool
- ❌ `tools_lib_clear()` - Clear tool library
- ❌ `tools_lib_delete(int index)` - Delete tool
- ❌ `tools_lib_insert(const APIToolsLibInfoForSet* info)` - Insert tool

#### Work Orders (2)
- ❌ `work_order_add(order_code, data)` - Add work order
- ❌ `work_order_delete(const std::string& order_code)` - Delete work order

#### Other Commands (2)
- ❌ `log_add(const std::string& text)` - Add log entry
- ❌ `show_ui_dialog(const std::string& name)` - Show UI dialog

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

The `main.cpp` program includes complete tests for all implemented methods:

1. **GET Methods Test** - Automatic tests for all 27 GET methods
2. **Real-time Monitoring** - 10 seconds of real-time CNC monitoring
3. **SET Methods Test** (interactive) - Tests for all 15 implemented SET methods
4. **CMD Methods Test** (interactive) - Test cnc_start/stop with 5-second wait

Run:
```bash
.\x64\Debug\CncAPIClient.exe
```

## 📄 License

This is a C++ port of the original RosettaCNC Python API (v1.5.3).
