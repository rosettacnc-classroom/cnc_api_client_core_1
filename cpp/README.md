# RosettaCNC API Client - C++

This directory contains the C++14 version of `cnc_api_client_core.py` for
accessing the RosettaCNC API Server protocol.

## Contents

- `cnc_api_client_core.h`: public API, constants, and data structures.
- `cnc_api_client_core.cpp`: TCP/TLS client implementation.
- `main.cpp`: usage example and simple test calls.
- `CncAPIClient.vcxproj`: Visual Studio 2019 project.

## Building

Requirements: Windows 10 or later, Visual Studio 2019 or later, and Platform
Toolset v142.

```powershell
msbuild CncAPIClient.vcxproj /p:Configuration=Release /p:Platform=x64 /t:Build
```

## TODO

- Verify and complete `set_kinematics()` when the expected payload and behavior
  are defined by the Python reference/API Server.
- Strengthen validation of incomplete or malformed responses by checking
  required fields before setting `has_data = true`.
- Implement `connect_direct()` when a C/C++ backend or documented ABI becomes
  available for the proprietary `cnc_direct_access` module.
