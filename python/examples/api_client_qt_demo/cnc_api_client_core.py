"""CNC API Client Core for RosettaCNC & derived NC Systems."""
#-------------------------------------------------------------------------------
# Name:         cnc_api_client_core
#
# Purpose:      CNC API Client Core for RosettaCNC & derived NC Systems
#
# Note:         Compatible with API server version 1.5.3
#               1 (on 1.x.y) means interface contract
#               x (on 1.x.y) means version
#               y (on 1.x.y) means release
#
# Note:         Checked with Python 3.11.9
#
# Note:         Some data values or code are aligned to specified text columns to
#               simplify data identification during the update of the API client
#               to a newer version of the API server.
#
# Note:         The use of generic exception raising and catching is intentional.
#               As a client, we are not concerned with logging the specific
#               exceptions that occur. Instead, our focus is on handling these
#               exceptions to maintain the desired execution flow within set
#               parameters.
#
# TO DO:        To change the direct dict value recovery j[''][''] with j.get('')
#               to avoid exception when received response do not contains the
#               key:value. This permit to increase compatibility of API.
#
# TO DO:        Use isinstance(data, type) or isinstance(data, (type, type)) to
#               verify data type. For int you can use type(int) because bool is
#               a specific subclass of int and isinstance will fail.
#
# Author:       support@rosettacnc.com
#
# Created:      03/06/2026
# Copyright:    RosettaCNC (c) 2016-2026
# Licence:      RosettaCNC License 1.0 (RCNC-1.0)
# Coding Style: https://www.python.org/dev/peps/pep-0008/
#-------------------------------------------------------------------------------
# pylint: disable=C0103 -> invalid-name
# pylint: disable=C0123 -> unidiomatic-typecheck
# pylint: disable=C0200 -> consider-using-enumerate         ## TO BE IMPROVED!!!
# pylint: disable=C0301 -> line-too-long
# pylint: disable=C0302 -> too-many-lines
# pylint: disable=R0902 -> too-many-instance-attributes
# pylint: disable=R0903 -> too-few-public-methods
# pylint: disable=R0904 -> too-many-public-methods
# pylint: disable=R0911 -> too-many-return-statements
# pylint: disable=R0912 -> too-many-branches
# pylint: disable=R0915 -> too-many-statements
# pylint: disable=R1702 -> too-many-nested-blocks
# pylint: disable=R1732 -> consider-using-with
# pylint: disable=W0718 -> broad-exception-caught           ## take care when you use that ##
# pylint: disable=W0719 -> broad-exception-raised           ## take care when you use that ##
#-------------------------------------------------------------------------------
from __future__ import annotations

import ssl
import math
import json
import time
import base64
import socket
import threading

from typing import Any, Callable, List
from statistics import median
from datetime import datetime, timedelta

# evaluate if cnc direct access is available
# direct access is used only when Python is hosted inside the Delphi OPC UA
# server process, so API requests bypass TCP/IP socket transport on purpose
from importlib import import_module
try:
    cda = import_module('cnc_direct_access')
    cnc_direct_access_available = True
except ImportError:
    cnc_direct_access_available = False

# module version
__version__ = '1.5.3'                           # module version

# transport timeouts
DEFAULT_REQUEST_FIRST_TIMEOUT      = 5.0       # default timeout for first server response chunk
DEFAULT_REQUEST_CHUNK_TIMEOUT      = 2.0       # default timeout between following response chunks
DEFAULT_FORCE_SYNC_TIMEOUT         = 160.0     # default timeout for force_sync server commands

# units mode
UM_METRIC                           = 0         # units mode: metric system
UM_IMPERIAL                         = 1         # units mode: imperial system

# analysis mode
ANALYSIS_MT                         = 'mt'      # model path with tools colors
ANALYSIS_RT                         = 'rt'      # real path with tools colors
ANALYSIS_RF                         = 'rf'      # real path with colors related to feed
ANALYSIS_RV                         = 'rv'      # real path with colors related to velocity
ANALYSIS_RZ                         = 'rz'      # real path with colors related to the Z level of the feed

# axis id
X_AXIS_ID                           = 1         # X axis id
Y_AXIS_ID                           = 2         # Y axis id
Z_AXIS_ID                           = 3         # Z axis id
A_AXIS_ID                           = 4         # A axis id
B_AXIS_ID                           = 5         # B axis id
C_AXIS_ID                           = 6         # C axis id
U_AXIS_ID                           = 7         # U axis id
V_AXIS_ID                           = 8         # V axis id
W_AXIS_ID                           = 9         # W axis id

# axis index (used on axes data arrays)
X_AXIS_INDEX                        = 0         # X-axis index
Y_AXIS_INDEX                        = 1         # Y-axis index
Z_AXIS_INDEX                        = 2         # Z-axis index
A_AXIS_INDEX                        = 3         # A-axis index
B_AXIS_INDEX                        = 4         # B-axis index
C_AXIS_INDEX                        = 5         # C-axis index

# axis mask
X_AXIS_MASK                         = 0x0001    # X-axis mask
Y_AXIS_MASK                         = 0x0002    # Y-axis mask
Z_AXIS_MASK                         = 0x0004    # Z-axis mask
A_AXIS_MASK                         = 0x0008    # A-axis mask
B_AXIS_MASK                         = 0x0010    # B-axis mask
C_AXIS_MASK                         = 0x0020    # C-axis mask
U_AXIS_MASK                         = 0x0040    # U-axis mask
V_AXIS_MASK                         = 0x0080    # V-axis mask
W_AXIS_MASK                         = 0x0100    # W-axis mask

# axes mask
X2Z_AXIS_MASK                       = 0x0007    # X to Z axes mask
X2C_AXIS_MASK                       = 0x003F    # X to C axes mask
X2W_AXIS_MASK                       = 0x01FF    # X to W axes mask

# compiler mode
CM_NONE                             = 0         # compiler mode: none
CM_MDI                              = 1         # compiler mode: MDI
CM_MACRO                            = 2         # compiler mode: macro
CM_PROGRAM                          = 3         # compiler mode: program
CM_PROGRAM_FROM_LINE                = 4         # compiler mode: program from line
CM_PROGRAM_FOR_RESUME               = 5         # compiler mode: program for resume
CM_PROGRAM_FOR_RESUME_FROM_LINE     = 6         # compiler mode: program for resume from line
CM_PROGRAM_FOR_ANALYSIS             = 7         # compiler mode: program for analysis

# compiler state
CS_INIT                             = 0         # compiler state: init
CS_READY                            = 1         # compiler state: ready
CS_ERROR                            = 2         # compiler state: error
CS_FIRST_STEP                       = 3         # compiler state: first step
CS_FIRST_STEP_RUNNING               = 4         # compiler state: first step running
CS_WAITING_FOR_DATA                 = 5         # compiler state: waiting for data
CS_WAITING_FOR_DATA_RUNNING         = 6         # compiler state: waiting for data running
CS_FINISHED                         = 7         # compiler state: finished

# jog command
JC_NONE                             = 0         # none (or stop the active JOG movement)
JC_X_BW                             = 1         # start the JOG X-axis moving backward
JC_X_FW                             = 2         # start the JOG X-axis moving forward
JC_Y_BW                             = 3         # start the JOG Y-axis moving backward
JC_Y_FW                             = 4         # start the JOG Y-axis moving forward
JC_Z_BW                             = 5         # start the JOG Z-axis moving backward
JC_Z_FW                             = 6         # start the JOG Z-axis moving forward
JC_A_BW                             = 7         # start the JOG A-axis moving backward
JC_A_FW                             = 8         # start the JOG A-axis moving forward
JC_B_BW                             = 9         # start the JOG B-axis moving backward
JC_B_FW                             = 10        # start the JOG B-axis moving forward
JC_C_BW                             = 11        # start the JOG C-axis moving backward
JC_C_FW                             = 12        # start the JOG C-axis moving forward

# state machine
SM_DISCONNECTED                     = 0         # Control Software state: internal state : DISCONNECTED
SM_SIMULATOR                        = 1         # Control Software state: internal state : SIMULATOR
SM_INIT                             = 2         # CNC Board: SM_INIT                     : INIT
SM_INIT_FIELDBUS                    = 3         # CNC Board: SM_INIT_FIELDBUS            : INIT FIELDBUS
SM_ALARM                            = 4         # CNC Board: ST_MACH.SM_ALARM            : ALARM
SM_IDLE                             = 5         # CNC Board: ST_MACH.SM_IDLE             : IDLE
SM_HOMING                           = 6         # CNC Board: ST_MACH.SM_HOMING           : HOMING
SM_JOG                              = 7         # CNC Board: ST_MACH.SM_JOG              : JOG
SM_RUN                              = 8         # CNC Board: ST_MACH.SM_RUN              : RUN
SM_PAUSE                            = 9         # CNC Board: ST_MACH.SM_PAUSE            : PAUSE
SM_LIMIT                            = 10        # CNC Board: ST_MACH.SM_LIMIT            : LIMIT
SM_MEASURE_TOOL                     = 11        # CNC Board: ST_MACH.SM_MEASURE_TOOL     : MEASURE TOOL
SM_SCAN_3D                          = 12        # CNC Board: ST_MACH.SM_SCAN3D           : SCANNING
SM_SAFETY_JOG                       = 13        # CNC Board: ST_MACH.SM_SAFETY_IDLE      : SAFETY JOG
SM_CHANGE_TOOL                      = 14        # CNC Board: ST_MACH.SM_CHANGE_TOOL      : CHANGE TOOL
SM_SAFETY                           = 15        # CNC Board: ST_MACH.SM_SAFETY           : SAFETY
SM_WAIT_MAIN_POWER                  = 16        # CNC Board: ST_MACH.SM_WAIT_MAIN_POWER  : WAIT MAIN POWER
SM_RETRACT                          = 17        # CNC Board: ST_MACH.SM_RETRACT          : RETRACT

# simulator state
SIM_IDLE                            = 0         # simulator state: idle
SIM_RUN                             = 1         # simulator state: run
SIM_PAUSE                           = 2         # simulator state: pause

# cnc connection state
CCS_DISCONNECTED                    = 0         # CNC Connection State: disconnected
CCS_CONNECTING                      = 1         # CNC Connection State: connecting
CCS_CONNECTED                       = 2         # CNC Connection State: connected
CCS_ERROR                           = 3         # CNC Connection State: error

# spindle direction
SD_STOPPED                          = 1         # spindle direction: stopped
SD_CW                               = 2         # spindle direction: clockwise
SD_CCW                              = 3         # spindle direction: counterclockwise

# spindle phase
SP_STOPPED                          = 0         # spindle phase: stopped
SP_RUNNING                          = 1         # spindle phase: running
SP_RUNNING_WAIT_SETTLE              = 2         # spindle phase: running, waiting for settle time
SP_RUNNING_WAIT_AT_SPEED            = 3         # spindle phase: running, waiting for at-speed input
SP_STOPPING_WAIT_SETTLE             = 4         # spindle phase: stopping, waiting for settle time
SP_STOPPING_WAIT_ZERO_SPEED         = 5         # spindle phase: stopping, waiting for zero-speed input

# spindle shaft
ST_STOPPED                          = 0         # spindle shaft: stopped
ST_ROTATING                         = 1         # spindle shaft: rotating

# spindle status
SS_COLLET_OPEN                      = 0         # spindle status: collet open
SS_COLLET_CLOSED_TOOL_HOLDER_ABSENT = 1         # spindle status: collet closed tool holder absent
SS_TOOL_HOLDER_BLOCKED_CORRECTLY    = 2         # spindle status: tool holder blocked correctly

# tool type
TT_GENERIC                          = 0         # tool type: generic
TT_FLAT_END_MILL                    = 1         # tool type: flat end mill
TT_BALL_NOSE_END_MILL               = 2         # tool type: ball nose end mill
TT_DRILL                            = 3         # tool type: drill
TT_PROBE                            = 4         # tool type: probe
TT_SAW                              = 5         # tool type: saw
TT_PLASMA                           = 6         # tool type: plasma
TT_DRAG_KNIFE                       = 7         # tool type: drag knife
TT_LATHE                            = 8         # tool type: lathe
TT_LASER                            = 9         # tool type: laser
TT_WATER_JET                        = 10        # tool type: water jet

# units mode
UM_METRIC                           = 0         # units mode: metric (mm)
UM_IMPERIAL                         = 1         # units mode: imperial (in)

# work mode
WM_NORMAL                           = 0         # work mode: normal
WM_WORK_ORDER                       = 1         # work mode: work order

# work order file type
WO_FT_DIRECTORY                     = 0         # work order file type: directory
WO_FT_FILE                          = 1         # work order file type: file

# work order priority
WO_PR_LOWEST                        = 0         # work order priority: lowest
WO_PR_LOW                           = 1         # work order priority: low
WO_PR_NORMAL                        = 2         # work order priority: normal
WO_PR_HIGH                          = 3         # work order priority: high
WO_PR_HIGHEST                       = 4         # work order priority: highest

# work order file state
WO_FS_CLOSED                        = 0         # work order file state: closed
WO_FS_OPEN                          = 1         # work order file state: open
WO_FS_RUNNING                       = 2         # work order file state: running

# work order state
WO_ST_DRAFT                         = 0         # work order state: draft
WO_ST_EDIT                          = 1         # work order state: edit
WO_ST_RELEASED                      = 2         # work order state: released
WO_ST_READY                         = 3         # work order state: ready
WO_ST_ACTIVE                        = 4         # work order state: active
WO_ST_RUNNING                       = 5         # work order state: running
WO_ST_COMPLETED                     = 6         # work order state: completed
WO_ST_ARCHIVED                      = 7         # work order state: archived
WO_ST_DO_NOT_EXITS                  = 8         # work order state: does not exists

# work order log id
WO_LI_NONE                          = 0         # work order log id: none
WO_LI_ACTIVATED                     = 1         # work order log id: activated
WO_LI_DEACTIVATED                   = 2         # work order log id: deactivated
WO_LI_FILE_OPENED                   = 3         # work order log id: opened
WO_LI_FILE_CLOSED                   = 4         # work order log id: closed
WO_LI_FILE_STARTED                  = 5         # work order log id: started
WO_LI_FILE_STOPPED                  = 6         # work order log id: stopped
WO_LI_FILE_FINISHED                 = 7         # work order log id: finished
WO_LI_ARCHIVED                      = 8         # work order log id: archived

# machine type
MT_MILL                             = 0         # machine type: mill
MT_LATHE                            = 1         # machine type: lathe

# kinematics model
KM_TRIVIAL                          = 0         # kinematics model: trivial
KM_INDEPENDENT_ROT_AXES             = 1         # kinematics model: independent rotational axes
KM_ROTARY_TABLE_A                   = 10        # kinematics model: rotary table A
KM_ROTARY_TABLE_B                   = 11        # kinematics model: rotary table B
KM_TILTING_HEAD_A                   = 20        # kinematics model: tilting head A
KM_TILTING_HEAD_B                   = 21        # kinematics model: tilting head B
KM_ROTARY_TABLE_AB                  = 30        # kinematics model: rotary table A/B
KM_ROTARY_TABLE_BA                  = 31        # kinematics model: rotary table B/A
KM_ROTARY_TABLE_AC                  = 32        # kinematics model: rotary table A/C
KM_ROTARY_TABLE_BC                  = 33        # kinematics model: rotary table B/C
KM_TILTING_HEAD_AB                  = 40        # kinematics model: tilting head A/B
KM_TILTING_HEAD_BA                  = 41        # kinematics model: tilting head B/A
KM_TILTING_HEAD_CA                  = 42        # kinematics model: tilting head C/A
KM_TILTING_HEAD_CB                  = 43        # kinematics model: tilting head C/B
KM_TILTING_HEAD_CB_CUSTOM           = 100       # kinematics model: tilting head C/B custom

# axis type
AT_DISABLED                         = 0         # axis type: disabled
AT_LINEAR                           = 1         # axis type: linear axis
AT_ROTARY_FREE                      = 2         # axis type: rotary axis free
AT_ROTARY_HEAD                      = 3         # axis type: rotary axis for head
AT_ROTARY_TABLE                     = 4         # axis type: rotary axis for table
AT_GANTRY_1                         = 5         # axis type: slave axis for gantry 1
AT_GANTRY_2                         = 6         # axis type: slave axis for gantry 2: IMPLEMENTED ONLY ON ETHERCAT !!!
AT_GANTRY_3                         = 7         # axis type: slave axis for gantry 3: NOT IMPLEMENTED YET !!!

# operator request type
ORQT_NONE                           = 0         # operator request type: none

ORQT_USER_MEDIA_CONTINUE            = 1         # operator request type: user media with continue
ORQT_USER_MEDIA_STOP                = 2         # operator request type: user media with stop
ORQT_USER_MEDIA_STOP_CONTINUE       = 3         # operator request type: user media with stop or continue
ORQT_USER_MEDIA_VALUE_OR_STOP       = 4         # operator request type: user media with value, and continue, or stop
ORQT_USER_MEDIA_VALUES_OR_STOP      = 5         # operator request type: user media with values, and continue, or stop

ORQT_USER_MESSAGE_CONTINUE          = 6         # operator request type: user message with continue
ORQT_USER_MESSAGE_STOP              = 7         # operator request type: user message with stop
ORQT_USER_MESSAGE_STOP_CONTINUE     = 8         # operator request type: user message with stop or continue
ORQT_USER_MESSAGE_VALUE_OR_STOP     = 9         # operator request type: user message with value, and continue, or stop
ORQT_USER_MESSAGE_VALUES_OR_STOP    = 10        # operator request type: user message with values, and continue, or stop

# operator response type
ORPT_CONTINUE                       = 0         # operator response type = continue
ORPT_STOP                           = 1         # operator response type = stop

# runtime data state
RDST_IDLE                           = 0         # runtime data state: idle
RDST_WAITING_DATA                   = 1         # runtime data state: waiting for data
RDST_DATA_READY                     = 2         # runtime data state: data are ready

# runtime data canon code
RDCC_NOP                            = 0         # runtime data canon code: none operation
RDCC_STRAIGHT_PROBE                 = 24        # runtime data canon code: straight probe (G38.2|3|4|5)
RDCC_WAIT_INPUT                     = 48        # runtime data canon code: wait input (M66)
RDCC_USER_MESSAGE                   = 59        # runtime data canon code: user message (M109)
RDCC_USER_MEDIA_PATH                = 60        # runtime data canon code: user media (M120)
RDCC_READ_INPUT_GROUP               = 66        # runtime data canon code: read input group (M166/M167)

# function state name
FS_NM_SPINDLE_CW                    = 0         # function state name: spindle clockwise
FS_NM_SPINDLE_CCW                   = 1         # function state name: spindle counter-clockwise
FS_NM_MIST                          = 10        # function state name: cooler mist
FS_NM_FLOOD                         = 11        # function state name: cooler flood
FS_NM_TORCH                         = 20        # function state name: plasma/laser/waterjet torch
FS_NM_THC_DISABLED                  = 21        # function state name: plasma/laser/waterjet THC disabled
FS_NM_JOG_MODE                      = 30        # function state name: jog movements mode
FS_NM_AUX_01                        = 40        # function state name: digital output auxiliary 1
FS_NM_AUX_02                        = 41        # function state name: digital output auxiliary 2
FS_NM_AUX_03                        = 42        # function state name: digital output auxiliary 3
FS_NM_AUX_04                        = 43        # function state name: digital output auxiliary 4
FS_NM_AUX_05                        = 44        # function state name: digital output auxiliary 5
FS_NM_AUX_06                        = 45        # function state name: digital output auxiliary 6
FS_NM_AUX_07                        = 46        # function state name: digital output auxiliary 7
FS_NM_AUX_08                        = 47        # function state name: digital output auxiliary 8
FS_NM_AUX_09                        = 48        # function state name: digital output auxiliary 9
FS_NM_AUX_10                        = 49        # function state name: digital output auxiliary 10
FS_NM_AUX_11                        = 50        # function state name: digital output auxiliary 11
FS_NM_AUX_12                        = 51        # function state name: digital output auxiliary 12
FS_NM_AUX_13                        = 52        # function state name: digital output auxiliary 13
FS_NM_AUX_14                        = 53        # function state name: digital output auxiliary 14
FS_NM_AUX_15                        = 54        # function state name: digital output auxiliary 15
FS_NM_AUX_16                        = 55        # function state name: digital output auxiliary 16
FS_NM_AUX_17                        = 56        # function state name: digital output auxiliary 17
FS_NM_AUX_18                        = 57        # function state name: digital output auxiliary 18
FS_NM_AUX_19                        = 58        # function state name: digital output auxiliary 19
FS_NM_AUX_20                        = 59        # function state name: digital output auxiliary 20
FS_NM_AUX_21                        = 60        # function state name: digital output auxiliary 21
FS_NM_AUX_22                        = 61        # function state name: digital output auxiliary 22
FS_NM_AUX_23                        = 62        # function state name: digital output auxiliary 23
FS_NM_AUX_24                        = 63        # function state name: digital output auxiliary 24
FS_NM_AUX_25                        = 64        # function state name: digital output auxiliary 25
FS_NM_AUX_26                        = 65        # function state name: digital output auxiliary 26
FS_NM_AUX_27                        = 66        # function state name: digital output auxiliary 27
FS_NM_AUX_28                        = 67        # function state name: digital output auxiliary 28
FS_NM_AUX_29                        = 68        # function state name: digital output auxiliary 29
FS_NM_AUX_30                        = 69        # function state name: digital output auxiliary 30
FS_NM_AUX_31                        = 70        # function state name: digital output auxiliary 31
FS_NM_AUX_32                        = 71        # function state name: digital output auxiliary 32

# function state mode
FS_MD_OFF                           = 0         # function state mode: set digital output state to OFF
FS_MD_ON                            = 1         # function state mode: set digital output state to ON
FS_MD_TOGGLE                        = 2         # function state mode: toggle actual digital output state
FS_MD_JOG_MODE_DEFAULT              = 3         # function state mode: set jog mode to default
FS_MD_JOG_MODE_ALONG_TOOL           = 4         # function state mode: set jog mode to along the tool
FS_MD_JOG_MODE_TOGGLE               = 5         # function state mode: toggle actual jog mode

# function state allowed combo
FS_ALLOWED_COMBO = {
    FS_NM_SPINDLE_CW:        {FS_MD_OFF, FS_MD_ON, FS_MD_TOGGLE},
    FS_NM_SPINDLE_CCW:       {FS_MD_OFF, FS_MD_ON, FS_MD_TOGGLE},
    FS_NM_MIST:              {FS_MD_OFF, FS_MD_ON, FS_MD_TOGGLE},
    FS_NM_FLOOD:             {FS_MD_OFF, FS_MD_ON, FS_MD_TOGGLE},
    FS_NM_TORCH:             {FS_MD_OFF, FS_MD_ON, FS_MD_TOGGLE},
    FS_NM_THC_DISABLED:      {FS_MD_OFF, FS_MD_ON, FS_MD_TOGGLE},
    FS_NM_JOG_MODE:          {FS_MD_JOG_MODE_DEFAULT, FS_MD_JOG_MODE_ALONG_TOOL, FS_MD_JOG_MODE_TOGGLE},
    FS_NM_AUX_01:            {FS_MD_OFF, FS_MD_ON, FS_MD_TOGGLE},
    FS_NM_AUX_02:            {FS_MD_OFF, FS_MD_ON, FS_MD_TOGGLE},
    FS_NM_AUX_03:            {FS_MD_OFF, FS_MD_ON, FS_MD_TOGGLE},
    FS_NM_AUX_04:            {FS_MD_OFF, FS_MD_ON, FS_MD_TOGGLE},
    FS_NM_AUX_05:            {FS_MD_OFF, FS_MD_ON, FS_MD_TOGGLE},
    FS_NM_AUX_06:            {FS_MD_OFF, FS_MD_ON, FS_MD_TOGGLE},
    FS_NM_AUX_07:            {FS_MD_OFF, FS_MD_ON, FS_MD_TOGGLE},
    FS_NM_AUX_08:            {FS_MD_OFF, FS_MD_ON, FS_MD_TOGGLE},
    FS_NM_AUX_09:            {FS_MD_OFF, FS_MD_ON, FS_MD_TOGGLE},
    FS_NM_AUX_10:            {FS_MD_OFF, FS_MD_ON, FS_MD_TOGGLE},
    FS_NM_AUX_11:            {FS_MD_OFF, FS_MD_ON, FS_MD_TOGGLE},
    FS_NM_AUX_12:            {FS_MD_OFF, FS_MD_ON, FS_MD_TOGGLE},
    FS_NM_AUX_13:            {FS_MD_OFF, FS_MD_ON, FS_MD_TOGGLE},
    FS_NM_AUX_14:            {FS_MD_OFF, FS_MD_ON, FS_MD_TOGGLE},
    FS_NM_AUX_15:            {FS_MD_OFF, FS_MD_ON, FS_MD_TOGGLE},
    FS_NM_AUX_16:            {FS_MD_OFF, FS_MD_ON, FS_MD_TOGGLE},
    FS_NM_AUX_17:            {FS_MD_OFF, FS_MD_ON, FS_MD_TOGGLE},
    FS_NM_AUX_18:            {FS_MD_OFF, FS_MD_ON, FS_MD_TOGGLE},
    FS_NM_AUX_19:            {FS_MD_OFF, FS_MD_ON, FS_MD_TOGGLE},
    FS_NM_AUX_20:            {FS_MD_OFF, FS_MD_ON, FS_MD_TOGGLE},
    FS_NM_AUX_21:            {FS_MD_OFF, FS_MD_ON, FS_MD_TOGGLE},
    FS_NM_AUX_22:            {FS_MD_OFF, FS_MD_ON, FS_MD_TOGGLE},
    FS_NM_AUX_23:            {FS_MD_OFF, FS_MD_ON, FS_MD_TOGGLE},
    FS_NM_AUX_24:            {FS_MD_OFF, FS_MD_ON, FS_MD_TOGGLE},
    FS_NM_AUX_25:            {FS_MD_OFF, FS_MD_ON, FS_MD_TOGGLE},
    FS_NM_AUX_26:            {FS_MD_OFF, FS_MD_ON, FS_MD_TOGGLE},
    FS_NM_AUX_27:            {FS_MD_OFF, FS_MD_ON, FS_MD_TOGGLE},
    FS_NM_AUX_28:            {FS_MD_OFF, FS_MD_ON, FS_MD_TOGGLE},
    FS_NM_AUX_29:            {FS_MD_OFF, FS_MD_ON, FS_MD_TOGGLE},
    FS_NM_AUX_30:            {FS_MD_OFF, FS_MD_ON, FS_MD_TOGGLE},
    FS_NM_AUX_31:            {FS_MD_OFF, FS_MD_ON, FS_MD_TOGGLE},
    FS_NM_AUX_32:            {FS_MD_OFF, FS_MD_ON, FS_MD_TOGGLE},
}

# show ui dialogs ID [ with Control Software in run as API Server ]
UID_ID_ABOUT                        = 1
UID_ID_ATC_MANAGEMENT               = 2         # requires connection with CNC in connected state
UID_ID_BOARD_ETHERCAT_MONITOR       = 3         # requires connection with CNC in connected state
UID_ID_BOARD_FIRMWARE_MANAGER       = 4
UID_ID_BOARD_MONITOR                = 5         # requires connection with CNC in connected state
UID_ID_BOARD_SETTINGS               = 6
UID_ID_CHANGE_BOARD_IP              = 7
UID_ID_MACROS_MANAGEMENT            = 8
UID_ID_PARAMETERS_LIBRARY           = 9
UID_ID_PROGRAM_SETTINGS             = 10
UID_ID_TOOLS_LIBRARY                = 11
UID_ID_WORK_COORDINATES             = 12

UID_ID_FIRST                        = UID_ID_ABOUT
UID_ID_LAST                         = UID_ID_WORK_COORDINATES

# service popup menu enabling mask [ with Control Software in run as API Server ] !!! UNUSED YET !!!
SPMEM_ABOUT                         =  1 << 0
SPMEM_ATC_MANAGEMENT                =  1 << 1
SPMEM_BOARD_ETHERCAT_MONITOR        =  1 << 2
SPMEM_BOARD_FIRMWARE_MANAGER        =  1 << 3
SPMEM_BOARD_MONITOR                 =  1 << 4
SPMEM_BOARD_SETTINGS                =  1 << 5
SPMEM_CHANGE_BOARD_IP               =  1 << 6
SPMEM_CONNECTION_OPEN               =  1 << 7
SPMEM_CONNECTION_CLOSE              =  1 << 8
SPMEM_EXIT                          =  1 << 9
SPMEM_MACROS_MANAGEMENT             =  1 << 10
SPMEM_PARAMETERS_LIBRARY            =  1 << 11
SPMEM_PROGRAM_SETTINGS              =  1 << 12
SPMEM_TOOLS_LIBRARY                 =  1 << 13
SPMEM_WORK_COORDINATES              =  1 << 14


class APIComparableMixin:
    """
    This class adds automatic recursive comparison to APIxx classes.
    It handles: nested classes, lists of objects, datetime, enum, etc.

    NOTE
    ====
    Mixing is a class that provides additional functionality to other classes through multiple inheritance,
    but is not intended to be instantiated on its own.
    """

    def is_equal(self, other: Any) -> bool:
        """Compare the instance with another of the same type."""
        if not isinstance(other, self.__class__):
            return False
        return _deep_compare(self.__dict__, other.__dict__)

    @staticmethod
    def are_equal(a: Any, b: Any) -> bool:
        """Compare two instances (they can be None)."""
        if a is None and b is None:
            return True
        if a is None or b is None:
            return False
        if a.__class__ is not b.__class__:
            return False
        return _deep_compare(a.__dict__, b.__dict__)

def _deep_compare(a: Any, b: Any) -> bool:
    """
    Deep recursive comparison.
    Handles: dict, list, objects with __dict__, primitive types.    """
    if type(a) != type(b):
        return False

    # lists (manages lists of objects or lists of primitives)
    if isinstance(a, list):
        if len(a) != len(b):
            return False
        return all(_deep_compare(x, y) for x, y in zip(a, b))

    # dictionaries (e.g., __dict__)
    if isinstance(a, dict):
        if a.keys() != b.keys():
            return False
        return all(_deep_compare(a[k], b[k]) for k in a)

    # objects with __dict__ (other classes)
    if hasattr(a, '__dict__'):
        return _deep_compare(a.__dict__, b.__dict__)

    # primitive types (int, str, float, bool, datetime, enum, etc.)
    return a == b

class APIAlarmsWarningsList(APIComparableMixin):
    """API data structure for alarms and warnings list."""

    class AlarmWarningData:
        """Data structure for alarm & warning list data."""
        def __init__(self):
            """Initialize alarm or warning entry data."""
            self.code: int                      = 0
            self.info_1: int                    = 0
            self.info_2: int                    = 0
            self.text: str                      = ''
            self.datetime: datetime             = datetime.min

    def __init__(self):
        """Initialize alarms and warnings list data."""
        self.has_data: bool                     = False
        self.list                               = []

class APIAnalogInputs(APIComparableMixin):
    """API data structure for analog inputs."""
    def __init__(self):
        """Initialize analog inputs data."""
        self.has_data                           = False
        self.value                              = [0.0] * 16

class APIAnalogOutputs(APIComparableMixin):
    """API data structure for analog outputs."""
    def __init__(self):
        """Initialize analog outputs data."""
        self.has_data                           = False
        self.value                              = [0.0] * 16

class APIAxesInfo(APIComparableMixin):
    """API data structure for axes info."""
    def __init__(self):
        """Initialize axes information data."""
        self.has_data                           = False
        self.joint_position                     = [0.0] * 6
        self.machine_position                   = [0.0] * 6
        self.program_position                   = [0.0] * 6
        self.machine_target_position            = [0.0] * 6
        self.program_target_position            = [0.0] * 6
        self.actual_velocity                    = [0.0] * 6
        self.working_wcs                        = 0
        self.working_offset                     = [0.0] * 6
        self.dynamic_offset                     = [0.0] * 3
        self.homing_done                        = False
        self.homing_done_mask                   = 0
        self.homing_running_mask                = 0
        self.homing_sensors_mask                = 0
        self.homing_correction_space            = [0.0] * 6

class APICncInfo(APIComparableMixin):
    """API data structure for cnc info."""
    def __init__(self):
        """Initialize CNC information data."""
        self.has_data                           = False
        self.file_name                          = ''
        self.units_mode                         = UM_METRIC
        self.axes_mask                          = 0
        self.state_machine                      = SM_DISCONNECTED
        self.connection_state                   = CCS_DISCONNECTED
        self.controller_settings_crc            = 0
        self.interp_buffer_level                = 0
        self.gcode_line                         = 0
        self.planned_time                       = '00:00:00'
        self.worked_time                        = '00:00:00'
        self.hud_user_message                   = ''
        self.toolpath_id                        = ''
        self.operator_request_id_pending        = ''
        self.program_gcode_sync_required        = False
        self.current_alarm_datetime             = datetime.min
        self.current_alarm_code                 = 0
        self.current_alarm_info1                = 0
        self.current_alarm_info2                = 0
        self.current_alarm_text                 = ''
        self.current_warning_datetime           = datetime.min
        self.current_warning_code               = 0
        self.current_warning_info1              = 0
        self.current_warning_info2              = 0
        self.current_warning_text               = ''
        self.aux_outputs                        = 0
        self.coolant_mist                       = False
        self.coolant_flood                      = False
        self.lube_axis_cycles_made              = 0
        self.lube_axis_time_to_next_cycle       = 0
        self.lube_spindle_cycles_made           = 0
        self.lube_spindle_time_to_next_cycle    = 0
        self.feed_programmed                    = 0.0
        self.feed_target                        = 0.0
        self.feed_reference                     = 0.0
        self.spindle_programmed                 = 0
        self.spindle_target                     = 0
        self.spindle_actual                     = 0
        self.spindle_load                       = 0
        self.spindle_torque                     = 0
        self.spindle_phase                      = SP_STOPPED
        self.spindle_direction                  = SD_STOPPED
        self.spindle_not_ready                  = False
        self.spindle_shaft                      = ST_STOPPED
        self.spindle_status                     = SS_COLLET_OPEN
        self.spindle_voltage                    = 0
        self.override_jog                       = 0
        self.override_jog_min                   = 0
        self.override_jog_max                   = 100
        self.override_jog_enabled               = False
        self.override_jog_locked                = False
        self.override_spindle                   = 0
        self.override_spindle_min               = 0
        self.override_spindle_max               = 100
        self.override_spindle_enabled           = False
        self.override_spindle_locked            = False
        self.override_fast                      = 0
        self.override_fast_min                  = 0
        self.override_fast_max                  = 100
        self.override_fast_enabled              = False
        self.override_fast_locked               = False
        self.override_feed                      = 0
        self.override_feed_min                  = 0
        self.override_feed_max                  = 100
        self.override_feed_enabled              = False
        self.override_feed_locked               = False
        self.override_feed_custom_1             = 0
        self.override_feed_custom_1_min         = 0
        self.override_feed_custom_1_max         = 100
        self.override_feed_custom_1_enabled     = False
        self.override_feed_custom_1_locked      = False
        self.override_feed_custom_2             = 0
        self.override_feed_custom_2_min         = 0
        self.override_feed_custom_2_max         = 100
        self.override_feed_custom_2_enabled     = False
        self.override_feed_custom_2_locked      = False
        self.override_plasma_power              = 0
        self.override_plasma_power_min          = 0
        self.override_plasma_power_max          = 100
        self.override_plasma_power_enabled      = False
        self.override_plasma_power_locked       = False
        self.override_plasma_voltage            = 0
        self.override_plasma_voltage_min        = 0
        self.override_plasma_voltage_max        = 100
        self.override_plasma_voltage_enabled    = False
        self.override_plasma_voltage_locked     = False
        self.tool_id                            = 0
        self.tool_slot                          = 0
        self.tool_slot_enabled                  = False
        self.tool_type                          = TT_GENERIC
        self.tool_diameter                      = 0.0
        self.tool_offset_x                      = 0.0
        self.tool_offset_y                      = 0.0
        self.tool_offset_z                      = 0.0
        self.tool_param_1                       = 0.0
        self.tool_param_2                       = 0.0
        self.tool_param_3                       = 0.0
        self.tool_description                   = ''
        self.simulator_available                = False
        self.simulator_state                    = SIM_IDLE
        self.simulator_planned_time_ms          = 0
        self.simulator_current_time_ms          = 0
        self.simulator_speed_track              = 0

class APICncParameters(APIComparableMixin):
    """API data structure for cnc parameters."""
    def __init__(self):
        """Initialize CNC parameters data."""
        self.has_data                           = False
        self.address                            = 0
        self.values                             = []
        self.descriptions                       = []

class APICompileInfo(APIComparableMixin):
    """API data structure for compile info."""
    def __init__(self):
        """Initialize compile information data."""
        self.has_data                           = False
        self.code                               = 0
        self.code_line                          = 0
        self.file_line                          = 0
        self.file_name                          = ''
        self.message                            = ''
        self.mode                               = CM_NONE
        self.state                              = CS_INIT

class APICoordinateSystemsInfo(APIComparableMixin):
    """API coordinate systems info."""
    def __init__(self):
        """Initialize coordinate systems information data."""
        self.has_data                           = False
        self.working_wcs                        = 0
        self.working_offset                     = [0.0] * 6
        self.wcs_1                              = [0.0] * 6
        self.wcs_2                              = [0.0] * 6
        self.wcs_3                              = [0.0] * 6
        self.wcs_4                              = [0.0] * 6
        self.wcs_5                              = [0.0] * 6
        self.wcs_6                              = [0.0] * 6
        self.wcs_7                              = [0.0] * 6
        self.wcs_8                              = [0.0] * 6
        self.wcs_9                              = [0.0] * 6

class APIDigitalInputs(APIComparableMixin):
    """API data structure for digital inputs."""
    def __init__(self):
        """Initialize digital inputs data."""
        self.has_data                           = False
        self.value                              = [0] * 128

class APIDigitalOutputs(APIComparableMixin):
    """API data structure for digital outputs."""
    def __init__(self):
        """Initialize digital outputs data."""
        self.has_data                           = False
        self.value                              = [0] * 128

class APIEnabledCommands(APIComparableMixin):
    """API data structure for enabled commands."""
    def __init__(self):
        """Initialize enabled commands data."""
        self.has_data                           = False
        self.cnc_csfm_aux                       = 0
        self.cnc_csfm_cooler_flood              = False
        self.cnc_csfm_cooler_mist               = False
        self.cnc_csfm_jog_mode                  = False
        self.cnc_csfm_spindle_cw                = False
        self.cnc_csfm_spindle_ccw               = False
        self.cnc_csfm_thc_disabled              = False
        self.cnc_csfm_torch                     = False
        self.cnc_connection_close               = False
        self.cnc_connection_open                = False
        self.cnc_continue                       = False
        self.cnc_homing                         = 0
        self.cnc_jog_command                    = 0
        self.cnc_mdi_command                    = False
        self.cnc_parameters                     = False
        self.cnc_pause                          = False
        self.cnc_resume                         = False
        self.cnc_resume_from_line               = False
        self.cnc_resume_from_point              = False
        self.cnc_start                          = False
        self.cnc_start_from_line                = False
        self.cnc_start_from_point               = False
        self.cnc_stop                           = False
        self.program_analysis                   = False
        self.program_analysis_abort             = False
        self.program_gcode_add_text             = False
        self.program_gcode_clear                = False
        self.program_gcode_modified             = False
        self.program_gcode_set_text             = False
        self.program_load                       = False
        self.program_new                        = False
        self.program_save                       = False
        self.program_save_as                    = False
        self.reset_alarms                       = False
        self.reset_alarms_history               = False
        self.reset_warnings                     = False
        self.reset_warnings_history             = False
        self.set_dynamic_offsets                = 0
        self.set_kinematics                     = False
        self.set_program_position               = 0
        self.set_simulator_current_time_ms      = False
        self.set_simulator_speed_track          = False
        self.show_ui_dialog                     = False
        self.simulator_continue                 = False
        self.simulator_pause                    = False
        self.simulator_start                    = False
        self.simulator_step_backward            = False
        self.simulator_step_forward             = False
        self.simulator_stop                     = False
        self.tools_lib_write                    = False

class APILocalizationInfo(APIComparableMixin):
    """API data structure with machine settings."""

    class LocalizationData:
        """Data structure for alarm & warning list data."""
        def __init__(self):
            """Initialize localization entry data."""
            self.locale_name                     = None
            self.description                    = None
            self.owner                          = None
            self.revisor                        = None
            self.version                        = None
            self.date                           = None
            self.program                        = None

    def __init__(self):
        """Initialize localization information data."""
        self.has_data                           = False
        self.units_mode                         = UM_METRIC
        self.locale_name                        = None
        self.description                        = None
        self.list                               = []

class APIMachineSettings(APIComparableMixin):
    """API data structure with machine settings."""
    def __init__(self):
        """Initialize machine settings data."""
        self.has_data                           = False
        self.axis_machine_type                  = MT_MILL
        self.axis_kinematics_model              = KM_TRIVIAL
        self.axis_x_type                        = AT_DISABLED
        self.axis_x_max_vel                     = 0.0
        self.axis_x_acc                         = 0.0
        self.axis_x_min_lim                     = 0.0
        self.axis_x_max_lim                     = 0.0
        self.axis_y_type                        = AT_DISABLED
        self.axis_y_max_vel                     = 0.0
        self.axis_y_acc                         = 0.0
        self.axis_y_min_lim                     = 0.0
        self.axis_y_max_lim                     = 0.0
        self.axis_z_type                        = AT_DISABLED
        self.axis_z_max_vel                     = 0.0
        self.axis_z_acc                         = 0.0
        self.axis_z_min_lim                     = 0.0
        self.axis_z_max_lim                     = 0.0
        self.axis_a_type                        = AT_DISABLED
        self.axis_a_max_vel                     = 0.0
        self.axis_a_acc                         = 0.0
        self.axis_a_min_lim                     = 0.0
        self.axis_a_max_lim                     = 0.0
        self.axis_b_type                        = AT_DISABLED
        self.axis_b_max_vel                     = 0.0
        self.axis_b_acc                         = 0.0
        self.axis_b_min_lim                     = 0.0
        self.axis_b_max_lim                     = 0.0
        self.axis_c_type                        = AT_DISABLED
        self.axis_c_max_vel                     = 0.0
        self.axis_c_acc                         = 0.0
        self.axis_c_min_lim                     = 0.0
        self.axis_c_max_lim                     = 0.0
        self.kinematics_h_x                     = 0.0
        self.kinematics_h_y                     = 0.0
        self.kinematics_h_z                     = 0.0
        self.kinematics_j_x                     = 0.0
        self.kinematics_j_y                     = 0.0
        self.kinematics_j_z                     = 0.0

class APIMachiningInfoUsedTool(APIComparableMixin):
    """API data structure with used tool info."""
    def __init__(self):
        """Initialize used tool machining data."""
        self.tool_id                            = 0
        self.in_fast                            = 0.0
        self.in_feed                            = 0.0

class APIMachiningInfo(APIComparableMixin):
    """API data structure for machining info."""
    def __init__(self):
        """Initialize machining information data."""
        self.has_data                           = False
        self.tool_path_in_fast                  = 0.0
        self.tool_path_in_feed                  = 0.0
        self.total_path                         = 0.0
        self.planned_time                       = '00:00:00'
        self.used_tool                          = []
        self.tcp_extents_in_fast_min_x          = 0.0
        self.tcp_extents_in_fast_min_y          = 0.0
        self.tcp_extents_in_fast_min_z          = 0.0
        self.tcp_extents_in_fast_max_x          = 0.0
        self.tcp_extents_in_fast_max_y          = 0.0
        self.tcp_extents_in_fast_max_z          = 0.0
        self.tcp_extents_in_fast_length_x       = 0.0
        self.tcp_extents_in_fast_length_y       = 0.0
        self.tcp_extents_in_fast_length_z       = 0.0
        self.tcp_extents_in_feed_min_x          = 0.0
        self.tcp_extents_in_feed_min_y          = 0.0
        self.tcp_extents_in_feed_min_z          = 0.0
        self.tcp_extents_in_feed_max_x          = 0.0
        self.tcp_extents_in_feed_max_y          = 0.0
        self.tcp_extents_in_feed_max_z          = 0.0
        self.tcp_extents_in_feed_length_x       = 0.0
        self.tcp_extents_in_feed_length_y       = 0.0
        self.tcp_extents_in_feed_length_z       = 0.0
        self.joints_in_fast_min_x               = 0.0
        self.joints_in_fast_min_y               = 0.0
        self.joints_in_fast_min_z               = 0.0
        self.joints_in_fast_min_a               = 0.0
        self.joints_in_fast_min_b               = 0.0
        self.joints_in_fast_min_c               = 0.0
        self.joints_in_fast_max_x               = 0.0
        self.joints_in_fast_max_y               = 0.0
        self.joints_in_fast_max_z               = 0.0
        self.joints_in_fast_max_a               = 0.0
        self.joints_in_fast_max_b               = 0.0
        self.joints_in_fast_max_c               = 0.0
        self.joints_in_fast_length_x            = 0.0
        self.joints_in_fast_length_y            = 0.0
        self.joints_in_fast_length_z            = 0.0
        self.joints_in_fast_length_a            = 0.0
        self.joints_in_fast_length_b            = 0.0
        self.joints_in_fast_length_c            = 0.0
        self.joints_in_feed_min_x               = 0.0
        self.joints_in_feed_min_y               = 0.0
        self.joints_in_feed_min_z               = 0.0
        self.joints_in_feed_min_a               = 0.0
        self.joints_in_feed_min_b               = 0.0
        self.joints_in_feed_min_c               = 0.0
        self.joints_in_feed_max_x               = 0.0
        self.joints_in_feed_max_y               = 0.0
        self.joints_in_feed_max_z               = 0.0
        self.joints_in_feed_max_a               = 0.0
        self.joints_in_feed_max_b               = 0.0
        self.joints_in_feed_max_c               = 0.0
        self.joints_in_feed_length_x            = 0.0
        self.joints_in_feed_length_y            = 0.0
        self.joints_in_feed_length_z            = 0.0
        self.joints_in_feed_length_a            = 0.0
        self.joints_in_feed_length_b            = 0.0
        self.joints_in_feed_length_c            = 0.0

class APIMRUProgramsList(APIComparableMixin):
    """API data structure for MRU program list."""
    def __init__(self):
        """Initialize operator request data."""
        self.has_data                           = False
        self.items: List[str]                   = []

class APIOperatorRequest(APIComparableMixin):
    """API data structure for operator request."""
    def __init__(self):
        """Initialize operator request data."""
        self.has_data                           = False
        self.id                                 = ''
        self.type                               = ORQT_NONE
        self.media                              = ''
        self.message                            = ''
        self.data_elements                      = 0
        self.data_d01                           = None
        self.data_d02                           = None
        self.data_d03                           = None
        self.data_d04                           = None
        self.data_d05                           = None
        self.data_d06                           = None
        self.data_d07                           = None
        self.data_d08                           = None
        self.data_d09                           = None
        self.data_d10                           = None
        self.external_continue_requested        = False

class APIOperatorResponse(APIComparableMixin):
    """API data structure for operator response."""
    def __init__(self):
        """Initialize operator response data."""
        self.id                                 = ''
        self.type                               = ORPT_STOP
        self.data_elements                      = 0
        self.data_d01                           = None
        self.data_d02                           = None
        self.data_d03                           = None
        self.data_d04                           = None
        self.data_d05                           = None
        self.data_d06                           = None
        self.data_d07                           = None
        self.data_d08                           = None
        self.data_d09                           = None
        self.data_d10                           = None

    def copy_data_from_request(self, request: APIOperatorRequest | None = None) -> bool:
        """Copy data from a request."""
        if not isinstance(request, APIOperatorRequest):
            return False
        self.data_elements                      = request.data_elements
        self.data_d01                           = request.data_d01
        self.data_d02                           = request.data_d02
        self.data_d03                           = request.data_d03
        self.data_d04                           = request.data_d04
        self.data_d05                           = request.data_d05
        self.data_d06                           = request.data_d06
        self.data_d07                           = request.data_d07
        self.data_d08                           = request.data_d08
        self.data_d09                           = request.data_d09
        self.data_d10                           = request.data_d10
        return True

class APIProgramInfo(APIComparableMixin):
    """API data structure for program info."""
    def __init__(self):
        """Initialize program information data."""
        self.has_data                           = False
        self.file_name                          = ""
        self.code                               = ""

class APIProgrammedPoints(APIComparableMixin):
    """API data structure for programmed points."""
    def __init__(self):
        """Initialize programmed points data."""
        self.has_data                           = False
        self.points                             = []

class APIRuntimeDataPendingItem(APIComparableMixin):
    """API data structure for runtime data pending item."""
    def __init__(self):
        """Initialize runtime data pending item."""
        self.gcode_line                         = 0
        self.canon_id                           = 0
        self.canon_code                         = RDCC_NOP
        self.canon_segment                      = 0
        self.text                               = ''

class APIRuntimeDataAcquiredItem(APIComparableMixin):
    """API data structure for runtime data acquired item."""
    def __init__(self):
        """Initialize runtime data acquired item."""
        self.datetime                           = datetime.min
        self.gcode_line                         = 0
        self.canon_id                           = 0
        self.canon_code                         = RDCC_NOP
        self.canon_segment                      = 0
        self.text                               = ''
        self.data                               = []

class APIRuntimeData(APIComparableMixin):
    """API data structure for runtime data."""
    def __init__(self):
        """Initialize runtime data."""
        self.has_data                           = False
        self.state                              = RDST_IDLE
        self.pending_item                       = APIRuntimeDataPendingItem()
        self.acquired_items: List[APIRuntimeDataAcquiredItem] = []

class APIScanningLaserInfo(APIComparableMixin):
    """API data structure for scanning laser info."""
    def __init__(self):
        """Initialize scanning laser information data."""
        self.has_data                           = False
        self.laser_out_bit                      = 0
        self.laser_out_umf                      = 0
        self.laser_h_measure                    = 0.0
        self.laser_mcs_x_position               = 0.0
        self.laser_mcs_y_position               = 0.0
        self.laser_mcs_z_position               = 0.0

class APISystemInfo(APIComparableMixin):
    """API data structure for system info."""
    def __init__(self):
        """Initialize system information data."""
        self.has_data = False
        self.machine_name                       = ''
        self.control_software_version           = ''
        self.core_version                       = ''
        self.api_server_version                 = ''
        self.firmware_version                   = ''
        self.firmware_version_tag               = ''
        self.firmware_interface_level           = ''
        self.order_code                         = ''
        self.customer_id                        = ''
        self.serial_number                      = ''
        self.part_number                        = ''
        self.customization_number               = ''
        self.hardware_version                   = ''
        self.operative_system                   = ''
        self.operative_system_crc               = ''
        self.pld_version                        = ''
        self.licensed_feature_panel_pc          = False
        self.licensed_feature_panel_pc_demo     = False
        self.licensed_feature_work_orders       = False
        self.licensed_feature_opc_ua_server     = False
        self.licensed_feature_probe_sdk_g1      = False
        self.licensed_feature_probe_sdk_g2      = False
        self.licensed_feature_probe_sdk_g3      = False
        self.licensed_feature_probe_sdk_g4      = False
        self.licensed_feature_probe_sdk_g5      = False

class APIToolpathData(APIComparableMixin):
    """API data structure for toolpath data."""
    def __init__(self):
        """Initialize toolpath data."""
        self.has_data                           = False
        self.data                               = None

class APIToolsLibCount(APIComparableMixin):
    """API data structure for tools library count."""
    def __init__(self):
        """Initialize tool library count data."""
        self.has_data                           = False
        self.count                              = 0

class APIToolsLibInfoForGet(APIComparableMixin):
    """API data structure for tools lib info for get."""
    def __init__(self):
        """Initialize tool library read data."""
        self.tool_index                         = 0
        self.tool_id                            = 0
        self.tool_slot                          = False
        self.tool_type                          = TT_GENERIC
        self.tool_diameter                      = 0.0
        self.tool_offset_x                      = 0.0
        self.tool_offset_y                      = 0.0
        self.tool_offset_z                      = 0.0
        self.tool_param_1                       = 0.0
        self.tool_param_2                       = 0.0
        self.tool_param_3                       = 0.0
        self.tool_param_4                       = 0.0
        self.tool_param_5                       = 0.0
        self.tool_param_6                       = 0.0
        self.tool_param_7                       = 0.0
        self.tool_param_8                       = 0.0
        self.tool_param_9                       = 0.0
        self.tool_param_10                      = 0.0
        self.tool_param_51                      = 0.0
        self.tool_param_52                      = 0.0
        self.tool_param_53                      = 0.0
        self.tool_param_54                      = 0.0
        self.tool_param_55                      = 0.0
        self.tool_param_56                      = 0.0
        self.tool_param_57                      = 0.0
        self.tool_param_58                      = 0.0
        self.tool_param_59                      = 0.0
        self.tool_param_60                      = 0.0
        self.tool_description                   = ''

class APIToolsLibInfoForSet(APIComparableMixin):
    """API data structure for tools lib info for set."""
    def __init__(self):
        """Initialize tool library write data."""
        self.tool_index                         = None
        self.tool_id                            = None
        self.tool_slot                          = None
        self.tool_type                          = None
        self.tool_diameter                      = None
        self.tool_offset_x                      = None
        self.tool_offset_y                      = None
        self.tool_offset_z                      = None
        self.tool_param_1                       = None
        self.tool_param_2                       = None
        self.tool_param_3                       = None
        self.tool_param_4                       = None
        self.tool_param_5                       = None
        self.tool_param_6                       = None
        self.tool_param_7                       = None
        self.tool_param_8                       = None
        self.tool_param_9                       = None
        self.tool_param_10                      = None
        self.tool_param_51                      = None
        self.tool_param_52                      = None
        self.tool_param_53                      = None
        self.tool_param_54                      = None
        self.tool_param_55                      = None
        self.tool_param_56                      = None
        self.tool_param_57                      = None
        self.tool_param_58                      = None
        self.tool_param_59                      = None
        self.tool_param_60                      = None
        self.tool_description                   = None

class APIToolsLibInfo(APIComparableMixin):
    """API data structure for tools library infos."""
    def __init__(self):
        """Initialize tool library information container."""
        self.has_data                           = False
        self.data: APIToolsLibInfoForGet        = APIToolsLibInfoForGet()

class APIToolsLibInfos(APIComparableMixin):
    """API data structure for tools library infos."""
    def __init__(self):
        """Initialize tool library information list data."""
        self.has_data                           = False
        self.slot_enabled                       = False
        self.data: List[APIToolsLibInfoForGet]  = []

class APIToolsLibToolIndexFromId(APIComparableMixin):
    """API data structure for tools library tool index from Id."""
    def __init__(self):
        """Initialize tool library index lookup data."""
        self.has_data                           = False
        self.index                              = -1

class APIVMGeometryInfo(APIComparableMixin):
    """API data structure for virtual machine geometry info."""
    def __init__(self):
        """Initialize virtual machine geometry data."""
        self.has_data                           = False
        self.name                               = ''
        self.x                                  = 0.0
        self.y                                  = 0.0
        self.z                                  = 0.0
        self.color                              = 0
        self.scale                              = 0.0
        self.visible                            = False
        self.edges_angle                        = 0.0
        self.edges_visible                      = False

class APIWorkInfo(APIComparableMixin):
    """API data structure for work info."""
    has_data                                    = False
    work_mode                                   = WM_NORMAL
    active_work_order_code                      = ''
    active_work_order_file_index                = -1
    file_name                                   = ''
    planned_time                                = '00:00:00'
    worked_time                                 = '00:00:00'

class APIWorkOrderCodeListData(APIComparableMixin):
    """API data structure for work order code list data."""
    order_code                                  = ''
    order_state                                 = WO_ST_DRAFT
    revision_number                             = 0

class APIWorkOrderCodeList(APIComparableMixin):
    """API data structure for work order code list."""

    class ListData:
        """Data structure for work order code list data."""
        order_code: str                         = ''
        order_state: int                        = WO_ST_DRAFT
        revision_number: int                    = 0

    has_data: bool                              = False
    data: List[ListData]                        = []

class APIWorkOrderDataForAdd(APIComparableMixin):
    """API data structure of work order data for add."""

    class FileData:
        """Data structure for work order data file list data."""
        file_name: str                          = None
        pieces_per_file: int                    = None
        requested_pieces: int                   = None

    order_locked: bool                          = None
    order_priority: int                         = None
    job_order_code: str                         = None
    customer_code: str                          = None
    item_code: str                              = None
    material_code: str                          = None
    order_notes: str                            = None
    use_deadline_datetime: bool                 = None
    deadline_datetime: datetime                 = None
    files                                       = None

    def __init__(self):
        """Initialize work order data for add operations."""
        self.files = [self.FileData() for _ in range(8)]

class APIWorkOrderDataForGet(APIComparableMixin):
    """API data structure for work order data for get."""

    class FileData:
        """Data structure for work order data file list data."""
        file_name: str                          = ''
        file_state: int                         = WO_FS_CLOSED
        pieces_per_file: int                    = 0
        requested_pieces: int                   = 0
        produced_pieces: int                    = 0
        discarded_pieces: int                   = 0

    class LogItemData:
        """Data structure for work order data log items data."""
        log_id: int                             = WO_LI_NONE
        log_datetime: datetime                  = datetime.min
        log_info_1: str                         = ""
        log_info_2: str                         = ""

    has_data: bool                              = False
    revision_number: int                        = 0
    order_state: int                            = WO_ST_DRAFT
    order_locked: bool                          = False
    order_code: str                             = ''
    order_priority: int                         = WO_PR_NORMAL
    job_order_code: str                         = ''
    customer_code: str                          = ''
    item_code: str                              = ''
    material_code: str                          = ''
    order_notes: str                            = ''
    files: List[FileData]                       = []
    use_deadline_datetime: bool                 = False
    creation_datetime: datetime                 = datetime.min
    deadline_datetime: datetime                 = datetime.min
    reception_datetime: datetime                = datetime.min
    acceptance_datetime: datetime               = datetime.min
    begin_datetime: datetime                    = datetime.min
    end_datetime: datetime                      = datetime.min
    archived_datetime: datetime                 = datetime.min
    time_for_setup: int                         = 0
    time_for_idle: int                          = 0
    time_for_work: int                          = 0
    time_total: int                             = 0
    operator_notes: str                         = ''
    log_items: List[LogItemData]                = []

    def __init__(self):
        """Initialize work order data for read operations."""
        self.files = [self.FileData() for _ in range(8)]

class APIWorkOrderDataForSet(APIComparableMixin):
    """API data structure of work order data for set."""

    class FileData:
        """Data structure for work order data file list data."""
        file_name: str                          = None
        pieces_per_file: int                    = None
        requested_pieces: int                   = None

    order_state: int                            = None
    order_locked: bool                          = None
    order_priority: int                         = None
    job_order_code: str                         = None
    customer_code: str                          = None
    item_code: str                              = None
    material_code: str                          = None
    order_notes: str                            = None
    use_deadline_datetime: bool                 = None
    deadline_datetime: datetime                 = None
    files                                       = None

    def __init__(self):
        """Initialize work order data for update operations."""
        self.files = [self.FileData() for _ in range(8)]

class APIWorkOrderFileList(APIComparableMixin):
    """API data structure for work order file list."""

    class FileData:
        """Data structure for work order data file list data."""
        type: int                               = 0
        name: str                               = ''
        size: int                               = 0
        creation_datetime: datetime             = datetime.min
        last_access_datetime: datetime          = datetime.min
        last_write_datetime: datetime           = datetime.min

    has_data: bool                              = False
    files: List[FileData]                       = []

    def __init__(self):
        """Initialize work order file list data."""
        self.files = []

class CncAPIClientCore:
    """
    Class with API client core implementation.

    An instance of this class reaches a single API Server.
    If you have several CNC to reach you need to instance this class for each server.
    """

    def __init__(self):
        """Initialize the CNC API client core."""
        self._use_cnc_direct_access = False
        self._is_connected = False
        self._ipc = None
        self._socket = None
        self._socket_ssl = None
        self._socket_ssl_info = ''
        self._connection_host = ''
        self._connection_port = 0
        self._connection_use_ssl = False
        self._force_sync_api = None
        self._force_sync_lock = threading.Lock()
        self._force_sync_thread = None


    # == BEG: property section
    #
    @property
    def is_connected(self) -> bool:
        """Return the current connection state."""
        return self._is_connected

    @property
    def socket_ssl_info(self) -> str:
        """Return the current SSL connection information."""
        return self._socket_ssl_info

    @property
    def connection_host(self) -> str:
        """Return the current connection host."""
        return self._connection_host

    @property
    def connection_port(self) -> int:
        """Return the current connection port."""
        return self._connection_port

    @property
    def connection_use_ssl(self) -> bool:
        """Return whether the current connection uses SSL."""
        return self._connection_use_ssl
    #
    # == END: property section


    # == BEG: public section
    #
    def connect(self, host: str, port: int, use_ssl: bool = False) -> bool:
        """
        Open the connection with the specified API server host/port.

        host        The server host address to connect to (eg.'192.168.0.220').
        port        The server host port to connect to (valid range 0..65535).
        use_ssl     The server is using the transport layer security (TLSv1_2 and TLSv1_3).
        return      True if the connection with the API server is or has been established.
        """

        def create_ssl_context(server_cert: str = None, server_key: str = None, ca_cert: str = None) -> ssl.SSLContext:
            """
            Create an SSL context for TLS and only safe Server Ciphers.

            server_cert     Full path and file name of server certificate (optional)
            server_key      Full path and file name of server key (optional)
            ca_cert         Full path and file name of ca certificate (optional)
            return          The SSL Context
            """

            # creates SSL context with support of TLSv1_2 and TLSv1_3
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            context.minimum_version = ssl.TLSVersion.TLSv1_2
            context.maximum_version = ssl.TLSVersion.TLSv1_3

            # checks if present and upload server certificate and private key
            if server_cert and server_key:
                context.load_cert_chain(certfile=server_cert, keyfile=server_key)

            # loads the CA certificate if necessary
            if ca_cert:
                context.load_verify_locations(cafile=ca_cert)

            # sets the verification type (optional for the client, but recommended)
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            # context.verify_mode = ssl.CERT_REQUIRED
            return context

        if self.is_connected:
            return True
        try:
            # creates client socket
            ipc_server_address = (host, port)
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            # evaluates if enabled use_ssl
            if use_ssl:
                # creates SSL context
                server_cert = None
                server_key = None
                ca_cert = None
                context = create_ssl_context(server_cert, server_key, ca_cert)

                # wraps the socket with SSL
                self._socket_ssl = context.wrap_socket(self._socket, server_hostname=host)

                # establishes an SSL connection to the server
                self._socket_ssl.connect((host, port))
                self._ipc = self._socket_ssl
                cipher = self._socket_ssl.cipher()
                self._socket_ssl_info = f'{cipher[1]} | {cipher[0]} | {cipher[2]}'
            else:
                self._socket.connect(ipc_server_address)
                self._ipc = self._socket

            self._is_connected = True
            self._connection_host = host
            self._connection_port = port
            self._connection_use_ssl = use_ssl
        except Exception:
            self._is_connected = False
            self._ipc = None
            self._socket = None
            self._socket_ssl = None
            self._socket_ssl_info = ''
            self._connection_host = ''
            self._connection_port = 0
            self._connection_use_ssl = False
            return False
        return True

    def connect_direct(self) -> bool:
        """Open a direct connection through the cnc_direct_access module."""
        if self.is_connected:
            return True
        if not cnc_direct_access_available:
            return False
        # direct access bypasses the TCP/IP transport and therefore cannot
        # provide cloned parallel API connections for threaded requests
        self._use_cnc_direct_access = True
        self._is_connected = True
        return True

    def connection_clone(self) -> CncAPIClientCore:
        """Create a clone of connection."""
        if not self.is_connected or self._use_cnc_direct_access:
            return None
        api = CncAPIClientCore()
        ret = api.connect(self._connection_host, self._connection_port, self._connection_use_ssl)
        if not ret:
            return None
        return api

    def close(self) -> bool:
        """
        Close the current connection with the API server

        return      True if the client is connected to an API server and connection is close or has been closed successfully.
        """
        def clean_states():
            self._use_cnc_direct_access = False
            self._is_connected = False
            self._ipc = None
            self._socket = None
            self._socket_ssl = None
            self._socket_ssl_info = ''
            self._connection_host = ''
            self._connection_port = 0
            self._connection_use_ssl = False
            self._force_sync_api = None
            self._force_sync_lock = threading.Lock()
            self._force_sync_thread = None

        force_sync_api = self._force_sync_api
        if force_sync_api is not None:
            try:
                force_sync_api.close()
            except Exception:
                pass

        if self.is_connected:
            try:
                if not self._use_cnc_direct_access:
                    self._ipc.close()
                clean_states()
                return True
            except Exception:
                clean_states()
                return False
        return True
    #
    # == END: public section


    # == BEG: API Server "cmd" requests section
    #
    def cnc_change_function_state_mode(self, name: int, mode: int) -> bool:
        """Execute the change of a cnc function state mode."""
        if type(name) is not int or type(mode) is not int:
            return False
        if name not in FS_ALLOWED_COMBO or mode not in FS_ALLOWED_COMBO[name]:
            return False
        request = {"cmd": "cnc.change.function.state.mode", "name": name, "mode": mode}
        return self.__execute_request(json.dumps(request))

    def cnc_connection_close(self) -> bool:
        """Close connection between Control Software and CNC."""
        request = {"cmd": "cnc.connection.close"}
        return self.__execute_request(self.create_compact_json_request(request))

    def cnc_connection_open(
        self,
        use_ui: bool = False,
        use_fast_mode: bool = False,
        skip_firmware_check: bool = False,
        overwrite_cnc_settings: bool = False
    ) -> bool:
        """
        Open connection between Control Software and CNC.

        This function is asynchronous so the API Server receive the command
        and return immediately the accepted state, but connection phase is
        made lately in asynchronous mode.

        Args:
            use_ui: Enable UI mode
            use_fast_mode: Enable fast mode
            skip_firmware_check: Skip firmware verification
            overwrite_cnc_settings: Overwrite existing CNC settings

        Returns:
            True if connection command was accepted, False otherwise
        """
        params = [use_ui, use_fast_mode, skip_firmware_check, overwrite_cnc_settings]
        if not all(isinstance(param, bool) for param in params):
            return False
        request = {
            "cmd": "cnc.connection.open",
            "use.ui": use_ui,
            "use.fast.mode": use_fast_mode,
            "skip.firmware.check": skip_firmware_check,
            "overwrite.cnc.settings": overwrite_cnc_settings,
        }
        return self.__execute_request(json.dumps(request))

    def cnc_continue(self) -> bool:
        """Resume the execution of an NC program/Macro or MDI command from the PAUSE state."""
        request = {"cmd": "cnc.continue"}
        return self.__execute_request(self.create_compact_json_request(request))

    def cnc_homing(self, axes_mask: int) -> bool:
        """Execute the HOMING procedure for the required axes."""
        if type(axes_mask) is not int:
            return False
        if axes_mask <= 0 or axes_mask > X2C_AXIS_MASK:
            return False
        request = {"cmd": "cnc.homing", "axes.mask": axes_mask}
        return self.__execute_request(self.create_compact_json_request(request))

    def cnc_jog_command(self, command: int) -> bool:
        """Execute a JOG motion command."""
        if type(command) is not int:
            return False
        if command < JC_NONE or command > JC_C_FW:
            return False
        request = {"cmd": "cnc.jog.command", "command": command}
        return self.__execute_request(self.create_compact_json_request(request))

    def cnc_mdi_command(self, command: str) -> bool:
        """Execute an MDI command."""
        if not isinstance(command, str):
            return False
        request = {"cmd": "cnc.mdi.command", "command": command}
        return self.__execute_request(self.create_compact_json_request(request))

    def cnc_pause(self) -> bool:
        """Request the numerical control to enter the PAUSE state."""
        request = {"cmd": "cnc.pause"}
        return self.__execute_request(self.create_compact_json_request(request))

    def cnc_resume(self, force_sync: bool = False, timeout: float = DEFAULT_FORCE_SYNC_TIMEOUT) -> bool:
        """
        Resume the execution of an NC program after a STOP.

        Args:
            force_sync  : when True, wait for the real completion of the server command
            timeout     : use this timeout only when force_sync is True
        """
        request = {"cmd": "cnc.resume"}
        if not self.__append_force_sync(request, force_sync):
            return False
        first_timeout = self.__get_force_sync_timeout(force_sync, timeout)
        if first_timeout is None:
            return False
        return self.__execute_request(self.create_compact_json_request(request), first_timeout=first_timeout)

    def cnc_resume_threaded(self, timeout: float = DEFAULT_FORCE_SYNC_TIMEOUT, on_done: Callable[[bool | None], None] = None) -> bool:
        """
        Resume the execution of an NC program after a STOP in a worker thread using a parallel API server connection.

        Args:
            timeout     : define the timeout used by the forced synchronous server request
            on_done     : call this callback at end with result True, False or None
        """
        if self.__get_force_sync_timeout(True, timeout) is None:
            return False
        return self.__start_force_sync_async_request(
            lambda api: api.cnc_resume(force_sync=True, timeout=timeout),
            on_done
        )

    def cnc_resume_from_line(self, line: int, force_sync: bool = False, timeout: float = DEFAULT_FORCE_SYNC_TIMEOUT) -> bool:
        """
        Resume the execution of an NC program after a STOP, starting from a specific line.

        Args:
            line        : define the line number from which the program must resume
            force_sync  : when True, wait for the real completion of the server command
            timeout     : use this timeout only when force_sync is True
        """
        request = {"cmd": "cnc.resume.from.line", "line": line}
        if not self.__append_force_sync(request, force_sync):
            return False
        first_timeout = self.__get_force_sync_timeout(force_sync, timeout)
        if first_timeout is None:
            return False
        return self.__execute_request(self.create_compact_json_request(request), first_timeout=first_timeout)

    def cnc_resume_from_line_threaded(self, line: int, timeout: float = DEFAULT_FORCE_SYNC_TIMEOUT, on_done: Callable[[bool | None], None] = None) -> bool:
        """
        Resume the execution of an NC program after a STOP from a line in a worker thread using a parallel API server connection.

        Args:
            line        : define the line number from which the program must resume
            timeout     : define the timeout used by the forced synchronous server request
            on_done     : call this callback at end with result True, False or None
        """
        if not isinstance(line, int) or isinstance(line, bool):
            return False
        if self.__get_force_sync_timeout(True, timeout) is None:
            return False
        return self.__start_force_sync_async_request(
            lambda api: api.cnc_resume_from_line(line, force_sync=True, timeout=timeout),
            on_done
        )

    def cnc_resume_from_point(self, point: int, force_sync: bool = False, timeout: float = DEFAULT_FORCE_SYNC_TIMEOUT) -> bool:
        """
        Resume the execution of an NC program after a STOP, starting from a specific point.

        Args:
            point       : define the point index from which the program must resume
            force_sync  : when True, wait for the real completion of the server command
            timeout     : use this timeout only when force_sync is True
        """
        request = {"cmd": "cnc.resume.from.point", "point": point}
        if not self.__append_force_sync(request, force_sync):
            return False
        first_timeout = self.__get_force_sync_timeout(force_sync, timeout)
        if first_timeout is None:
            return False
        return self.__execute_request(self.create_compact_json_request(request), first_timeout=first_timeout)

    def cnc_resume_from_point_threaded(self, point: int, timeout: float = DEFAULT_FORCE_SYNC_TIMEOUT, on_done: Callable[[bool | None], None] = None) -> bool:
        """
        Resume the execution of an NC program after a STOP from a point in a worker thread using a parallel API server connection.

        Args:
            point       : define the point index from which the program must resume
            timeout     : define the timeout used by the forced synchronous server request
            on_done     : call this callback at end with result True, False or None
        """
        if not isinstance(point, int) or isinstance(point, bool):
            return False
        if self.__get_force_sync_timeout(True, timeout) is None:
            return False
        return self.__start_force_sync_async_request(
            lambda api: api.cnc_resume_from_point(point, force_sync=True, timeout=timeout),
            on_done
        )

    def cnc_start(self, force_sync: bool = False, timeout: float = DEFAULT_FORCE_SYNC_TIMEOUT) -> bool:
        """
        Start the execution of the NC program.

        Args:
            force_sync  : when True, wait for the real completion of the server command
            timeout     : use this timeout only when force_sync is True
        """
        request = {"cmd": "cnc.start"}
        if not self.__append_force_sync(request, force_sync):
            return False
        first_timeout = self.__get_force_sync_timeout(force_sync, timeout)
        if first_timeout is None:
            return False
        return self.__execute_request(self.create_compact_json_request(request), first_timeout=first_timeout)

    def cnc_start_threaded(self, timeout: float = DEFAULT_FORCE_SYNC_TIMEOUT, on_done: Callable[[bool | None], None] = None) -> bool:
        """
        Start the execution of the NC program in a worker thread using a parallel API server connection.

        Args:
            timeout     : define the timeout used by the forced synchronous server request
            on_done     : call this callback at end with result True, False or None
        """
        if self.__get_force_sync_timeout(True, timeout) is None:
            return False
        return self.__start_force_sync_async_request(
            lambda api: api.cnc_start(force_sync=True, timeout=timeout),
            on_done
        )

    def cnc_start_from_line(self, line: int, force_sync: bool = False, timeout: float = DEFAULT_FORCE_SYNC_TIMEOUT) -> bool:
        """
        Start the execution of the NC program from a specific line.

        Args:
            line        : define the line number from which the program must start
            force_sync  : when True, wait for the real completion of the server command
            timeout     : use this timeout only when force_sync is True
        """
        request = {"cmd": "cnc.start.from.line", "line": line}
        if not self.__append_force_sync(request, force_sync):
            return False
        first_timeout = self.__get_force_sync_timeout(force_sync, timeout)
        if first_timeout is None:
            return False
        return self.__execute_request(self.create_compact_json_request(request), first_timeout=first_timeout)

    def cnc_start_from_line_threaded(self, line: int, timeout: float = DEFAULT_FORCE_SYNC_TIMEOUT, on_done: Callable[[bool | None], None] = None) -> bool:
        """
        Start the execution of the NC program from a line in a worker thread using a parallel API server connection.

        Args:
            line        : define the line number from which the program must start
            timeout     : define the timeout used by the forced synchronous server request
            on_done     : call this callback at end with result True, False or None
        """
        if not isinstance(line, int) or isinstance(line, bool):
            return False
        if self.__get_force_sync_timeout(True, timeout) is None:
            return False
        return self.__start_force_sync_async_request(
            lambda api: api.cnc_start_from_line(line, force_sync=True, timeout=timeout),
            on_done
        )

    def cnc_start_from_point(self, point: int, force_sync: bool = False, timeout: float = DEFAULT_FORCE_SYNC_TIMEOUT) -> bool:
        """
        Start the execution of the NC program from a specific point.

        Args:
            point       : define the point index from which the program must start
            force_sync  : when True, wait for the real completion of the server command
            timeout     : use this timeout only when force_sync is True
        """
        request = {"cmd": "cnc.start.from.point", "point": point}
        if not self.__append_force_sync(request, force_sync):
            return False
        first_timeout = self.__get_force_sync_timeout(force_sync, timeout)
        if first_timeout is None:
            return False
        return self.__execute_request(self.create_compact_json_request(request), first_timeout=first_timeout)

    def cnc_start_from_point_threaded(self, point: int, timeout: float = DEFAULT_FORCE_SYNC_TIMEOUT, on_done: Callable[[bool | None], None] = None) -> bool:
        """
        Start the execution of the NC program from a point in a worker thread using a parallel API server connection.

        Args:
            point       : define the point index from which the program must start
            timeout     : define the timeout used by the forced synchronous server request
            on_done     : call this callback at end with result True, False or None
        """
        if not isinstance(point, int) or isinstance(point, bool):
            return False
        if self.__get_force_sync_timeout(True, timeout) is None:
            return False
        return self.__start_force_sync_async_request(
            lambda api: api.cnc_start_from_point(point, force_sync=True, timeout=timeout),
            on_done
        )

    def cnc_stop(self) -> bool:
        """Stop the execution of the NC code or the ongoing procedure."""
        request = {"cmd": "cnc.stop"}
        return self.__execute_request(self.create_compact_json_request(request))

    def log_add(self, text: str) -> bool:
        """Add a message to the control software log."""
        request = {"cmd": "log.add", "text": text}
        return self.__execute_request(self.create_compact_json_request(request))

    def mru_programs_list_clear(self) -> bool:
        """Clear the MRU programs list."""
        request = {"cmd": "mdi.programs.list.clear"}
        return self.__execute_request(self.create_compact_json_request(request))

    def mru_programs_list_remove_item(self, index: int) -> bool:
        """Remove an item from the MRU programs list."""
        if not isinstance(index, int) or isinstance(index, bool):
            return False
        request = {
            "cmd": "mru.programs.list.remove.item",
            "index": index
        }
        return self.__execute_request(json.dumps(request))

    def program_analysis(self, mode: str, force_sync: bool = False, timeout: float = DEFAULT_FORCE_SYNC_TIMEOUT) -> bool:
        """
        Start the analysis of the NC program.

        Args:
            mode        : define the analysis mode to execute
            force_sync  : when True, wait for the real completion of the server command
            timeout     : use this timeout only when force_sync is True
        """
        request = {"cmd": "program.analysis", "mode": mode}
        if not self.__append_force_sync(request, force_sync):
            return False
        first_timeout = self.__get_force_sync_timeout(force_sync, timeout)
        if first_timeout is None:
            return False
        return self.__execute_request(self.create_compact_json_request(request), first_timeout=first_timeout)

    def program_analysis_threaded(self, mode: str, timeout: float = DEFAULT_FORCE_SYNC_TIMEOUT, on_done: Callable[[bool | None], None] = None) -> bool:
        """
        Start the analysis of the NC program in a worker thread using a parallel API server connection.

        Args:
            mode        : define the analysis mode to execute
            timeout     : define the timeout used by the forced synchronous server request
            on_done     : call this callback at end with result True, False or None
        """
        if not isinstance(mode, str):
            return False
        if self.__get_force_sync_timeout(True, timeout) is None:
            return False
        return self.__start_force_sync_async_request(
            lambda api: api.program_analysis(mode, force_sync=True, timeout=timeout),
            on_done
        )

    def program_analysis_abort(self) -> bool:
        """Abort the analysis of the NC program."""
        request = {"cmd": "program.analysis.abort"}
        return self.__execute_request(self.create_compact_json_request(request))

    def program_gcode_add_text(self, text: str) -> bool:
        """Add a line of text (block) to the NC program."""
        request = {"cmd": "program.gcode.add.text", "text": text}
        return self.__execute_request(self.create_compact_json_request(request))

    def program_gcode_clear(self) -> bool:
        """Clear the content of the NC program."""
        request = {"cmd": "program.gcode.clear"}
        return self.__execute_request(self.create_compact_json_request(request))

    def program_gcode_modified(self) -> bool:
        """Set program modified state to invalidate derived runtime data."""
        if not self.is_connected:
            return False
        request = {"cmd": "program.gcode.modified"}
        return self.__execute_request(self.create_compact_json_request(request))

    def program_gcode_set_text(self, text: str) -> bool:
        """Set the content of the NC program."""
        request = {"cmd": "program.gcode.set.text", "text": text}
        return self.__execute_request(self.create_compact_json_request(request))

    def program_load(self, file_name: str, force_sync: bool = False, timeout: float = DEFAULT_FORCE_SYNC_TIMEOUT) -> bool:
        """
        Load an NC program from the specified file.

        Args:
            file_name   : define the file name of the program to load
            force_sync  : when True, wait for the real completion of the server command
            timeout     : use this timeout only when force_sync is True
        """
        if not isinstance(file_name, str):
            return False
        request = {"cmd": "program.load", "name": file_name}
        if not self.__append_force_sync(request, force_sync):
            return False
        first_timeout = self.__get_force_sync_timeout(force_sync, timeout)
        if first_timeout is None:
            return False
        return self.__execute_request(self.create_compact_json_request(request), first_timeout=first_timeout)

    def program_load_threaded(self, file_name: str, timeout: float = DEFAULT_FORCE_SYNC_TIMEOUT, on_done: Callable[[bool | None], None] = None) -> bool:
        """
        Load an NC program from the specified file in a worker thread using a parallel API server connection.

        Args:
            file_name   : define the file name of the program to load
            timeout     : define the timeout used by the forced synchronous server request
            on_done     : call this callback at end with result True, False or None
        """
        if not isinstance(file_name, str):
            return False
        if self.__get_force_sync_timeout(True, timeout) is None:
            return False
        return self.__start_force_sync_async_request(
            lambda api: api.program_load(file_name, force_sync=True, timeout=timeout),
            on_done
        )

    def program_new(self) -> bool:
        """Create a new NC program."""
        request = {"cmd": "program.new"}
        return self.__execute_request(self.create_compact_json_request(request))

    def program_save(self, force_sync: bool = False, timeout: float = DEFAULT_FORCE_SYNC_TIMEOUT) -> bool:
        """
        Save the NC program.

        Args:
            force_sync  : when True, wait for the real completion of the server command
            timeout     : use this timeout only when force_sync is True
        """
        request = {"cmd": "program.save"}
        if not self.__append_force_sync(request, force_sync):
            return False
        first_timeout = self.__get_force_sync_timeout(force_sync, timeout)
        if first_timeout is None:
            return False
        return self.__execute_request(self.create_compact_json_request(request), first_timeout=first_timeout)

    def program_save_threaded(self, timeout: float = DEFAULT_FORCE_SYNC_TIMEOUT, on_done: Callable[[bool | None], None] = None) -> bool:
        """
        Save the NC program in a worker thread using a parallel API server connection.

        Args:
            timeout     : define the timeout used by the forced synchronous server request
            on_done     : call this callback at end with result True, False or None
        """
        if self.__get_force_sync_timeout(True, timeout) is None:
            return False
        return self.__start_force_sync_async_request(
            lambda api: api.program_save(force_sync=True, timeout=timeout),
            on_done
        )

    def program_save_as(self, file_name: str, force_sync: bool = False, timeout: float = DEFAULT_FORCE_SYNC_TIMEOUT) -> bool:
        """
        Save the NC program to the specified file.

        Args:
            file_name   : define the destination file name
            force_sync  : when True, wait for the real completion of the server command
            timeout     : use this timeout only when force_sync is True
        """
        try:
            if not isinstance(file_name, str):
                return False
            request = {"cmd": "program.save.as", "file.name": file_name}
            if not self.__append_force_sync(request, force_sync):
                return False
            first_timeout = self.__get_force_sync_timeout(force_sync, timeout)
            if first_timeout is None:
                return False
            return self.__execute_request(self.create_compact_json_request(request), first_timeout=first_timeout)
        except Exception:
            return False

    def program_save_as_threaded(self, file_name: str, timeout: float = DEFAULT_FORCE_SYNC_TIMEOUT, on_done: Callable[[bool | None], None] = None) -> bool:
        """
        Save the NC program to the specified file in a worker thread using a parallel API server connection.

        Args:
            file_name   : define the destination file name
            timeout     : define the timeout used by the forced synchronous server request
            on_done     : call this callback at end with result True, False or None
        """
        if not isinstance(file_name, str):
            return False
        if self.__get_force_sync_timeout(True, timeout) is None:
            return False
        return self.__start_force_sync_async_request(
            lambda api: api.program_save_as(file_name, force_sync=True, timeout=timeout),
            on_done
        )

    def reset_alarms(self) -> bool:
        """Reset the current alarms in the numerical control."""
        request = {"cmd": "reset.alarms"}
        return self.__execute_request(self.create_compact_json_request(request))

    def reset_alarms_history(self) -> bool:
        """Reset the alarm history in the numerical control."""
        request = {"cmd": "reset.alarms.history"}
        return self.__execute_request(self.create_compact_json_request(request))

    def reset_warnings(self) -> bool:
        """Reset the current warnings in the numerical control."""
        request = {"cmd": "reset.warnings"}
        return self.__execute_request(self.create_compact_json_request(request))

    def reset_warnings_history(self) -> bool:
        """Reset the warning history in the numerical control."""
        request = {"cmd": "reset.warnings.history"}
        return self.__execute_request(self.create_compact_json_request(request))

    def show_ui_dialog(self, uid_id: int = 0) -> bool:
        """Show UI dialog by user interface dialog ID."""
        if not isinstance(uid_id, int) or type(uid_id) is bool:
            return False
        if not UID_ID_FIRST <= uid_id <= UID_ID_LAST:
            return False
        request = {"cmd": "show.ui.dialog", "uid_id": uid_id}
        return self.__execute_request(json.dumps(request))

    def simulator_continue(self) -> bool:
        """Resume the NC program simulation from the pause state."""
        request = {"cmd": "simulator.continue"}
        return self.__execute_request(self.create_compact_json_request(request))

    def simulator_pause(self) -> bool:
        """Pause the NC program simulation."""
        request = {"cmd": "simulator.pause"}
        return self.__execute_request(self.create_compact_json_request(request))

    def simulator_place_and_pause_to_line(self, line: int) -> bool:
        """Place and pause the NC program simulation to specified line."""
        if not isinstance(line, int) or isinstance(line, bool):
            return False
        request = {"cmd": "simulator.place.and.pause.to.line", "line": line}
        return self.__execute_request(json.dumps(request))

    def simulator_start(self) -> bool:
        """Start the NC program simulation."""
        request = {"cmd": "simulator.start"}
        return self.__execute_request(self.create_compact_json_request(request))

    def simulator_step_backward(self) -> bool:
        """Step the NC program simulation backward."""
        request = {"cmd": "simulator.step.backward"}
        return self.__execute_request(self.create_compact_json_request(request))

    def simulator_step_forward(self) -> bool:
        """Step the NC program simulation forward."""
        request = {"cmd": "simulator.step.forward"}
        return self.__execute_request(self.create_compact_json_request(request))

    def simulator_stop(self) -> bool:
        """Stop the NC program simulation."""
        request = {"cmd": "simulator.stop"}
        return self.__execute_request(self.create_compact_json_request(request))

    def tools_lib_add(self, info: APIToolsLibInfoForSet | None = None) -> bool:
        """Add a tool with optional info into the NC tools library."""
        try:
            if not isinstance(info, APIToolsLibInfoForSet):
                return False

            if not isinstance(info.tool_id, (type(None), int)):
                return False
            if not isinstance(info.tool_slot, (type(None), int)):
                return False
            if not isinstance(info.tool_type, (type(None), int)):
                return False
            if not isinstance(info.tool_diameter, (type(None), int, float)):
                return False
            if not isinstance(info.tool_offset_x, (type(None), int, float)):
                return False
            if not isinstance(info.tool_offset_y, (type(None), int, float)):
                return False
            if not isinstance(info.tool_offset_z, (type(None), int, float)):
                return False
            if not isinstance(info.tool_param_1, (type(None), int, float)):
                return False
            if not isinstance(info.tool_param_2, (type(None), int, float)):
                return False
            if not isinstance(info.tool_param_3, (type(None), int, float)):
                return False
            if not isinstance(info.tool_param_4, (type(None), int, float)):
                return False
            if not isinstance(info.tool_param_5, (type(None), int, float)):
                return False
            if not isinstance(info.tool_param_6, (type(None), int, float)):
                return False
            if not isinstance(info.tool_param_7, (type(None), int, float)):
                return False
            if not isinstance(info.tool_param_8, (type(None), int, float)):
                return False
            if not isinstance(info.tool_param_9, (type(None), int, float)):
                return False
            if not isinstance(info.tool_param_10, (type(None), int, float)):
                return False
            if not isinstance(info.tool_param_51, (type(None), int, float)):
                return False
            if not isinstance(info.tool_param_52, (type(None), int, float)):
                return False
            if not isinstance(info.tool_param_53, (type(None), int, float)):
                return False
            if not isinstance(info.tool_param_54, (type(None), int, float)):
                return False
            if not isinstance(info.tool_param_55, (type(None), int, float)):
                return False
            if not isinstance(info.tool_param_56, (type(None), int, float)):
                return False
            if not isinstance(info.tool_param_57, (type(None), int, float)):
                return False
            if not isinstance(info.tool_param_58, (type(None), int, float)):
                return False
            if not isinstance(info.tool_param_59, (type(None), int, float)):
                return False
            if not isinstance(info.tool_param_60, (type(None), int, float)):
                return False
            if not isinstance(info.tool_description, (type(None), str)):
                return False

            data = {
                "cmd": "tools.lib.add"
            }

            # add optional fields only if they are not None
            optional_fields = [
                ("id", info.tool_id),
                ("slot", info.tool_slot),
                ("type", info.tool_type),
                ("diameter", info.tool_diameter),
                ("offset.x", info.tool_offset_x),
                ("offset.y", info.tool_offset_y),
                ("offset.z", info.tool_offset_z),
                ("param.1", info.tool_param_1),
                ("param.2", info.tool_param_2),
                ("param.3", info.tool_param_3),
                ("param.4", info.tool_param_4),
                ("param.5", info.tool_param_5),
                ("param.6", info.tool_param_6),
                ("param.7", info.tool_param_7),
                ("param.8", info.tool_param_8),
                ("param.9", info.tool_param_9),
                ("param.10", info.tool_param_10),
                ("param.51", info.tool_param_51),
                ("param.52", info.tool_param_52),
                ("param.53", info.tool_param_53),
                ("param.54", info.tool_param_54),
                ("param.55", info.tool_param_55),
                ("param.56", info.tool_param_56),
                ("param.57", info.tool_param_57),
                ("param.58", info.tool_param_58),
                ("param.59", info.tool_param_59),
                ("param.60", info.tool_param_60),
                ("description", info.tool_description),
            ]

            for key, value in optional_fields:
                if value is not None:
                    data[key] = value

            request = self.create_compact_json_request(data)
            return self.__execute_request(request)
        except Exception:
            return False

    def tools_lib_clear(self) -> bool:
        """Clear the NC tools library."""
        request = {"cmd": "tools.lib.clear"}
        return self.__execute_request(self.create_compact_json_request(request))

    def tools_lib_delete(self, index: int | None = None) -> bool:
        """Delete a tool from the NC tools library."""
        try:
            if not isinstance(index, int):
                return False
            request = {"cmd": "tools.lib.delete", "index": index}
            return self.__execute_request(self.create_compact_json_request(request))
        except Exception:
            return False

    def tools_lib_insert(self, info: APIToolsLibInfoForSet | None = None) -> bool:
        """Insert a tool into the NC tools library."""
        try:
            if not isinstance(info, APIToolsLibInfoForSet):
                return False

            if not isinstance(info.tool_index, int):
                return False
            if not isinstance(info.tool_id, (type(None), int)):
                return False
            if not isinstance(info.tool_slot, (type(None), int)):
                return False
            if not isinstance(info.tool_type, (type(None), int)):
                return False
            if not isinstance(info.tool_diameter, (type(None), int, float)):
                return False
            if not isinstance(info.tool_offset_x, (type(None), int, float)):
                return False
            if not isinstance(info.tool_offset_y, (type(None), int, float)):
                return False
            if not isinstance(info.tool_offset_z, (type(None), int, float)):
                return False
            if not isinstance(info.tool_param_1, (type(None), int, float)):
                return False
            if not isinstance(info.tool_param_2, (type(None), int, float)):
                return False
            if not isinstance(info.tool_param_3, (type(None), int, float)):
                return False
            if not isinstance(info.tool_param_4, (type(None), int, float)):
                return False
            if not isinstance(info.tool_param_5, (type(None), int, float)):
                return False
            if not isinstance(info.tool_param_6, (type(None), int, float)):
                return False
            if not isinstance(info.tool_param_7, (type(None), int, float)):
                return False
            if not isinstance(info.tool_param_8, (type(None), int, float)):
                return False
            if not isinstance(info.tool_param_9, (type(None), int, float)):
                return False
            if not isinstance(info.tool_param_10, (type(None), int, float)):
                return False
            if not isinstance(info.tool_param_51, (type(None), int, float)):
                return False
            if not isinstance(info.tool_param_52, (type(None), int, float)):
                return False
            if not isinstance(info.tool_param_53, (type(None), int, float)):
                return False
            if not isinstance(info.tool_param_54, (type(None), int, float)):
                return False
            if not isinstance(info.tool_param_55, (type(None), int, float)):
                return False
            if not isinstance(info.tool_param_56, (type(None), int, float)):
                return False
            if not isinstance(info.tool_param_57, (type(None), int, float)):
                return False
            if not isinstance(info.tool_param_58, (type(None), int, float)):
                return False
            if not isinstance(info.tool_param_59, (type(None), int, float)):
                return False
            if not isinstance(info.tool_param_60, (type(None), int, float)):
                return False
            if not isinstance(info.tool_description, (type(None), str)):
                return False

            data = {
                "cmd": "tools.lib.insert",
                "index": info.tool_index
            }

            # add optional fields only if they are not None
            optional_fields = [
                ("id", info.tool_id),
                ("slot", info.tool_slot),
                ("type", info.tool_type),
                ("diameter", info.tool_diameter),
                ("offset.x", info.tool_offset_x),
                ("offset.y", info.tool_offset_y),
                ("offset.z", info.tool_offset_z),
                ("param.1", info.tool_param_1),
                ("param.2", info.tool_param_2),
                ("param.3", info.tool_param_3),
                ("param.4", info.tool_param_4),
                ("param.5", info.tool_param_5),
                ("param.6", info.tool_param_6),
                ("param.7", info.tool_param_7),
                ("param.8", info.tool_param_8),
                ("param.9", info.tool_param_9),
                ("param.10", info.tool_param_10),
                ("param.51", info.tool_param_51),
                ("param.52", info.tool_param_52),
                ("param.53", info.tool_param_53),
                ("param.54", info.tool_param_54),
                ("param.55", info.tool_param_55),
                ("param.56", info.tool_param_56),
                ("param.57", info.tool_param_57),
                ("param.58", info.tool_param_58),
                ("param.59", info.tool_param_59),
                ("param.60", info.tool_param_60),
                ("description", info.tool_description),
            ]

            for key, value in optional_fields:
                if value is not None:
                    data[key] = value

            request = self.create_compact_json_request(data)
            return self.__execute_request(request)
        except Exception:
            return False

    def work_order_add(self, order_code: str, data: APIWorkOrderDataForAdd | None = None) -> bool:
        """Add a work order to the list of orders in the control software."""
        try:
            if not self.is_connected:
                return False

            request_data = {
                "cmd": "work.order.add",
                "order.code": order_code
            }

            if data:
                if not isinstance(data, APIWorkOrderDataForAdd):
                    return False

                order_data = {}

                if data.order_locked is not None:
                    if isinstance(data.order_locked, bool):
                        order_data["order.locked"] = data.order_locked
                    else:
                        return False

                if data.order_priority is not None:
                    if isinstance(data.order_priority, int) and WO_PR_LOWEST <= data.order_priority <= WO_PR_HIGHEST:
                        order_data["order.priority"] = data.order_priority
                    else:
                        return False

                if data.job_order_code is not None:
                    if isinstance(data.job_order_code, str):
                        order_data["job.order.code"] = data.job_order_code
                    else:
                        return False

                if data.customer_code is not None:
                    if isinstance(data.customer_code, str):
                        order_data["customer.code"] = data.customer_code
                    else:
                        return False

                if data.item_code is not None:
                    if isinstance(data.item_code, str):
                        order_data["item.code"] = data.item_code
                    else:
                        return False

                if data.material_code is not None:
                    if isinstance(data.material_code, str):
                        order_data["material.code"] = data.material_code
                    else:
                        return False

                if data.order_notes is not None:
                    if isinstance(data.order_notes, str):
                        order_data["order.notes"] = data.order_notes
                    else:
                        return False

                if data.use_deadline_datetime is not None:
                    if isinstance(data.use_deadline_datetime, bool):
                        order_data["use.deadline.datetime"] = data.use_deadline_datetime
                        if data.use_deadline_datetime:
                            if isinstance(data.deadline_datetime, datetime):
                                order_data["deadline.datetime"] = self.datetime_to_filetime(data.deadline_datetime)
                            else:
                                return False
                    else:
                        return False

                if data.files:
                    files_data = []
                    for file in data.files:
                        file_data = {}
                        if file.file_name is not None:
                            file_data["file.name"] = file.file_name
                        if file.pieces_per_file is not None:
                            file_data["pieces.per.file"] = file.pieces_per_file
                        if file.requested_pieces is not None:
                            file_data["requested.pieces"] = file.requested_pieces
                        files_data.append(file_data)
                    order_data["files"] = files_data

                request_data["data"] = order_data

            request_json = json.dumps(request_data)
            return self.__execute_request(request_json)
        except Exception:
            return False

    def work_order_delete(self, order_code: str) -> bool:
        """Delete a work order from the list of orders in the control software."""
        try:
            if not isinstance(order_code, str):
                return False
            order_code_json = json.dumps(order_code)
            return self.__execute_request(f'{{"cmd":"work.order.delete","order.code":{order_code_json}}}')
        except Exception:
            return False
    #
    # == END: API Server "cmd" requests section


    # == BEG: API Server "get" requests section
    #
    def get_alarms_current_list(self) -> APIAlarmsWarningsList:
        """Return current alarms list."""
        try:
            data = APIAlarmsWarningsList()
            if not self.is_connected:
                return data
            request = '{"get":"alarms.current.list"}'
            response = self.__send_command(request)
            if response:
                j = json.loads(response)
                l = j['res']['list']
                if len(l) == 0:
                    data.list = []
                else:
                    data.list = [data.AlarmWarningData() for _ in range(len(l))]
                    for i in range(len(data.list)):
                        data.list[i].code               = l[i]['code']
                        data.list[i].info_1             = l[i]['info.1']
                        data.list[i].info_2             = l[i]['info.2']
                        data.list[i].text               = l[i]['text']
                        data.list[i].datetime           = self.__d(l[i]['datetime'])
                data.has_data = True
            return data
        except Exception:
            return APIAlarmsWarningsList()

    def get_alarms_history_list(self) -> APIAlarmsWarningsList:
        """Return alarms history list."""
        try:
            data = APIAlarmsWarningsList()
            if not self.is_connected:
                return data
            request = '{"get":"alarms.history.list"}'
            response = self.__send_command(request)
            if response:
                j = json.loads(response)
                l = j['res']['list']
                if len(l) == 0:
                    data.list = []
                else:
                    data.list = [data.AlarmWarningData() for _ in range(len(l))]
                    for i in range(len(data.list)):
                        data.list[i].code               = l[i]['code']
                        data.list[i].info_1             = l[i]['info.1']
                        data.list[i].info_2             = l[i]['info.2']
                        data.list[i].text               = l[i]['text']
                        data.list[i].datetime           = self.__d(l[i]['datetime'])
                data.has_data = True
            return data
        except Exception:
            return APIAlarmsWarningsList()

    def get_analog_inputs(self) -> APIAnalogInputs:
        """Return analog inputs values."""
        try:
            data = APIAnalogInputs()
            if not self.is_connected:
                return data
            request = '{"get":"analog.inputs"}'
            response = self.__send_command(request)
            if response:
                j = json.loads(response)
                data.value                              = j['res']['value']
                data.has_data                           = True
            return data
        except Exception:
            return APIAnalogInputs()

    def get_analog_outputs(self) -> APIAnalogOutputs:
        """Return analog outputs values."""
        try:
            data = APIAnalogOutputs()
            if not self.is_connected:
                return data
            request = '{"get":"analog.outputs"}'
            response = self.__send_command(request)
            if response:
                j = json.loads(response)
                data.value                              = j['res']['value']
                data.has_data                           = True
            return data
        except Exception:
            return APIAnalogOutputs()

    def get_axes_info(self) -> APIAxesInfo:
        """Return axes information."""
        try:
            data = APIAxesInfo()
            if not self.is_connected:
                return data
            request = '{"get":"axes.info"}'
            response = self.__send_command(request)
            if response:
                j = json.loads(response)
                data.joint_position                     = j['res']['joint.position']
                data.machine_position                   = j['res']['machine.position']
                data.program_position                   = j['res']['program.position']
                data.machine_target_position            = j['res']['machine.target.position']
                data.program_target_position            = j['res']['program.target.position']
                data.actual_velocity                    = j['res']['actual.velocity']
                data.working_wcs                        = j['res']['working.wcs']
                data.working_offset                     = j['res']['working.offset']
                data.dynamic_offset                     = j['res']['dynamic.offset']
                data.homing_done                        = j['res']['homing.done']
                data.homing_done_mask                   = j['res']['homing.done.mask']
                data.homing_running_mask                = j['res']['homing.running.mask']
                data.homing_sensors_mask                = j['res']['homing.sensors.mask']
                data.homing_correction_space            = j['res']['homing.correction.space']
                data.has_data                           = True
            return data
        except Exception:
            return APIAxesInfo()

    def get_cnc_info(self) -> APICncInfo:
        """Return CNC information."""
        try:
            data = APICncInfo()
            if not self.is_connected:
                return data
            request = '{"get":"cnc.info"}'
            response = self.__send_command(request)
            if response:
                j = json.loads(response)
                data.file_name                          = j['res']['file.name']
                data.units_mode                         = j['res']['units.mode']
                data.axes_mask                          = j['res']['axes.mask']
                data.state_machine                      = j['res']['state.machine']
                data.connection_state                   = j['res']['connection.state']
                data.controller_settings_crc            = j['res']['controller.settings.crc']
                data.interp_buffer_level                = j['res']['interp.buffer.level']
                data.gcode_line                         = j['res']['gcode.line']
                data.planned_time                       = j['res']['planned.time']
                data.worked_time                        = j['res']['worked.time']
                data.hud_user_message                   = j['res']['hud.user.message']
                data.toolpath_id                        = j['res']['toolpath.id']
                data.operator_request_id_pending        = j['res']['operator.request.id.pending']
                data.program_gcode_sync_required        = j['res']['program.gcode.sync.required']
                data.current_alarm_datetime             = self.__d(j['res']['current.alarm']['datetime'])
                data.current_alarm_code                 = j['res']['current.alarm']['code']
                data.current_alarm_info1                = j['res']['current.alarm']['info1']
                data.current_alarm_info2                = j['res']['current.alarm']['info2']
                data.current_alarm_text                 = j['res']['current.alarm']['text']
                data.current_warning_datetime           = self.__d(j['res']['current.warning']['datetime'])
                data.current_warning_code               = j['res']['current.warning']['code']
                data.current_warning_info1              = j['res']['current.warning']['info1']
                data.current_warning_info2              = j['res']['current.warning']['info2']
                data.current_warning_text               = j['res']['current.warning']['text']
                data.aux_outputs                        = j['res']['aux.outputs']
                data.coolant_mist                       = j['res']['coolant']['mist']
                data.coolant_flood                      = j['res']['coolant']['flood']
                data.lube_axis_cycles_made              = j['res']['lube']['axis.cycles.made']
                data.lube_axis_time_to_next_cycle       = j['res']['lube']['axis.time.to.next.cycle']
                data.lube_spindle_cycles_made           = j['res']['lube']['spindle.cycles.made']
                data.lube_spindle_time_to_next_cycle    = j['res']['lube']['spindle.time.to.next.cycle']
                data.feed_programmed                    = j['res']['feed']['programmed']
                data.feed_target                        = j['res']['feed']['target']
                data.feed_reference                     = j['res']['feed']['reference']
                data.spindle_programmed                 = j['res']['spindle']['programmed']
                data.spindle_target                     = j['res']['spindle']['target']
                data.spindle_actual                     = j['res']['spindle']['actual']
                data.spindle_load                       = j['res']['spindle']['load']
                data.spindle_torque                     = j['res']['spindle']['torque']
                data.spindle_phase                      = j['res']['spindle']['phase']
                data.spindle_direction                  = j['res']['spindle']['direction']
                data.spindle_not_ready                  = j['res']['spindle']['not.ready']
                data.spindle_shaft                      = j['res']['spindle']['shaft']
                data.spindle_status                     = j['res']['spindle']['status']
                data.spindle_voltage                    = j['res']['spindle']['voltage']
                data.override_jog                       = j['res']['override']['jog']
                data.override_jog_min                   = j['res']['override']['jog.min']
                data.override_jog_max                   = j['res']['override']['jog.max']
                data.override_jog_enabled               = j['res']['override']['jog.enabled']
                data.override_jog_locked                = j['res']['override']['jog.locked']
                data.override_spindle                   = j['res']['override']['spindle']
                data.override_spindle_min               = j['res']['override']['spindle.min']
                data.override_spindle_max               = j['res']['override']['spindle.max']
                data.override_spindle_enabled           = j['res']['override']['spindle.enabled']
                data.override_spindle_locked            = j['res']['override']['spindle.locked']
                data.override_fast                      = j['res']['override']['fast']
                data.override_fast_min                  = j['res']['override']['fast.min']
                data.override_fast_max                  = j['res']['override']['fast.max']
                data.override_fast_enabled              = j['res']['override']['fast.enabled']
                data.override_fast_locked               = j['res']['override']['fast.locked']
                data.override_feed                      = j['res']['override']['feed']
                data.override_feed_min                  = j['res']['override']['feed.min']
                data.override_feed_max                  = j['res']['override']['feed.max']
                data.override_feed_enabled              = j['res']['override']['feed.enabled']
                data.override_feed_locked               = j['res']['override']['feed.locked']
                data.override_feed_custom_1             = j['res']['override']['feed.custom.1']
                data.override_feed_custom_1_min         = j['res']['override']['feed.custom.1.min']
                data.override_feed_custom_1_max         = j['res']['override']['feed.custom.1.max']
                data.override_feed_custom_1_enabled     = j['res']['override']['feed.custom.1.enabled']
                data.override_feed_custom_1_locked      = j['res']['override']['feed.custom.1.locked']
                data.override_feed_custom_2             = j['res']['override']['feed.custom.2']
                data.override_feed_custom_2_min         = j['res']['override']['feed.custom.2.min']
                data.override_feed_custom_2_max         = j['res']['override']['feed.custom.2.max']
                data.override_feed_custom_2_enabled     = j['res']['override']['feed.custom.2.enabled']
                data.override_feed_custom_2_locked      = j['res']['override']['feed.custom.2.locked']
                data.override_plasma_power              = j['res']['override']['plasma.power']
                data.override_plasma_power_min          = j['res']['override']['plasma.power.min']
                data.override_plasma_power_max          = j['res']['override']['plasma.power.max']
                data.override_plasma_power_enabled      = j['res']['override']['plasma.power.enabled']
                data.override_plasma_power_locked       = j['res']['override']['plasma.power.locked']
                data.override_plasma_voltage            = j['res']['override']['plasma.voltage']
                data.override_plasma_voltage_min        = j['res']['override']['plasma.voltage.min']
                data.override_plasma_voltage_max        = j['res']['override']['plasma.voltage.max']
                data.override_plasma_voltage_enabled    = j['res']['override']['plasma.voltage.enabled']
                data.override_plasma_voltage_locked     = j['res']['override']['plasma.voltage.locked']
                data.tool_id                            = j['res']['tool']['id']
                data.tool_slot                          = j['res']['tool']['slot']
                data.tool_slot_enabled                  = j['res']['tool']['slot.enabled']
                data.tool_type                          = j['res']['tool']['type']
                data.tool_diameter                      = j['res']['tool']['diameter']
                data.tool_offset_x                      = j['res']['tool']['offset.x']
                data.tool_offset_y                      = j['res']['tool']['offset.y']
                data.tool_offset_z                      = j['res']['tool']['offset.z']
                data.tool_param_1                       = j['res']['tool']['param.1']
                data.tool_param_2                       = j['res']['tool']['param.2']
                data.tool_param_3                       = j['res']['tool']['param.3']
                data.tool_description                   = j['res']['tool']['description']
                data.simulator_available                = j['res']['simulator']['available']
                data.simulator_state                    = j['res']['simulator']['state']
                data.simulator_planned_time_ms          = j['res']['simulator']['planned.time.ms']
                data.simulator_current_time_ms          = j['res']['simulator']['current.time.ms']
                data.simulator_speed_track              = j['res']['simulator']['speed.track']
                data.has_data = True
            return data
        except Exception:
            return APICncInfo()

    def get_cnc_parameters(self, address: int, elements: int) -> APICncParameters:
        """Return CNC parameters starting from the specified address."""
        try:
            data = APICncParameters()
            if not self.is_connected:
                return data
            request = self.create_compact_json_request(
                {
                    "get"       : "cnc.parameters",
                    "address"   : address,
                    "elements"  : elements
                }
            )
            response = self.__send_command(request)
            if response:
                j = json.loads(response)
                data.values                             = j['res']['values']
                data.descriptions                       = j['res']['descriptions']
                data.has_data = True
            return data
        except Exception:
            return APICncParameters()

    def get_compile_info(self) -> APICompileInfo:
        """Return compile information."""
        try:
            data = APICompileInfo()
            if not self.is_connected:
                return data
            request = '{"get":"compile.info"}'
            response = self.__send_command(request)
            if response:
                j = json.loads(response)
                data.code                               = j['res']['code']
                data.code_line                          = j['res']['code.line']
                data.file_line                          = j['res']['file.line']
                data.file_name                          = j['res']['file.name']
                data.message                            = j['res']['message']
                data.mode                               = j['res']['mode']
                data.state                              = j['res']['state']
                data.has_data = True
            return data
        except Exception:
            return APICompileInfo()

    def get_coordinate_systems_info(self) -> APICoordinateSystemsInfo:
        """Return coordinate systems information."""
        try:
            data = APICoordinateSystemsInfo()
            if not self.is_connected:
                return data
            request = '{"get":"coordinate.systems.info"}'
            response = self.__send_command(request)
            if response:
                j = json.loads(response)
                data.working_wcs                        = j['res']['working.wcs']
                data.working_offset                     = j['res']['working.offset']
                data.wcs_1                              = j['res']['wcs.1']
                data.wcs_2                              = j['res']['wcs.2']
                data.wcs_3                              = j['res']['wcs.3']
                data.wcs_4                              = j['res']['wcs.4']
                data.wcs_5                              = j['res']['wcs.5']
                data.wcs_6                              = j['res']['wcs.6']
                data.wcs_7                              = j['res']['wcs.7']
                data.wcs_8                              = j['res']['wcs.8']
                data.wcs_9                              = j['res']['wcs.9']
                data.has_data                           = True
            return data
        except Exception:
            return APICoordinateSystemsInfo()

    def get_digital_inputs(self) -> APIDigitalInputs:
        """Return digital inputs values."""
        try:
            data = APIDigitalInputs()
            if not self.is_connected:
                return data
            request = '{"get":"digital.inputs"}'
            response = self.__send_command(request)
            if response:
                j = json.loads(response)
                data.value                              = j['res']['value']
                data.has_data                           = True
            return data
        except Exception:
            return APIDigitalInputs()

    def get_digital_outputs(self) -> APIDigitalOutputs:
        """Return digital outputs values."""
        try:
            data = APIDigitalOutputs()
            if not self.is_connected:
                return data
            request = '{"get":"digital.outputs"}'
            response = self.__send_command(request)
            if response:
                j = json.loads(response)
                data.value                              = j['res']['value']
                data.has_data                           = True
            return data
        except Exception:
            return APIDigitalOutputs()

    def get_enabled_commands(self) -> APIEnabledCommands:
        """Return enabled commands state."""
        try:
            data = APIEnabledCommands()
            if not self.is_connected:
                return data
            request = '{"get":"enabled.commands"}'
            response = self.__send_command(request)
            if response:
                j = json.loads(response)
                data.cnc_csfm_aux                       = j['res']['cnc.csfm.aux']
                data.cnc_csfm_cooler_flood              = j['res']['cnc.csfm.cooler.flood']
                data.cnc_csfm_cooler_mist               = j['res']['cnc.csfm.cooler.mist']
                data.cnc_csfm_jog_mode                  = j['res']['cnc.csfm.jog.mode']
                data.cnc_csfm_spindle_cw                = j['res']['cnc.csfm.spindle.cw']
                data.cnc_csfm_spindle_ccw               = j['res']['cnc.csfm.spindle.ccw']
                data.cnc_csfm_thc_disabled              = j['res']['cnc.csfm.thc.disabled']
                data.cnc_csfm_torch                     = j['res']['cnc.csfm.torch']
                data.cnc_connection_close               = j['res']['cnc.connection.close']
                data.cnc_connection_open                = j['res']['cnc.connection.open']
                data.cnc_continue                       = j['res']['cnc.continue']
                data.cnc_homing                         = j['res']['cnc.homing']
                data.cnc_jog_command                    = j['res']['cnc.jog.command']
                data.cnc_mdi_command                    = j['res']['cnc.mdi.command']
                data.cnc_parameters                     = j['res']['cnc.parameters']
                data.cnc_pause                          = j['res']['cnc.pause']
                data.cnc_resume                         = j['res']['cnc.resume']
                data.cnc_resume_from_line               = j['res']['cnc.resume.from.line']
                data.cnc_resume_from_point              = j['res']['cnc.resume.from.point']
                data.cnc_start                          = j['res']['cnc.start']
                data.cnc_start_from_line                = j['res']['cnc.start.from.line']
                data.cnc_start_from_point               = j['res']['cnc.start.from.point']
                data.cnc_stop                           = j['res']['cnc.stop']
                data.program_analysis                   = j['res']['program.analysis']
                data.program_analysis_abort             = j['res']['program.analysis.abort']
                data.program_gcode_add_text             = j['res']['program.gcode.add.text']
                data.program_gcode_clear                = j['res']['program.gcode.clear']
                data.program_gcode_modified             = j['res']['program.gcode.modified']
                data.program_gcode_set_text             = j['res']['program.gcode.set.text']
                data.program_load                       = j['res']['program.load']
                data.program_new                        = j['res']['program.new']
                data.program_save                       = j['res']['program.save']
                data.program_save_as                    = j['res']['program.save.as']
                data.reset_alarms                       = j['res']['reset.alarms']
                data.reset_alarms_history               = j['res']['reset.alarms.history']
                data.reset_warnings                     = j['res']['reset.warnings']
                data.reset_warnings_history             = j['res']['reset.warnings.history']
                data.set_dynamic_offsets                = j['res']['set.dynamic.offsets']
                data.set_kinematics                     = j['res']['set.kinematics']
                data.set_program_position               = j['res']['set.program.position']
                data.set_simulator_current_time_ms      = j['res']['set.simulator.current.time.ms']
                data.set_simulator_speed_track          = j['res']['set.simulator.speed.track']
                data.show_ui_dialog                     = j['res']['show.ui.dialog']
                data.simulator_continue                 = j['res']['simulator.continue']
                data.simulator_pause                    = j['res']['simulator.pause']
                data.simulator_start                    = j['res']['simulator.start']
                data.simulator_step_backward            = j['res']['simulator.step.backward']
                data.simulator_step_forward             = j['res']['simulator.step.forward']
                data.simulator_stop                     = j['res']['simulator.stop']
                data.tools_lib_write                    = j['res']['tools.lib.write']
                data.has_data                           = True
            return data
        except Exception:
            return APIEnabledCommands()

    def get_localization_info(self) -> APILocalizationInfo:
        """Return localization information."""
        try:
            data = APILocalizationInfo()
            if not self.is_connected:
                return data
            request = '{"get":"localization.info"}'
            response = self.__send_command(request)
            if response:
                j = json.loads(response)
                data.units_mode                         = j['res']['units.mode']
                data.locale_name                        = j['res']['locale.name']
                data.description                        = j['res']['description']
                l = j['res']['list']
                if len(l) == 0:
                    data.list = []
                else:
                    data.list = [data.LocalizationData() for _ in range(len(l))]
                    for i in range(len(data.list)):
                        data.list[i].locale_name        = l[i]['locale.name']
                        data.list[i].description        = l[i]['description']
                        data.list[i].owner              = l[i]['owner']
                        data.list[i].revisor            = l[i]['revisor']
                        data.list[i].version            = l[i]['version']
                        data.list[i].date               = l[i]['date']
                        data.list[i].program            = l[i]['program']
                data.has_data = True
            return data
        except Exception:
            return APILocalizationInfo()

    def get_machine_settings(self) -> APIMachineSettings:
        """Return machine settings."""
        try:
            data = APIMachineSettings()
            if not self.is_connected:
                return data
            request = '{"get":"machine.settings"}'
            response = self.__send_command(request)
            if response:
                j = json.loads(response)
                data.axis_machine_type                  = j['res']['axis']['machine.type']
                data.axis_kinematics_model              = j['res']['axis']['kinematics.model']
                data.axis_x_type                        = j['res']['axis']['x.type']
                data.axis_x_max_vel                     = j['res']['axis']['x.max.vel']
                data.axis_x_acc                         = j['res']['axis']['x.acc']
                data.axis_x_min_lim                     = j['res']['axis']['x.min.lim']
                data.axis_x_max_lim                     = j['res']['axis']['x.max.lim']
                data.axis_y_type                        = j['res']['axis']['y.type']
                data.axis_y_max_vel                     = j['res']['axis']['y.max.vel']
                data.axis_y_acc                         = j['res']['axis']['y.acc']
                data.axis_y_min_lim                     = j['res']['axis']['y.min.lim']
                data.axis_y_max_lim                     = j['res']['axis']['y.max.lim']
                data.axis_z_type                        = j['res']['axis']['z.type']
                data.axis_z_max_vel                     = j['res']['axis']['z.max.vel']
                data.axis_z_acc                         = j['res']['axis']['z.acc']
                data.axis_z_min_lim                     = j['res']['axis']['z.min.lim']
                data.axis_z_max_lim                     = j['res']['axis']['z.max.lim']
                data.axis_a_type                        = j['res']['axis']['a.type']
                data.axis_a_max_vel                     = j['res']['axis']['a.max.vel']
                data.axis_a_acc                         = j['res']['axis']['a.acc']
                data.axis_a_min_lim                     = j['res']['axis']['a.min.lim']
                data.axis_a_max_lim                     = j['res']['axis']['a.max.lim']
                data.axis_b_type                        = j['res']['axis']['b.type']
                data.axis_b_max_vel                     = j['res']['axis']['b.max.vel']
                data.axis_b_acc                         = j['res']['axis']['b.acc']
                data.axis_b_min_lim                     = j['res']['axis']['b.min.lim']
                data.axis_b_max_lim                     = j['res']['axis']['b.max.lim']
                data.axis_c_type                        = j['res']['axis']['c.type']
                data.axis_c_max_vel                     = j['res']['axis']['c.max.vel']
                data.axis_c_acc                         = j['res']['axis']['c.acc']
                data.axis_c_min_lim                     = j['res']['axis']['c.min.lim']
                data.axis_c_max_lim                     = j['res']['axis']['c.max.lim']
                data.kinematics_h_x                     = j['res']['axis']['kinematics.h.x']
                data.kinematics_h_y                     = j['res']['axis']['kinematics.h.y']
                data.kinematics_h_z                     = j['res']['axis']['kinematics.h.z']
                data.kinematics_j_x                     = j['res']['axis']['kinematics.j.x']
                data.kinematics_j_y                     = j['res']['axis']['kinematics.j.y']
                data.kinematics_j_z                     = j['res']['axis']['kinematics.j.z']
                data.has_data                           = True
            return data
        except Exception:
            return APIMachineSettings()

    def get_machining_info(self) -> APIMachiningInfo:
        """Return machining information."""

        def get_machining_info_used_tool(j):
            l = len(j['res']['tool.path']['used.tool'])
            if l == 0:
                return []
            ret = []
            for i in range(l):
                elem = APIMachiningInfoUsedTool()
                elem.tool_id = j['res']['tool.path']['used.tool'][i]['id']
                elem.in_fast = j['res']['tool.path']['used.tool'][i]['in.fast']
                elem.in_feed = j['res']['tool.path']['used.tool'][i]['in.feed']
                ret.append(elem)
            return ret

        try:
            data = APIMachiningInfo()
            if not self.is_connected:
                return data
            request = '{"get":"machining.info"}'
            response = self.__send_command(request)
            if response:
                j = json.loads(response)
                data.tool_path_in_fast                  = j['res']['tool.path']['in.fast']
                data.tool_path_in_feed                  = j['res']['tool.path']['in.feed']
                data.total_path                         = j['res']['tool.path']['total.path']
                data.planned_time                       = j['res']['tool.path']['planned.time']
                data.used_tool = get_machining_info_used_tool(j)
                data.tcp_extents_in_fast_min_x          = j['res']['tcp.extents.in.fast']['min.x']
                data.tcp_extents_in_fast_min_y          = j['res']['tcp.extents.in.fast']['min.y']
                data.tcp_extents_in_fast_min_z          = j['res']['tcp.extents.in.fast']['min.z']
                data.tcp_extents_in_fast_max_x          = j['res']['tcp.extents.in.fast']['max.x']
                data.tcp_extents_in_fast_max_y          = j['res']['tcp.extents.in.fast']['max.y']
                data.tcp_extents_in_fast_max_z          = j['res']['tcp.extents.in.fast']['max.z']
                data.tcp_extents_in_fast_length_x       = j['res']['tcp.extents.in.fast']['length.x']
                data.tcp_extents_in_fast_length_y       = j['res']['tcp.extents.in.fast']['length.y']
                data.tcp_extents_in_fast_length_z       = j['res']['tcp.extents.in.fast']['length.z']
                data.tcp_extents_in_feed_min_x          = j['res']['tcp.extents.in.feed']['min.x']
                data.tcp_extents_in_feed_min_y          = j['res']['tcp.extents.in.feed']['min.y']
                data.tcp_extents_in_feed_min_z          = j['res']['tcp.extents.in.feed']['min.z']
                data.tcp_extents_in_feed_max_x          = j['res']['tcp.extents.in.feed']['max.x']
                data.tcp_extents_in_feed_max_y          = j['res']['tcp.extents.in.feed']['max.y']
                data.tcp_extents_in_feed_max_z          = j['res']['tcp.extents.in.feed']['max.z']
                data.tcp_extents_in_feed_length_x       = j['res']['tcp.extents.in.feed']['length.x']
                data.tcp_extents_in_feed_length_y       = j['res']['tcp.extents.in.feed']['length.y']
                data.tcp_extents_in_feed_length_z       = j['res']['tcp.extents.in.feed']['length.z']
                data.joints_in_fast_min_x               = j['res']['joints.in.fast']['min.x']
                data.joints_in_fast_min_y               = j['res']['joints.in.fast']['min.y']
                data.joints_in_fast_min_z               = j['res']['joints.in.fast']['min.z']
                data.joints_in_fast_min_a               = j['res']['joints.in.fast']['min.a']
                data.joints_in_fast_min_b               = j['res']['joints.in.fast']['min.b']
                data.joints_in_fast_min_c               = j['res']['joints.in.fast']['min.c']
                data.joints_in_fast_max_x               = j['res']['joints.in.fast']['max.x']
                data.joints_in_fast_max_y               = j['res']['joints.in.fast']['max.y']
                data.joints_in_fast_max_z               = j['res']['joints.in.fast']['max.z']
                data.joints_in_fast_max_a               = j['res']['joints.in.fast']['max.a']
                data.joints_in_fast_max_b               = j['res']['joints.in.fast']['max.b']
                data.joints_in_fast_max_c               = j['res']['joints.in.fast']['max.c']
                data.joints_in_fast_length_x            = j['res']['joints.in.fast']['length.x']
                data.joints_in_fast_length_y            = j['res']['joints.in.fast']['length.y']
                data.joints_in_fast_length_z            = j['res']['joints.in.fast']['length.z']
                data.joints_in_fast_length_a            = j['res']['joints.in.fast']['length.a']
                data.joints_in_fast_length_b            = j['res']['joints.in.fast']['length.b']
                data.joints_in_fast_length_c            = j['res']['joints.in.fast']['length.c']
                data.joints_in_feed_min_x               = j['res']['joints.in.feed']['min.x']
                data.joints_in_feed_min_y               = j['res']['joints.in.feed']['min.y']
                data.joints_in_feed_min_z               = j['res']['joints.in.feed']['min.z']
                data.joints_in_feed_min_a               = j['res']['joints.in.feed']['min.a']
                data.joints_in_feed_min_b               = j['res']['joints.in.feed']['min.b']
                data.joints_in_feed_min_c               = j['res']['joints.in.feed']['min.c']
                data.joints_in_feed_max_x               = j['res']['joints.in.feed']['max.x']
                data.joints_in_feed_max_y               = j['res']['joints.in.feed']['max.y']
                data.joints_in_feed_max_z               = j['res']['joints.in.feed']['max.z']
                data.joints_in_feed_max_a               = j['res']['joints.in.feed']['max.a']
                data.joints_in_feed_max_b               = j['res']['joints.in.feed']['max.b']
                data.joints_in_feed_max_c               = j['res']['joints.in.feed']['max.c']
                data.joints_in_feed_length_x            = j['res']['joints.in.feed']['length.x']
                data.joints_in_feed_length_y            = j['res']['joints.in.feed']['length.y']
                data.joints_in_feed_length_z            = j['res']['joints.in.feed']['length.z']
                data.joints_in_feed_length_a            = j['res']['joints.in.feed']['length.a']
                data.joints_in_feed_length_b            = j['res']['joints.in.feed']['length.b']
                data.joints_in_feed_length_c            = j['res']['joints.in.feed']['length.c']
                data.has_data = True
            return data
        except Exception:
            return APIMachiningInfo()

    def get_mru_programs_list(self) -> APIMRUProgramsList:
        """Return the MRU programs list."""
        try:
            data = APIMRUProgramsList()
            if not self.is_connected:
                return data
            request = '{"get":"mru.programs.list"}'
            response = self.__send_command(request)
            if response:
                j = json.loads(response)
                data.items                              = j['res']['items']
                data.has_data = True
            return data
        except Exception:
            return APIMRUProgramsList()

    def get_operator_request(self) -> APIOperatorRequest:
        """Return pending operator request information."""
        try:
            data = APIOperatorRequest()
            if not self.is_connected:
                return data
            request = '{"get":"operator.request"}'
            response = self.__send_command(request)
            if response:
                j = json.loads(response)
                data.id                                 = j['res']['id']
                data.type                               = j['res']['type']
                data.media                              = j['res']['media']
                data.message                            = j['res']['message']
                data.data_elements                      = j['res']['data']['elements']
                data.data_d01                           = j['res']['data']['d01']
                data.data_d02                           = j['res']['data']['d02']
                data.data_d03                           = j['res']['data']['d03']
                data.data_d04                           = j['res']['data']['d04']
                data.data_d05                           = j['res']['data']['d05']
                data.data_d06                           = j['res']['data']['d06']
                data.data_d07                           = j['res']['data']['d07']
                data.data_d08                           = j['res']['data']['d08']
                data.data_d09                           = j['res']['data']['d09']
                data.data_d10                           = j['res']['data']['d10']
                data.external_continue_requested        = j['res']['external.continue.requested']
                data.has_data = True
            return data
        except Exception:
            return APIOperatorRequest()

    def get_program_info(self) -> APIProgramInfo:
        """Return loaded program information."""
        try:
            data = APIProgramInfo()
            if not self.is_connected:
                return data
            request = '{"get":"program.info"}'
            response = self.__send_command(request, first_timeout=50)
            if response:
                j = json.loads(response)
                data.file_name                          = j['res']['file.name']
                data.code                               = j['res']['code']
                data.has_data = True
            return data
        except Exception:
            return APIProgramInfo()

    def get_programmed_points(self) -> APIProgrammedPoints:
        """Return programmed points information."""
        try:
            data = APIProgrammedPoints()
            if not self.is_connected:
                return data
            request = '{"get":"programmed.points"}'
            response = self.__send_command(request)
            if response:
                j = json.loads(response)
                data.points                             = j['res']['points']
                data.has_data = True
            return data
        except Exception:
            return APIProgrammedPoints()

    def get_runtime_data(self) -> APIRuntimeData:
        """Return runtime data information."""
        try:
            data = APIRuntimeData()
            if not self.is_connected:
                return data
            request = '{"get":"runtime.data"}'
            response = self.__send_command(request)
            if response:
                j = json.loads(response)
                data.state                              = j['res']['state']
                data.pending_item.gcode_line            = j['res']['pending.item']['gcode.line']
                data.pending_item.canon_id              = j['res']['pending.item']['canon.id']
                data.pending_item.canon_code            = j['res']['pending.item']['canon.code']
                data.pending_item.canon_segment         = j['res']['pending.item']['canon.segment']
                data.pending_item.text                  = j['res']['pending.item']['text']
                data.acquired_items                     = []
                for item in j['res']['acquired.items']:
                    acquired_item = APIRuntimeDataAcquiredItem()
                    acquired_item.datetime              = self.__d(item['datetime'])
                    acquired_item.gcode_line            = item['gcode.line']
                    acquired_item.canon_id              = item['canon.id']
                    acquired_item.canon_code            = item['canon.code']
                    acquired_item.canon_segment         = item['canon.segment']
                    acquired_item.text                  = item['text']
                    acquired_item.data                  = item['data']
                    data.acquired_items.append(acquired_item)
                data.has_data = True
            return data
        except Exception:
            return APIRuntimeData()

    def get_scanning_laser_info(self) -> APIScanningLaserInfo:
        """Return scanning laser information."""
        try:
            data = APIScanningLaserInfo()
            if not self.is_connected:
                return data
            request = '{"get":"scanning.laser.info"}'
            response = self.__send_command(request)
            if response:
                j = json.loads(response)
                data.laser_out_bit                      = j['res']['laser.out.bit']
                data.laser_out_umf                      = j['res']['laser.out.umf']
                data.laser_h_measure                    = j['res']['laser.h.measure']
                data.laser_mcs_x_position               = j['res']['laser.mcs.x.position']
                data.laser_mcs_y_position               = j['res']['laser.mcs.y.position']
                data.laser_mcs_z_position               = j['res']['laser.mcs.z.position']
                data.has_data = True
            return data
        except Exception:
            return APIScanningLaserInfo()

    def get_system_info(self) -> APISystemInfo:
        """Return system information."""
        try:
            data = APISystemInfo()
            if not self.is_connected:
                return data
            request = '{"get":"system.info"}'
            response = self.__send_command(request)
            if response:
                j = json.loads(response)
                data.machine_name                       = j['res']['machine.name']
                data.control_software_version           = j['res']['control.software.version']
                data.core_version                       = j['res']['core.version']
                data.api_server_version                 = j['res']['api.server.version']
                data.firmware_version                   = j['res']['firmware.version']
                data.firmware_version_tag               = j['res']['firmware.version.tag']
                data.firmware_interface_level           = j['res']['firmware.interface.level']
                data.order_code                         = j['res']['order.code']
                data.customer_id                        = j['res']['customer.id']
                data.serial_number                      = j['res']['serial.number']
                data.part_number                        = j['res']['part.number']
                data.customization_number               = j['res']['customization.number']
                data.hardware_version                   = j['res']['hardware.version']
                data.operative_system                   = j['res']['operative.system']
                data.operative_system_crc               = j['res']['operative.system.crc']
                data.pld_version                        = j['res']['pld.version']
                data.licensed_feature_panel_pc          = j['res']['licensed.feature']['panel.pc']
                data.licensed_feature_panel_pc_demo     = j['res']['licensed.feature']['panel.pc.demo']
                data.licensed_feature_work_orders       = j['res']['licensed.feature']['work.orders']
                data.licensed_feature_opc_ua_server     = j['res']['licensed.feature']['opc.ua.server']
                data.licensed_feature_probe_sdk_g1      = j['res']['licensed.feature']['probe.sdk.g1']
                data.licensed_feature_probe_sdk_g2      = j['res']['licensed.feature']['probe.sdk.g2']
                data.licensed_feature_probe_sdk_g3      = j['res']['licensed.feature']['probe.sdk.g3']
                data.licensed_feature_probe_sdk_g4      = j['res']['licensed.feature']['probe.sdk.g4']
                data.licensed_feature_probe_sdk_g5      = j['res']['licensed.feature']['probe.sdk.g5']
                data.has_data = True
            return data
        except Exception:
            return APISystemInfo()

    def get_toolpath_data(self, mode: int = 0) -> APIToolpathData:
        """Get toolpath data as numpy data array in normal or raw mode."""
        try:
            data = APIToolpathData()
            if not self.is_connected:
                return data

            if not isinstance(mode, int) or isinstance(mode, bool):
                return data

            if mode == 0:
                request = '{"get":"toolpath.data"}'
                response = self.__send_command(request)
                if response:
                    j = json.loads(response)
                    b64_string                              = j['res']['data']
                    data.data = base64.b64decode(b64_string)
                    data.has_data = True
            elif mode == 1:
                request = '{"get":"toolpath.data","mode":1}'
                raw = self.__send_command_raw(request)
                if raw is None:
                    return data
                data.data = raw
                data.has_data = True

            return data
        except Exception:
            return APIToolpathData()

    def get_tools_lib_count(self) -> APIToolsLibCount:
        """Return tool library count."""
        try:
            data = APIToolsLibCount()
            if not self.is_connected:
                return data
            request = '{"get":"tools.lib.count"}'
            response = self.__send_command(request)
            if response:
                j = json.loads(response)
                data.count                              = j['res']['count']
                data.has_data = True
            return data
        except Exception:
            return APIToolsLibCount()

    def get_tools_lib_info(self, index: int | None = None) -> APIToolsLibInfo:
        """Return tool library information for the specified index."""
        try:
            data = APIToolsLibInfo()
            if not self.is_connected:
                return data
            if not isinstance(index, int):
                return data
            request = '{' + f'"get":"tools.lib.info","index":{index}' + '}'
            response = self.__send_command(request)
            if response:
                j = json.loads(response)
                data.data.tool_index                    = j['res']['index']
                data.data.tool_id                       = j['res']['id']
                data.data.tool_slot                     = j['res']['slot']
                data.data.tool_type                     = j['res']['type']
                data.data.tool_diameter                 = j['res']['diameter']
                data.data.tool_offset_x                 = j['res']['offset.x']
                data.data.tool_offset_y                 = j['res']['offset.y']
                data.data.tool_offset_z                 = j['res']['offset.z']
                data.data.tool_param_1                  = j['res']['param.1']
                data.data.tool_param_2                  = j['res']['param.2']
                data.data.tool_param_3                  = j['res']['param.3']
                data.data.tool_param_4                  = j['res']['param.4']
                data.data.tool_param_5                  = j['res']['param.5']
                data.data.tool_param_6                  = j['res']['param.6']
                data.data.tool_param_7                  = j['res']['param.7']
                data.data.tool_param_8                  = j['res']['param.8']
                data.data.tool_param_9                  = j['res']['param.9']
                data.data.tool_param_10                 = j['res']['param.10']
                data.data.tool_param_51                 = j['res']['param.51']
                data.data.tool_param_52                 = j['res']['param.52']
                data.data.tool_param_53                 = j['res']['param.53']
                data.data.tool_param_54                 = j['res']['param.54']
                data.data.tool_param_55                 = j['res']['param.55']
                data.data.tool_param_56                 = j['res']['param.56']
                data.data.tool_param_57                 = j['res']['param.57']
                data.data.tool_param_58                 = j['res']['param.58']
                data.data.tool_param_59                 = j['res']['param.59']
                data.data.tool_param_60                 = j['res']['param.60']
                data.data.tool_description              = j['res']['description']
                data.has_data = True
            return data
        except Exception:
            return APIToolsLibInfo()

    def get_tools_lib_infos(self) -> APIToolsLibInfos:
        """Return all tool library information entries."""
        try:
            data = APIToolsLibInfos()
            if not self.is_connected:
                return data
            request = '{"get":"tools.lib.infos"}'
            response = self.__send_command(request)
            if response:
                j = json.loads(response)
                data.slot_enabled                       = j['res']['slot.enabled']
                tools = j['res'].get('tools', [])
                if tools:
                    data.data = [APIToolsLibInfoForGet() for _ in range(len(tools))]
                    for i in range(len(data.data)):
                        data.data[i].tool_index         = tools[i]['index']
                        data.data[i].tool_id            = tools[i]['id']
                        data.data[i].tool_slot          = tools[i]['slot']
                        data.data[i].tool_type          = tools[i]['type']
                        data.data[i].tool_diameter      = tools[i]['diameter']
                        data.data[i].tool_offset_x      = tools[i]['offset.x']
                        data.data[i].tool_offset_y      = tools[i]['offset.y']
                        data.data[i].tool_offset_z      = tools[i]['offset.z']
                        data.data[i].tool_param_1       = tools[i]['param.1']
                        data.data[i].tool_param_2       = tools[i]['param.2']
                        data.data[i].tool_param_3       = tools[i]['param.3']
                        data.data[i].tool_param_4       = tools[i]['param.4']
                        data.data[i].tool_param_5       = tools[i]['param.5']
                        data.data[i].tool_param_6       = tools[i]['param.6']
                        data.data[i].tool_param_7       = tools[i]['param.7']
                        data.data[i].tool_param_8       = tools[i]['param.8']
                        data.data[i].tool_param_9       = tools[i]['param.9']
                        data.data[i].tool_param_10      = tools[i]['param.10']
                        data.data[i].tool_param_51      = tools[i]['param.51']
                        data.data[i].tool_param_52      = tools[i]['param.52']
                        data.data[i].tool_param_53      = tools[i]['param.53']
                        data.data[i].tool_param_54      = tools[i]['param.54']
                        data.data[i].tool_param_55      = tools[i]['param.55']
                        data.data[i].tool_param_56      = tools[i]['param.56']
                        data.data[i].tool_param_57      = tools[i]['param.57']
                        data.data[i].tool_param_58      = tools[i]['param.58']
                        data.data[i].tool_param_59      = tools[i]['param.59']
                        data.data[i].tool_param_60      = tools[i]['param.60']
                        data.data[i].tool_description   = tools[i]['description']
                data.has_data = True
            return data
        except Exception:
            return APIToolsLibInfos()

    def get_tools_lib_tool_index_from_id(self, tool_id: int | None = None) -> APIToolsLibToolIndexFromId:
        """Return tool library index for the specified tool id."""
        try:
            data = APIToolsLibToolIndexFromId()
            if not self.is_connected:
                return data
            if not isinstance(tool_id, int):
                return data
            request = '{' + f'"get":"tools.lib.tool.index.from.id","id":{tool_id}' + '}'
            response = self.__send_command(request)
            if response:
                j = json.loads(response)
                data.index                              = j['res']['index']
                data.has_data = True
            return data
        except Exception:
            return APIToolsLibToolIndexFromId()

    def get_warnings_current_list(self) -> APIAlarmsWarningsList:
        """Return current warnings list."""
        try:
            data = APIAlarmsWarningsList()
            if not self.is_connected:
                return data
            request = '{"get":"warnings.current.list"}'
            response = self.__send_command(request)
            if response:
                j = json.loads(response)
                l = j['res']['list']
                if len(l) == 0:
                    data.list = []
                else:
                    data.list = [data.AlarmWarningData() for _ in range(len(l))]
                    for i in range(len(data.list)):
                        data.list[i].code               = l[i]['code']
                        data.list[i].info_1             = l[i]['info.1']
                        data.list[i].info_2             = l[i]['info.2']
                        data.list[i].text               = l[i]['text']
                        data.list[i].datetime           = self.__d(l[i]['datetime'])
                data.has_data = True
            return data
        except Exception:
            return APIAlarmsWarningsList()

    def get_warnings_history_list(self) -> APIAlarmsWarningsList:
        """Return warnings history list."""
        try:
            data = APIAlarmsWarningsList()
            if not self.is_connected:
                return data
            request = '{"get":"warnings.history.list"}'
            response = self.__send_command(request)
            if response:
                j = json.loads(response)
                l = j['res']['list']
                if len(l) == 0:
                    data.list = []
                else:
                    data.list = [data.AlarmWarningData() for _ in range(len(l))]
                    for i in range(len(data.list)):
                        data.list[i].code               = l[i]['code']
                        data.list[i].info_1             = l[i]['info.1']
                        data.list[i].info_2             = l[i]['info.2']
                        data.list[i].text               = l[i]['text']
                        data.list[i].datetime           = self.__d(l[i]['datetime'])
                data.has_data = True
            return data
        except Exception:
            return APIAlarmsWarningsList()

    def get_vm_geometry_info(self, names: list[str]) -> list[APIVMGeometryInfo] | None:
        """Return virtual machine geometry information for the specified names."""
        try:
            if not isinstance(names, list):
                return None
            names_count = len(names)
            if names_count == 0:
                return None
            data = [APIVMGeometryInfo() for _ in range(names_count)]
            for name in names:
                if not isinstance(name, str):
                    return None
            request = self.create_compact_json_request({
                "get": "vm.geometry.info",
                "name": names
            })
            response = self.__send_command(request)
            if response:
                j = json.loads(response)
                for i in range(names_count):
                    data[i].name                        = j['res'][i]['name']
                    data[i].x                           = j['res'][i]['x']
                    data[i].y                           = j['res'][i]['y']
                    data[i].z                           = j['res'][i]['z']
                    data[i].color                       = j['res'][i]['color']
                    data[i].scale                       = j['res'][i]['scale']
                    data[i].visible                     = j['res'][i]['visible']
                    data[i].edges_angle                 = j['res'][i]['edges.angle']
                    data[i].edges_visible               = j['res'][i]['edges.visible']
                    data[i].has_data = data[i].name != ''
            return data
        except Exception:
            return None

    def get_work_info(self) -> APIWorkInfo:
        """Return work information."""
        try:
            if not self.is_connected:
                raise Exception()
            data = APIWorkInfo()
            request = '{"get":"work.info"}'
            response = self.__send_command(request)
            if response:
                j = json.loads(response)
                data.work_mode                          = j['res']['work.mode']
                data.active_work_order_code             = j['res']['active.work.order.code']
                data.active_work_order_file_index       = j['res']['active.work.order.file.index']
                data.file_name                          = j['res']['file.name']
                data.planned_time                       = j['res']['planned.time']
                data.worked_time                        = j['res']['worked.time']
                data.has_data = True
            return data
        except Exception:
            return APIWorkInfo()

    def get_work_order_code_list(self) -> APIWorkOrderCodeList:
        """Return work order code list."""
        try:
            if self.is_connected is False:
                raise Exception()
            data = APIWorkOrderCodeList()
            request = '{"get":"work.order.code.list"}'
            response = self.__send_command(request)
            if response:
                j = json.loads(response)
                if len(j['res']) == 0:
                    data.data = []
                else:
                    data.data = [data.ListData() for _ in range(len(j['res']))]
                    for i in range(len(data.data)):
                        data.data[i].order_code         = j['res'][i][0]
                        data.data[i].order_state        = j['res'][i][1]
                        data.data[i].revision_number    = j['res'][i][2]
                data.has_data = True
            return data
        except Exception:
            return APIWorkOrderCodeList()

    def get_work_order_data(self, order_code: str, mode: int = 0) -> APIWorkOrderDataForGet:
        """Return work order data for the specified order code."""
        try:
            if self.is_connected is False:
                raise Exception()
            data = APIWorkOrderDataForGet()

            mode_request = ''
            if isinstance(mode, int) and mode == 1:
                mode_request = ',"mode":1'

            request = '{"get":"work.order.data","order.code":"' + order_code + '"' + mode_request + '}'
            response = self.__send_command(request)
            if response:
                j = json.loads(response)
                data.revision_number                    = self.__i(j['res']['revision.number'])
                data.order_state                        = self.__s(j['res']['order.state'])
                data.order_locked                       = self.__b(j['res']['order.locked'])
                data.order_code                         = j['res']['order.code']
                data.order_priority                     = j['res']['order.priority']
                data.job_order_code                     = j['res']['job.order.code']
                data.customer_code                      = j['res']['customer.code']
                data.item_code                          = j['res']['item.code']
                data.material_code                      = j['res']['material.code']
                data.order_notes                        = j['res']['order.notes']
                for i in range(8):
                    data.files[i].file_name             = j['res']['files'][i]['file.name']
                    data.files[i].file_state            = j['res']['files'][i]['file.state']
                    data.files[i].pieces_per_file       = j['res']['files'][i]['pieces.per.file']
                    data.files[i].requested_pieces      = j['res']['files'][i]['requested.pieces']
                    data.files[i].produced_pieces       = j['res']['files'][i]['produced.pieces']
                    data.files[i].discarded_pieces      = j['res']['files'][i]['discarded.pieces']
                data.use_deadline_datetime              = bool(j['res']['use.deadline.datetime'])
                data.creation_datetime                  = self.__d(j['res']['creation.datetime'])
                data.deadline_datetime                  = self.__d(j['res']['deadline.datetime'])
                data.reception_datetime                 = self.__d(j['res']['reception.datetime'])
                data.acceptance_datetime                = self.__d(j['res']['acceptance.datetime'])
                data.begin_datetime                     = self.__d(j['res']['begin.datetime'])
                data.end_datetime                       = self.__d(j['res']['end.datetime'])
                data.archived_datetime                  = self.__d(j['res']['archived.datetime'])
                data.time_for_setup                     = self.__i(j['res']['time.for.setup'])
                data.time_for_idle                      = self.__i(j['res']['time.for.idle'])
                data.time_for_work                      = self.__i(j['res']['time.for.work'])
                data.time_total                         = self.__i(j['res']['time.total'])
                data.operator_notes                     = self.__s(j['res']['operator.notes'])
                data.log_items                          = []
                log_items = len(j['res']['log.items'])
                if log_items > 0:
                    data.log_items = [data.LogItemData() for _ in range(log_items)]
                    for i in range(log_items):
                        data.log_items[i].log_id        = j['res']['log.items'][i]['log.id']
                        data.log_items[i].log_datetime  = self.__d(j['res']['log.items'][i]['log.datetime'])
                        data.log_items[i].log_info_1    = j['res']['log.items'][i]['log.info.1']
                        data.log_items[i].log_info_2    = j['res']['log.items'][i]['log.info.2']
                data.has_data = True
            return data
        except Exception:
            return APIWorkOrderDataForGet()

    def get_work_order_file_list(self, path: str ='', file_filter: str ='') -> APIWorkOrderFileList:
        """Return work order file list."""
        try:
            if self.is_connected is False:
                raise Exception()
            data = APIWorkOrderFileList()
            request = '{"get":"work.order.file.list"'
            if path:
                request = request + ',"path":"' + path + '"'
            if file_filter:
                request = request + ',"file.filter":"' + file_filter + '"'
            request = request + '}'
            response = self.__send_command(request)
            if response:
                j = json.loads(response)
                files = len(j["res"])
                if files > 0:
                    data.files = [data.FileData() for _ in range(files)]
                    for i in range(files):
                        data.files[i].type                  = j['res'][i]['type']
                        data.files[i].name                  = j['res'][i]['name']
                        data.files[i].size                  = j['res'][i]['size']
                        data.files[i].creation_datetime     = self.__d(j['res'][i]['creation.datetime'])
                        data.files[i].last_access_datetime  = self.__d(j['res'][i]['last.access.datetime'])
                        data.files[i].last_write_datetime   = self.__d(j['res'][i]['last.write.datetime'])
                data.has_data = True
            return data
        except Exception:
            return APIWorkOrderFileList()
    #
    # == END: API Server "get" requests section


    # == BEG: API Server "set" requests section
    #
    def set_cnc_parameters(self, address: int, values: list | None = None, descriptions: list | None = None) -> bool:
        """
        Set CNC parameters with validation for values and descriptions.

        Args:
            address (int)                   : The address for the parameters.
            values (list, optional)         : A list of numeric values (int or float).
            descriptions (list, optional)   : A list of string descriptions.

        Returns:
            bool                            : True if parameters are valid and processed; False otherwise.

        NOTE:
            - The `values` argument must contain at least one element if provided.
            - The `descriptions` argument must contain at least one element if provided.
            - If both `values` and `descriptions` are provided, they must have the same number of elements.
        """
        try:
            if not self.is_connected:
                return False

            if values is None and descriptions is None:
                return False

            v_count = 0
            d_count = 0

            if values is not None:
                if not isinstance(values, list):
                    return False
                v_count = len(values)
                if v_count < 1:
                    return False
                if not all(isinstance(value, (float, int)) for value in values):
                    return False

            if descriptions is not None:
                if not isinstance(descriptions, list):
                    return False
                d_count = len(descriptions)
                if d_count < 1:
                    return False
                if not all(isinstance(description, str) for description in descriptions):
                    return False

            if v_count == 0 and d_count == 0:
                return False
            if v_count and d_count and v_count != d_count:
                return False

            request = '{"set":"cnc.parameters","address":' + str(address) + ','
            if v_count:
                request += '"values":['
                for idx, value in enumerate(values):
                    request = request + str(value)
                    if idx < (len(values) - 1):
                        request = request + ','
                request += ']'
            if d_count:
                if v_count:
                    request += ','
                request += '"descriptions":['
                for idx, value in enumerate(descriptions):
                    request = request + '"' + value + '"'
                    if idx < (len(descriptions) - 1):
                        request = request + ','
                request += ']'
            request += '}'
            return self.__execute_request(request)
        except Exception:
            return False

    def set_dynamic_offset_x(self, value: int | float) -> bool:
        """Set dynamic offset for x-axis in um."""
        try:
            if not self.is_connected:
                return False
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                return False
            data = {
                "set": "dynamic.offsets",
                "offset.x": value,
            }
            request = self.create_compact_json_request(data)
            return self.__execute_request(request)
        except Exception:
            return False

    def set_dynamic_offset_y(self, value: int | float) -> bool:
        """Set dynamic offset for y-axis in um."""
        try:
            if not self.is_connected:
                return False
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                return False
            data = {
                "set": "dynamic.offsets",
                "offset.y": value,
            }
            request = self.create_compact_json_request(data)
            return self.__execute_request(request)
        except Exception:
            return False

    def set_dynamic_offset_z(self, value: int | float) -> bool:
        """Set dynamic offset for z-axis in um."""
        try:
            if not self.is_connected:
                return False
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                return False
            data = {
                "set": "dynamic.offsets",
                "offset.z": value,
            }
            request = self.create_compact_json_request(data)
            return self.__execute_request(request)
        except Exception:
            return False

    def set_dynamic_offsets(self, x: int | float | None = None, y: int | float | None = None, z: int | float | None = None) -> bool:
        """Set dynamic offsets for xyz-axes in um."""
        try:
            if not self.is_connected:
                return False
            data = {
                "set": "dynamic.offsets",
            }
            if x is not None:
                if not isinstance(x, (int, float)) or isinstance(x, bool):
                    return False
                data["offset.x"] = x
            if y is not None:
                if not isinstance(y, (int, float)) or isinstance(y, bool):
                    return False
                data["offset.y"] = y
            if z is not None:
                if not isinstance(z, (int, float)) or isinstance(z, bool):
                    return False
                data["offset.z"] = z
            if len(data) == 1:
                return False
            request = self.create_compact_json_request(data)
            return self.__execute_request(request)
        except Exception:
            return False

    def set_kinematics(self) -> bool:
        """NOT IMPLEMENTED HERE YET!"""
        return False

    def set_localization(self, units_mode: int | None = None, locale_name: str | None = None) -> bool:
        """Set localization values."""
        try:
            if not self.is_connected:
                return False

            has_data = False
            data = {"set": "localization"}

            if units_mode is not None:
                if type(units_mode) is not int:
                    return False
                if units_mode not in [UM_METRIC, UM_IMPERIAL]:
                    return False
                data['units.mode'] = units_mode
                has_data = True

            if locale_name is not None:
                if not isinstance(locale_name, str) or not locale_name.strip():
                    return False
                data['locale.name'] = locale_name.strip()
                has_data = True

            if not has_data:
                return False

            request = self.create_compact_json_request(data)
            return self.__execute_request(request)
        except Exception:
            return False

    def set_operator_response(self, response: APIOperatorResponse | None = None) -> bool:
        """Set operator response."""
        try:
            if not self.is_connected:
                return False

            if not isinstance(response, APIOperatorResponse):
                return False
            if not isinstance(response.id, str):
                return False
            if not isinstance(response.type, int) or isinstance(response.type, bool):
                return False
            if response.type not in [ORPT_CONTINUE, ORPT_STOP]:
                return False
            if not isinstance(response.data_elements, int) or isinstance(response.data_elements, bool):
                return False
            if response.data_elements < 0 or response.data_elements > 10:
                return False

            data = {
                "set": "operator.response",
                "id": response.id,
                "type": response.type
            }
            data["data"] = {}
            data["data"]["elements"] = response.data_elements
            if response.data_elements != 0:

                for idx in range(response.data_elements):
                    name = f'd{(idx + 1):02}'
                    value = getattr(response, f'data_{name}')
                    if isinstance(value, float):
                        if not math.isfinite(value):
                            value = None
                    else:
                        if value is not None:
                            value = None
                    data["data"][name] = value

            request = self.create_compact_json_request(data)
            return self.__execute_request(request)
        except Exception:
            return False

    def set_override_fast(self, value: int) -> bool:
        """Set fast override value."""
        try:
            if not self.is_connected:
                return False
            if not isinstance(value, int):
                return False
            return self.__execute_request(f'{{"set":"override", "name":"fast", "value":{value}}}')
        except Exception:
            return False

    def set_override_feed(self, value: int) -> bool:
        """Set feed override value."""
        try:
            if not self.is_connected:
                return False
            if not isinstance(value, int):
                return False
            return self.__execute_request(f'{{"set":"override", "name":"feed", "value":{value}}}')
        except Exception:
            return False

    def set_override_feed_custom_1(self, value: int) -> bool:
        """Set custom feed override 1 value."""
        try:
            if not self.is_connected:
                return False
            if not isinstance(value, int):
                return False
            return self.__execute_request(f'{{"set":"override", "name":"feed.custom.1", "value":{value}}}')
        except Exception:
            return False

    def set_override_feed_custom_2(self, value: int) -> bool:
        """Set custom feed override 2 value."""
        try:
            if not self.is_connected:
                return False
            if not isinstance(value, int):
                return False
            return self.__execute_request(f'{{"set":"override", "name":"feed.custom.2", "value":{value}}}')
        except Exception:
            return False

    def set_override_jog(self, value: int) -> bool:
        """Set jog override value."""
        try:
            if not self.is_connected:
                return False
            if not isinstance(value, int):
                return False
            return self.__execute_request(f'{{"set":"override", "name":"jog", "value":{value}}}')
        except Exception:
            return False

    def set_override_plasma_power(self, value: int) -> bool:
        """Set plasma power override value."""
        try:
            if not self.is_connected:
                return False
            if not isinstance(value, int):
                return False
            return self.__execute_request(f'{{"set":"override", "name":"plasma.power", "value":{value}}}')
        except Exception:
            return False

    def set_override_plasma_voltage(self, value: int) -> bool:
        """Set plasma voltage override value."""
        try:
            if not self.is_connected:
                return False
            if not isinstance(value, int):
                return False
            return self.__execute_request(f'{{"set":"override", "name":"plasma.voltage", "value":{value}}}')
        except Exception:
            return False

    def set_override_spindle(self, value: int) -> bool:
        """Set spindle override value."""
        try:
            if not self.is_connected:
                return False
            if not isinstance(value, int):
                return False
            return self.__execute_request(f'{{"set":"override", "name":"spindle", "value":{value}}}')
        except Exception:
            return False

    def set_program_position_a(self, value: float) -> bool:
        """Set A-axis program position value."""
        if not self.is_connected:
            return False
        return self.__execute_request('{"set":"program.position", "data":{"a":' + str(value) + '}}')

    def set_program_position_b(self, value: float) -> bool:
        """Set B-axis program position value."""
        if not self.is_connected:
            return False
        return self.__execute_request('{"set":"program.position", "data":{"b":' + str(value) + '}}')

    def set_program_position_c(self, value: float) -> bool:
        """Set C-axis program position value."""
        if not self.is_connected:
            return False
        return self.__execute_request('{"set":"program.position", "data":{"c":' + str(value) + '}}')

    def set_program_position_x(self, value: float) -> bool:
        """Set X-axis program position value."""
        if not self.is_connected:
            return False
        return self.__execute_request('{"set":"program.position", "data":{"x":' + str(value) + '}}')

    def set_program_position_x_with_laser_reference(self, value: float = 0.0) -> bool:
        """Set X-axis program position value using MCS.X position returned by scanning laser info."""
        if not self.is_connected:
            return False
        try:
            # check value
            if type(value) not in (int, float) or not math.isfinite(value):
                return False

            # get scanning laser info
            scanning_laser_info = self.get_scanning_laser_info()
            if not scanning_laser_info.has_data:
                return False

            # set x-axis program position
            return self.set_program_position_x(value - scanning_laser_info.laser_mcs_x_position)
        except Exception:
            return False

    def set_program_position_y(self, value: float) -> bool:
        """Set Y-axis program position value."""
        if not self.is_connected:
            return False
        return self.__execute_request('{"set":"program.position", "data":{"y":' + str(value) + '}}')

    def set_program_position_y_with_laser_reference(self, value: float = 0.0) -> bool:
        """Set Y-axis program position value using MCS.Y position returned by scanning laser info."""
        if not self.is_connected:
            return False
        try:
            # check value
            if type(value) not in (int, float) or not math.isfinite(value):
                return False

            # get scanning laser info
            scanning_laser_info = self.get_scanning_laser_info()
            if not scanning_laser_info.has_data:
                return False

            # set y-axis program position
            return self.set_program_position_y(value - scanning_laser_info.laser_mcs_y_position)
        except Exception:
            return False

    def set_program_position_z(self, value: float) -> bool:
        """Set Z-axis program position value."""
        if not self.is_connected:
            return False
        return self.__execute_request('{"set":"program.position", "data":{"z":' + str(value) + '}}')

    def set_program_position_z_with_laser_reference(self, value: float = 0.0, sample_count: int = 3) -> bool:
        """Set Z-axis program position value using MCS.Z position returned by scanning laser info."""
        if not self.is_connected:
            return False
        try:
            # check value and sample count
            if type(value) not in (int, float) or not math.isfinite(value):
                return False
            if type(sample_count) is not int or not 1 <= sample_count <= 10:
                return False

            # acquire laser mcs z position samples, at 0.2 s intervals, to evaluate the median value
            laser_mcs_z_positions = []
            for _ in range(sample_count):
                scanning_laser_info = self.get_scanning_laser_info()
                if not scanning_laser_info.has_data:
                    return False
                laser_mcs_z_positions.append(scanning_laser_info.laser_mcs_z_position)
                time.sleep(0.2)
            laser_mcs_z_position = median(laser_mcs_z_positions)

            # set z-axis program position
            return self.set_program_position_z(-laser_mcs_z_position - value)
        except Exception:
            return False

    def set_simulator_current_time_ms(self, value: int) -> bool:
        """Set simulator current time as ms."""
        try:
            if not self.is_connected:
                return False
            if not isinstance(value, int) or isinstance(value, bool):
                return False
            request = {"set":"simulator.current.time.ms", "value": value}
            return self.__execute_request(json.dumps(request))
        except Exception:
            return False

    def set_simulator_speed_track(self, value: int) -> bool:
        """Set simulator speed track in interval."""
        try:
            if not self.is_connected:
                return False
            if not isinstance(value, int) or isinstance(value, bool):
                return False
            request = {"set":"simulator.speed.track", "value": value}
            return self.__execute_request(json.dumps(request))
        except Exception:
            return False

    def set_tools_lib_info(self, info: APIToolsLibInfoForSet | None = None) -> bool:
        """Set info of a tool into the NC tools library."""
        try:
            if not self.is_connected:
                return False
            if not isinstance(info, APIToolsLibInfoForSet):
                return False

            if not isinstance(info.tool_index, int):
                return False
            if not isinstance(info.tool_id, (type(None), int)):
                return False
            if not isinstance(info.tool_slot, (type(None), int)):
                return False
            if not isinstance(info.tool_type, (type(None), int)):
                return False
            if not isinstance(info.tool_diameter, (type(None), int, float)):
                return False
            if not isinstance(info.tool_offset_x, (type(None), int, float)):
                return False
            if not isinstance(info.tool_offset_y, (type(None), int, float)):
                return False
            if not isinstance(info.tool_offset_z, (type(None), int, float)):
                return False
            if not isinstance(info.tool_param_1, (type(None), int, float)):
                return False
            if not isinstance(info.tool_param_2, (type(None), int, float)):
                return False
            if not isinstance(info.tool_param_3, (type(None), int, float)):
                return False
            if not isinstance(info.tool_param_4, (type(None), int, float)):
                return False
            if not isinstance(info.tool_param_5, (type(None), int, float)):
                return False
            if not isinstance(info.tool_param_6, (type(None), int, float)):
                return False
            if not isinstance(info.tool_param_7, (type(None), int, float)):
                return False
            if not isinstance(info.tool_param_8, (type(None), int, float)):
                return False
            if not isinstance(info.tool_param_9, (type(None), int, float)):
                return False
            if not isinstance(info.tool_param_10, (type(None), int, float)):
                return False
            if not isinstance(info.tool_param_51, (type(None), int, float)):
                return False
            if not isinstance(info.tool_param_52, (type(None), int, float)):
                return False
            if not isinstance(info.tool_param_53, (type(None), int, float)):
                return False
            if not isinstance(info.tool_param_54, (type(None), int, float)):
                return False
            if not isinstance(info.tool_param_55, (type(None), int, float)):
                return False
            if not isinstance(info.tool_param_56, (type(None), int, float)):
                return False
            if not isinstance(info.tool_param_57, (type(None), int, float)):
                return False
            if not isinstance(info.tool_param_58, (type(None), int, float)):
                return False
            if not isinstance(info.tool_param_59, (type(None), int, float)):
                return False
            if not isinstance(info.tool_param_60, (type(None), int, float)):
                return False
            if not isinstance(info.tool_description, (type(None), str)):
                return False

            data = {
                "set": "tools.lib.info",
                "index": info.tool_index,
            }

            # add optional fields only if they are not None
            optional_fields = [
                ("id", info.tool_id),
                ("slot", info.tool_slot),
                ("type", info.tool_type),
                ("diameter", info.tool_diameter),
                ("offset.x", info.tool_offset_x),
                ("offset.y", info.tool_offset_y),
                ("offset.z", info.tool_offset_z),
                ("param.1", info.tool_param_1),
                ("param.2", info.tool_param_2),
                ("param.3", info.tool_param_3),
                ("param.4", info.tool_param_4),
                ("param.5", info.tool_param_5),
                ("param.6", info.tool_param_6),
                ("param.7", info.tool_param_7),
                ("param.8", info.tool_param_8),
                ("param.9", info.tool_param_9),
                ("param.10", info.tool_param_10),
                ("param.51", info.tool_param_51),
                ("param.52", info.tool_param_52),
                ("param.53", info.tool_param_53),
                ("param.54", info.tool_param_54),
                ("param.55", info.tool_param_55),
                ("param.56", info.tool_param_56),
                ("param.57", info.tool_param_57),
                ("param.58", info.tool_param_58),
                ("param.59", info.tool_param_59),
                ("param.60", info.tool_param_60),
                ("description", info.tool_description),
            ]

            for key, value in optional_fields:
                if value is not None:
                    data[key] = value

            request = self.create_compact_json_request(data)
            return self.__execute_request(request)
        except Exception:
            return False

    def set_wcs_info(self, wcs: int, offset: list, activate: bool = False) -> bool:
        """
        Set desired WCS offsets.

        Args:
            wcs         : define what of wcs, from 1 to 9, you want to set offsets
            activate    : if True wcs become working wcs
            offset      : a list of 6 elements, representing x/y/z/a/b/c axes, where any element could be:
                            None    = not change this axis value
                            int     = will be internally converted to float
                            float   = will be used as is as
        """
        try:
            if not self.is_connected:
                return False

            if type(wcs) is not int:
                return False
            if (wcs < 1) or (wcs > 9):
                return False

            if not isinstance(offset, list):
                return False
            if len(offset) != 6:
                return False

            data = {
                "set": "wcs.info",
                "wcs": wcs,
            }

            if activate:
                data["activate"] = activate

            has_data = False
            data["data"] = {}
            axis = ['x','y','z','a','b','c']
            for idx, item in enumerate(offset):
                if item is None:
                    continue
                if not (isinstance(item, float) or type(item) is int):
                    return False

                data['data'][f'{axis[idx]}'] = float(item)
                has_data = True

            if not has_data and not activate:
                return False

            request = self.create_compact_json_request(data)
            return self.__execute_request(request)
        except Exception:
            return False

    def set_vm_geometry_info(self, values: list) -> bool:
        """Set virtual machine geometry information."""
        try:
            if not self.is_connected:
                return False
            if len(values) == 0:
                return False
            request = '{"set":"vm.geometry.info", "data":['
            for idx, value in enumerate(values):
                if not isinstance(value, APIVMGeometryInfo):
                    return False
                request = request + '{'
                request = request + '"name":"' + value.name + '",'
                request = request + '"x":' + str(value.x) + ','
                request = request + '"y":' + str(value.y) + ','
                request = request + '"z":' + str(value.z) + ','
                request = request + '"color":' + str(value.color) + ','
                request = request + '"scale":' + str(value.scale) + ','
                request = request + '"visible":' + str(value.visible).lower() + ','
                request = request + '"edges.angle":' + str(value.edges_angle) + ','
                request = request + '"edges.visible":' + str(value.edges_visible).lower()
                if idx < (len(values) - 1):
                    request = request + '},'
                else:
                    request = request + '}'
            request = request + ']}'
            return self.__execute_request(request)
        except Exception:
            return False

    def set_work_order_data(self, order_code: str, data: APIWorkOrderDataForSet) -> bool:
        """Set work order data for the specified order code."""
        if not self.is_connected:
            return False

        request_data = {
            "set": "work.order.data",
            "order.code": order_code
        }

        if data:
            if not isinstance(data, APIWorkOrderDataForSet):
                return False

            order_data = {}

            if data.order_state is not None:
                if isinstance(data.order_state, int) and WO_ST_DRAFT <= data.order_state <= WO_ST_ARCHIVED:
                    order_data["order.state"] = data.order_state
                else:
                    return False

            if data.order_locked is not None:
                if isinstance(data.order_locked, bool):
                    order_data["order.locked"] = data.order_locked
                else:
                    return False

            if data.order_priority is not None:
                if isinstance(data.order_priority, int) and WO_PR_LOWEST <= data.order_priority <= WO_PR_HIGHEST:
                    order_data["order.priority"] = data.order_priority
                else:
                    return False

            if data.job_order_code is not None:
                if isinstance(data.job_order_code, str):
                    order_data["job.order.code"] = data.job_order_code
                else:
                    return False

            if data.customer_code is not None:
                if isinstance(data.customer_code, str):
                    order_data["customer.code"] = data.customer_code
                else:
                    return False

            if data.item_code is not None:
                if isinstance(data.item_code, str):
                    order_data["item.code"] = data.item_code
                else:
                    return False

            if data.material_code is not None:
                if isinstance(data.material_code, str):
                    order_data["material.code"] = data.material_code
                else:
                    return False

            if data.order_notes is not None:
                if isinstance(data.order_notes, str):
                    order_data["order.notes"] = data.order_notes
                else:
                    return False

            if data.use_deadline_datetime is not None:
                if isinstance(data.use_deadline_datetime, bool):
                    order_data["use.deadline.datetime"] = data.use_deadline_datetime
                    if data.deadline_datetime:
                        if isinstance(data.deadline_datetime, datetime):
                            order_data["deadline.datetime"] = self.datetime_to_filetime(data.deadline_datetime)
                        else:
                            return False
                else:
                    return False

            if data.files:
                files_data = []
                for file in data.files:
                    file_data = {}
                    if file.file_name is not None:
                        file_data["file.name"] = file.file_name
                    if file.pieces_per_file is not None:
                        file_data["pieces.per.file"] = file.pieces_per_file
                    if file.requested_pieces is not None:
                        file_data["requested.pieces"] = file.requested_pieces
                    files_data.append(file_data)
                order_data["files"] = files_data

            request_data["data"] = order_data

        request_json = json.dumps(request_data)
        return self.__execute_request(request_json)
    #
    # == END: API Server "set" requests section


    # == BEG: private section
    #
    @staticmethod
    def __evaluate_response(response: str) -> bool:
        """Evaluate API server response."""
        try:
            if len(response) == 0:
                return False
            j = json.loads(response)
            if str(j['res']).lower() == 'true':
                return True
            return False
        except Exception:
            return False

    @staticmethod
    def __append_force_sync(request_data: dict, force_sync: bool) -> bool:
        """Append force_sync request flag when required."""
        if type(force_sync) is not bool:
            return False
        if force_sync:
            request_data["force.sync"] = True
        return True

    def __get_force_sync_api(self) -> CncAPIClientCore | None:
        """Return the dedicated clone connection used by forced synchronous worker requests."""
        try:
            if not self.is_connected or self._use_cnc_direct_access:
                return None

            if self._force_sync_api is not None and self._force_sync_api.is_connected:
                return self._force_sync_api

            if self._force_sync_api is not None:
                try:
                    self._force_sync_api.close()
                except Exception:
                    pass

            self._force_sync_api = self.connection_clone()
            return self._force_sync_api
        except Exception:
            return None

    def __start_force_sync_async_request(
        self,
        worker_proc: Callable[[CncAPIClientCore], bool],
        on_done: Callable[[bool | None], None] = None
    ) -> bool:
        """
        Start a forced synchronous request in a worker thread.

        Args:
            worker_proc : call this procedure with the dedicated clone connection
            on_done     : call this callback at end with result True, False or None
        """
        if not callable(worker_proc):
            return False
        if on_done is not None and not callable(on_done):
            return False
        if not self.is_connected or self._use_cnc_direct_access:
            return False
        if not self._force_sync_lock.acquire(blocking=False):
            return False
        force_sync_lock = self._force_sync_lock

        api = self.__get_force_sync_api()
        if api is None:
            force_sync_lock.release()
            return False

        def worker():
            result = None
            try:
                if api.is_connected:
                    result = worker_proc(api)
            except Exception:
                result = None
            finally:
                try:
                    if on_done is not None:
                        on_done(result)
                except Exception:
                    pass
                self._force_sync_thread = None
                force_sync_lock.release()

        try:
            self._force_sync_thread = threading.Thread(target=worker, daemon=True)
            self._force_sync_thread.start()
            return True
        except Exception:
            self._force_sync_thread = None
            force_sync_lock.release()
            return False

    @staticmethod
    def __get_force_sync_timeout(force_sync: bool, timeout: float) -> float | None:
        """Return timeout to use for requests that can be forced synchronous."""
        if not force_sync:
            return DEFAULT_REQUEST_FIRST_TIMEOUT
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)):
            return None
        if timeout <= 0.0:
            return None
        return float(timeout)

    def __execute_request(self, request: str, first_timeout: float = DEFAULT_REQUEST_FIRST_TIMEOUT) -> bool:
        """Execute a request and evaluate the API server response."""
        try:
            if self.is_connected is False:
                return False
            response = self.__send_command(request, first_timeout=first_timeout)
            return self.__evaluate_response(response)
        except Exception:
            return False

    def __send_command(
        self,
        request: str,
        first_timeout: float = DEFAULT_REQUEST_FIRST_TIMEOUT,
        chunk_timeout: float = DEFAULT_REQUEST_CHUNK_TIMEOUT
    ) -> str:
        """Send a request and return the textual response payload."""

        def __flush_receiving_buffer(max_flush: int = 1048576):
            try:
                self._ipc.settimeout(0.0)
                flushed = 0
                while flushed < max_flush:
                    data = self._ipc.recv(4096)
                    if not data:
                        break
                    flushed += len(data)
            except (BlockingIOError, socket.error):
                pass

        if not self.is_connected or not request:
            return ''

        if not request.endswith('\n'):
            request += '\n'

        if self._use_cnc_direct_access:
            try:
                return cda.api_server_request(request)
            except Exception:
                self.close()
                return ''

        try:
            # flush receiving buffer and send request
            __flush_receiving_buffer()
            self._ipc.sendall(request.encode())

            # init receive attributes
            buffer = bytearray()
            chunk_size = 65536
            search_start = 0
            first_chunk = True

            # set timeout to cover API Server request evaluation -> response time
            self._ipc.settimeout(first_timeout)

            # response receiving loop
            while True:
                # get chunk of data checking for connection closed (chunk is empty)
                chunk = self._ipc.recv(chunk_size)
                if not chunk:
                    self.close()
                    return ''

                # switch to chunk_timeout after first chunk of data received
                if first_chunk:
                    self._ipc.settimeout(chunk_timeout)
                    first_chunk = False

                # add received chunk of data to buffer
                buffer.extend(chunk)

                # search \n only in the new part of the buffer
                newline_pos = buffer.find(b'\n', search_start)
                if newline_pos != -1:
                    return buffer[:newline_pos].decode('utf-8')

                search_start = len(buffer)

        except socket.timeout:
            return ''
        except socket.error:
            self.close()
            return ''

    def __send_command_raw(
        self,
        request: str,
        first_timeout: float = DEFAULT_REQUEST_FIRST_TIMEOUT,
        chunk_timeout: float = DEFAULT_REQUEST_CHUNK_TIMEOUT
    ) -> bytearray | None:
        """Send a request and return the raw binary payload."""

        def __flush_receiving_buffer(max_flush: int = 1048576):
            try:
                self._ipc.settimeout(0.0)
                flushed = 0
                while flushed < max_flush:
                    data = self._ipc.recv(4096)
                    if not data:
                        break
                    flushed += len(data)
            except (BlockingIOError, socket.error):
                pass

        def __extract_data_size(header_bytes: bytes) -> int | None:
            """
            Extract numeric value from:
            {"res":{"data_size":123}}
            without using json.loads().
            """
            marker = b'"data_size":'
            start = header_bytes.find(marker)
            if start == -1:
                return None

            start += len(marker)

            # skip optional spaces
            while start < len(header_bytes) and header_bytes[start] in b' \t':
                start += 1

            end = start
            while end < len(header_bytes) and 48 <= header_bytes[end] <= 57:  # '0'..'9'
                end += 1

            if end == start:
                return None

            try:
                return int(header_bytes[start:end])
            except Exception:
                return None

        if not self.is_connected or not request:
            return None

        if not request.endswith('\n'):
            request += '\n'

        if self._use_cnc_direct_access:
            # raw mode not supported here unless cda.api_server_request()
            # is updated to return raw bytes in the same way
            try:
                response = cda.api_server_request(request)
                if isinstance(response, (bytes, bytearray)):
                    return bytearray(response)
                return None
            except Exception:
                self.close()
                return None

        try:
            __flush_receiving_buffer()
            self._ipc.sendall(request.encode('utf-8'))

            chunk_size = 65536
            header_buffer = bytearray()
            first_chunk = True

            self._ipc.settimeout(first_timeout)

            # ------------------------------------------------------------
            # Step 1: read header until '\n'
            # ------------------------------------------------------------
            while True:
                chunk = self._ipc.recv(chunk_size)
                if not chunk:
                    self.close()
                    return None

                if first_chunk:
                    self._ipc.settimeout(chunk_timeout)
                    first_chunk = False

                newline_pos = chunk.find(b'\n')
                if newline_pos != -1:
                    # header part
                    header_buffer.extend(chunk[:newline_pos])

                    # any bytes after '\n' already belong to the raw payload
                    payload = bytearray(chunk[newline_pos + 1:])
                    break

                header_buffer.extend(chunk)

            # ------------------------------------------------------------
            # Step 2: parse data_size from header
            # ------------------------------------------------------------
            data_size = __extract_data_size(header_buffer)
            if data_size is None or data_size < 0:
                return None

            # special case: empty payload
            if data_size == 0:
                return bytearray()

            # ------------------------------------------------------------
            # Step 3: complete raw payload receive
            # ------------------------------------------------------------
            while len(payload) < data_size:
                chunk = self._ipc.recv(min(chunk_size, data_size - len(payload)))
                if not chunk:
                    self.close()
                    return None
                payload.extend(chunk)

            # if server accidentally sent more than expected in the same frame,
            # keep only the declared payload size
            if len(payload) > data_size:
                del payload[data_size:]

            return payload

        except socket.timeout:
            return None
        except socket.error:
            self.close()
            return None

    @staticmethod
    def create_compact_json_request(data: dict) -> str:
        """
        Convert a dictionary to a compact JSON string without spaces between fields.

        Args:
            data (dict): The dictionary to convert.

        Returns:
            str: A compact JSON string.
        """
        return json.dumps(data, separators=(',', ':'))

    @staticmethod
    def datetime_to_filetime(dt: datetime) -> int:
        """Convert a UTC datetime to FILETIME timestamps (100 ns intervals from 1 January 1601)."""
        epoch_start = datetime(1601, 1, 1, tzinfo=dt.tzinfo)
        delta = dt - epoch_start
        filetime = int((delta.days * 86400 + delta.seconds) * 10**7 + delta.microseconds * 10)
        return filetime

    @staticmethod
    def __d(filetime: int) -> datetime:
        """
        Convert FILETIME timestamps (100 ns intervals from 1 January 1601) to a UTC datetime.

        For a translation test use: https://www.silisoftware.com/tools/date.php
        """
        try:
            # set epoch of FILETIME begin at 1 January 1601
            epoch_start = datetime(1601, 1, 1)

            # convert from 100 nanoseconds to microseconds (1 microsecond = 10 intervals of 100 nanoseconds)
            microseconds = int(filetime) // 10

            # create a datetime object adding microseconds from epoch_start
            return epoch_start + timedelta(microseconds=microseconds)
        except Exception:
            return datetime.min

    @staticmethod
    def __b(value) -> bool:
        """Convert a value to bool."""
        return bool(value)

    @staticmethod
    def __i(value) -> int:
        """Convert a value to int."""
        return int(value)

    @staticmethod
    def __s(value) -> str:
        """Convert a value to str."""
        return str(value)
    #
    # == END: private section


class CncAPIInfoContext:
    """Service class for cnc api info context"""
    axes_info           = APIAxesInfo()
    cnc_info            = APICncInfo()
    compile_info        = APICompileInfo()
    enabled_commands    = APIEnabledCommands()

    def __init__(self, api):
        """Initialize CNC API info context service."""
        self.__api = api


    # == BEG: public section
    #
    def update(self) -> bool:
        """
        Update cnc api info context.

        :return                 False when the is no connection with the API server
        :rtype                  (bool)
        """
        if self.__api.is_connected:
            self.axes_info = self.__api.get_axes_info()
            self.cnc_info = self.__api.get_cnc_info()
            self.compile_info = self.__api.get_compile_info()
            self.enabled_commands = self.__api.get_enabled_commands()
            return True
        self.axes_info = APIAxesInfo()
        self.cnc_info = APICncInfo()
        self.compile_info = APICompileInfo()
        self.enabled_commands = APIEnabledCommands()
        return False
    #
    # == END: public section
