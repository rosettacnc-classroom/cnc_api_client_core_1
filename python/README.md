# API Client for Python
This API Client is the initial implementation designed to align with the **Server API Interface Specification 1.5.1**.<br>
It is compatible with the **API Server** running in RosettaCNC Control Software version 1.13.1.

The API Client was developed and rigorously tested with RosettaCNC's **NC Embedded Python** version 3.11.9.

## NC Embedded Python Overview
During the installation of the NC Control Software, an embedded version of Python 3.11.9 is automatically installed<br>
in one of the following paths, depending on the RosettaCNC version:

- **RosettaCNC STD version:**<br>
  %LOCALAPPDATA%\Programs\RosettaCNC.python\
  <br><br>

- **RosettaCNC PPH version:**<br>
  %LOCALAPPDATA%\Programs\RosettaCNCPPH.python\
  <br><br>

- **RosettaCNC PPV version:**<br>
  %LOCALAPPDATA%\Programs\RosettaCNCPPV.python\
  <br><br>

**NC Embedded Python** comes preloaded with numerous packages to facilitate seamless integration and development.

The **NC Embedded Python** path was not voluntarily added to the **system** or **user****** path, so as not to invalidate<br>
eventualy existing Python versions.

### List of pre-installed packages on RosettaCNC NC Embedded Python:
|Package                |Version
|---------------------- |-------------
|aiofiles               |24.1.0
|aiosqlite              |0.20.0
|asyncua                |1.1.5
|cffi                   |1.17.1
|contourpy              |1.3.1
|cryptography           |43.0.3
|customtkinter          |5.2.2
|cycler                 |0.12.1
|darkdetect             |0.8.0
|delphifmx              |1.0.9
|delphivcl              |1.0.6
|fonttools              |4.55.0
|keyboard               |0.13.5
|kiwisolver             |1.4.7
|matplotlib             |3.9.2
|msvc_runtime           |14.42.34433
|mysql-connector-python |9.1.0
|numpy                  |2.1.3
|numpy-stl              |3.1.2
|opencv-contrib-python  |4.10.0.84
|packaging              |24.2
|pbr                    |6.1.0
|pillow                 |11.0.0
|pip                    |24.3.1
|pybind11               |2.13.6
|pycparser              |2.22
|pymeshlab              |2023.12.post2
|pymodbus               |3.7.4
|PyOpenGL               |3.1.7
|PyOpenGL-accelerate    |3.1.7
|pyOpenSSL              |24.2.1
|pyparsing              |3.2.0
|PySide6                |6.8.0.2
|PySide6_Addons         |6.8.0.2
|PySide6_Essentials     |6.8.0.2
|PySimpleGUI            |4.70.1
|python-dateutil        |2.9.0.post0
|python-utils           |3.9.0
|pytz                   |2024.2
|scipy                  |1.14.1
|screeninfo             |0.8.1
|setuptools             |75.6.0
|shiboken6              |6.8.0.2
|six                    |1.16.0
|skia-python            |87.6
|sortedcontainers       |2.4.0
|tendo                  |0.3.0
|typing_extensions      |4.12.2
|vtk                    |9.3.1
|wheel                  |0.45.0

