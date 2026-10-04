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
- **GET Methods**: 36/36 ✅ (100%)
- **SET Methods**: 31/32 ✅ (97%)
- **CMD Methods**: 56/56 ✅ (100%)
- **Threaded Convenience Methods**: 10/10 ✅ (100%)

The totals above are based on the public synchronous methods currently exposed by
`../python/cnc_api_client_core.py`. The 10 Python convenience wrappers whose names end
in `_threaded` are reported separately and are not included in the CMD total.

---

## ✅ Implemented GET Methods (36/36 - 100%)

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
28. ✅ `get_compiler_settings()` - Compiler settings
29. ✅ `get_coordinate_systems_info()` - Coordinate systems and WCS offsets
30. ✅ `get_mru_programs_list()` - Most recently used programs
31. ✅ `get_operator_request()` - Pending operator request
32. ✅ `get_program_info()` - Loaded program information
33. ✅ `get_runtime_data()` - Runtime pending and acquired data
34. ✅ `get_simulator_data(data_type)` - Raw simulator data
35. ✅ `get_toolpath_data(mode)` - Decoded or raw toolpath data
36. ✅ `get_vm_geometry_info(names)` - Virtual machine geometry information

---

## ✅ Implemented SET Methods (31/32 - 97%)

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

### Other SET (17/18) ✅
15. ✅ `set_cnc_parameters(address, values, descriptions)` - Set CNC parameters
16. ✅ `set_localization(units_mode, locale_name)` - Set localization (units and locale)
17. ✅ `set_compiler_settings(data)` - Set selected compiler settings
18. ✅ `set_dynamic_offset_x(value)` - Set X dynamic offset
19. ✅ `set_dynamic_offset_y(value)` - Set Y dynamic offset
20. ✅ `set_dynamic_offset_z(value)` - Set Z dynamic offset
21. ✅ `set_dynamic_offsets(x, y, z)` - Set selected XYZ dynamic offsets
22. ✅ `set_operator_response(response)` - Send an operator response
23. ✅ `set_program_position_x_with_laser_reference(value)` - Set X using the laser reference
24. ✅ `set_program_position_y_with_laser_reference(value)` - Set Y using the laser reference
25. ✅ `set_program_position_z_with_laser_reference(value, sample_count)` - Set Z using median laser samples
26. ✅ `set_simulator_current_time_ms(value)` - Set simulator current time
27. ✅ `set_simulator_speed_track(value)` - Set simulator speed track
28. ✅ `set_tools_lib_info(info)` - Update tool information
29. ✅ `set_wcs_info(wcs, offset, activate)` - Set WCS offsets and activation
30. ✅ `set_vm_geometry_info(values)` - Set virtual machine geometry
31. ✅ `set_work_order_data(order_code, data)` - Update work order data

### ⚠️ SET Method Unsupported By The Python Reference (1)

- ⚠️ `set_kinematics()` — the Python v1.5.3 reference contains only a placeholder that returns `False`; no request payload is defined

---

## ✅ Implemented CMD Methods (56/56 - 100%)

All public synchronous CMD methods exposed by the Python reference are implemented.
This includes CNC execution and connection control, homing and JOG, MDI, file
import/export, MRU management, program editing and persistence, analysis,
alarms/warnings, simulator control, tool-library operations, work orders, logging,
and UI dialogs.

Commands supporting the Python `force_sync` option use the same request flag and a
configurable first-response timeout. Numeric and boolean request fields are emitted as
JSON values rather than strings, and strings are JSON-escaped.

### ✅ Threaded Convenience Methods (10/10, excluded from CMD total)

All ten Python `_threaded` convenience methods have C++ equivalents. Each operation
uses a dedicated cloned API connection, allows only one active worker per client, and
reports the final command result through `CompletionCallback`. The callback runs on the
worker thread; UI applications must marshal UI updates to their UI thread.

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

1. **GET Methods Test** - Automatic calls for all 36 GET methods
2. **Real-time Monitoring** - 10 seconds of real-time CNC monitoring
3. **SET Methods Test** (interactive) - Tests for the core SET methods
4. **CMD Methods Test** (interactive) - Test program_load, cnc_start/stop

Run:
```bash
.\x64\Debug\CncAPIClient.exe
```

## 📄 License

This is a C++ port of the original RosettaCNC Python API (v1.5.3).
