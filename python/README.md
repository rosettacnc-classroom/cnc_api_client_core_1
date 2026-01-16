# API Client for Python
This API Client is the initial implementation designed to align with the **Server API Interface Specification 1.5.2**.<br>
It is compatible with the **API Server** running in RosettaCNC Control Software version 1.14.2.

The API Client was developed and rigorously tested with RosettaCNC's **NC Embedded Python** version 3.11.9.

## NC Embedded Python Overview
During the installation of the NC Control Software, an embedded version of Python 3.11.9 is automatically installed<br>
in one of the following paths, depending on the RosettaCNC version:

- **RosettaCNC STD version:**<br>
  %LOCALAPPDATA%\Programs\RosettaCNC.python\

- **RosettaCNC PPH version:**<br>
  %LOCALAPPDATA%\Programs\RosettaCNCPPH.python\

- **RosettaCNC PPV version:**<br>
  %LOCALAPPDATA%\Programs\RosettaCNCPPV.python\

**NC Embedded Python** comes preloaded with numerous packages to facilitate seamless integration and development.

The **NC Embedded Python** path was not voluntarily added to the **system** or **user** path, so as not to invalidate<br>
eventualy existing Python versions.

### List of pre-installed packages on RosettaCNC NC Embedded Python:
|Package                |Version
|---------------------- |-------------
|aiofiles               |24.1.0
|aiosqlite              |0.21.0
|asyncua                |1.1.6
|cffi                   |1.17.1
|contourpy              |1.3.3
|cryptography           |45.0.6
|customtkinter          |5.2.2
|cycler                 |0.12.1
|darkdetect             |0.8.0
|delphifmx              |1.1.0
|delphivcl              |1.0.7
|fonttools              |4.59.0
|keyboard               |0.13.5
|kiwisolver             |1.4.8
|matplotlib             |3.10.5
|msvc_runtime           |14.44.35112
|mysql-connector-python |9.4.0
|numpy                  |2.2.6
|numpy-stl              |3.2.0
|opencv-contrib-python  |4.12.0.88
|packaging              |25.0
|pbr                    |6.1.1
|pillow                 |11.3.0
|pip                    |25.1.1
|pybind11               |3.0.0
|pycparser              |2.22
|pymeshlab              |2025.7
|pymodbus               |3.11.0
|PyOpenGL               |3.1.9
|PyOpenGL-accelerate    |3.1.9
|pyOpenSSL              |25.1.0
|pyparsing              |3.2.3
|PySide6                |6.9.1
|PySide6_Addons         |6.9.1
|PySide6_Essentials     |6.9.1
|python-dateutil        |2.9.0.post0
|python-utils           |3.9.1
|pytz                   |2025.2
|scipy                  |1.16.1
|screeninfo             |0.8.1
|setuptools             |80.9.0
|shiboken6              |6.9.1
|six                    |1.17.0
|skia-python            |138.0
|sortedcontainers       |2.4.0
|tendo                  |0.3.0
|tkinter-embed          |3.11.0
|typing_extensions      |4.14.1
|vtk                    |9.5.0
|wait_for2              |0.3.2
|wheel                  |0.45.1
