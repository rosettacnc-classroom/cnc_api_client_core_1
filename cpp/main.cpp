/**
 * Example usage of CNC API Client Core
 * 
 * This is a simple example showing how to use the CNC API Client
 * Updated to use the new cnc_api_client_core.h API (one-to-one Python port)
 */

#include "cnc_api_client_core.h"
#include <iostream>
#include <thread>
#include <chrono>

using namespace RosettaCNC;

// Helper function to get state machine description
const char* get_state_machine_name(int state) {
    switch (state) {
        case SM_DISCONNECTED: return "DISCONNECTED";
        case SM_SIMULATOR: return "SIMULATOR";
        case SM_INIT: return "INIT";
        case SM_INIT_FIELDBUS: return "INIT_FIELDBUS";
        case SM_ALARM: return "ALARM";
        case SM_IDLE: return "IDLE";
        case SM_HOMING: return "HOMING";
        case SM_JOG: return "JOG";
        case SM_RUN: return "RUN";
        case SM_PAUSE: return "PAUSE";
        case SM_LIMIT: return "LIMIT";
        case SM_MEASURE_TOOL: return "MEASURE_TOOL";
        case SM_SCAN_3D: return "SCAN_3D";
        case SM_SAFETY_JOG: return "SAFETY_JOG";
        case SM_CHANGE_TOOL: return "CHANGE_TOOL";
        case SM_SAFETY: return "SAFETY";
        case SM_WAIT_MAIN_POWER: return "WAIT_MAIN_POWER";
        case SM_RETRACT: return "RETRACT";
        default: return "UNKNOWN";
    }
}

int main() {
    std::cout << "CNC API Client Example - Version " << MODULE_VERSION << std::endl;
    std::cout << "========================================" << std::endl;
    
    // Create CNC API Client Core
    CncAPIClientCore client;
    
    // Connection parameters
    std::string host = "localhost";  // Change to your CNC host
    int port = 8000;                // Default API port
    bool use_ssl = false;            // Set to true for SSL/TLS connection
    
    std::cout << "\nConnecting to " << host << ":" << port << "..." << std::endl;
    
    // Connect to API server
    if (!client.connect(host, port, use_ssl)) {
        std::cerr << "Failed to connect to CNC API server!" << std::endl;
        return 1;
    }
    
    std::cout << "Connected successfully!" << std::endl;
    
    // Create info context for easier access to CNC state
    CncAPIInfoContext context(&client);
    
    // Test new GET methods
    std::cout << "\n========================================" << std::endl;
    std::cout << "Testing New GET Methods" << std::endl;
    std::cout << "========================================" << std::endl;
    
    // Test 1: Get System Info
    std::cout << "\n--- System Info ---" << std::endl;
    APISystemInfo sys_info = client.get_system_info();
    if (sys_info.has_data) {
        std::cout << "Machine Name: " << sys_info.machine_name << std::endl;
        std::cout << "Control Software: " << sys_info.control_software_version << std::endl;
        std::cout << "Core Version: " << sys_info.core_version << std::endl;
        std::cout << "API Server: " << sys_info.api_server_version << std::endl;
        std::cout << "Firmware: " << sys_info.firmware_version << std::endl;
        std::cout << "Order Code: " << sys_info.order_code << std::endl;
        std::cout << "Serial Number: " << sys_info.serial_number << std::endl;
    } else {
        std::cout << "Failed to get system info!" << std::endl;
    }
    
    // Test 2: Get Digital Inputs
    std::cout << "\n--- Digital Inputs (first 16) ---" << std::endl;
    APIDigitalInputs dig_inputs = client.get_digital_inputs();
    if (dig_inputs.has_data) {
        std::cout << "Digital Inputs: ";
        for (int i = 0; i < 16 && i < static_cast<int>(dig_inputs.value.size()); ++i) {
            std::cout << dig_inputs.value[i];
            if (i < 15) std::cout << ", ";
        }
        std::cout << std::endl;
        
        // Count active inputs
        int active_count = 0;
        for (size_t i = 0; i < dig_inputs.value.size(); ++i) {
            if (dig_inputs.value[i] != 0) active_count++;
        }
        std::cout << "Active Inputs: " << active_count << " / " << dig_inputs.value.size() << std::endl;
    } else {
        std::cout << "Failed to get digital inputs!" << std::endl;
    }
    
    // Test 3: Get Digital Outputs
    std::cout << "\n--- Digital Outputs (first 16) ---" << std::endl;
    APIDigitalOutputs dig_outputs = client.get_digital_outputs();
    if (dig_outputs.has_data) {
        std::cout << "Digital Outputs: ";
        for (int i = 0; i < 16 && i < static_cast<int>(dig_outputs.value.size()); ++i) {
            std::cout << dig_outputs.value[i];
            if (i < 15) std::cout << ", ";
        }
        std::cout << std::endl;
        
        // Count active outputs
        int active_count = 0;
        for (size_t i = 0; i < dig_outputs.value.size(); ++i) {
            if (dig_outputs.value[i] != 0) active_count++;
        }
        std::cout << "Active Outputs: " << active_count << " / " << dig_outputs.value.size() << std::endl;
    } else {
        std::cout << "Failed to get digital outputs!" << std::endl;
    }
    
    // Test 4: Get Current Alarms
    std::cout << "\n--- Current Alarms ---" << std::endl;
    APIAlarmsWarningsList alarms = client.get_alarms_current_list();
    if (alarms.has_data) {
        if (alarms.list.empty()) {
            std::cout << "No active alarms (OK)" << std::endl;
        } else {
            std::cout << "Active Alarms: " << alarms.list.size() << std::endl;
            for (size_t i = 0; i < alarms.list.size(); ++i) {
                std::cout << "  [" << (i+1) << "] Code: " << alarms.list[i].code 
                         << " - " << alarms.list[i].text << std::endl;
            }
        }
    } else {
        std::cout << "Failed to get alarms list!" << std::endl;
    }
    
    // Test 5: Get Analog Inputs
    std::cout << "\n--- Analog Inputs (first 8) ---" << std::endl;
    APIAnalogInputs analog_in = client.get_analog_inputs();
    if (analog_in.has_data) {
        std::cout << "Analog Inputs: ";
        for (int i = 0; i < 8 && i < static_cast<int>(analog_in.value.size()); ++i) {
            std::cout << analog_in.value[i];
            if (i < 7) std::cout << ", ";
        }
        std::cout << std::endl;
    } else {
        std::cout << "Failed to get analog inputs!" << std::endl;
    }
    
    // Test 6: Get Analog Outputs
    std::cout << "\n--- Analog Outputs (first 8) ---" << std::endl;
    APIAnalogOutputs analog_out = client.get_analog_outputs();
    if (analog_out.has_data) {
        std::cout << "Analog Outputs: ";
        for (int i = 0; i < 8 && i < static_cast<int>(analog_out.value.size()); ++i) {
            std::cout << analog_out.value[i];
            if (i < 7) std::cout << ", ";
        }
        std::cout << std::endl;
    } else {
        std::cout << "Failed to get analog outputs!" << std::endl;
    }
    
    // Test 7: Get Work Info
    std::cout << "\n--- Work Info ---" << std::endl;
    APIWorkInfo work_info = client.get_work_info();
    if (work_info.has_data) {
        std::cout << "Work Mode: " << work_info.work_mode << std::endl;
        std::cout << "File Name: " << work_info.file_name << std::endl;
        std::cout << "Planned Time: " << work_info.planned_time << std::endl;
        std::cout << "Worked Time: " << work_info.worked_time << std::endl;
        if (!work_info.active_work_order_code.empty()) {
            std::cout << "Active Order: " << work_info.active_work_order_code << std::endl;
        }
    } else {
        std::cout << "Failed to get work info!" << std::endl;
    }
    
    // Test 8: Get Machining Info
    std::cout << "\n--- Machining Info ---" << std::endl;
    APIMachiningInfo machining_info = client.get_machining_info();
    if (machining_info.has_data) {
        std::cout << "Tool Path in Fast: " << machining_info.tool_path_in_fast << " mm" << std::endl;
        std::cout << "Tool Path in Feed: " << machining_info.tool_path_in_feed << " mm" << std::endl;
        std::cout << "Total Path: " << machining_info.total_path << " mm" << std::endl;
        std::cout << "Planned Time: " << machining_info.planned_time << std::endl;
    } else {
        std::cout << "Failed to get machining info!" << std::endl;
    }
    
    // Test 9: Get Tool Library Info (tool at index 1)
    std::cout << "\n--- Tool Library Info (Index 1) ---" << std::endl;
    APIToolsLibInfo tool_info = client.get_tools_lib_info(1);
    if (tool_info.has_data) {
        std::cout << "Tool Index: " << tool_info.data.tool_index << std::endl;
        std::cout << "Tool ID: " << tool_info.data.tool_id << std::endl;
        std::cout << "Tool Type: " << tool_info.data.tool_type << std::endl;
        std::cout << "Diameter: " << tool_info.data.tool_diameter << " mm" << std::endl;
        std::cout << "Offset Z: " << tool_info.data.tool_offset_z << " mm" << std::endl;
        std::cout << "Description: " << tool_info.data.tool_description << std::endl;
    } else {
        std::cout << "Failed to get tool info!" << std::endl;
    }
    
    // Test 10: Get Tool Library Infos (all tools)
    std::cout << "\n--- Tool Library Infos (All) ---" << std::endl;
    APIToolsLibInfos tools_infos = client.get_tools_lib_infos();
    if (tools_infos.has_data) {
        std::cout << "Slot Enabled: " << (tools_infos.slot_enabled ? "YES" : "NO") << std::endl;
        std::cout << "Tools Count: " << tools_infos.data.size() << std::endl;
    } else {
        std::cout << "Failed to get tools library infos!" << std::endl;
    }
    
    std::cout << "\n========================================" << std::endl;
    std::cout << "Real-Time CNC Monitoring (10 updates)" << std::endl;
    std::cout << "========================================" << std::endl;
    
    // Main loop - query CNC state every second
    for (int i = 0; i < 10; ++i) {
        std::cout << "\n--- Update " << (i + 1) << " ---" << std::endl;
        
        // Update all info
        if (context.update()) {
            // Display CNC info
            std::cout << "State Machine: " << context.cnc_info.state_machine 
                     << " (" << get_state_machine_name(context.cnc_info.state_machine) << ")" << std::endl;
            
            // Check if alarm is active (when current_alarm_code != 0)
            bool is_alarm_active = (context.cnc_info.current_alarm_code != 0);
            std::cout << "Alarm Active: " << (is_alarm_active ? "YES" : "NO") << std::endl;
            
            if (is_alarm_active) {
                std::cout << "Alarm Code: " << context.cnc_info.current_alarm_code << std::endl;
                std::cout << "Alarm Message: " << context.cnc_info.current_alarm_text << std::endl;
            }
            
            // Display enabled commands
            std::cout << "Can Start: " << (context.enabled_commands.cnc_start ? "YES" : "NO") << std::endl;
            std::cout << "Can Pause: " << (context.enabled_commands.cnc_pause ? "YES" : "NO") << std::endl;
            std::cout << "Can Resume: " << (context.enabled_commands.cnc_resume ? "YES" : "NO") << std::endl;
            std::cout << "Can Stop: " << (context.enabled_commands.cnc_stop ? "YES" : "NO") << std::endl;
            std::cout << "Can Jog: " << (context.enabled_commands.cnc_jog_command != 0 ? "YES" : "NO") << std::endl;
            std::cout << "Can Home: " << (context.enabled_commands.cnc_homing != 0 ? "YES" : "NO") << std::endl;
            
            // Display axes info (positions from axes_info)
            if (context.axes_info.has_data) {
                std::cout << "Machine Position - X: " << context.axes_info.machine_position[X_AXIS_INDEX]
                         << " Y: " << context.axes_info.machine_position[Y_AXIS_INDEX]
                         << " Z: " << context.axes_info.machine_position[Z_AXIS_INDEX] << std::endl;
                
                std::cout << "Program Position - X: " << context.axes_info.program_position[X_AXIS_INDEX]
                         << " Y: " << context.axes_info.program_position[Y_AXIS_INDEX]
                         << " Z: " << context.axes_info.program_position[Z_AXIS_INDEX] << std::endl;
            }
            
            // Display tool info (from cnc_info)
            if (context.cnc_info.has_data) {
                std::cout << "Tool ID: " << context.cnc_info.tool_id
                         << " Slot: " << context.cnc_info.tool_slot
                         << " Type: " << context.cnc_info.tool_type
                         << " Diameter: " << context.cnc_info.tool_diameter << std::endl;
                std::cout << "Tool Description: " << context.cnc_info.tool_description << std::endl;
            }
            
            // Display spindle info (from cnc_info)
            if (context.cnc_info.has_data) {
                std::cout << "Spindle Direction: " << context.cnc_info.spindle_direction
                         << " Programmed: " << context.cnc_info.spindle_programmed
                         << " Actual: " << context.cnc_info.spindle_actual << " RPM" << std::endl;
            }
        } else {
            std::cout << "Failed to update CNC info!" << std::endl;
        }
        
        // Wait 1 second before next update
        std::this_thread::sleep_for(std::chrono::seconds(1));
    }
    
    // Check if alarm is active and reset it
    if (context.cnc_info.current_alarm_code != 0) {
        std::cout << "\n--- Resetting Alarm ---" << std::endl;
        std::cout << "Resetting alarm..." << std::endl;
        if (client.reset_alarms()) {
            std::cout << "Alarm reset successfully!" << std::endl;
        } else {
            std::cout << "Failed to reset alarm!" << std::endl;
        }
    }
    
    /* Commented out - these commands require proper CNC setup and files
    
    // Load a file
    std::cout << "Loading file..." << std::endl;
    if (client.program_load("C:\\CNC\\Programs\\test.nc")) {
        std::cout << "File loaded successfully!" << std::endl;
    } else {
        std::cout << "Failed to load file!" << std::endl;
    }
    
    // Start program
    if (context.enabled_commands.cnc_start) {
        std::cout << "Starting program..." << std::endl;
        if (client.cnc_start()) {
            std::cout << "Program started successfully!" << std::endl;
        } else {
            std::cout << "Failed to start program!" << std::endl;
        }
    }
    
    // Jog example (move X axis forward)
    if (context.enabled_commands.cnc_jog_command != 0) {
        std::cout << "Jogging X axis forward..." << std::endl;
        if (client.cnc_jog_command(JC_X_FW)) {
            std::cout << "Jog command sent!" << std::endl;
            std::this_thread::sleep_for(std::chrono::seconds(2));
            
            // Stop jog
            client.cnc_jog_command(JC_NONE);
            std::cout << "Jog stopped!" << std::endl;
        }
    }
    */
    
    // Example of work order management
    /*
    std::cout << "\n--- Adding Work Order ---" << std::endl;
    
    APIWorkOrderDataForAdd order;
    
    // Set order properties (all are optional pointers)
    order.order_priority = new int(WO_PR_NORMAL);
    order.job_order_code = new std::string("JOB-2026-001");
    order.customer_code = new std::string("CUSTOMER-001");
    order.item_code = new std::string("ITEM-001");
    order.order_notes = new std::string("Test order from C++ API");
    
    // Add files to the order
    if (order.files.size() > 0) {
        order.files[0].file_name = new std::string("part1.nc");
        order.files[0].pieces_per_file = new int(10);
        order.files[0].requested_pieces = new int(50);
    }
    
    if (order.files.size() > 1) {
        order.files[1].file_name = new std::string("part2.nc");
        order.files[1].pieces_per_file = new int(5);
        order.files[1].requested_pieces = new int(25);
    }
    
    if (client.work_order_add("ORDER-2026-001", &order)) {
        std::cout << "Work order added successfully!" << std::endl;
    } else {
        std::cout << "Failed to add work order!" << std::endl;
    }
    
    // Note: order destructor will clean up allocated memory
    */
    
    // Close connection
    std::cout << "\nClosing connection..." << std::endl;
    client.close();
    std::cout << "Connection closed." << std::endl;
    
    return 0;
}
