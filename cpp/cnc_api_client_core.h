/**
 * CNC API Client Core for RosettaCNC & derivated NC Systems
 * 
 * Purpose:      CNC API Client Core for RosettaCNC & derivated NC Systems
 * 
 * Note:         Compatible with API server version 1.5.3
 *               1 (on 1.x.y) means interface contract
 *               x (on 1.x.y) means version
 *               y (on 1.x.y) means release
 * 
 * Note:         Complete C++ port from Python (one-to-one conversion)
 *               Requires nlohmann/json library for JSON parsing
 * 
 * Author:       support@rosettacnc.com
 * Created:      05/02/2026
 * Copyright:    RosettaCNC (c) 2016-2026
 * Licence:      RosettaCNC License 1.0 (RCNC-1.0)
 */

#pragma once

#define NOMINMAX  // Prevent Windows.h from defining min/max macros

#include <string>
#include <vector>
#include <map>
#include <memory>
#include <ctime>
#include <chrono>
#include <winsock2.h>
#include <ws2tcpip.h>
#include <wincrypt.h>
#include <schannel.h>
#define SECURITY_WIN32
#include <security.h>
#include <sspi.h>

// Link with required libraries
#pragma comment(lib, "ws2_32.lib")
#pragma comment(lib, "crypt32.lib")
#pragma comment(lib, "secur32.lib")

// Module version
#define MODULE_VERSION "1.5.3"

// Analysis mode
#define ANALYSIS_MT "mt"    // model path with tools colors
#define ANALYSIS_RT "rt"    // real path with tools colors
#define ANALYSIS_RF "rf"    // real path with colors related to feed
#define ANALYSIS_RV "rv"    // real path with colors related to velocity
#define ANALYSIS_RZ "rz"    // real path with colors related to the Z level of the feed

// Axis ID
#define X_AXIS_ID 1
#define Y_AXIS_ID 2
#define Z_AXIS_ID 3
#define A_AXIS_ID 4
#define B_AXIS_ID 5
#define C_AXIS_ID 6
#define U_AXIS_ID 7
#define V_AXIS_ID 8
#define W_AXIS_ID 9

// Axis index (used on axes data arrays)
#define X_AXIS_INDEX 0
#define Y_AXIS_INDEX 1
#define Z_AXIS_INDEX 2
#define A_AXIS_INDEX 3
#define B_AXIS_INDEX 4
#define C_AXIS_INDEX 5

// Axis mask
#define X_AXIS_MASK 0x0001
#define Y_AXIS_MASK 0x0002
#define Z_AXIS_MASK 0x0004
#define A_AXIS_MASK 0x0008
#define B_AXIS_MASK 0x0010
#define C_AXIS_MASK 0x0020
#define U_AXIS_MASK 0x0040
#define V_AXIS_MASK 0x0080
#define W_AXIS_MASK 0x0100

// Axes mask
#define X2Z_AXIS_MASK 0x0007
#define X2C_AXIS_MASK 0x003F
#define X2W_AXIS_MASK 0x01FF

// Compiler state
#define CS_INIT 0
#define CS_READY 1
#define CS_ERROR 2
#define CS_FIRST_STEP 3
#define CS_FIRST_STEP_RUNNING 4
#define CS_WAITING_FOR_DATA 5
#define CS_WAITING_FOR_DATA_RUNNING 6
#define CS_FINISHED 7

// Jog command
#define JC_NONE 0
#define JC_X_BW 1
#define JC_X_FW 2
#define JC_Y_BW 3
#define JC_Y_FW 4
#define JC_Z_BW 5
#define JC_Z_FW 6
#define JC_A_BW 7
#define JC_A_FW 8
#define JC_B_BW 9
#define JC_B_FW 10
#define JC_C_BW 11
#define JC_C_FW 12

// State machine
#define SM_DISCONNECTED 0
#define SM_SIMULATOR 1
#define SM_INIT 2
#define SM_INIT_FIELDBUS 3
#define SM_ALARM 4
#define SM_IDLE 5
#define SM_HOMING 6
#define SM_JOG 7
#define SM_RUN 8
#define SM_PAUSE 9
#define SM_LIMIT 10
#define SM_MEASURE_TOOL 11
#define SM_SCAN_3D 12
#define SM_SAFETY_JOG 13
#define SM_CHANGE_TOOL 14
#define SM_SAFETY 15
#define SM_WAIT_MAIN_POWER 16
#define SM_RETRACT 17

// Spindle direction
#define SD_STOPPED 1
#define SD_CW 2
#define SD_CCW 3

// Spindle shaft
#define ST_STOPPED 0
#define ST_ROTATING 1

// Spindle status
#define SS_COLLET_OPEN 0
#define SS_COLLET_CLOSED_TOOL_HOLDER_ABSENT 1
#define SS_TOOL_HOLDER_BLOCKED_CORRECTLY 2

// Tool type
#define TT_GENERIC 0
#define TT_FLAT_END_MILL 1
#define TT_BALL_NOSE_END_MILL 2
#define TT_DRILL 3
#define TT_PROBE 4
#define TT_SAW 5
#define TT_PLASMA 6
#define TT_DRAG_KNIFE 7
#define TT_LATHE 8
#define TT_LASER 9
#define TT_WATER_JET 10

// Units mode
#define UM_METRIC 0
#define UM_IMPERIAL 1

// Work mode
#define WM_NORMAL 0
#define WM_WORK_ORDER 1

// Work order file type
#define WO_FT_DIRECTORY 0
#define WO_FT_FILE 1

// Work order priority
#define WO_PR_LOWEST 0
#define WO_PR_LOW 1
#define WO_PR_NORMAL 2
#define WO_PR_HIGH 3
#define WO_PR_HIGHEST 4

// Work order file state
#define WO_FS_CLOSED 0
#define WO_FS_OPEN 1
#define WO_FS_RUNNING 2

// Work order state
#define WO_ST_DRAFT 0
#define WO_ST_EDIT 1
#define WO_ST_RELEASED 2
#define WO_ST_READY 3
#define WO_ST_ACTIVE 4
#define WO_ST_RUNNING 5
#define WO_ST_COMPLETED 6
#define WO_ST_ARCHIVED 7
#define WO_ST_DO_NOT_EXITS 8

// Work order log id
#define WO_LI_NONE 0
#define WO_LI_ACTIVATED 1
#define WO_LI_DEACTIVATED 2
#define WO_LI_FILE_OPENED 3
#define WO_LI_FILE_CLOSED 4
#define WO_LI_FILE_STARTED 5
#define WO_LI_FILE_STOPPED 6
#define WO_LI_FILE_FINISHED 7
#define WO_LI_ARCHIVED 8

// Machine type
#define MT_MILL 0
#define MT_LATHE 1

// Kinematics model
#define KM_TRIVIAL 0
#define KM_INDEPENDENT_ROT_AXES 1
#define KM_ROTARY_TABLE_A 10
#define KM_ROTARY_TABLE_B 11
#define KM_TILTING_HEAD_A 20
#define KM_TILTING_HEAD_B 21
#define KM_ROTARY_TABLE_AB 30
#define KM_ROTARY_TABLE_BA 31
#define KM_ROTARY_TABLE_AC 32
#define KM_ROTARY_TABLE_BC 33
#define KM_TILTING_HEAD_AB 40
#define KM_TILTING_HEAD_BA 41
#define KM_TILTING_HEAD_CA 42
#define KM_TILTING_HEAD_CB 43
#define KM_TILTING_HEAD_CB_CUSTOM 100

// Axis type
#define AT_DISABLED 0
#define AT_LINEAR 1
#define AT_ROTARY_FREE 2
#define AT_ROTARY_HEAD 3
#define AT_ROTARY_TABLE 4
#define AT_GANTRY_1 5
#define AT_GANTRY_2 6
#define AT_GANTRY_3 7

// Function state name
#define FS_NM_SPINDLE_CW 0
#define FS_NM_SPINDLE_CCW 1
#define FS_NM_MIST 10
#define FS_NM_FLOOD 11
#define FS_NM_TORCH 20
#define FS_NM_THC_DISABLED 21
#define FS_NM_JOG_MODE 30
#define FS_NM_AUX_01 40
#define FS_NM_AUX_02 41
#define FS_NM_AUX_03 42
#define FS_NM_AUX_04 43
#define FS_NM_AUX_05 44
#define FS_NM_AUX_06 45
#define FS_NM_AUX_07 46
#define FS_NM_AUX_08 47
#define FS_NM_AUX_09 48
#define FS_NM_AUX_10 49
#define FS_NM_AUX_11 50
#define FS_NM_AUX_12 51
#define FS_NM_AUX_13 52
#define FS_NM_AUX_14 53
#define FS_NM_AUX_15 54
#define FS_NM_AUX_16 55
#define FS_NM_AUX_17 56
#define FS_NM_AUX_18 57
#define FS_NM_AUX_19 58
#define FS_NM_AUX_20 59
#define FS_NM_AUX_21 60
#define FS_NM_AUX_22 61
#define FS_NM_AUX_23 62
#define FS_NM_AUX_24 63
#define FS_NM_AUX_25 64
#define FS_NM_AUX_26 65
#define FS_NM_AUX_27 66
#define FS_NM_AUX_28 67
#define FS_NM_AUX_29 68
#define FS_NM_AUX_30 69
#define FS_NM_AUX_31 70
#define FS_NM_AUX_32 71

// Function state mode
#define FS_MD_OFF 0
#define FS_MD_ON 1
#define FS_MD_TOGGLE 2
#define FS_MD_JOG_MODE_DEFAULT 3
#define FS_MD_JOG_MODE_ALONG_TOOL 4
#define FS_MD_JOG_MODE_TOGGLE 5

// UI dialogs name
#define UID_ABOUT "about"
#define UID_ATC_MANAGEMENT "atc.management"
#define UID_BOARD_ETHERCAT_MONITOR "board.ethercat.monitor"
#define UID_BOARD_FIRMWARE_MANAGER "board.firmware.manager"
#define UID_BOARD_MONITOR "board.monitor"
#define UID_BOARD_SETTINGS "board.settings"
#define UID_CHANGE_BOARD_IP "change.board.ip"
#define UID_MACROS_MANAGEMENT "macros.management"
#define UID_PARAMETERS_LIBRARY "parameters.library"
#define UID_PROGRAM_SETTINGS "program.settings"
#define UID_TOOLS_LIBRARY "tools.library"
#define UID_WORK_COORDINATES "work.coordinates"

// Service popup menu enabling mask
#define SPMEM_ABOUT (1 << 0)
#define SPMEM_ATC_MANAGEMENT (1 << 1)
#define SPMEM_BOARD_ETHERCAT_MONITOR (1 << 2)
#define SPMEM_BOARD_FIRMWARE_MANAGER (1 << 3)
#define SPMEM_BOARD_MONITOR (1 << 4)
#define SPMEM_BOARD_SETTINGS (1 << 5)
#define SPMEM_CHANGE_BOARD_IP (1 << 6)
#define SPMEM_CONNECTION_OPEN (1 << 7)
#define SPMEM_CONNECTION_CLOSE (1 << 8)
#define SPMEM_EXIT (1 << 9)
#define SPMEM_MACROS_MANAGEMENT (1 << 10)
#define SPMEM_PARAMETERS_LIBRARY (1 << 11)
#define SPMEM_PROGRAM_SETTINGS (1 << 12)
#define SPMEM_TOOLS_LIBRARY (1 << 13)
#define SPMEM_WORK_COORDINATES (1 << 14)

namespace RosettaCNC {

// Forward declarations
class CncAPIClientCore;

// ========== DateTime Helper ==========
struct DateTime {
    int year, month, day;
    int hour, minute, second;
    int microsecond;
    
    DateTime() : year(1601), month(1), day(1), hour(0), minute(0), second(0), microsecond(0) {}
    
    static DateTime min_value() {
        return DateTime();
    }
    
    bool operator==(const DateTime& other) const {
        return year == other.year && month == other.month && day == other.day &&
               hour == other.hour && minute == other.minute && second == other.second;
    }
};

// ========== API Data Structures ==========

class APIAlarmsWarningsList {
public:
    struct AlarmWarningData {
        int code;
        int info_1;
        int info_2;
        std::string text;
        DateTime datetime;
        
        AlarmWarningData() : code(0), info_1(0), info_2(0) {}
    };
    
    bool has_data;
    std::vector<AlarmWarningData> list;
    
    APIAlarmsWarningsList() : has_data(false) {}
};

class APIAnalogInputs {
public:
    bool has_data;
    std::vector<double> value;
    
    APIAnalogInputs() : has_data(false), value(16, 0.0) {}
};

class APIAnalogOutputs {
public:
    bool has_data;
    std::vector<double> value;
    
    APIAnalogOutputs() : has_data(false), value(16, 0.0) {}
};

class APIAxesInfo {
public:
    bool has_data;
    std::vector<double> joint_position;
    std::vector<double> machine_position;
    std::vector<double> program_position;
    std::vector<double> machine_target_position;
    std::vector<double> program_target_position;
    std::vector<double> actual_velocity;
    int working_wcs;
    std::vector<double> working_offset;
    std::vector<double> dynamic_offset;
    bool homing_done;
    int homing_done_mask;
    
    APIAxesInfo() : 
        has_data(false),
        joint_position(6, 0.0),
        machine_position(6, 0.0),
        program_position(6, 0.0),
        machine_target_position(6, 0.0),
        program_target_position(6, 0.0),
        actual_velocity(6, 0.0),
        working_wcs(0),
        working_offset(6, 0.0),
        dynamic_offset(3, 0.0),
        homing_done(false),
        homing_done_mask(0) {}
};

class APICncInfo {
public:
    bool has_data;
    int units_mode;
    int axes_mask;
    int state_machine;
    int gcode_line;
    std::string planned_time;
    std::string worked_time;
    std::string hud_user_message;
    DateTime current_alarm_datetime;
    int current_alarm_code;
    int current_alarm_info1;
    int current_alarm_info2;
    std::string current_alarm_text;
    DateTime current_warning_datetime;
    int current_warning_code;
    int current_warning_info1;
    int current_warning_info2;
    std::string current_warning_text;
    int aux_outputs;
    bool coolant_mist;
    bool coolant_flood;
    int lube_axis_cycles_made;
    int lube_axis_time_to_next_cycle;
    int lube_spindle_cycles_made;
    int lube_spindle_time_to_next_cycle;
    double feed_programmed;
    double feed_target;
    double feed_reference;
    int spindle_programmed;
    int spindle_target;
    int spindle_actual;
    int spindle_load;
    int spindle_torque;
    int spindle_direction;
    bool spindle_not_ready;
    int spindle_shaft;
    int spindle_status;
    int spindle_voltage;
    int override_jog;
    int override_jog_min;
    int override_jog_max;
    bool override_jog_enabled;
    bool override_jog_locked;
    int override_spindle;
    int override_spindle_min;
    int override_spindle_max;
    bool override_spindle_enabled;
    bool override_spindle_locked;
    int override_fast;
    int override_fast_min;
    int override_fast_max;
    bool override_fast_enabled;
    bool override_fast_locked;
    int override_feed;
    int override_feed_min;
    int override_feed_max;
    bool override_feed_enabled;
    bool override_feed_locked;
    int override_feed_custom_1;
    int override_feed_custom_1_min;
    int override_feed_custom_1_max;
    bool override_feed_custom_1_enabled;
    bool override_feed_custom_1_locked;
    int override_feed_custom_2;
    int override_feed_custom_2_min;
    int override_feed_custom_2_max;
    bool override_feed_custom_2_enabled;
    bool override_feed_custom_2_locked;
    int override_plasma_power;
    int override_plasma_power_min;
    int override_plasma_power_max;
    bool override_plasma_power_enabled;
    bool override_plasma_power_locked;
    int override_plasma_voltage;
    int override_plasma_voltage_min;
    int override_plasma_voltage_max;
    bool override_plasma_voltage_enabled;
    bool override_plasma_voltage_locked;
    int tool_id;
    int tool_slot;
    bool tool_slot_enabled;
    int tool_type;
    double tool_diameter;
    double tool_offset_x;
    double tool_offset_y;
    double tool_offset_z;
    double tool_param_1;
    double tool_param_2;
    double tool_param_3;
    std::string tool_description;
    
    APICncInfo();
};

class APICncParameters {
public:
    bool has_data;
    int address;
    std::vector<double> values;
    std::vector<std::string> descriptions;
    
    APICncParameters() : has_data(false), address(0) {}
};

class APICompileInfo {
public:
    bool has_data;
    int code;
    int code_line;
    int file_line;
    std::string file_name;
    std::string message;
    int state;
    
    APICompileInfo() : has_data(false), code(0), code_line(0), file_line(0), state(CS_INIT) {}
};

class APIDigitalInputs {
public:
    bool has_data;
    std::vector<int> value;
    
    APIDigitalInputs() : has_data(false), value(128, 0) {}
};

class APIDigitalOutputs {
public:
    bool has_data;
    std::vector<int> value;
    
    APIDigitalOutputs() : has_data(false), value(128, 0) {}
};

class APIEnabledCommands {
public:
    bool has_data;
    bool cnc_connection_close;
    bool cnc_connection_open;
    bool cnc_continue;
    int cnc_homing;
    int cnc_jog_command;
    bool cnc_mdi_command;
    bool cnc_parameters;
    bool cnc_pause;
    bool cnc_resume;
    bool cnc_resume_from_line;
    bool cnc_resume_from_point;
    bool cnc_start;
    bool cnc_start_from_line;
    bool cnc_start_from_point;
    bool cnc_stop;
    bool program_analysis;
    bool program_analysis_abort;
    bool program_gcode_add_text;
    bool program_gcode_clear;
    bool program_gcode_set_text;
    bool program_load;
    bool program_new;
    bool program_save;
    bool program_save_as;
    bool reset_alarms;
    bool reset_alarms_history;
    bool reset_warnings;
    bool reset_warnings_history;
    int set_program_position;
    bool show_ui_dialog;
    bool tools_lib_write;
    
    APIEnabledCommands();
};

class APILocalizationInfo {
public:
    struct LocalizationData {
        std::string locale;
        std::string description;
        std::string owner;
        std::string revisor;
        std::string version;
        std::string date;
        std::string program;
    };
    
    bool has_data;
    std::string locale;
    std::string description;
    std::string language;
    std::string language_list;
    std::vector<LocalizationData> list;
    
    APILocalizationInfo() : has_data(false) {}
};

class APIMachineSettings {
public:
    bool has_data;
    int machine_type;
    int axis_machine_type;
    int axis_kinematics_model;
    int axis_x_type;
    double axis_x_max_vel;
    double axis_x_acc;
    double axis_x_min_lim;
    double axis_x_max_lim;
    int axis_y_type;
    double axis_y_max_vel;
    double axis_y_acc;
    double axis_y_min_lim;
    double axis_y_max_lim;
    int axis_z_type;
    double axis_z_max_vel;
    double axis_z_acc;
    double axis_z_min_lim;
    double axis_z_max_lim;
    int axis_a_type;
    double axis_a_max_vel;
    double axis_a_acc;
    double axis_a_min_lim;
    double axis_a_max_lim;
    int axis_b_type;
    double axis_b_max_vel;
    double axis_b_acc;
    double axis_b_min_lim;
    double axis_b_max_lim;
    int axis_c_type;
    double axis_c_max_vel;
    double axis_c_acc;
    double axis_c_min_lim;
    double axis_c_max_lim;
    double kinematics_h_x;
    double kinematics_h_y;
    double kinematics_h_z;
    double kinematics_j_x;
    double kinematics_j_y;
    double kinematics_j_z;
    
    APIMachineSettings();
};

class APIMachiningInfoUsedTool {
public:
    int tool_id;
    double in_fast;
    double in_feed;
    
    APIMachiningInfoUsedTool() : tool_id(0), in_fast(0.0), in_feed(0.0) {}
};

class APIMachiningInfo {
public:
    bool has_data;
    double tool_path_in_fast;
    double tool_path_in_feed;
    double total_path;
    std::string planned_time;
    std::vector<APIMachiningInfoUsedTool> used_tool;
    double tcp_extents_in_fast_min_x;
    double tcp_extents_in_fast_min_y;
    double tcp_extents_in_fast_min_z;
    double tcp_extents_in_fast_max_x;
    double tcp_extents_in_fast_max_y;
    double tcp_extents_in_fast_max_z;
    double tcp_extents_in_fast_length_x;
    double tcp_extents_in_fast_length_y;
    double tcp_extents_in_fast_length_z;
    double tcp_extents_in_feed_min_x;
    double tcp_extents_in_feed_min_y;
    double tcp_extents_in_feed_min_z;
    double tcp_extents_in_feed_max_x;
    double tcp_extents_in_feed_max_y;
    double tcp_extents_in_feed_max_z;
    double tcp_extents_in_feed_length_x;
    double tcp_extents_in_feed_length_y;
    double tcp_extents_in_feed_length_z;
    double joints_in_fast_min_x;
    double joints_in_fast_min_y;
    double joints_in_fast_min_z;
    double joints_in_fast_min_a;
    double joints_in_fast_min_b;
    double joints_in_fast_min_c;
    double joints_in_fast_max_x;
    double joints_in_fast_max_y;
    double joints_in_fast_max_z;
    double joints_in_fast_max_a;
    double joints_in_fast_max_b;
    double joints_in_fast_max_c;
    double joints_in_fast_length_x;
    double joints_in_fast_length_y;
    double joints_in_fast_length_z;
    double joints_in_fast_length_a;
    double joints_in_fast_length_b;
    double joints_in_fast_length_c;
    double joints_in_feed_min_x;
    double joints_in_feed_min_y;
    double joints_in_feed_min_z;
    double joints_in_feed_min_a;
    double joints_in_feed_min_b;
    double joints_in_feed_min_c;
    double joints_in_feed_max_x;
    double joints_in_feed_max_y;
    double joints_in_feed_max_z;
    double joints_in_feed_max_a;
    double joints_in_feed_max_b;
    double joints_in_feed_max_c;
    double joints_in_feed_length_x;
    double joints_in_feed_length_y;
    double joints_in_feed_length_z;
    double joints_in_feed_length_a;
    double joints_in_feed_length_b;
    double joints_in_feed_length_c;
    
    APIMachiningInfo();
};

class APIProgrammedPoints {
public:
    bool has_data;
    std::vector<std::vector<double>> points;
    
    APIProgrammedPoints() : has_data(false) {}
};

class APIScanningLaserInfo {
public:
    bool has_data;
    int laser_out_bit;
    int laser_out_umf;
    double laser_h_measure;
    double laser_mcs_x_position;
    double laser_mcs_y_position;
    double laser_mcs_z_position;
    
    APIScanningLaserInfo() : has_data(false), laser_out_bit(0), laser_out_umf(0),
        laser_h_measure(0.0), laser_mcs_x_position(0.0), laser_mcs_y_position(0.0),
        laser_mcs_z_position(0.0) {}
};

class APISystemInfo {
public:
    bool has_data;
    std::string machine_name;
    std::string control_software_version;
    std::string core_version;
    std::string api_server_version;
    std::string firmware_version;
    std::string firmware_version_tag;
    std::string firmware_interface_level;
    std::string order_code;
    std::string customer_id;
    std::string serial_number;
    std::string part_number;
    std::string customization_number;
    std::string hardware_version;
    std::string operative_system;
    std::string operative_system_crc;
    std::string pld_version;
    
    APISystemInfo() : has_data(false) {}
    
    bool is_equal(const APISystemInfo& data) const;
    static bool are_equal(const APISystemInfo& data_a, const APISystemInfo& data_b);
};

class APIToolsLibCount {
public:
    bool has_data;
    int count;
    
    APIToolsLibCount() : has_data(false), count(0) {}
};

class APIToolsLibInfoForGet {
public:
    int tool_index;
    int tool_id;
    bool tool_slot;
    int tool_type;
    double tool_diameter;
    double tool_offset_x;
    double tool_offset_y;
    double tool_offset_z;
    double tool_param_1;
    double tool_param_2;
    double tool_param_3;
    double tool_param_4;
    double tool_param_5;
    double tool_param_6;
    double tool_param_7;
    double tool_param_8;
    double tool_param_9;
    double tool_param_10;
    double tool_param_51;
    double tool_param_52;
    double tool_param_53;
    double tool_param_54;
    double tool_param_55;
    double tool_param_56;
    double tool_param_57;
    double tool_param_58;
    double tool_param_59;
    double tool_param_60;
    std::string tool_description;
    
    APIToolsLibInfoForGet();
};

class APIToolsLibInfoForSet {
public:
    int* tool_index;
    int* tool_id;
    int* tool_slot;
    int* tool_type;
    double* tool_diameter;
    double* tool_offset_x;
    double* tool_offset_y;
    double* tool_offset_z;
    double* tool_param_1;
    double* tool_param_2;
    double* tool_param_3;
    double* tool_param_4;
    double* tool_param_5;
    double* tool_param_6;
    double* tool_param_7;
    double* tool_param_8;
    double* tool_param_9;
    double* tool_param_10;
    double* tool_param_51;
    double* tool_param_52;
    double* tool_param_53;
    double* tool_param_54;
    double* tool_param_55;
    double* tool_param_56;
    double* tool_param_57;
    double* tool_param_58;
    double* tool_param_59;
    double* tool_param_60;
    std::string* tool_description;
    
    APIToolsLibInfoForSet();
    ~APIToolsLibInfoForSet();
};

class APIToolsLibInfo {
public:
    bool has_data;
    APIToolsLibInfoForGet data;
    
    APIToolsLibInfo() : has_data(false) {}
};

class APIToolsLibInfos {
public:
    bool has_data;
    bool slot_enabled;
    std::vector<APIToolsLibInfoForGet> data;
    
    APIToolsLibInfos() : has_data(false), slot_enabled(false) {}
};

class APIToolsLibToolIndexFromId {
public:
    bool has_data;
    int index;
    
    APIToolsLibToolIndexFromId() : has_data(false), index(-1) {}
};

class APIVMGeometryInfo {
public:
    bool has_data;
    std::string name;
    double x;
    double y;
    double z;
    int color;
    double scale;
    bool visible;
    double edges_angle;
    bool edges_visible;
    
    APIVMGeometryInfo();
};

class APIWorkInfo {
public:
    bool has_data;
    int work_mode;
    std::string active_work_order_code;
    int active_work_order_file_index;
    std::string file_name;
    std::string planned_time;
    std::string worked_time;
    
    APIWorkInfo();
};

class APIWorkOrderCodeList {
public:
    struct ListData {
        std::string order_code;
        int order_state;
        int revision_number;
        
        ListData() : order_state(WO_ST_DRAFT), revision_number(0) {}
    };
    
    bool has_data;
    std::vector<ListData> data;
    
    APIWorkOrderCodeList() : has_data(false) {}
};

class APIWorkOrderDataForAdd {
public:
    struct FileData {
        std::string* file_name;
        int* pieces_per_file;
        int* requested_pieces;
        
        FileData();
        ~FileData();
    };
    
    bool* order_locked;
    int* order_priority;
    std::string* job_order_code;
    std::string* customer_code;
    std::string* item_code;
    std::string* material_code;
    std::string* order_notes;
    bool* use_deadline_datetime;
    DateTime* deadline_datetime;
    std::vector<FileData> files;
    
    APIWorkOrderDataForAdd();
    ~APIWorkOrderDataForAdd();
};

class APIWorkOrderDataForGet {
public:
    struct FileData {
        std::string file_name;
        int file_state;
        int pieces_per_file;
        int requested_pieces;
        int produced_pieces;
        int discarded_pieces;
        
        FileData();
    };
    
    struct LogItemData {
        int log_id;
        DateTime log_datetime;
        std::string log_info_1;
        std::string log_info_2;
        
        LogItemData();
    };
    
    bool has_data;
    int revision_number;
    int order_state;
    bool order_locked;
    std::string order_code;
    int order_priority;
    std::string job_order_code;
    std::string customer_code;
    std::string item_code;
    std::string material_code;
    std::string order_notes;
    std::vector<FileData> files;
    bool use_deadline_datetime;
    DateTime creation_datetime;
    DateTime deadline_datetime;
    DateTime reception_datetime;
    DateTime acceptance_datetime;
    DateTime begin_datetime;
    DateTime end_datetime;
    DateTime archived_datetime;
    int time_for_setup;
    int time_for_idle;
    int time_for_work;
    int time_total;
    std::string operator_notes;
    std::vector<LogItemData> log_items;
    
    APIWorkOrderDataForGet();
};

class APIWorkOrderDataForSet {
public:
    struct FileData {
        std::string* file_name;
        int* pieces_per_file;
        int* requested_pieces;
        
        FileData();
        ~FileData();
    };
    
    int* order_state;
    bool* order_locked;
    int* order_priority;
    std::string* job_order_code;
    std::string* customer_code;
    std::string* item_code;
    std::string* material_code;
    std::string* order_notes;
    bool* use_deadline_datetime;
    DateTime* deadline_datetime;
    std::vector<FileData> files;
    
    APIWorkOrderDataForSet();
    ~APIWorkOrderDataForSet();
};

class APIWorkOrderFileList {
public:
    struct FileData {
        int type;
        std::string name;
        int64_t size;
        DateTime creation_datetime;
        DateTime last_access_datetime;
        DateTime last_write_datetime;
        
        FileData() : type(0), size(0) {}
    };
    
    bool has_data;
    std::vector<FileData> files;
    
    APIWorkOrderFileList() : has_data(false) {}
};

// ========== Main CNC API Client Core Class ==========

class CncAPIClientCore {
public:
    CncAPIClientCore();
    ~CncAPIClientCore();
    
    // ========== Connection Management ==========
    bool connect(const std::string& host, int port, bool use_ssl = false);
    bool connect_direct();
    bool close();
    bool is_connected() const { return m_is_connected; }
    
    // ========== API Server "cmd" Requests ==========
    bool cnc_change_function_state_mode(int name, int mode);
    bool cnc_connection_close();
    bool cnc_connection_open(bool use_ui = false, bool use_fast_mode = false,
                            bool skip_firmware_check = false, bool overwrite_cnc_settings = false);
    bool cnc_continue();
    bool cnc_homing(int axes_mask);
    bool cnc_jog_command(int command);
    bool cnc_mdi_command(const std::string& command);
    bool cnc_pause();
    bool cnc_resume(int line = 0);
    bool cnc_resume_from_line(int line);
    bool cnc_resume_from_point(int point);
    bool cnc_start();
    bool cnc_start_from_line(int line);
    bool cnc_start_from_point(int point);
    bool cnc_stop();
    bool log_add(const std::string& text);
    bool program_analysis(const std::string& mode);
    bool program_analysis_abort();
    bool program_gcode_add_text(const std::string& text);
    bool program_gcode_clear();
    bool program_gcode_set_text(const std::string& text);
    bool program_load(const std::string& file_name);
    bool program_new();
    bool program_save();
    bool program_save_as(const std::string& file_name);
    bool reset_alarms();
    bool reset_alarms_history();
    bool reset_warnings();
    bool reset_warnings_history();
    bool show_ui_dialog(const std::string& name = "");
    bool tools_lib_add(const APIToolsLibInfoForSet* info = nullptr);
    bool tools_lib_clear();
    bool tools_lib_delete(int index);
    bool tools_lib_insert(const APIToolsLibInfoForSet* info);
    bool work_order_add(const std::string& order_code, const APIWorkOrderDataForAdd* data = nullptr);
    bool work_order_delete(const std::string& order_code);
    
    // ========== API Server "get" Requests ==========
    APIAlarmsWarningsList get_alarms_current_list();
    APIAlarmsWarningsList get_alarms_history_list();
    APIAnalogInputs get_analog_inputs();
    APIAnalogOutputs get_analog_outputs();
    APIAxesInfo get_axes_info();
    APICncInfo get_cnc_info();
    APICncParameters get_cnc_parameters(int address, int elements);
    APICompileInfo get_compile_info();
    APIDigitalInputs get_digital_inputs();
    APIDigitalOutputs get_digital_outputs();
    APIEnabledCommands get_enabled_commands();
    APILocalizationInfo get_localization_info();
    APIMachineSettings get_machine_settings();
    APIMachiningInfo get_machining_info();
    APIProgrammedPoints get_programmed_points();
    APIScanningLaserInfo get_scanning_laser_info();
    APISystemInfo get_system_info();
    APIToolsLibCount get_tools_lib_count();
    APIToolsLibInfo get_tools_lib_info(int index);
    APIToolsLibInfos get_tools_lib_infos();
    APIToolsLibToolIndexFromId get_tools_lib_tool_index_from_id(int tool_id);
    std::vector<APIVMGeometryInfo> get_vm_geometry_info(const std::vector<std::string>& names);
    APIAlarmsWarningsList get_warnings_current_list();
    APIAlarmsWarningsList get_warnings_history_list();
    APIWorkInfo get_work_info();
    APIWorkOrderCodeList get_work_order_code_list();
    APIWorkOrderDataForGet get_work_order_data(const std::string& order_code, int mode = 0);
    APIWorkOrderFileList get_work_order_file_list(const std::string& path = "", const std::string& file_filter = "");
    
    // ========== API Server "set" Requests ==========
    bool set_cnc_parameters(int address, const std::vector<double>* values = nullptr,
                           const std::vector<std::string>* descriptions = nullptr);
    bool set_override_fast(int value);
    bool set_override_feed(int value);
    bool set_override_feed_custom_1(int value);
    bool set_override_feed_custom_2(int value);
    bool set_override_jog(int value);
    bool set_override_plasma_power(int value);
    bool set_override_plasma_voltage(int value);
    bool set_override_spindle(int value);
    bool set_program_position_a(double value);
    bool set_program_position_b(double value);
    bool set_program_position_c(double value);
    bool set_program_position_x(double value);
    bool set_program_position_y(double value);
    bool set_program_position_z(double value);
    bool set_tools_lib_info(const APIToolsLibInfoForSet* info);
    bool set_vm_geometry_info(const std::vector<APIVMGeometryInfo>& values);
    bool set_work_order_data(const std::string& order_code, const APIWorkOrderDataForSet& data);
    
    // ========== Utility Methods ==========
    static std::string create_compact_json_request(const std::map<std::string, std::string>& data);
    static int64_t datetime_to_filetime(const DateTime& dt);
    
private:
    // Socket and connection
    SOCKET m_socket;
    bool m_is_connected;
    bool m_use_ssl;
    bool m_use_cnc_direct_access;
    std::string m_host;
    int m_port;
    
    // SSL context (for TLS 1.2)
    CredHandle m_cred_handle;
    CtxtHandle m_context_handle;
    bool m_ssl_initialized;
    
    // Windows Sockets initialization
    static bool s_winsock_initialized;
    static bool initialize_winsock();
    static void cleanup_winsock();
    
    // Communication methods
    std::string send_command(const std::string& request);
    bool execute_request(const std::string& request);
    static bool evaluate_response(const std::string& response);
    void flush_receiving_buffer();
    
    // SSL/TLS methods
    bool initialize_ssl();
    void cleanup_ssl();
    bool ssl_handshake();
    std::string ssl_send_receive(const std::string& data);
    
    // Helper methods for parsing
    static DateTime filetime_to_datetime(int64_t filetime);
    static std::string escape_json_string(const std::string& str);
    
    // JSON helper (Note: Consider using nlohmann/json library for production)
    std::string build_json_string(const std::string& key, const std::string& value);
    std::string build_json_int(const std::string& key, int value);
    std::string build_json_double(const std::string& key, double value);
    std::string build_json_bool(const std::string& key, bool value);
};

// ========== CNC API Info Context ==========

class CncAPIInfoContext {
public:
    APIAxesInfo axes_info;
    APICncInfo cnc_info;
    APICompileInfo compile_info;
    APIEnabledCommands enabled_commands;
    
    CncAPIInfoContext(CncAPIClientCore* api);
    bool update();
    
private:
    CncAPIClientCore* m_api;
};

} // namespace RosettaCNC
