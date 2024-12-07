"""API Client Demo using Embarcadero FMX UI."""
#-------------------------------------------------------------------------------
# Name:         api_client_fmx_demo
#
# Purpose:      API Client Demo with Embarcadero delphifmx UI
#               https://pypi.org/project/delphifmx/
#
# Note          Compatible with API server version 1.5.1
#               1 (on 1.x.y) means interface contract
#               x (on 1.x.y) means version
#               y (on 1.x.y) means release
#
# Note          Checked with Python 3.11.9
#
# Author:       rosettacnc-classroom@gmail.com
#
# Created:      07/12/2024
# Copyright:    RosettaCNC (c) 2016-2024
# Licence:      RosettaCNC License 1.0 (RCNC-1.0)
# Coding Style  https://www.python.org/dev/peps/pep-0008/
#               With cnc_vision_vcl/fmx objects is used Delphi coding style
#-------------------------------------------------------------------------------
import os

from delphifmx import *

from api_client_fmx_demo_desktop_view import ApiClientFmxDemoDesktopView

# == style settings
styles = [
    'Air.style',                    # 0
    'Amakrits.style',               # 1
    'AquaGraphite.style',           # 2
    'Blend.style',                  # 3
    'CopperDark.Win.style',         # 4
    'Dark.style',                   # 5
    'GoldenGraphite.style',         # 6
    'Light.style',                  # 7
    'RubyGraphite.style',           # 8
    'Transparent.style',            # 9
    'WindowsModern.style',          # 10
    'WindowsModernBlue.style',      # 11
    'WindowsModernDark.style',      # 12
    'WindowsModernGreen.style',     # 13
    'WindowsModernPurple.style',    # 14
    'WindowsModernSlateGray.style', # 15
    ]

STYLE_PATH = os.getcwd() + '\\styles\\'
STYLE_NAME = None
STYLE_NAME = styles[9]

def main():
    """Main entry point."""

    # apply required style
    if not STYLE_NAME is None:
        style_manager = StyleManager()
        style_manager.SetStyleFromFile(STYLE_PATH + STYLE_NAME)

    # initialize application and enter in main loop
    Application.Initialize()
    Application.Title = 'API Client FMX Demo'
    Application.MainForm = ApiClientFmxDemoDesktopView(Application)
    Application.MainForm.Show()
    Application.Run()
    Application.MainForm.Destroy()

if __name__ == '__main__':
    main()
