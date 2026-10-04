/**
 * CNC API Client Core for RosettaCNC & derivated NC Systems
 * Implementation file - Native C++ port from Python
 * 
 * The protocol JSON helpers below are dependency-free and support the value
 * shapes used by API server version 1.5.3.
 */

#include "cnc_api_client_core.h"
#include <sstream>
#include <algorithm>
#include <iostream>
#include <iomanip>
#include <cmath>
#include <cstring>
#include <cstdint>
#include <limits>
#include <thread>
#include <mutex>
#include <atomic>
#include <cctype>

// Dependency-free JSON helpers for the API v1.5.3 protocol shapes.
namespace SimpleJSON {
    // Basic JSON escape function
    std::string escape(const std::string& str) {
        std::string result;
        for (char c : str) {
            switch (c) {
                case '"': result += "\\\""; break;
                case '\\': result += "\\\\"; break;
                case '\b': result += "\\b"; break;
                case '\f': result += "\\f"; break;
                case '\n': result += "\\n"; break;
                case '\r': result += "\\r"; break;
                case '\t': result += "\\t"; break;
                default:
                    if (c < 32) {
                        char buf[8];
                        sprintf_s(buf, sizeof(buf), "\\u%04x", (int)c);
                        result += buf;
                    } else {
                        result += c;
                    }
            }
        }
        return result;
    }
    
    // Basic JSON parser - extracts values from simple JSON
    class Parser {
    public:
        static std::string trim(const std::string& str) {
            size_t start = str.find_first_not_of(" \t\r\n");
            if (start == std::string::npos) return "";
            size_t end = str.find_last_not_of(" \t\r\n");
            return str.substr(start, end - start + 1);
        }
        
        static std::string unquote(const std::string& str) {
            std::string s = trim(str);
            if (s.length() >= 2 && s.front() == '"' && s.back() == '"') {
                std::string result;
                for (size_t i = 1; i + 1 < s.length(); ++i) {
                    if (s[i] != '\\' || i + 2 >= s.length()) {
                        result += s[i];
                        continue;
                    }
                    const char escaped = s[++i];
                    switch (escaped) {
                        case '"': result += '"'; break;
                        case '\\': result += '\\'; break;
                        case '/': result += '/'; break;
                        case 'b': result += '\b'; break;
                        case 'f': result += '\f'; break;
                        case 'n': result += '\n'; break;
                        case 'r': result += '\r'; break;
                        case 't': result += '\t'; break;
                        case 'u': {
                            if (i + 4 >= s.length() - 1) return "";
                            unsigned int code = 0;
                            for (int digit = 0; digit < 4; ++digit) {
                                const char h = s[++i];
                                code <<= 4;
                                if (h >= '0' && h <= '9') code += h - '0';
                                else if (h >= 'a' && h <= 'f') code += h - 'a' + 10;
                                else if (h >= 'A' && h <= 'F') code += h - 'A' + 10;
                                else return "";
                            }
                            if (code >= 0xD800 && code <= 0xDBFF && i + 6 < s.length() - 1 &&
                                s[i + 1] == '\\' && s[i + 2] == 'u') {
                                unsigned int low = 0;
                                bool valid = true;
                                for (int digit = 0; digit < 4; ++digit) {
                                    const char h = s[i + 3 + digit];
                                    low <<= 4;
                                    if (h >= '0' && h <= '9') low += h - '0';
                                    else if (h >= 'a' && h <= 'f') low += h - 'a' + 10;
                                    else if (h >= 'A' && h <= 'F') low += h - 'A' + 10;
                                    else valid = false;
                                }
                                if (valid && low >= 0xDC00 && low <= 0xDFFF) {
                                    code = 0x10000 + ((code - 0xD800) << 10) + (low - 0xDC00);
                                    i += 6;
                                }
                            }
                            if (code <= 0x7F) result += static_cast<char>(code);
                            else if (code <= 0x7FF) {
                                result += static_cast<char>(0xC0 | (code >> 6));
                                result += static_cast<char>(0x80 | (code & 0x3F));
                            } else if (code <= 0xFFFF) {
                                result += static_cast<char>(0xE0 | (code >> 12));
                                result += static_cast<char>(0x80 | ((code >> 6) & 0x3F));
                                result += static_cast<char>(0x80 | (code & 0x3F));
                            } else {
                                result += static_cast<char>(0xF0 | (code >> 18));
                                result += static_cast<char>(0x80 | ((code >> 12) & 0x3F));
                                result += static_cast<char>(0x80 | ((code >> 6) & 0x3F));
                                result += static_cast<char>(0x80 | (code & 0x3F));
                            }
                            break;
                        }
                        default: return "";
                    }
                }
                return result;
            }
            return s;
        }
        
        static std::map<std::string, std::string> parse_object(const std::string& json) {
            std::map<std::string, std::string> result;
            
            // Find object boundaries
            size_t start = json.find('{');
            size_t end = json.rfind('}');
            if (start == std::string::npos || end == std::string::npos) return result;
            
            std::string content = json.substr(start + 1, end - start - 1);
            
            // Simple parser: split by comma (doesn't handle nested objects perfectly)
            size_t pos = 0;
            int brace_depth = 0;
            int bracket_depth = 0;
            bool in_string = false;
            size_t key_start = 0;
            
            for (size_t i = 0; i < content.length(); ++i) {
                char c = content[i];
                
                if (c == '"' && (i == 0 || content[i-1] != '\\')) {
                    in_string = !in_string;
                }
                if (!in_string) {
                    if (c == '{') brace_depth++;
                    else if (c == '}') brace_depth--;
                    else if (c == '[') bracket_depth++;
                    else if (c == ']') bracket_depth--;
                    else if (c == ',' && brace_depth == 0 && bracket_depth == 0) {
                        parse_key_value(content.substr(key_start, i - key_start), result);
                        key_start = i + 1;
                    }
                }
            }
            // Parse last item
            if (key_start < content.length()) {
                parse_key_value(content.substr(key_start), result);
            }
            
            return result;
        }
        
        static void parse_key_value(const std::string& pair, std::map<std::string, std::string>& result) {
            size_t colon = pair.find(':');
            if (colon != std::string::npos) {
                std::string key = unquote(pair.substr(0, colon));
                std::string value = trim(pair.substr(colon + 1));
                
                // Handle arrays by converting to comma-separated string
                if (!value.empty() && value[0] == '[') {
                    value = value.substr(1, value.length() - 2); // Remove [ ]
                }
                
                result[key] = unquote(value);
            }
        }
        
        static std::vector<double> parse_double_array(const std::string& array_str) {
            std::vector<double> result;
            std::string s = trim(array_str);
            if (s.empty()) return result;
            
            // Remove brackets if present
            if (s.front() == '[') s = s.substr(1);
            if (!s.empty() && s.back() == ']') s = s.substr(0, s.length() - 1);
            
            // Split by comma
            std::stringstream ss(s);
            std::string item;
            while (std::getline(ss, item, ',')) {
                try {
                    result.push_back(std::stod(trim(item)));
                } catch (...) {
                    result.push_back(0.0);
                }
            }
            return result;
        }
        
        static std::vector<int> parse_int_array(const std::string& array_str) {
            std::vector<int> result;
            std::string s = trim(array_str);
            if (s.empty()) return result;
            
            // Remove brackets if present
            if (s.front() == '[') s = s.substr(1);
            if (!s.empty() && s.back() == ']') s = s.substr(0, s.length() - 1);
            
            // Split by comma
            std::stringstream ss(s);
            std::string item;
            while (std::getline(ss, item, ',')) {
                try {
                    result.push_back(std::stoi(trim(item)));
                } catch (...) {
                    result.push_back(0);
                }
            }
            return result;
        }

        static std::vector<std::string> split_array_items(const std::string& array_str) {
            std::vector<std::string> result;
            std::string s = trim(array_str);
            if (s.empty()) return result;
            if (s.front() == '[') s.erase(s.begin());
            if (!s.empty() && s.back() == ']') s.pop_back();

            size_t item_start = 0;
            int brace_depth = 0;
            int bracket_depth = 0;
            bool in_string = false;
            bool escaped = false;
            for (size_t i = 0; i < s.size(); ++i) {
                const char c = s[i];
                if (in_string) {
                    if (escaped) escaped = false;
                    else if (c == '\\') escaped = true;
                    else if (c == '"') in_string = false;
                    continue;
                }
                if (c == '"') in_string = true;
                else if (c == '{') ++brace_depth;
                else if (c == '}') --brace_depth;
                else if (c == '[') ++bracket_depth;
                else if (c == ']') --bracket_depth;
                else if (c == ',' && brace_depth == 0 && bracket_depth == 0) {
                    result.push_back(trim(s.substr(item_start, i - item_start)));
                    item_start = i + 1;
                }
            }
            if (item_start < s.size()) result.push_back(trim(s.substr(item_start)));
            return result;
        }

        static std::vector<std::string> parse_string_array(const std::string& array_str) {
            std::vector<std::string> result;
            const std::vector<std::string> items = split_array_items(array_str);
            for (size_t i = 0; i < items.size(); ++i) {
                result.push_back(unquote(items[i]));
            }
            return result;
        }

        static std::string get_value(const std::string& json, const std::string& key) {
            const std::string search = "\"" + key + "\":";
            size_t pos = json.find(search);
            if (pos == std::string::npos) return "";
            pos += search.length();
            while (pos < json.length() && (json[pos] == ' ' || json[pos] == '\t')) ++pos;
            return extract_value(json, pos);
        }

        static bool has_key(const std::string& json, const std::string& key) {
            return json.find("\"" + key + "\":") != std::string::npos;
        }
        
        // Extract nested object value from JSON response
        // e.g., get_nested_value(json, "res", "current.alarm", "code") 
        // extracts value from {"res":{"current.alarm":{"code":123}}}
        static std::string get_nested_value(const std::string& json, const std::string& field1, const std::string& field2, const std::string& field3 = "") {
            // Find "field1":
            std::string search1 = "\"" + field1 + "\":";
            size_t pos1 = json.find(search1);
            if (pos1 == std::string::npos) return "";
            pos1 += search1.length();
            
            // Skip whitespace
            while (pos1 < json.length() && (json[pos1] == ' ' || json[pos1] == '\t')) pos1++;
            
            // Find "field2": within field1's object
            std::string search2 = "\"" + field2 + "\":";
            size_t pos2 = json.find(search2, pos1);
            if (pos2 == std::string::npos) return "";
            pos2 += search2.length();
            
            // Skip whitespace
            while (pos2 < json.length() && (json[pos2] == ' ' || json[pos2] == '\t')) pos2++;
            
            if (!field3.empty()) {
                // Need to go one level deeper
                std::string search3 = "\"" + field3 + "\":";
                size_t pos3 = json.find(search3, pos2);
                if (pos3 == std::string::npos) return "";
                pos3 += search3.length();
                
                // Skip whitespace
                while (pos3 < json.length() && (json[pos3] == ' ' || json[pos3] == '\t')) pos3++;
                
                return extract_value(json, pos3);
            }
            
            return extract_value(json, pos2);
        }
        
        static std::string extract_value(const std::string& json, size_t start_pos) {
            if (start_pos >= json.length()) return "";
            
            // Handle string value
            if (json[start_pos] == '"') {
                bool escaped = false;
                for (size_t end = start_pos + 1; end < json.length(); ++end) {
                    if (escaped) {
                        escaped = false;
                    } else if (json[end] == '\\') {
                        escaped = true;
                    } else if (json[end] == '"') {
                        return unquote(json.substr(start_pos, end - start_pos + 1));
                    }
                }
                return "";
            }
            
            // Handle array value
            if (json[start_pos] == '[') {
                int bracket_count = 1;
                size_t pos = start_pos + 1;
                bool in_string = false;
                bool escaped = false;
                while (pos < json.length() && bracket_count > 0) {
                    if (in_string) {
                        if (escaped) escaped = false;
                        else if (json[pos] == '\\') escaped = true;
                        else if (json[pos] == '"') in_string = false;
                    } else if (json[pos] == '"') in_string = true;
                    else if (json[pos] == '[') bracket_count++;
                    else if (json[pos] == ']') bracket_count--;
                    pos++;
                }
                return json.substr(start_pos, pos - start_pos);
            }
            
            // Handle object value
            if (json[start_pos] == '{') {
                int brace_count = 1;
                size_t pos = start_pos + 1;
                bool in_string = false;
                while (pos < json.length() && (brace_count > 0 || in_string)) {
                    if (json[pos] == '"' && (pos == 0 || json[pos-1] != '\\')) {
                        in_string = !in_string;
                    }
                    if (!in_string) {
                        if (json[pos] == '{') brace_count++;
                        else if (json[pos] == '}') brace_count--;
                    }
                    pos++;
                }
                return json.substr(start_pos, pos - start_pos);
            }
            
            // Handle numeric/boolean/null value
            size_t end = start_pos;
            while (end < json.length() && json[end] != ',' && json[end] != '}' && json[end] != ']') {
                end++;
            }
            return trim(json.substr(start_pos, end - start_pos));
        }
        
        static bool get_bool(const std::map<std::string, std::string>& obj, const std::string& key, bool default_value = false) {
            auto it = obj.find(key);
            if (it != obj.end()) {
                std::string val = it->second;
                std::transform(val.begin(), val.end(), val.begin(), ::tolower);
                return (val == "true" || val == "1");
            }
            return default_value;
        }
        
        static int get_int(const std::map<std::string, std::string>& obj, const std::string& key, int default_value = 0) {
            auto it = obj.find(key);
            if (it != obj.end()) {
                try {
                    return std::stoi(it->second);
                } catch (...) {}
            }
            return default_value;
        }
        
        static double get_double(const std::map<std::string, std::string>& obj, const std::string& key, double default_value = 0.0) {
            auto it = obj.find(key);
            if (it != obj.end()) {
                try {
                    return std::stod(it->second);
                } catch (...) {}
            }
            return default_value;
        }
        
        static std::string get_string(const std::map<std::string, std::string>& obj, const std::string& key, const std::string& default_value = "") {
            auto it = obj.find(key);
            if (it != obj.end()) {
                return it->second;
            }
            return default_value;
        }
    };
}

namespace {
    int json_to_int(const std::string& value, int default_value = 0) {
        try { return value.empty() ? default_value : std::stoi(value); }
        catch (...) { return default_value; }
    }

    int64_t json_to_int64(const std::string& value, int64_t default_value = 0) {
        try { return value.empty() ? default_value : std::stoll(value); }
        catch (...) { return default_value; }
    }

    double json_to_double(const std::string& value, double default_value = 0.0) {
        try { return value.empty() ? default_value : std::stod(value); }
        catch (...) { return default_value; }
    }

    bool json_to_bool(const std::string& value, bool default_value = false) {
        if (value == "true" || value == "1") return true;
        if (value == "false" || value == "0") return false;
        return default_value;
    }

    std::string json_object_value(const std::string& object, const char* key) {
        return SimpleJSON::Parser::get_value(object, key);
    }

    RosettaCNC::APIToolsLibInfoForGet parse_tool_info(const std::string& object) {
        RosettaCNC::APIToolsLibInfoForGet tool;
        tool.tool_index = json_to_int(json_object_value(object, "index"));
        tool.tool_id = json_to_int(json_object_value(object, "id"));
        tool.tool_slot = json_to_int(json_object_value(object, "slot"));
        tool.tool_type = json_to_int(json_object_value(object, "type"));
        tool.tool_diameter = json_to_double(json_object_value(object, "diameter"));
        tool.tool_offset_x = json_to_double(json_object_value(object, "offset.x"));
        tool.tool_offset_y = json_to_double(json_object_value(object, "offset.y"));
        tool.tool_offset_z = json_to_double(json_object_value(object, "offset.z"));
        double* params[] = {
            &tool.tool_param_1, &tool.tool_param_2, &tool.tool_param_3, &tool.tool_param_4,
            &tool.tool_param_5, &tool.tool_param_6, &tool.tool_param_7, &tool.tool_param_8,
            &tool.tool_param_9, &tool.tool_param_10, &tool.tool_param_51, &tool.tool_param_52,
            &tool.tool_param_53, &tool.tool_param_54, &tool.tool_param_55, &tool.tool_param_56,
            &tool.tool_param_57, &tool.tool_param_58, &tool.tool_param_59, &tool.tool_param_60
        };
        const int numbers[] = {1,2,3,4,5,6,7,8,9,10,51,52,53,54,55,56,57,58,59,60};
        for (size_t i = 0; i < sizeof(numbers) / sizeof(numbers[0]); ++i) {
            *params[i] = json_to_double(json_object_value(object,
                ("param." + std::to_string(numbers[i])).c_str()));
        }
        tool.tool_description = json_object_value(object, "description");
        return tool;
    }

    RosettaCNC::DateTime parse_filetime_value(const std::string& text) {
        const int64_t raw = json_to_int64(text, -1);
        if (raw < 0) return RosettaCNC::DateTime::min_value();
        ULARGE_INTEGER value;
        value.QuadPart = static_cast<ULONGLONG>(raw);
        FILETIME filetime = {value.LowPart, value.HighPart};
        SYSTEMTIME system = {};
        if (!FileTimeToSystemTime(&filetime, &system)) return RosettaCNC::DateTime::min_value();
        RosettaCNC::DateTime result;
        result.year = system.wYear; result.month = system.wMonth; result.day = system.wDay;
        result.hour = system.wHour; result.minute = system.wMinute; result.second = system.wSecond;
        result.microsecond = system.wMilliseconds * 1000 +
            static_cast<int>((value.QuadPart % 10000ULL) / 10ULL);
        return result;
    }

    std::vector<RosettaCNC::APIAlarmsWarningsList::AlarmWarningData>
    parse_alarm_warning_items(const std::string& response) {
        std::vector<RosettaCNC::APIAlarmsWarningsList::AlarmWarningData> result;
        const std::string res = SimpleJSON::Parser::get_value(response, "res");
        const std::string list = SimpleJSON::Parser::get_value(res, "list");
        for (const std::string& object : SimpleJSON::Parser::split_array_items(list)) {
            if (object.empty()) continue;
            RosettaCNC::APIAlarmsWarningsList::AlarmWarningData item;
            item.code = json_to_int(json_object_value(object, "code"));
            item.info_1 = json_to_int(json_object_value(object, "info.1"));
            item.info_2 = json_to_int(json_object_value(object, "info.2"));
            item.text = json_object_value(object, "text");
            item.datetime = parse_filetime_value(json_object_value(object, "datetime"));
            result.push_back(item);
        }
        return result;
    }

    bool decode_base64(const std::string& encoded, std::vector<unsigned char>& decoded) {
        static const std::string alphabet =
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
        decoded.clear();
        unsigned int accumulator = 0;
        int bits = -8;
        for (size_t i = 0; i < encoded.size(); ++i) {
            const unsigned char c = static_cast<unsigned char>(encoded[i]);
            if (c == '=') break;
            if (c == ' ' || c == '\r' || c == '\n' || c == '\t') continue;
            const size_t value = alphabet.find(static_cast<char>(c));
            if (value == std::string::npos) {
                decoded.clear();
                return false;
            }
            accumulator = (accumulator << 6) | static_cast<unsigned int>(value);
            bits += 6;
            if (bits >= 0) {
                decoded.push_back(static_cast<unsigned char>((accumulator >> bits) & 0xFF));
                bits -= 8;
            }
        }
        return true;
    }

    std::string json_number(double value) {
        std::ostringstream stream;
        stream << std::setprecision(17) << value;
        return stream.str();
    }

    void append_json_raw(std::string& json, bool& first, const std::string& key,
                         const std::string& value) {
        if (!first) json += ',';
        json += "\"" + key + "\":" + value;
        first = false;
    }

    void append_json_string(std::string& json, bool& first, const std::string& key,
                            const std::string& value) {
        append_json_raw(json, first, key, "\"" + SimpleJSON::escape(value) + "\"");
    }

    bool valid_force_sync_timeout(double timeout) {
        const double max_seconds =
            static_cast<double>((std::numeric_limits<DWORD>::max)()) / 1000.0;
        return std::isfinite(timeout) && timeout > 0.0 && timeout <= max_seconds;
    }
}

namespace RosettaCNC {

// ========== Static Initialization ==========
bool CncAPIClientCore::s_winsock_initialized = false;

struct CncAPIClientCore::ForceSyncState {
    std::atomic<bool> running;
    std::mutex mutex;
    std::shared_ptr<CncAPIClientCore> api;

    ForceSyncState() : running(false) {}
};

APICompilerSettingsForGet::APICompilerSettingsForGet() :
    has_data(false),
    current_toolpath_mode(ANALYSIS_MT),
    default_toolpath_mode(ANALYSIS_MT),
    modal_macro_motion_mode(CP_MODAL_MACRO_MOTION_MODE_IN_FAST),
    cutter_compensation_mode(CP_CUTTER_COMPENSATION_MODE_NORMAL),
    cutter_compensation_gouging_threshold(0),
    arc_radius_tolerance(0.005),
    infinite_loop_threshold(0),
    gcode_block_skip_enabled(false),
    g43_persistent(true),
    g52_independent(true),
    g92_persistent(false),
    origin_offset_persistent(true),
    user_m_codes_arguments_enabled(true),
    user_macro_path_mode(CP_USER_MACRO_PATH_MODE_DISABLED),
    jpdc_axis_x(0.0), jpdc_axis_y(0.0), jpdc_axis_z(0.0),
    jpdc_axis_a(0.0), jpdc_axis_b(0.0), jpdc_axis_c(0.0),
    restart_default_movement_mode(CP_RESTART_DEF_MOV_MODE_IN_FEED),
    restart_first_movement_feed(100.0), restart_max_distance(1.0),
    restart_force_tool_measurement(false), toolpath_resolution(0.2),
    use_points_per_block(false), points_per_block(100),
    tool_xx0_color(0x00C02E1D), tool_xx1_color(0x00F16C20),
    tool_xx2_color(0x00DBB417), tool_xx3_color(0x00879F4D),
    tool_xx4_color(0x00028097), tool_xx5_color(0x000D3C56),
    tool_xx6_color(0x00800080), tool_xx7_color(0x00800000),
    tool_xx8_color(0x00436B58), tool_xx9_color(0x008000FF),
    rapid_move_color(0x0000CB9A), rf_threshold(50),
    rf_threshold_color_lower(0x000000FF), rf_threshold_color_equal(0x0000FF00),
    rf_threshold_color_upper(0x00FF0000), rv_color_mode(CP_RV_COLOR_MODE_SPECTRAL),
    rv_wavelength_min(520), rv_wavelength_max(700),
    rv_gradient_color_min(0x0000FFFF), rv_gradient_color_max(0x00FF0000),
    rz_color_mode(CP_RZ_COLOR_MODE_GRADIENT), rz_wavelength_min(520),
    rz_wavelength_max(700), rz_gradient_color_min(0x00000000),
    rz_gradient_color_max(0x00FFFFFF) {}

APICompilerSettingsForSet::APICompilerSettingsForSet() : has_data(false) {
#define SET_NULL(field) field = nullptr
    SET_NULL(current_toolpath_mode); SET_NULL(default_toolpath_mode);
    SET_NULL(modal_macro_motion_mode); SET_NULL(cutter_compensation_mode);
    SET_NULL(cutter_compensation_gouging_threshold); SET_NULL(arc_radius_tolerance);
    SET_NULL(infinite_loop_threshold); SET_NULL(gcode_block_skip_enabled);
    SET_NULL(g43_persistent); SET_NULL(g52_independent); SET_NULL(g92_persistent);
    SET_NULL(origin_offset_persistent); SET_NULL(user_m_codes_arguments_enabled);
    SET_NULL(user_macro_path_mode); SET_NULL(user_macro_path);
    SET_NULL(jpdc_axis_x); SET_NULL(jpdc_axis_y); SET_NULL(jpdc_axis_z);
    SET_NULL(jpdc_axis_a); SET_NULL(jpdc_axis_b); SET_NULL(jpdc_axis_c);
    SET_NULL(restart_default_movement_mode); SET_NULL(restart_first_movement_feed);
    SET_NULL(restart_max_distance); SET_NULL(restart_force_tool_measurement);
    SET_NULL(toolpath_resolution); SET_NULL(use_points_per_block); SET_NULL(points_per_block);
    SET_NULL(tool_xx0_color); SET_NULL(tool_xx1_color); SET_NULL(tool_xx2_color);
    SET_NULL(tool_xx3_color); SET_NULL(tool_xx4_color); SET_NULL(tool_xx5_color);
    SET_NULL(tool_xx6_color); SET_NULL(tool_xx7_color); SET_NULL(tool_xx8_color);
    SET_NULL(tool_xx9_color); SET_NULL(rapid_move_color); SET_NULL(rf_threshold);
    SET_NULL(rf_threshold_color_lower); SET_NULL(rf_threshold_color_equal);
    SET_NULL(rf_threshold_color_upper); SET_NULL(rv_color_mode);
    SET_NULL(rv_wavelength_min); SET_NULL(rv_wavelength_max);
    SET_NULL(rv_gradient_color_min); SET_NULL(rv_gradient_color_max);
    SET_NULL(rz_color_mode); SET_NULL(rz_wavelength_min); SET_NULL(rz_wavelength_max);
    SET_NULL(rz_gradient_color_min); SET_NULL(rz_gradient_color_max);
#undef SET_NULL
}

APICompilerSettingsForSet::~APICompilerSettingsForSet() {
#define DELETE_FIELD(field) delete field
    DELETE_FIELD(current_toolpath_mode); DELETE_FIELD(default_toolpath_mode);
    DELETE_FIELD(modal_macro_motion_mode); DELETE_FIELD(cutter_compensation_mode);
    DELETE_FIELD(cutter_compensation_gouging_threshold); DELETE_FIELD(arc_radius_tolerance);
    DELETE_FIELD(infinite_loop_threshold); DELETE_FIELD(gcode_block_skip_enabled);
    DELETE_FIELD(g43_persistent); DELETE_FIELD(g52_independent); DELETE_FIELD(g92_persistent);
    DELETE_FIELD(origin_offset_persistent); DELETE_FIELD(user_m_codes_arguments_enabled);
    DELETE_FIELD(user_macro_path_mode); DELETE_FIELD(user_macro_path);
    DELETE_FIELD(jpdc_axis_x); DELETE_FIELD(jpdc_axis_y); DELETE_FIELD(jpdc_axis_z);
    DELETE_FIELD(jpdc_axis_a); DELETE_FIELD(jpdc_axis_b); DELETE_FIELD(jpdc_axis_c);
    DELETE_FIELD(restart_default_movement_mode); DELETE_FIELD(restart_first_movement_feed);
    DELETE_FIELD(restart_max_distance); DELETE_FIELD(restart_force_tool_measurement);
    DELETE_FIELD(toolpath_resolution); DELETE_FIELD(use_points_per_block); DELETE_FIELD(points_per_block);
    DELETE_FIELD(tool_xx0_color); DELETE_FIELD(tool_xx1_color); DELETE_FIELD(tool_xx2_color);
    DELETE_FIELD(tool_xx3_color); DELETE_FIELD(tool_xx4_color); DELETE_FIELD(tool_xx5_color);
    DELETE_FIELD(tool_xx6_color); DELETE_FIELD(tool_xx7_color); DELETE_FIELD(tool_xx8_color);
    DELETE_FIELD(tool_xx9_color); DELETE_FIELD(rapid_move_color); DELETE_FIELD(rf_threshold);
    DELETE_FIELD(rf_threshold_color_lower); DELETE_FIELD(rf_threshold_color_equal);
    DELETE_FIELD(rf_threshold_color_upper); DELETE_FIELD(rv_color_mode);
    DELETE_FIELD(rv_wavelength_min); DELETE_FIELD(rv_wavelength_max);
    DELETE_FIELD(rv_gradient_color_min); DELETE_FIELD(rv_gradient_color_max);
    DELETE_FIELD(rz_color_mode); DELETE_FIELD(rz_wavelength_min); DELETE_FIELD(rz_wavelength_max);
    DELETE_FIELD(rz_gradient_color_min); DELETE_FIELD(rz_gradient_color_max);
#undef DELETE_FIELD
}

APICoordinateSystemsInfo::APICoordinateSystemsInfo() :
    has_data(false), working_wcs(0), working_offset(6, 0.0),
    wcs_1(6, 0.0), wcs_2(6, 0.0), wcs_3(6, 0.0),
    wcs_4(6, 0.0), wcs_5(6, 0.0), wcs_6(6, 0.0),
    wcs_7(6, 0.0), wcs_8(6, 0.0), wcs_9(6, 0.0) {}

APIOperatorRequest::APIOperatorRequest() :
    has_data(false), type(ORQT_NONE), data_elements(0),
    data_d01(std::numeric_limits<double>::quiet_NaN()),
    data_d02(std::numeric_limits<double>::quiet_NaN()),
    data_d03(std::numeric_limits<double>::quiet_NaN()),
    data_d04(std::numeric_limits<double>::quiet_NaN()),
    data_d05(std::numeric_limits<double>::quiet_NaN()),
    data_d06(std::numeric_limits<double>::quiet_NaN()),
    data_d07(std::numeric_limits<double>::quiet_NaN()),
    data_d08(std::numeric_limits<double>::quiet_NaN()),
    data_d09(std::numeric_limits<double>::quiet_NaN()),
    data_d10(std::numeric_limits<double>::quiet_NaN()),
    external_continue_requested(false) {}

APIOperatorResponse::APIOperatorResponse() :
    type(ORPT_STOP), data_elements(0),
    data_d01(std::numeric_limits<double>::quiet_NaN()),
    data_d02(std::numeric_limits<double>::quiet_NaN()),
    data_d03(std::numeric_limits<double>::quiet_NaN()),
    data_d04(std::numeric_limits<double>::quiet_NaN()),
    data_d05(std::numeric_limits<double>::quiet_NaN()),
    data_d06(std::numeric_limits<double>::quiet_NaN()),
    data_d07(std::numeric_limits<double>::quiet_NaN()),
    data_d08(std::numeric_limits<double>::quiet_NaN()),
    data_d09(std::numeric_limits<double>::quiet_NaN()),
    data_d10(std::numeric_limits<double>::quiet_NaN()) {}

bool APIOperatorResponse::copy_data_from_request(const APIOperatorRequest& request) {
    data_elements = request.data_elements;
    data_d01 = request.data_d01; data_d02 = request.data_d02;
    data_d03 = request.data_d03; data_d04 = request.data_d04;
    data_d05 = request.data_d05; data_d06 = request.data_d06;
    data_d07 = request.data_d07; data_d08 = request.data_d08;
    data_d09 = request.data_d09; data_d10 = request.data_d10;
    return true;
}

// ========== APICncInfo Constructor ==========
APICncInfo::APICncInfo() :
    has_data(false),
    units_mode(UM_METRIC),
    axes_mask(0),
    state_machine(SM_DISCONNECTED),
    connection_state(0),
    controller_settings_crc(0),
    interp_buffer_level(0),
    gcode_line(0),
    gcode_block_skip_enabled(false),
    planned_time("00:00:00"),
    worked_time("00:00:00"),
    program_gcode_sync_required(false),
    current_alarm_code(0),
    current_alarm_info1(0),
    current_alarm_info2(0),
    current_warning_code(0),
    current_warning_info1(0),
    current_warning_info2(0),
    aux_outputs(0),
    coolant_mist(false),
    coolant_flood(false),
    lube_axis_cycles_made(0),
    lube_axis_time_to_next_cycle(0),
    lube_spindle_cycles_made(0),
    lube_spindle_time_to_next_cycle(0),
    feed_programmed(0.0),
    feed_target(0.0),
    feed_reference(0.0),
    spindle_programmed(0),
    spindle_target(0),
    spindle_actual(0),
    spindle_load(0),
    spindle_torque(0),
    spindle_phase(0.0),
    spindle_direction(SD_STOPPED),
    spindle_not_ready(false),
    spindle_shaft(ST_STOPPED),
    spindle_status(SS_COLLET_OPEN),
    spindle_voltage(0),
    override_jog(0),
    override_jog_min(0),
    override_jog_max(100),
    override_jog_enabled(false),
    override_jog_locked(false),
    override_spindle(0),
    override_spindle_min(0),
    override_spindle_max(100),
    override_spindle_enabled(false),
    override_spindle_locked(false),
    override_fast(0),
    override_fast_min(0),
    override_fast_max(100),
    override_fast_enabled(false),
    override_fast_locked(false),
    override_feed(0),
    override_feed_min(0),
    override_feed_max(100),
    override_feed_enabled(false),
    override_feed_locked(false),
    override_feed_custom_1(0),
    override_feed_custom_1_min(0),
    override_feed_custom_1_max(100),
    override_feed_custom_1_enabled(false),
    override_feed_custom_1_locked(false),
    override_feed_custom_2(0),
    override_feed_custom_2_min(0),
    override_feed_custom_2_max(100),
    override_feed_custom_2_enabled(false),
    override_feed_custom_2_locked(false),
    override_plasma_power(0),
    override_plasma_power_min(0),
    override_plasma_power_max(100),
    override_plasma_power_enabled(false),
    override_plasma_power_locked(false),
    override_plasma_voltage(0),
    override_plasma_voltage_min(0),
    override_plasma_voltage_max(100),
    override_plasma_voltage_enabled(false),
    override_plasma_voltage_locked(false),
    tool_id(0),
    tool_slot(0),
    tool_slot_enabled(false),
    tool_type(TT_GENERIC),
    tool_diameter(0.0),
    tool_offset_x(0.0),
    tool_offset_y(0.0),
    tool_offset_z(0.0),
    tool_param_1(0.0),
    tool_param_2(0.0),
    tool_param_3(0.0),
    simulator_available(false),
    simulator_state(0),
    simulator_planned_time_ms(0),
    simulator_current_time_ms(0),
    simulator_speed_track(0) {}

// ========== APIEnabledCommands Constructor ==========
APIEnabledCommands::APIEnabledCommands() :
    has_data(false),
    cnc_csfm_aux(0),
    cnc_csfm_cooler_flood(false),
    cnc_csfm_cooler_mist(false),
    cnc_csfm_jog_mode(false),
    cnc_csfm_spindle_cw(false),
    cnc_csfm_spindle_ccw(false),
    cnc_csfm_thc_disabled(false),
    cnc_csfm_torch(false),
    cnc_connection_close(false),
    cnc_connection_open(false),
    cnc_continue(false),
    cnc_homing(0),
    cnc_jog_command(0),
    cnc_mdi_command(false),
    cnc_parameters(false),
    cnc_pause(false),
    cnc_resume(false),
    cnc_resume_from_line(false),
    cnc_resume_from_point(false),
    cnc_start(false),
    cnc_start_from_line(false),
    cnc_start_from_point(false),
    cnc_stop(false),
    program_analysis(false),
    program_analysis_abort(false),
    program_gcode_add_text(false),
    program_gcode_clear(false),
    program_gcode_modified(false),
    program_gcode_set_text(false),
    program_load(false),
    program_new(false),
    program_save(false),
    program_save_as(false),
    reset_alarms(false),
    reset_alarms_history(false),
    reset_warnings(false),
    reset_warnings_history(false),
    set_compiler_settings(false),
    set_dynamic_offsets(0),
    set_kinematics(false),
    set_program_position(0),
    set_simulator_current_time_ms(false),
    set_simulator_speed_track(false),
    show_ui_dialog(false),
    simulator_continue(false),
    simulator_pause(false),
    simulator_start(false),
    simulator_step_backward(false),
    simulator_step_forward(false),
    simulator_stop(false),
    tools_lib_write(false) {}

// ========== APIMachineSettings Constructor ==========
APIMachineSettings::APIMachineSettings() :
    has_data(false),
    machine_type(MT_MILL),
    axis_machine_type(MT_MILL),
    axis_kinematics_model(KM_TRIVIAL),
    axis_x_type(AT_DISABLED),
    axis_x_max_vel(0.0),
    axis_x_acc(0.0),
    axis_x_min_lim(0.0),
    axis_x_max_lim(0.0),
    axis_y_type(AT_DISABLED),
    axis_y_max_vel(0.0),
    axis_y_acc(0.0),
    axis_y_min_lim(0.0),
    axis_y_max_lim(0.0),
    axis_z_type(AT_DISABLED),
    axis_z_max_vel(0.0),
    axis_z_acc(0.0),
    axis_z_min_lim(0.0),
    axis_z_max_lim(0.0),
    axis_a_type(AT_DISABLED),
    axis_a_max_vel(0.0),
    axis_a_acc(0.0),
    axis_a_min_lim(0.0),
    axis_a_max_lim(0.0),
    axis_b_type(AT_DISABLED),
    axis_b_max_vel(0.0),
    axis_b_acc(0.0),
    axis_b_min_lim(0.0),
    axis_b_max_lim(0.0),
    axis_c_type(AT_DISABLED),
    axis_c_max_vel(0.0),
    axis_c_acc(0.0),
    axis_c_min_lim(0.0),
    axis_c_max_lim(0.0),
    kinematics_h_x(0.0),
    kinematics_h_y(0.0),
    kinematics_h_z(0.0),
    kinematics_j_x(0.0),
    kinematics_j_y(0.0),
    kinematics_j_z(0.0) {}

// ========== APIMachiningInfo Constructor ==========
APIMachiningInfo::APIMachiningInfo() :
    has_data(false),
    tool_path_in_fast(0.0),
    tool_path_in_feed(0.0),
    total_path(0.0),
    planned_time("00:00:00"),
    tcp_extents_in_fast_min_x(0.0),
    tcp_extents_in_fast_min_y(0.0),
    tcp_extents_in_fast_min_z(0.0),
    tcp_extents_in_fast_max_x(0.0),
    tcp_extents_in_fast_max_y(0.0),
    tcp_extents_in_fast_max_z(0.0),
    tcp_extents_in_fast_length_x(0.0),
    tcp_extents_in_fast_length_y(0.0),
    tcp_extents_in_fast_length_z(0.0),
    tcp_extents_in_feed_min_x(0.0),
    tcp_extents_in_feed_min_y(0.0),
    tcp_extents_in_feed_min_z(0.0),
    tcp_extents_in_feed_max_x(0.0),
    tcp_extents_in_feed_max_y(0.0),
    tcp_extents_in_feed_max_z(0.0),
    tcp_extents_in_feed_length_x(0.0),
    tcp_extents_in_feed_length_y(0.0),
    tcp_extents_in_feed_length_z(0.0),
    joints_in_fast_min_x(0.0),
    joints_in_fast_min_y(0.0),
    joints_in_fast_min_z(0.0),
    joints_in_fast_min_a(0.0),
    joints_in_fast_min_b(0.0),
    joints_in_fast_min_c(0.0),
    joints_in_fast_max_x(0.0),
    joints_in_fast_max_y(0.0),
    joints_in_fast_max_z(0.0),
    joints_in_fast_max_a(0.0),
    joints_in_fast_max_b(0.0),
    joints_in_fast_max_c(0.0),
    joints_in_fast_length_x(0.0),
    joints_in_fast_length_y(0.0),
    joints_in_fast_length_z(0.0),
    joints_in_fast_length_a(0.0),
    joints_in_fast_length_b(0.0),
    joints_in_fast_length_c(0.0),
    joints_in_feed_min_x(0.0),
    joints_in_feed_min_y(0.0),
    joints_in_feed_min_z(0.0),
    joints_in_feed_min_a(0.0),
    joints_in_feed_min_b(0.0),
    joints_in_feed_min_c(0.0),
    joints_in_feed_max_x(0.0),
    joints_in_feed_max_y(0.0),
    joints_in_feed_max_z(0.0),
    joints_in_feed_max_a(0.0),
    joints_in_feed_max_b(0.0),
    joints_in_feed_max_c(0.0),
    joints_in_feed_length_x(0.0),
    joints_in_feed_length_y(0.0),
    joints_in_feed_length_z(0.0),
    joints_in_feed_length_a(0.0),
    joints_in_feed_length_b(0.0),
    joints_in_feed_length_c(0.0) {}

// ========== APIToolsLibInfoForGet Constructor ==========
APIToolsLibInfoForGet::APIToolsLibInfoForGet() :
    tool_index(0),
    tool_id(0),
    tool_slot(false),
    tool_type(TT_GENERIC),
    tool_diameter(0.0),
    tool_offset_x(0.0),
    tool_offset_y(0.0),
    tool_offset_z(0.0),
    tool_param_1(0.0),
    tool_param_2(0.0),
    tool_param_3(0.0),
    tool_param_4(0.0),
    tool_param_5(0.0),
    tool_param_6(0.0),
    tool_param_7(0.0),
    tool_param_8(0.0),
    tool_param_9(0.0),
    tool_param_10(0.0),
    tool_param_51(0.0),
    tool_param_52(0.0),
    tool_param_53(0.0),
    tool_param_54(0.0),
    tool_param_55(0.0),
    tool_param_56(0.0),
    tool_param_57(0.0),
    tool_param_58(0.0),
    tool_param_59(0.0),
    tool_param_60(0.0) {}

// ========== APIToolsLibInfoForSet Constructor & Destructor ==========
APIToolsLibInfoForSet::APIToolsLibInfoForSet() :
    tool_index(nullptr), tool_id(nullptr), tool_slot(nullptr), tool_type(nullptr),
    tool_diameter(nullptr), tool_offset_x(nullptr), tool_offset_y(nullptr), tool_offset_z(nullptr),
    tool_param_1(nullptr), tool_param_2(nullptr), tool_param_3(nullptr), tool_param_4(nullptr),
    tool_param_5(nullptr), tool_param_6(nullptr), tool_param_7(nullptr), tool_param_8(nullptr),
    tool_param_9(nullptr), tool_param_10(nullptr), tool_param_51(nullptr), tool_param_52(nullptr),
    tool_param_53(nullptr), tool_param_54(nullptr), tool_param_55(nullptr), tool_param_56(nullptr),
    tool_param_57(nullptr), tool_param_58(nullptr), tool_param_59(nullptr), tool_param_60(nullptr),
    tool_description(nullptr) {}

APIToolsLibInfoForSet::~APIToolsLibInfoForSet() {
    delete tool_index;
    delete tool_id;
    delete tool_slot;
    delete tool_type;
    delete tool_diameter;
    delete tool_offset_x;
    delete tool_offset_y;
    delete tool_offset_z;
    delete tool_param_1;
    delete tool_param_2;
    delete tool_param_3;
    delete tool_param_4;
    delete tool_param_5;
    delete tool_param_6;
    delete tool_param_7;
    delete tool_param_8;
    delete tool_param_9;
    delete tool_param_10;
    delete tool_param_51;
    delete tool_param_52;
    delete tool_param_53;
    delete tool_param_54;
    delete tool_param_55;
    delete tool_param_56;
    delete tool_param_57;
    delete tool_param_58;
    delete tool_param_59;
    delete tool_param_60;
    delete tool_description;
}

// ========== APIVMGeometryInfo Constructor ==========
APIVMGeometryInfo::APIVMGeometryInfo() :
    has_data(false),
    x(0.0), y(0.0), z(0.0),
    color(0),
    scale(0.0),
    visible(false),
    edges_angle(0.0),
    edges_visible(false) {}

// ========== APIWorkInfo Constructor ==========
APIWorkInfo::APIWorkInfo() :
    has_data(false),
    work_mode(WM_NORMAL),
    active_work_order_file_index(-1),
    planned_time("00:00:00"),
    worked_time("00:00:00") {}

// ========== APIWorkOrderDataForAdd Constructors & Destructors ==========
APIWorkOrderDataForAdd::FileData::FileData() :
    file_name(nullptr), pieces_per_file(nullptr), requested_pieces(nullptr) {}

APIWorkOrderDataForAdd::FileData::~FileData() {
    delete file_name;
    delete pieces_per_file;
    delete requested_pieces;
}

APIWorkOrderDataForAdd::FileData::FileData(FileData&& other) noexcept :
    file_name(other.file_name), pieces_per_file(other.pieces_per_file),
    requested_pieces(other.requested_pieces) {
    other.file_name = nullptr; other.pieces_per_file = nullptr; other.requested_pieces = nullptr;
}

APIWorkOrderDataForAdd::FileData& APIWorkOrderDataForAdd::FileData::operator=(FileData&& other) noexcept {
    if (this != &other) {
        delete file_name; delete pieces_per_file; delete requested_pieces;
        file_name = other.file_name; pieces_per_file = other.pieces_per_file;
        requested_pieces = other.requested_pieces;
        other.file_name = nullptr; other.pieces_per_file = nullptr; other.requested_pieces = nullptr;
    }
    return *this;
}

APIWorkOrderDataForAdd::APIWorkOrderDataForAdd() :
    order_locked(nullptr),
    order_priority(nullptr),
    job_order_code(nullptr),
    customer_code(nullptr),
    item_code(nullptr),
    material_code(nullptr),
    order_notes(nullptr),
    use_deadline_datetime(nullptr),
    deadline_datetime(nullptr) {
    files.resize(8);
}

APIWorkOrderDataForAdd::~APIWorkOrderDataForAdd() {
    delete order_locked;
    delete order_priority;
    delete job_order_code;
    delete customer_code;
    delete item_code;
    delete material_code;
    delete order_notes;
    delete use_deadline_datetime;
    delete deadline_datetime;
}

// ========== APIWorkOrderDataForGet Constructors ==========
APIWorkOrderDataForGet::FileData::FileData() :
    file_state(WO_FS_CLOSED),
    pieces_per_file(0),
    requested_pieces(0),
    produced_pieces(0),
    discarded_pieces(0) {}

APIWorkOrderDataForGet::LogItemData::LogItemData() :
    log_id(WO_LI_NONE) {}

APIWorkOrderDataForGet::APIWorkOrderDataForGet() :
    has_data(false),
    revision_number(0),
    order_state(WO_ST_DRAFT),
    order_locked(false),
    order_priority(WO_PR_NORMAL),
    use_deadline_datetime(false),
    time_for_setup(0),
    time_for_idle(0),
    time_for_work(0),
    time_total(0) {
    files.resize(8);
}

// ========== APIWorkOrderDataForSet Constructors & Destructors ==========
APIWorkOrderDataForSet::FileData::FileData() :
    file_name(nullptr), pieces_per_file(nullptr), requested_pieces(nullptr) {}

APIWorkOrderDataForSet::FileData::~FileData() {
    delete file_name;
    delete pieces_per_file;
    delete requested_pieces;
}

APIWorkOrderDataForSet::FileData::FileData(FileData&& other) noexcept :
    file_name(other.file_name), pieces_per_file(other.pieces_per_file),
    requested_pieces(other.requested_pieces) {
    other.file_name = nullptr; other.pieces_per_file = nullptr; other.requested_pieces = nullptr;
}

APIWorkOrderDataForSet::FileData& APIWorkOrderDataForSet::FileData::operator=(FileData&& other) noexcept {
    if (this != &other) {
        delete file_name; delete pieces_per_file; delete requested_pieces;
        file_name = other.file_name; pieces_per_file = other.pieces_per_file;
        requested_pieces = other.requested_pieces;
        other.file_name = nullptr; other.pieces_per_file = nullptr; other.requested_pieces = nullptr;
    }
    return *this;
}

APIWorkOrderDataForSet::APIWorkOrderDataForSet() :
    order_state(nullptr),
    order_locked(nullptr),
    order_priority(nullptr),
    job_order_code(nullptr),
    customer_code(nullptr),
    item_code(nullptr),
    material_code(nullptr),
    order_notes(nullptr),
    use_deadline_datetime(nullptr),
    deadline_datetime(nullptr) {
    files.resize(8);
}

APIWorkOrderDataForSet::~APIWorkOrderDataForSet() {
    delete order_state;
    delete order_locked;
    delete order_priority;
    delete job_order_code;
    delete customer_code;
    delete item_code;
    delete material_code;
    delete order_notes;
    delete use_deadline_datetime;
    delete deadline_datetime;
}

// ========== APISystemInfo Methods ==========
bool APISystemInfo::is_equal(const APISystemInfo& data) const {
    return machine_name == data.machine_name &&
           control_software_version == data.control_software_version &&
           core_version == data.core_version &&
           api_server_version == data.api_server_version &&
           firmware_version == data.firmware_version &&
           firmware_version_tag == data.firmware_version_tag &&
           firmware_interface_level == data.firmware_interface_level &&
           order_code == data.order_code &&
           customer_id == data.customer_id &&
           serial_number == data.serial_number &&
           part_number == data.part_number &&
           customization_number == data.customization_number &&
           hardware_version == data.hardware_version &&
           operative_system == data.operative_system &&
           operative_system_crc == data.operative_system_crc &&
           pld_version == data.pld_version &&
           licensed_feature_panel_pc == data.licensed_feature_panel_pc &&
           licensed_feature_panel_pc_demo == data.licensed_feature_panel_pc_demo &&
           licensed_feature_work_orders == data.licensed_feature_work_orders &&
           licensed_feature_opc_ua_server == data.licensed_feature_opc_ua_server &&
           licensed_feature_probe_sdk_g1 == data.licensed_feature_probe_sdk_g1 &&
           licensed_feature_probe_sdk_g2 == data.licensed_feature_probe_sdk_g2 &&
           licensed_feature_probe_sdk_g3 == data.licensed_feature_probe_sdk_g3 &&
           licensed_feature_probe_sdk_g4 == data.licensed_feature_probe_sdk_g4 &&
           licensed_feature_probe_sdk_g5 == data.licensed_feature_probe_sdk_g5;
}

bool APISystemInfo::are_equal(const APISystemInfo& data_a, const APISystemInfo& data_b) {
    return data_a.is_equal(data_b);
}

// ========== CncAPIClientCore Constructor & Destructor ==========
CncAPIClientCore::CncAPIClientCore() :
    m_socket(INVALID_SOCKET),
    m_is_connected(false),
    m_use_ssl(false),
    m_use_cnc_direct_access(false),
    m_port(0),
    m_last_response(""),
    m_force_sync_state(std::make_shared<ForceSyncState>()),
    m_ssl_initialized(false) {
    
    initialize_winsock();
    ZeroMemory(&m_cred_handle, sizeof(m_cred_handle));
    ZeroMemory(&m_context_handle, sizeof(m_context_handle));
    ZeroMemory(&m_ssl_stream_sizes, sizeof(m_ssl_stream_sizes));
}

CncAPIClientCore::~CncAPIClientCore() {
    close();
}

// ========== Winsock Management ==========
bool CncAPIClientCore::initialize_winsock() {
    if (s_winsock_initialized) {
        return true;
    }
    
    WSADATA wsaData;
    int result = WSAStartup(MAKEWORD(2, 2), &wsaData);
    if (result != 0) {
        std::cerr << "WSAStartup failed: " << result << std::endl;
        return false;
    }
    
    s_winsock_initialized = true;
    return true;
}

void CncAPIClientCore::cleanup_winsock() {
    if (s_winsock_initialized) {
        WSACleanup();
        s_winsock_initialized = false;
    }
}

// ========== Connection Management ==========
bool CncAPIClientCore::connect(const std::string& host, int port, bool use_ssl) {
    if (m_is_connected) {
        return true;
    }
    
    try {
        m_host = host;
        m_port = port;
        m_use_ssl = use_ssl;
        
        // Create socket
        m_socket = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
        if (m_socket == INVALID_SOCKET) {
            std::cerr << "Socket creation failed: " << WSAGetLastError() << std::endl;
            return false;
        }
        
        // Resolve host
        struct addrinfo hints = {0}, *result_addr = nullptr;
        hints.ai_family = AF_INET;
        hints.ai_socktype = SOCK_STREAM;
        hints.ai_protocol = IPPROTO_TCP;
        
        std::string port_str = std::to_string(port);
        if (getaddrinfo(host.c_str(), port_str.c_str(), &hints, &result_addr) != 0) {
            std::cerr << "getaddrinfo failed: " << WSAGetLastError() << std::endl;
            closesocket(m_socket);
            m_socket = INVALID_SOCKET;
            m_host.clear(); m_port = 0; m_use_ssl = false;
            return false;
        }
        
        // Connect
        if (::connect(m_socket, result_addr->ai_addr, (int)result_addr->ai_addrlen) == SOCKET_ERROR) {
            std::cerr << "Connection failed: " << WSAGetLastError() << std::endl;
            freeaddrinfo(result_addr);
            closesocket(m_socket);
            m_socket = INVALID_SOCKET;
            m_host.clear(); m_port = 0; m_use_ssl = false;
            return false;
        }
        
        freeaddrinfo(result_addr);
        
        // If SSL is enabled, perform SSL handshake
        if (use_ssl) {
            if (!initialize_ssl() || !ssl_handshake()) {
                cleanup_ssl();
                closesocket(m_socket);
                m_socket = INVALID_SOCKET;
                m_host.clear(); m_port = 0; m_use_ssl = false;
                return false;
            }
        }
        
        m_is_connected = true;
        return true;
    } catch (...) {
        m_is_connected = false;
        if (m_socket != INVALID_SOCKET) {
            closesocket(m_socket);
            m_socket = INVALID_SOCKET;
        }
        m_host.clear(); m_port = 0; m_use_ssl = false; m_socket_ssl_info.clear();
        return false;
    }
}

bool CncAPIClientCore::connect_direct() {
    // The Python implementation delegates this mode to the external,
    // proprietary `cnc_direct_access` module.  No equivalent backend or ABI is
    // part of this repository, so reporting a successful connection here would
    // create a connection that can never execute a request.
    return false;
}

std::unique_ptr<CncAPIClientCore> CncAPIClientCore::connection_clone() const {
    std::unique_ptr<CncAPIClientCore> clone(new CncAPIClientCore());
    if (!m_is_connected || m_use_cnc_direct_access ||
        !clone->connect(m_host, m_port, m_use_ssl)) {
        return std::unique_ptr<CncAPIClientCore>();
    }
    return clone;
}

bool CncAPIClientCore::close() {
    stop_force_sync_worker();
    if (m_is_connected) {
        try {
            if (!m_use_cnc_direct_access) {
                if (m_use_ssl && m_ssl_initialized) {
                    cleanup_ssl();
                }
                if (m_socket != INVALID_SOCKET) {
                    closesocket(m_socket);
                    m_socket = INVALID_SOCKET;
                }
            }
            m_use_cnc_direct_access = false;
            m_is_connected = false;
            m_host.clear();
            m_port = 0;
            m_use_ssl = false;
            m_socket_ssl_info.clear();
            return true;
        } catch (...) {
            m_use_cnc_direct_access = false;
            m_is_connected = false;
            m_host.clear();
            m_port = 0;
            m_use_ssl = false;
            m_socket_ssl_info.clear();
            if (m_socket != INVALID_SOCKET) {
                closesocket(m_socket);
                m_socket = INVALID_SOCKET;
            }
            return false;
        }
    }
    m_host.clear();
    m_port = 0;
    m_use_ssl = false;
    m_socket_ssl_info.clear();
    return true;
}

// ========== SSL/TLS Methods ==========
bool CncAPIClientCore::initialize_ssl() {
    // Initialize Schannel credentials for TLS 1.2
    SCHANNEL_CRED schannel_cred = {0};
    schannel_cred.dwVersion = SCHANNEL_CRED_VERSION;
    schannel_cred.grbitEnabledProtocols = SP_PROT_TLS1_2_CLIENT;
    schannel_cred.dwFlags = SCH_CRED_NO_DEFAULT_CREDS | SCH_CRED_AUTO_CRED_VALIDATION;
    
    // Use const_cast for UNISP_NAME_A as required by AcquireCredentialsHandleA
    SECURITY_STATUS status = AcquireCredentialsHandleA(
        nullptr,
        const_cast<char*>(UNISP_NAME_A),
        SECPKG_CRED_OUTBOUND,
        nullptr,
        &schannel_cred,
        nullptr,
        nullptr,
        &m_cred_handle,
        nullptr
    );
    
    if (status != SEC_E_OK) {
        std::cerr << "AcquireCredentialsHandle failed: " << status << std::endl;
        return false;
    }
    
    m_ssl_initialized = true;
    return true;
}

void CncAPIClientCore::cleanup_ssl() {
    if (m_ssl_initialized) {
        DeleteSecurityContext(&m_context_handle);
        FreeCredentialsHandle(&m_cred_handle);
        m_ssl_initialized = false;
        m_ssl_received.clear();
        m_socket_ssl_info.clear();
    }
}

bool CncAPIClientCore::ssl_handshake() {
    const DWORD flags = ISC_REQ_SEQUENCE_DETECT | ISC_REQ_REPLAY_DETECT |
        ISC_REQ_CONFIDENTIALITY | ISC_RET_EXTENDED_ERROR |
        ISC_REQ_ALLOCATE_MEMORY | ISC_REQ_STREAM;
    DWORD out_flags = 0;
    TimeStamp expiry = {};
    std::vector<unsigned char> incoming;
    bool have_context = false;

    for (;;) {
        SecBuffer out = {0, SECBUFFER_TOKEN, nullptr};
        SecBufferDesc out_desc = {SECBUFFER_VERSION, 1, &out};
        SecBuffer in[2] = {};
        SecBufferDesc in_desc = {SECBUFFER_VERSION, 2, in};
        SecBufferDesc* input = nullptr;
        if (!incoming.empty()) {
            in[0].BufferType = SECBUFFER_TOKEN;
            in[0].pvBuffer = incoming.data();
            in[0].cbBuffer = static_cast<unsigned long>(incoming.size());
            in[1].BufferType = SECBUFFER_EMPTY;
            input = &in_desc;
        }

        SECURITY_STATUS status = InitializeSecurityContextA(
            &m_cred_handle, have_context ? &m_context_handle : nullptr,
            const_cast<char*>(m_host.c_str()), flags, 0, SECURITY_NATIVE_DREP,
            input, 0, &m_context_handle, &out_desc, &out_flags, &expiry);
        have_context = true;

        if (out.pvBuffer && out.cbBuffer) {
            size_t sent = 0;
            while (sent < out.cbBuffer) {
                const int count = send(m_socket,
                    static_cast<const char*>(out.pvBuffer) + sent,
                    static_cast<int>(out.cbBuffer - sent), 0);
                if (count <= 0) {
                    FreeContextBuffer(out.pvBuffer);
                    return false;
                }
                sent += static_cast<size_t>(count);
            }
            FreeContextBuffer(out.pvBuffer);
        }

        if (status == SEC_E_OK) {
            if (input && in[1].BufferType == SECBUFFER_EXTRA) {
                const size_t extra = in[1].cbBuffer;
                m_ssl_received.assign(incoming.end() - extra, incoming.end());
            } else {
                m_ssl_received.clear();
            }
            break;
        }
        if (status != SEC_I_CONTINUE_NEEDED && status != SEC_E_INCOMPLETE_MESSAGE) {
            std::cerr << "TLS handshake failed: " << status << std::endl;
            return false;
        }
        if (status == SEC_I_CONTINUE_NEEDED && input) {
            if (in[1].BufferType == SECBUFFER_EXTRA) {
                const size_t extra = in[1].cbBuffer;
                std::vector<unsigned char> remainder(incoming.end() - extra, incoming.end());
                incoming.swap(remainder);
                continue;
            } else {
                incoming.clear();
            }
        }
        unsigned char buffer[16384];
        const int received = recv(m_socket, reinterpret_cast<char*>(buffer), sizeof(buffer), 0);
        if (received <= 0) return false;
        incoming.insert(incoming.end(), buffer, buffer + received);
    }

    if (QueryContextAttributes(&m_context_handle, SECPKG_ATTR_STREAM_SIZES,
                               &m_ssl_stream_sizes) != SEC_E_OK) return false;
    SecPkgContext_ConnectionInfo info = {};
    if (QueryContextAttributes(&m_context_handle, SECPKG_ATTR_CONNECTION_INFO, &info) == SEC_E_OK) {
        std::ostringstream text;
        text << "TLS | cipher " << info.aiCipher << " | " << info.dwCipherStrength << " bit";
        m_socket_ssl_info = text.str();
    } else {
        m_socket_ssl_info = "TLS";
    }
    return true;
}

bool CncAPIClientCore::ssl_send_data(const std::string& data) {
    size_t offset = 0;
    while (offset < data.size()) {
        const size_t plain_size = (std::min)(data.size() - offset,
            static_cast<size_t>(m_ssl_stream_sizes.cbMaximumMessage));
        std::vector<unsigned char> packet(m_ssl_stream_sizes.cbHeader + plain_size +
                                          m_ssl_stream_sizes.cbTrailer);
        std::memcpy(packet.data() + m_ssl_stream_sizes.cbHeader, data.data() + offset, plain_size);
        SecBuffer buffers[4] = {};
        buffers[0] = {m_ssl_stream_sizes.cbHeader, SECBUFFER_STREAM_HEADER, packet.data()};
        buffers[1] = {static_cast<unsigned long>(plain_size), SECBUFFER_DATA,
                      packet.data() + m_ssl_stream_sizes.cbHeader};
        buffers[2] = {m_ssl_stream_sizes.cbTrailer, SECBUFFER_STREAM_TRAILER,
                      packet.data() + m_ssl_stream_sizes.cbHeader + plain_size};
        buffers[3].BufferType = SECBUFFER_EMPTY;
        SecBufferDesc desc = {SECBUFFER_VERSION, 4, buffers};
        if (EncryptMessage(&m_context_handle, 0, &desc, 0) != SEC_E_OK) return false;
        const size_t packet_size = buffers[0].cbBuffer + buffers[1].cbBuffer + buffers[2].cbBuffer;
        size_t sent = 0;
        while (sent < packet_size) {
            const int count = send(m_socket, reinterpret_cast<const char*>(packet.data()) + sent,
                                   static_cast<int>(packet_size - sent), 0);
            if (count <= 0) return false;
            sent += static_cast<size_t>(count);
        }
        offset += plain_size;
    }

    return true;
}

bool CncAPIClientCore::ssl_receive_plaintext(std::vector<unsigned char>& plaintext) {
    plaintext.clear();

    for (;;) {
        if (!m_ssl_received.empty()) {
            SecBuffer buffers[4] = {};
            buffers[0] = {static_cast<unsigned long>(m_ssl_received.size()), SECBUFFER_DATA,
                          m_ssl_received.data()};
            for (int i = 1; i < 4; ++i) buffers[i].BufferType = SECBUFFER_EMPTY;
            SecBufferDesc desc = {SECBUFFER_VERSION, 4, buffers};
            const SECURITY_STATUS status = DecryptMessage(&m_context_handle, &desc, 0, nullptr);
            if (status == SEC_E_OK) {
                std::vector<unsigned char> extra;
                for (int i = 1; i < 4; ++i) {
                    if (buffers[i].BufferType == SECBUFFER_DATA && buffers[i].cbBuffer) {
                        const unsigned char* begin =
                            static_cast<const unsigned char*>(buffers[i].pvBuffer);
                        plaintext.insert(plaintext.end(), begin, begin + buffers[i].cbBuffer);
                    } else if (buffers[i].BufferType == SECBUFFER_EXTRA && buffers[i].cbBuffer) {
                        const unsigned char* begin =
                            static_cast<const unsigned char*>(buffers[i].pvBuffer);
                        extra.assign(begin, begin + buffers[i].cbBuffer);
                    }
                }
                m_ssl_received.swap(extra);
                if (!plaintext.empty()) return true;
                continue;
            }
            if (status == SEC_I_CONTEXT_EXPIRED) return false;
            if (status != SEC_E_INCOMPLETE_MESSAGE) return false;
        }

        unsigned char input[65536];
        const int received = recv(m_socket, reinterpret_cast<char*>(input), sizeof(input), 0);
        if (received <= 0) return false;
        m_ssl_received.insert(m_ssl_received.end(), input, input + received);
    }
}

std::string CncAPIClientCore::ssl_send_receive(const std::string& data,
                                               DWORD first_timeout_ms,
                                               DWORD chunk_timeout_ms) {
    if (!ssl_send_data(data)) return "";

    std::string plaintext;
    DWORD timeout = first_timeout_ms;
    setsockopt(m_socket, SOL_SOCKET, SO_RCVTIMEO, reinterpret_cast<const char*>(&timeout), sizeof(timeout));
    for (;;) {
        std::vector<unsigned char> chunk;
        if (!ssl_receive_plaintext(chunk)) return "";
        plaintext.append(reinterpret_cast<const char*>(chunk.data()), chunk.size());
        const size_t newline = plaintext.find('\n');
        if (newline != std::string::npos) {
            m_last_response = plaintext.substr(0, newline);
            return m_last_response;
        }
        timeout = chunk_timeout_ms;
        setsockopt(m_socket, SOL_SOCKET, SO_RCVTIMEO,
                   reinterpret_cast<const char*>(&timeout), sizeof(timeout));
    }
}

bool CncAPIClientCore::ssl_send_receive_raw(const std::string& data,
                                            std::vector<unsigned char>& payload,
                                            DWORD first_timeout_ms,
                                            DWORD chunk_timeout_ms) {
    if (!ssl_send_data(data)) return false;

    DWORD timeout = first_timeout_ms;
    setsockopt(m_socket, SOL_SOCKET, SO_RCVTIMEO,
               reinterpret_cast<const char*>(&timeout), sizeof(timeout));

    std::vector<unsigned char> plaintext;
    size_t payload_offset = std::string::npos;
    size_t expected_size = 0;
    for (;;) {
        std::vector<unsigned char> chunk;
        if (!ssl_receive_plaintext(chunk)) return false;
        plaintext.insert(plaintext.end(), chunk.begin(), chunk.end());

        if (payload_offset == std::string::npos) {
            const std::vector<unsigned char>::iterator newline =
                std::find(plaintext.begin(), plaintext.end(), static_cast<unsigned char>('\n'));
            if (newline != plaintext.end()) {
                payload_offset = static_cast<size_t>(newline - plaintext.begin()) + 1;
                const std::string header(plaintext.begin(), newline);
                m_last_response = header;
                const int64_t data_size = json_to_int64(
                    SimpleJSON::Parser::get_nested_value(header, "res", "data_size"), -1);
                if (data_size < 0 || static_cast<uint64_t>(data_size) >
                        static_cast<uint64_t>(std::numeric_limits<size_t>::max())) {
                    return false;
                }
                expected_size = static_cast<size_t>(data_size);
            }
        }

        if (payload_offset != std::string::npos &&
            plaintext.size() >= payload_offset &&
            expected_size <= plaintext.size() - payload_offset) {
            payload.assign(plaintext.begin() + payload_offset,
                           plaintext.begin() + payload_offset + expected_size);
            return true;
        }

        timeout = chunk_timeout_ms;
        setsockopt(m_socket, SOL_SOCKET, SO_RCVTIMEO,
                   reinterpret_cast<const char*>(&timeout), sizeof(timeout));
    }
}

// ========== Communication Methods ==========
void CncAPIClientCore::flush_receiving_buffer() {
    if (!m_is_connected || m_socket == INVALID_SOCKET) {
        return;
    }
    
    try {
        m_ssl_received.clear();
        // Set non-blocking mode temporarily
        u_long mode = 1;
        ioctlsocket(m_socket, FIONBIO, &mode);
        
        char buffer[4096];
        size_t flushed = 0;
        const size_t max_flush = 1024 * 1024;
        while (flushed < max_flush) {
            const int received = recv(m_socket, buffer, sizeof(buffer), 0);
            if (received <= 0) break;
            flushed += static_cast<size_t>(received);
        }
        
        // Set back to blocking mode
        mode = 0;
        ioctlsocket(m_socket, FIONBIO, &mode);
    } catch (...) {
        // Ignore errors during flush
    }
}

std::string CncAPIClientCore::send_command(const std::string& request, DWORD first_timeout_ms,
                                           DWORD chunk_timeout_ms) {
    if (!m_is_connected) {
        return "";
    }
    
    if (request.empty()) {
        return "";
    }
    
    // Ensure request ends with newline
    std::string cmd = request;
    if (cmd.back() != '\n') {
        cmd += '\n';
    }
    
    // Handle direct access mode
    if (m_use_cnc_direct_access) {
        // Placeholder for direct access
        // In Python: return cda.api_server_request(request)
        return "";
    }
    
    try {
        // Flush buffer before sending
        flush_receiving_buffer();
        
        // Send request
        if (m_use_ssl && m_ssl_initialized) {
            // Use SSL send
            return ssl_send_receive(cmd, first_timeout_ms, chunk_timeout_ms);
        } else {
            // Regular socket send
            size_t sent = 0;
            while (sent < cmd.size()) {
                const int send_result = send(m_socket, cmd.data() + sent,
                                             static_cast<int>(cmd.size() - sent), 0);
                if (send_result == SOCKET_ERROR || send_result == 0) {
                    std::cerr << "Send failed: " << WSAGetLastError() << std::endl;
                    close();
                    return "";
                }
                sent += static_cast<size_t>(send_result);
            }
        }
        
        // Receive response
        std::string response;
        char buffer[65536];
        
        // Set the caller-selected timeout for the first byte.
        DWORD timeout_ms = first_timeout_ms;
        setsockopt(m_socket, SOL_SOCKET, SO_RCVTIMEO, (const char*)&timeout_ms, sizeof(timeout_ms));
        
        while (true) {
            const int bytes_received = recv(m_socket, buffer, sizeof(buffer), 0);
            
            if (bytes_received <= 0) {
                if (bytes_received == 0) close();
                else if (WSAGetLastError() != WSAETIMEDOUT) close();
                break;
            }
            
            // Switch to the caller-selected timeout for subsequent chunks.
            timeout_ms = chunk_timeout_ms;
            setsockopt(m_socket, SOL_SOCKET, SO_RCVTIMEO, (const char*)&timeout_ms, sizeof(timeout_ms));
            
            const char* newline = static_cast<const char*>(
                std::memchr(buffer, '\n', static_cast<size_t>(bytes_received)));
            if (newline != nullptr) {
                response.append(buffer, static_cast<size_t>(newline - buffer));
                break;
            }

            response.append(buffer, static_cast<size_t>(bytes_received));
        }
        
        m_last_response = response;  // Store for debugging
        return response;
    } catch (...) {
        close();
        return "";
    }
}

bool CncAPIClientCore::send_command_raw(const std::string& request,
                                        std::vector<unsigned char>& payload,
                                        DWORD first_timeout_ms,
                                        DWORD chunk_timeout_ms) {
    payload.clear();
    if (!m_is_connected || request.empty() || m_use_cnc_direct_access) {
        return false;
    }

    std::string cmd = request;
    if (cmd.back() != '\n') cmd += '\n';

    try {
        flush_receiving_buffer();

        if (m_use_ssl && m_ssl_initialized) {
            return ssl_send_receive_raw(cmd, payload, first_timeout_ms, chunk_timeout_ms);
        }

        size_t sent = 0;
        while (sent < cmd.size()) {
            const int result = send(m_socket, cmd.data() + sent,
                                    static_cast<int>(cmd.size() - sent), 0);
            if (result == SOCKET_ERROR || result == 0) {
                close();
                return false;
            }
            sent += static_cast<size_t>(result);
        }

        DWORD timeout_ms = first_timeout_ms;
        setsockopt(m_socket, SOL_SOCKET, SO_RCVTIMEO,
                   reinterpret_cast<const char*>(&timeout_ms), sizeof(timeout_ms));

        std::string header;
        std::vector<unsigned char> received_payload;
        char buffer[65536];
        bool header_complete = false;

        while (!header_complete) {
            const int count = recv(m_socket, buffer, sizeof(buffer), 0);
            if (count <= 0) return false;

            timeout_ms = chunk_timeout_ms;
            setsockopt(m_socket, SOL_SOCKET, SO_RCVTIMEO,
                       reinterpret_cast<const char*>(&timeout_ms), sizeof(timeout_ms));

            const char* newline = static_cast<const char*>(
                std::memchr(buffer, '\n', static_cast<size_t>(count)));
            if (newline == nullptr) {
                header.append(buffer, static_cast<size_t>(count));
                continue;
            }

            const size_t header_part = static_cast<size_t>(newline - buffer);
            header.append(buffer, header_part);
            const size_t payload_part = static_cast<size_t>(count) - header_part - 1;
            if (payload_part > 0) {
                const unsigned char* begin = reinterpret_cast<const unsigned char*>(newline + 1);
                received_payload.insert(received_payload.end(), begin, begin + payload_part);
            }
            header_complete = true;
        }

        m_last_response = header;
        const int64_t data_size = json_to_int64(
            SimpleJSON::Parser::get_nested_value(header, "res", "data_size"), -1);
        if (data_size < 0 || static_cast<uint64_t>(data_size) >
                static_cast<uint64_t>(std::numeric_limits<size_t>::max())) {
            return false;
        }

        const size_t expected_size = static_cast<size_t>(data_size);
        while (received_payload.size() < expected_size) {
            const size_t remaining = expected_size - received_payload.size();
            const int count = recv(m_socket, buffer,
                                   static_cast<int>((std::min)(remaining, sizeof(buffer))), 0);
            if (count <= 0) return false;
            const unsigned char* begin = reinterpret_cast<const unsigned char*>(buffer);
            received_payload.insert(received_payload.end(), begin, begin + count);
        }

        if (received_payload.size() > expected_size) received_payload.resize(expected_size);
        payload.swap(received_payload);
        return true;
    } catch (...) {
        return false;
    }
}

bool CncAPIClientCore::evaluate_response(const std::string& response) {
    if (response.empty()) {
        return false;
    }
    
    try {
        const std::map<std::string, std::string> object =
            SimpleJSON::Parser::parse_object(response);
        const std::map<std::string, std::string>::const_iterator res = object.find("res");
        if (res == object.end()) return false;
        std::string value = SimpleJSON::Parser::trim(res->second);
        std::transform(value.begin(), value.end(), value.begin(),
                       [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
        return value == "true";
    } catch (...) {
        return false;
    }
}

bool CncAPIClientCore::execute_request(const std::string& request) {
    if (!m_is_connected) {
        return false;
    }
    
    try {
        std::string response = send_command(request);
        return evaluate_response(response);
    } catch (...) {
        return false;
    }
}

bool CncAPIClientCore::execute_force_sync_request(std::string request, bool force_sync,
                                                   double timeout) {
    if (!m_is_connected || request.empty() || request.back() != '}') return false;
    DWORD first_timeout_ms = static_cast<DWORD>(DEFAULT_REQUEST_FIRST_TIMEOUT * 1000.0);
    if (force_sync) {
        if (!valid_force_sync_timeout(timeout)) return false;
        request.insert(request.size() - 1, ",\"force.sync\":true");
        first_timeout_ms = static_cast<DWORD>(std::ceil(timeout * 1000.0));
    }
    return evaluate_response(send_command(request, first_timeout_ms));
}

bool CncAPIClientCore::start_force_sync_async_request(
        std::function<bool(CncAPIClientCore&)> worker_proc,
        CompletionCallback on_done) {
    if (!worker_proc || !m_is_connected || m_use_cnc_direct_access ||
        !m_force_sync_state) return false;

    bool expected = false;
    if (!m_force_sync_state->running.compare_exchange_strong(expected, true)) return false;

    if (m_force_sync_thread.joinable()) {
        if (m_force_sync_thread.get_id() == std::this_thread::get_id()) {
            m_force_sync_thread.detach();
        } else {
            m_force_sync_thread.join();
        }
    }

    std::shared_ptr<CncAPIClientCore> api = std::make_shared<CncAPIClientCore>();
    if (!api->connect(m_host, m_port, m_use_ssl)) {
        m_force_sync_state->running.store(false);
        return false;
    }
    {
        std::lock_guard<std::mutex> lock(m_force_sync_state->mutex);
        m_force_sync_state->api = api;
    }

    const std::shared_ptr<ForceSyncState> state = m_force_sync_state;
    try {
        m_force_sync_thread = std::thread([state, api, worker_proc, on_done]() {
            bool result = false;
            try {
                if (api->is_connected()) result = worker_proc(*api);
            } catch (...) {
                result = false;
            }
            {
                std::lock_guard<std::mutex> lock(state->mutex);
                if (state->api == api) {
                    api->close();
                    state->api.reset();
                }
            }
            state->running.store(false);
            try {
                if (on_done) on_done(result);
            } catch (...) {
                // Callback exceptions do not escape the worker thread.
            }
        });
        return true;
    } catch (...) {
        {
            std::lock_guard<std::mutex> lock(state->mutex);
            state->api.reset();
        }
        api->close();
        state->running.store(false);
        return false;
    }
}

void CncAPIClientCore::stop_force_sync_worker() {
    if (!m_force_sync_state) return;
    std::shared_ptr<CncAPIClientCore> api;
    {
        std::lock_guard<std::mutex> lock(m_force_sync_state->mutex);
        api = m_force_sync_state->api;
        m_force_sync_state->api.reset();
    }
    if (api) api->close();
    if (m_force_sync_thread.joinable()) {
        if (m_force_sync_thread.get_id() == std::this_thread::get_id()) {
            m_force_sync_thread.detach();
        } else {
            m_force_sync_thread.join();
        }
    }
    m_force_sync_state->running.store(false);
}

// ========== Helper Methods ==========
std::string CncAPIClientCore::escape_json_string(const std::string& str) {
    return SimpleJSON::escape(str);
}

DateTime CncAPIClientCore::filetime_to_datetime(int64_t filetime) {
    if (filetime < 0) return DateTime::min_value();
    ULARGE_INTEGER value;
    value.QuadPart = static_cast<ULONGLONG>(filetime);
    FILETIME ft;
    ft.dwLowDateTime = value.LowPart;
    ft.dwHighDateTime = value.HighPart;
    SYSTEMTIME st = {};
    if (!FileTimeToSystemTime(&ft, &st)) return DateTime::min_value();

    DateTime dt;
    dt.year = st.wYear;
    dt.month = st.wMonth;
    dt.day = st.wDay;
    dt.hour = st.wHour;
    dt.minute = st.wMinute;
    dt.second = st.wSecond;
    dt.microsecond = st.wMilliseconds * 1000 + static_cast<int>((value.QuadPart % 10000ULL) / 10ULL);
    return dt;
}

int64_t CncAPIClientCore::datetime_to_filetime(const DateTime& dt) {
    if (dt.microsecond < 0 || dt.microsecond > 999999) return 0;
    SYSTEMTIME st = {};
    st.wYear = static_cast<WORD>(dt.year);
    st.wMonth = static_cast<WORD>(dt.month);
    st.wDay = static_cast<WORD>(dt.day);
    st.wHour = static_cast<WORD>(dt.hour);
    st.wMinute = static_cast<WORD>(dt.minute);
    st.wSecond = static_cast<WORD>(dt.second);
    st.wMilliseconds = static_cast<WORD>(dt.microsecond / 1000);
    FILETIME ft = {};
    if (!SystemTimeToFileTime(&st, &ft)) return 0;
    ULARGE_INTEGER value;
    value.LowPart = ft.dwLowDateTime;
    value.HighPart = ft.dwHighDateTime;
    value.QuadPart += static_cast<ULONGLONG>(dt.microsecond % 1000) * 10ULL;
    if (value.QuadPart > static_cast<ULONGLONG>((std::numeric_limits<int64_t>::max)())) return 0;
    return static_cast<int64_t>(value.QuadPart);
}

std::string CncAPIClientCore::create_compact_json_request(const std::map<std::string, std::string>& data) {
    std::ostringstream json;
    json << "{";
    bool first = true;
    for (const auto& pair : data) {
        if (!first) json << ",";
        json << "\"" << pair.first << "\":\"" << escape_json_string(pair.second) << "\"";
        first = false;
    }
    json << "}";
    return json.str();
}

std::string CncAPIClientCore::build_json_string(const std::string& key, const std::string& value) {
    return "\"" + key + "\":\"" + escape_json_string(value) + "\"";
}

std::string CncAPIClientCore::build_json_int(const std::string& key, int value) {
    return "\"" + key + "\":" + std::to_string(value);
}

std::string CncAPIClientCore::build_json_double(const std::string& key, double value) {
    std::ostringstream oss;
    oss << "\"" << key << "\":" << std::fixed << std::setprecision(6) << value;
    return oss.str();
}

std::string CncAPIClientCore::build_json_bool(const std::string& key, bool value) {
    return "\"" + key + "\":" + (value ? "true" : "false");
}

// ========== API Command Methods ==========

bool CncAPIClientCore::cnc_change_function_state_mode(int name, int mode) {
    const bool digital_name = name == FS_NM_SPINDLE_CW || name == FS_NM_SPINDLE_CCW ||
        name == FS_NM_MIST || name == FS_NM_FLOOD || name == FS_NM_TORCH ||
        name == FS_NM_THC_DISABLED || (name >= FS_NM_AUX_01 && name <= FS_NM_AUX_32);
    const bool valid = (digital_name && mode >= FS_MD_OFF && mode <= FS_MD_TOGGLE) ||
        (name == FS_NM_JOG_MODE && mode >= FS_MD_JOG_MODE_DEFAULT &&
         mode <= FS_MD_JOG_MODE_TOGGLE);
    if (!valid) return false;
    return execute_request("{\"cmd\":\"cnc.change.function.state.mode\",\"name\":" +
                           std::to_string(name) + ",\"mode\":" + std::to_string(mode) + "}");
}

bool CncAPIClientCore::cnc_connection_close() {
    return execute_request("{\"cmd\":\"cnc.connection.close\"}");
}

bool CncAPIClientCore::cnc_connection_open(bool use_ui, bool use_fast_mode,
                                            bool skip_firmware_check,
                                            bool overwrite_cnc_settings) {
    return execute_request("{\"cmd\":\"cnc.connection.open\",\"use.ui\":" +
        std::string(use_ui ? "true" : "false") + ",\"use.fast.mode\":" +
        (use_fast_mode ? "true" : "false") + ",\"skip.firmware.check\":" +
        (skip_firmware_check ? "true" : "false") + ",\"overwrite.cnc.settings\":" +
        (overwrite_cnc_settings ? "true" : "false") + "}");
}

bool CncAPIClientCore::cnc_continue() {
    return execute_request("{\"cmd\":\"cnc.continue\"}");
}

bool CncAPIClientCore::cnc_homing(int axes_mask) {
    if (axes_mask <= 0 || axes_mask > X2C_AXIS_MASK) return false;
    return execute_request("{\"cmd\":\"cnc.homing\",\"axes.mask\":" +
                           std::to_string(axes_mask) + "}");
}

bool CncAPIClientCore::cnc_jog_command(int command) {
    if (command < JC_NONE || command > JC_C_FW) return false;
    return execute_request("{\"cmd\":\"cnc.jog.command\",\"command\":" +
                           std::to_string(command) + "}");
}

bool CncAPIClientCore::cnc_mdi_command(const std::string& command) {
    return execute_request("{\"cmd\":\"cnc.mdi.command\",\"command\":\"" +
                           escape_json_string(command) + "\"}");
}

bool CncAPIClientCore::cnc_pause() { return execute_request("{\"cmd\":\"cnc.pause\"}"); }

bool CncAPIClientCore::cnc_resume(bool force_sync, double timeout) {
    return execute_force_sync_request("{\"cmd\":\"cnc.resume\"}", force_sync, timeout);
}

bool CncAPIClientCore::cnc_resume_threaded(double timeout, CompletionCallback on_done) {
    if (!valid_force_sync_timeout(timeout)) return false;
    return start_force_sync_async_request(
        [timeout](CncAPIClientCore& api) { return api.cnc_resume(true, timeout); }, on_done);
}

bool CncAPIClientCore::cnc_resume_from_line(int line, bool force_sync, double timeout) {
    return execute_force_sync_request("{\"cmd\":\"cnc.resume.from.line\",\"line\":" +
        std::to_string(line) + "}", force_sync, timeout);
}

bool CncAPIClientCore::cnc_resume_from_line_threaded(int line, double timeout,
                                                      CompletionCallback on_done) {
    if (!valid_force_sync_timeout(timeout)) return false;
    return start_force_sync_async_request(
        [line, timeout](CncAPIClientCore& api) {
            return api.cnc_resume_from_line(line, true, timeout);
        }, on_done);
}

bool CncAPIClientCore::cnc_resume_from_point(int point, bool force_sync, double timeout) {
    return execute_force_sync_request("{\"cmd\":\"cnc.resume.from.point\",\"point\":" +
        std::to_string(point) + "}", force_sync, timeout);
}

bool CncAPIClientCore::cnc_resume_from_point_threaded(int point, double timeout,
                                                       CompletionCallback on_done) {
    if (!valid_force_sync_timeout(timeout)) return false;
    return start_force_sync_async_request(
        [point, timeout](CncAPIClientCore& api) {
            return api.cnc_resume_from_point(point, true, timeout);
        }, on_done);
}

bool CncAPIClientCore::cnc_start(bool force_sync, double timeout) {
    return execute_force_sync_request("{\"cmd\":\"cnc.start\"}", force_sync, timeout);
}

bool CncAPIClientCore::cnc_start_threaded(double timeout, CompletionCallback on_done) {
    if (!valid_force_sync_timeout(timeout)) return false;
    return start_force_sync_async_request(
        [timeout](CncAPIClientCore& api) { return api.cnc_start(true, timeout); }, on_done);
}

bool CncAPIClientCore::cnc_start_from_line(int line, bool force_sync, double timeout) {
    return execute_force_sync_request("{\"cmd\":\"cnc.start.from.line\",\"line\":" +
        std::to_string(line) + "}", force_sync, timeout);
}

bool CncAPIClientCore::cnc_start_from_line_threaded(int line, double timeout,
                                                     CompletionCallback on_done) {
    if (!valid_force_sync_timeout(timeout)) return false;
    return start_force_sync_async_request(
        [line, timeout](CncAPIClientCore& api) {
            return api.cnc_start_from_line(line, true, timeout);
        }, on_done);
}

bool CncAPIClientCore::cnc_start_from_point(int point, bool force_sync, double timeout) {
    return execute_force_sync_request("{\"cmd\":\"cnc.start.from.point\",\"point\":" +
        std::to_string(point) + "}", force_sync, timeout);
}

bool CncAPIClientCore::cnc_start_from_point_threaded(int point, double timeout,
                                                      CompletionCallback on_done) {
    if (!valid_force_sync_timeout(timeout)) return false;
    return start_force_sync_async_request(
        [point, timeout](CncAPIClientCore& api) {
            return api.cnc_start_from_point(point, true, timeout);
        }, on_done);
}

bool CncAPIClientCore::cnc_stop() { return execute_request("{\"cmd\":\"cnc.stop\"}"); }

#define FILE_COMMAND_BODY(command_name) \
    return execute_request("{\"cmd\":\"" command_name "\",\"file.name\":\"" + \
                           escape_json_string(file_name) + "\"}")
bool CncAPIClientCore::file_export_cpf(const std::string& file_name) {
    FILE_COMMAND_BODY("file.export.cpf");
}
bool CncAPIClientCore::file_export_csf(const std::string& file_name) {
    FILE_COMMAND_BODY("file.export.csf");
}
bool CncAPIClientCore::file_export_ctf(const std::string& file_name) {
    FILE_COMMAND_BODY("file.export.ctf");
}
bool CncAPIClientCore::file_export_msg(const std::string& file_name) {
    FILE_COMMAND_BODY("file.export.msg");
}
bool CncAPIClientCore::file_export_psf(const std::string& file_name) {
    FILE_COMMAND_BODY("file.export.psf");
}
bool CncAPIClientCore::file_import_cpf(const std::string& file_name) {
    FILE_COMMAND_BODY("file.import.cpf");
}
bool CncAPIClientCore::file_import_csf(const std::string& file_name) {
    FILE_COMMAND_BODY("file.import.csf");
}
bool CncAPIClientCore::file_import_ctf(const std::string& file_name) {
    FILE_COMMAND_BODY("file.import.ctf");
}
bool CncAPIClientCore::file_import_msg(const std::string& file_name) {
    FILE_COMMAND_BODY("file.import.msg");
}
bool CncAPIClientCore::file_import_psf(const std::string& file_name) {
    FILE_COMMAND_BODY("file.import.psf");
}
#undef FILE_COMMAND_BODY

bool CncAPIClientCore::log_add(const std::string& text) {
    return execute_request("{\"cmd\":\"log.add\",\"text\":\"" +
                           escape_json_string(text) + "\"}");
}

bool CncAPIClientCore::mru_programs_list_clear() {
    return execute_request("{\"cmd\":\"mdi.programs.list.clear\"}");
}

bool CncAPIClientCore::mru_programs_list_remove_item(int index) {
    return execute_request("{\"cmd\":\"mru.programs.list.remove.item\",\"index\":" +
                           std::to_string(index) + "}");
}

bool CncAPIClientCore::program_analysis(int mode, bool force_sync, double timeout) {
    if (mode < -1 || mode > ANALYSIS_RZ) return false;
    std::string request = "{\"cmd\":\"program.analysis\"";
    if (mode >= ANALYSIS_MT) request += ",\"mode\":" + std::to_string(mode);
    request += '}';
    return execute_force_sync_request(request, force_sync, timeout);
}

bool CncAPIClientCore::program_analysis_threaded(int mode, double timeout,
                                                  CompletionCallback on_done) {
    if (mode < -1 || mode > ANALYSIS_RZ || !valid_force_sync_timeout(timeout)) return false;
    return start_force_sync_async_request(
        [mode, timeout](CncAPIClientCore& api) {
            return api.program_analysis(mode, true, timeout);
        }, on_done);
}

bool CncAPIClientCore::program_analysis_abort() {
    return execute_request("{\"cmd\":\"program.analysis.abort\"}");
}

bool CncAPIClientCore::program_gcode_add_text(const std::string& text) {
    return execute_request("{\"cmd\":\"program.gcode.add.text\",\"text\":\"" +
                           escape_json_string(text) + "\"}");
}

bool CncAPIClientCore::program_gcode_clear() {
    return execute_request("{\"cmd\":\"program.gcode.clear\"}");
}

bool CncAPIClientCore::program_gcode_modified() {
    return execute_request("{\"cmd\":\"program.gcode.modified\"}");
}

bool CncAPIClientCore::program_gcode_set_text(const std::string& text) {
    return execute_request("{\"cmd\":\"program.gcode.set.text\",\"text\":\"" +
                           escape_json_string(text) + "\"}");
}

bool CncAPIClientCore::program_load(const std::string& file_name, bool force_sync,
                                    double timeout) {
    return execute_force_sync_request("{\"cmd\":\"program.load\",\"name\":\"" +
        escape_json_string(file_name) + "\"}", force_sync, timeout);
}

bool CncAPIClientCore::program_load_threaded(const std::string& file_name, double timeout,
                                              CompletionCallback on_done) {
    if (!valid_force_sync_timeout(timeout)) return false;
    return start_force_sync_async_request(
        [file_name, timeout](CncAPIClientCore& api) {
            return api.program_load(file_name, true, timeout);
        }, on_done);
}

bool CncAPIClientCore::program_new() { return execute_request("{\"cmd\":\"program.new\"}"); }

bool CncAPIClientCore::program_save(bool force_sync, double timeout) {
    return execute_force_sync_request("{\"cmd\":\"program.save\"}", force_sync, timeout);
}

bool CncAPIClientCore::program_save_threaded(double timeout, CompletionCallback on_done) {
    if (!valid_force_sync_timeout(timeout)) return false;
    return start_force_sync_async_request(
        [timeout](CncAPIClientCore& api) { return api.program_save(true, timeout); }, on_done);
}

bool CncAPIClientCore::program_save_as(const std::string& file_name, bool force_sync,
                                       double timeout) {
    return execute_force_sync_request("{\"cmd\":\"program.save.as\",\"file.name\":\"" +
        escape_json_string(file_name) + "\"}", force_sync, timeout);
}

bool CncAPIClientCore::program_save_as_threaded(const std::string& file_name, double timeout,
                                                 CompletionCallback on_done) {
    if (!valid_force_sync_timeout(timeout)) return false;
    return start_force_sync_async_request(
        [file_name, timeout](CncAPIClientCore& api) {
            return api.program_save_as(file_name, true, timeout);
        }, on_done);
}

bool CncAPIClientCore::reset_alarms() {
    return execute_request("{\"cmd\":\"reset.alarms\"}");
}
bool CncAPIClientCore::reset_alarms_history() {
    return execute_request("{\"cmd\":\"reset.alarms.history\"}");
}
bool CncAPIClientCore::reset_warnings() {
    return execute_request("{\"cmd\":\"reset.warnings\"}");
}
bool CncAPIClientCore::reset_warnings_history() {
    return execute_request("{\"cmd\":\"reset.warnings.history\"}");
}

bool CncAPIClientCore::show_ui_dialog(int uid_id) {
    if (uid_id < UID_ID_FIRST || uid_id > UID_ID_LAST) return false;
    return execute_request("{\"cmd\":\"show.ui.dialog\",\"uid_id\":" +
                           std::to_string(uid_id) + "}");
}

bool CncAPIClientCore::simulator_continue() {
    return execute_request("{\"cmd\":\"simulator.continue\"}");
}
bool CncAPIClientCore::simulator_pause() {
    return execute_request("{\"cmd\":\"simulator.pause\"}");
}
bool CncAPIClientCore::simulator_place_and_pause_to_line(int line) {
    return execute_request("{\"cmd\":\"simulator.place.and.pause.to.line\",\"line\":" +
                           std::to_string(line) + "}");
}
bool CncAPIClientCore::simulator_start() {
    return execute_request("{\"cmd\":\"simulator.start\"}");
}
bool CncAPIClientCore::simulator_step_backward() {
    return execute_request("{\"cmd\":\"simulator.step.backward\"}");
}
bool CncAPIClientCore::simulator_step_forward() {
    return execute_request("{\"cmd\":\"simulator.step.forward\"}");
}
bool CncAPIClientCore::simulator_stop() {
    return execute_request("{\"cmd\":\"simulator.stop\"}");
}

namespace {
    bool append_tool_command_fields(std::string& request, bool& first,
                                    const APIToolsLibInfoForSet& info) {
#define APPEND_TOOL_INT(field, key) if (info.field != nullptr) \
        append_json_raw(request, first, key, std::to_string(*info.field))
#define APPEND_TOOL_DOUBLE(field, key) if (info.field != nullptr) { \
        if (!std::isfinite(*info.field)) return false; \
        append_json_raw(request, first, key, json_number(*info.field)); }
        APPEND_TOOL_INT(tool_id, "id");
        APPEND_TOOL_INT(tool_slot, "slot");
        APPEND_TOOL_INT(tool_type, "type");
        APPEND_TOOL_DOUBLE(tool_diameter, "diameter");
        APPEND_TOOL_DOUBLE(tool_offset_x, "offset.x");
        APPEND_TOOL_DOUBLE(tool_offset_y, "offset.y");
        APPEND_TOOL_DOUBLE(tool_offset_z, "offset.z");
        APPEND_TOOL_DOUBLE(tool_param_1, "param.1");
        APPEND_TOOL_DOUBLE(tool_param_2, "param.2");
        APPEND_TOOL_DOUBLE(tool_param_3, "param.3");
        APPEND_TOOL_DOUBLE(tool_param_4, "param.4");
        APPEND_TOOL_DOUBLE(tool_param_5, "param.5");
        APPEND_TOOL_DOUBLE(tool_param_6, "param.6");
        APPEND_TOOL_DOUBLE(tool_param_7, "param.7");
        APPEND_TOOL_DOUBLE(tool_param_8, "param.8");
        APPEND_TOOL_DOUBLE(tool_param_9, "param.9");
        APPEND_TOOL_DOUBLE(tool_param_10, "param.10");
        APPEND_TOOL_DOUBLE(tool_param_51, "param.51");
        APPEND_TOOL_DOUBLE(tool_param_52, "param.52");
        APPEND_TOOL_DOUBLE(tool_param_53, "param.53");
        APPEND_TOOL_DOUBLE(tool_param_54, "param.54");
        APPEND_TOOL_DOUBLE(tool_param_55, "param.55");
        APPEND_TOOL_DOUBLE(tool_param_56, "param.56");
        APPEND_TOOL_DOUBLE(tool_param_57, "param.57");
        APPEND_TOOL_DOUBLE(tool_param_58, "param.58");
        APPEND_TOOL_DOUBLE(tool_param_59, "param.59");
        APPEND_TOOL_DOUBLE(tool_param_60, "param.60");
#undef APPEND_TOOL_INT
#undef APPEND_TOOL_DOUBLE
        if (info.tool_description != nullptr) {
            append_json_string(request, first, "description", *info.tool_description);
        }
        return true;
    }
}

bool CncAPIClientCore::tools_lib_add(const APIToolsLibInfoForSet* info) {
    if (!m_is_connected || info == nullptr) return false;
    std::string request = "{";
    bool first = true;
    append_json_string(request, first, "cmd", "tools.lib.add");
    if (!append_tool_command_fields(request, first, *info)) return false;
    request += '}';
    return execute_request(request);
}

bool CncAPIClientCore::tools_lib_clear() {
    return execute_request("{\"cmd\":\"tools.lib.clear\"}");
}

bool CncAPIClientCore::tools_lib_delete(int index) {
    return execute_request("{\"cmd\":\"tools.lib.delete\",\"index\":" +
                           std::to_string(index) + "}");
}

bool CncAPIClientCore::tools_lib_insert(const APIToolsLibInfoForSet* info) {
    if (!m_is_connected || info == nullptr || info->tool_index == nullptr) return false;
    std::string request = "{";
    bool first = true;
    append_json_string(request, first, "cmd", "tools.lib.insert");
    append_json_raw(request, first, "index", std::to_string(*info->tool_index));
    if (!append_tool_command_fields(request, first, *info)) return false;
    request += '}';
    return execute_request(request);
}

bool CncAPIClientCore::work_order_add(const std::string& order_code,
                                      const APIWorkOrderDataForAdd* data) {
    if (!m_is_connected) return false;
    std::string request = "{";
    bool first = true;
    append_json_string(request, first, "cmd", "work.order.add");
    append_json_string(request, first, "order.code", order_code);

    if (data != nullptr) {
        if (data->order_priority != nullptr &&
            (*data->order_priority < WO_PR_LOWEST || *data->order_priority > WO_PR_HIGHEST)) {
            return false;
        }
        std::string order_data = "{";
        bool first_data = true;
        if (data->order_locked != nullptr)
            append_json_raw(order_data, first_data, "order.locked",
                            *data->order_locked ? "true" : "false");
        if (data->order_priority != nullptr)
            append_json_raw(order_data, first_data, "order.priority",
                            std::to_string(*data->order_priority));
        if (data->job_order_code != nullptr)
            append_json_string(order_data, first_data, "job.order.code", *data->job_order_code);
        if (data->customer_code != nullptr)
            append_json_string(order_data, first_data, "customer.code", *data->customer_code);
        if (data->item_code != nullptr)
            append_json_string(order_data, first_data, "item.code", *data->item_code);
        if (data->material_code != nullptr)
            append_json_string(order_data, first_data, "material.code", *data->material_code);
        if (data->order_notes != nullptr)
            append_json_string(order_data, first_data, "order.notes", *data->order_notes);
        if (data->use_deadline_datetime != nullptr) {
            append_json_raw(order_data, first_data, "use.deadline.datetime",
                            *data->use_deadline_datetime ? "true" : "false");
            if (*data->use_deadline_datetime) {
                if (data->deadline_datetime == nullptr) return false;
                const int64_t deadline = datetime_to_filetime(*data->deadline_datetime);
                if (deadline == 0) return false;
                append_json_raw(order_data, first_data, "deadline.datetime",
                                std::to_string(deadline));
            }
        }
        if (!data->files.empty()) {
            std::string files = "[";
            for (size_t i = 0; i < data->files.size(); ++i) {
                if (i > 0) files += ',';
                files += '{';
                bool first_file = true;
                if (data->files[i].file_name != nullptr)
                    append_json_string(files, first_file, "file.name", *data->files[i].file_name);
                if (data->files[i].pieces_per_file != nullptr)
                    append_json_raw(files, first_file, "pieces.per.file",
                                    std::to_string(*data->files[i].pieces_per_file));
                if (data->files[i].requested_pieces != nullptr)
                    append_json_raw(files, first_file, "requested.pieces",
                                    std::to_string(*data->files[i].requested_pieces));
                files += '}';
            }
            files += ']';
            append_json_raw(order_data, first_data, "files", files);
        }
        order_data += '}';
        append_json_raw(request, first, "data", order_data);
    }
    request += '}';
    return execute_request(request);
}

bool CncAPIClientCore::work_order_delete(const std::string& order_code) {
    return execute_request("{\"cmd\":\"work.order.delete\",\"order.code\":\"" +
                           escape_json_string(order_code) + "\"}");
}

// ========== API Get Methods ==========

APIAxesInfo CncAPIClientCore::get_axes_info() {
    APIAxesInfo result;
    result.has_data = false;
    
    std::map<std::string, std::string> data;
    data["get"] = "axes.info";
    std::string request = create_compact_json_request(data);
    std::string response = send_command(request);
    
    if (response.empty()) {
        return result;
    }
    
    // Check if response contains "res" field
    if (response.find("\"res\":") == std::string::npos) {
        return result;
    }
    
    // Check for null response
    if (response.find("\"res\":null") != std::string::npos) {
        return result;
    }
    
    const std::string res = SimpleJSON::Parser::get_value(response, "res");
    const auto parse_fixed = [&res](const char* key, std::vector<double>& target) {
        const std::vector<double> values = SimpleJSON::Parser::parse_double_array(
            json_object_value(res, key));
        for (size_t i = 0; i < values.size() && i < target.size(); ++i) target[i] = values[i];
    };
    parse_fixed("joint.position", result.joint_position);
    parse_fixed("machine.position", result.machine_position);
    parse_fixed("program.position", result.program_position);
    parse_fixed("machine.target.position", result.machine_target_position);
    parse_fixed("program.target.position", result.program_target_position);
    parse_fixed("actual.velocity", result.actual_velocity);
    parse_fixed("working.offset", result.working_offset);
    parse_fixed("dynamic.offset", result.dynamic_offset);
    result.working_wcs = json_to_int(json_object_value(res, "working.wcs"));
    result.homing_done = json_to_bool(json_object_value(res, "homing.done"));
    result.homing_done_mask = json_to_int(json_object_value(res, "homing.done.mask"));
    result.homing_running_mask = json_to_int(json_object_value(res, "homing.running.mask"));
    result.homing_sensors_mask = json_to_int(json_object_value(res, "homing.sensors.mask"));
    parse_fixed("homing.correction.space", result.homing_correction_space);
    result.has_data = true;
    
    return result;
}

APICncInfo CncAPIClientCore::get_cnc_info() {
    APICncInfo result;
    result.has_data = false;
    
    std::map<std::string, std::string> data;
    data["get"] = "cnc.info";
    std::string request = create_compact_json_request(data);
    std::string response = send_command(request);
    
    if (response.empty()) {
        return result;
    }
    
    // Check if response contains "res" field
    if (response.find("\"res\":") == std::string::npos) {
        return result;
    }
    
    // Check for null response
    if (response.find("\"res\":null") != std::string::npos) {
        return result;
    }
    
    result.has_data = true;
    
    // Parse state_machine from res
    std::string state_machine_str = SimpleJSON::Parser::get_nested_value(response, "res", "state.machine");
    if (!state_machine_str.empty()) {
        try { result.state_machine = std::stoi(state_machine_str); } catch (...) {}
    }
    
    // Parse current alarm from nested object res -> current.alarm -> code
    std::string alarm_code_str = SimpleJSON::Parser::get_nested_value(response, "res", "current.alarm", "code");
    if (!alarm_code_str.empty()) {
        try { result.current_alarm_code = std::stoi(alarm_code_str); } catch (...) {}
    }
    
    std::string alarm_text_str = SimpleJSON::Parser::get_nested_value(response, "res", "current.alarm", "text");
    if (!alarm_text_str.empty()) {
        result.current_alarm_text = alarm_text_str;
    }
    
    // Parse current warning
    std::string warning_code_str = SimpleJSON::Parser::get_nested_value(response, "res", "current.warning", "code");
    if (!warning_code_str.empty()) {
        try { result.current_warning_code = std::stoi(warning_code_str); } catch (...) {}
    }
    
    std::string warning_text_str = SimpleJSON::Parser::get_nested_value(response, "res", "current.warning", "text");
    if (!warning_text_str.empty()) {
        result.current_warning_text = warning_text_str;
    }
    
    // Parse tool info from res -> tool -> ...
    std::string tool_id_str = SimpleJSON::Parser::get_nested_value(response, "res", "tool", "id");
    if (!tool_id_str.empty()) {
        try { result.tool_id = std::stoi(tool_id_str); } catch (...) {}
    }
    
    std::string tool_slot_str = SimpleJSON::Parser::get_nested_value(response, "res", "tool", "slot");
    if (!tool_slot_str.empty()) {
        try { result.tool_slot = std::stoi(tool_slot_str); } catch (...) {}
    }
    
    std::string tool_type_str = SimpleJSON::Parser::get_nested_value(response, "res", "tool", "type");
    if (!tool_type_str.empty()) {
        try { result.tool_type = std::stoi(tool_type_str); } catch (...) {}
    }
    
    std::string tool_diameter_str = SimpleJSON::Parser::get_nested_value(response, "res", "tool", "diameter");
    if (!tool_diameter_str.empty()) {
        try { result.tool_diameter = std::stod(tool_diameter_str); } catch (...) {}
    }
    
    std::string tool_description_str = SimpleJSON::Parser::get_nested_value(response, "res", "tool", "description");
    if (!tool_description_str.empty()) {
        result.tool_description = tool_description_str;
    }
    
    // Parse spindle info from res -> spindle -> ...
    std::string spindle_direction_str = SimpleJSON::Parser::get_nested_value(response, "res", "spindle", "direction");
    if (!spindle_direction_str.empty()) {
        try { result.spindle_direction = std::stoi(spindle_direction_str); } catch (...) {}
    }
    
    std::string spindle_programmed_str = SimpleJSON::Parser::get_nested_value(response, "res", "spindle", "programmed");
    if (!spindle_programmed_str.empty()) {
        try { result.spindle_programmed = std::stoi(spindle_programmed_str); } catch (...) {}
    }
    
    std::string spindle_actual_str = SimpleJSON::Parser::get_nested_value(response, "res", "spindle", "actual");
    if (!spindle_actual_str.empty()) {
        try { result.spindle_actual = std::stoi(spindle_actual_str); } catch (...) {}
    }
    
    // Parse feed info from res -> feed -> programmed
    std::string feed_programmed_str = SimpleJSON::Parser::get_nested_value(response, "res", "feed", "programmed");
    if (!feed_programmed_str.empty()) {
        try { result.feed_programmed = std::stod(feed_programmed_str); } catch (...) {}
    }

    const std::string res = SimpleJSON::Parser::get_value(response, "res");
    result.file_name = json_object_value(res, "file.name");
    result.units_mode = json_to_int(json_object_value(res, "units.mode"));
    result.axes_mask = json_to_int(json_object_value(res, "axes.mask"));
    result.connection_state = json_to_int(json_object_value(res, "connection.state"));
    result.controller_settings_crc = json_to_int(json_object_value(res, "controller.settings.crc"));
    result.interp_buffer_level = json_to_int(json_object_value(res, "interp.buffer.level"));
    result.gcode_line = json_to_int(json_object_value(res, "gcode.line"));
    result.gcode_block_skip_enabled = json_to_bool(json_object_value(res, "gcode.block.skip.enabled"));
    result.planned_time = json_object_value(res, "planned.time");
    result.worked_time = json_object_value(res, "worked.time");
    result.hud_user_message = json_object_value(res, "hud.user.message");
    result.toolpath_id = json_object_value(res, "toolpath.id");
    result.operator_request_id_pending = json_object_value(res, "operator.request.id.pending");
    result.program_gcode_sync_required = json_to_bool(json_object_value(res, "program.gcode.sync.required"));

    const std::string alarm = json_object_value(res, "current.alarm");
    result.current_alarm_datetime = filetime_to_datetime(json_to_int64(json_object_value(alarm, "datetime"), -1));
    result.current_alarm_code = json_to_int(json_object_value(alarm, "code"));
    result.current_alarm_info1 = json_to_int(json_object_value(alarm, "info1"));
    result.current_alarm_info2 = json_to_int(json_object_value(alarm, "info2"));
    result.current_alarm_text = json_object_value(alarm, "text");
    const std::string warning = json_object_value(res, "current.warning");
    result.current_warning_datetime = filetime_to_datetime(json_to_int64(json_object_value(warning, "datetime"), -1));
    result.current_warning_code = json_to_int(json_object_value(warning, "code"));
    result.current_warning_info1 = json_to_int(json_object_value(warning, "info1"));
    result.current_warning_info2 = json_to_int(json_object_value(warning, "info2"));
    result.current_warning_text = json_object_value(warning, "text");
    result.aux_outputs = json_to_int(json_object_value(res, "aux.outputs"));
    const std::string coolant = json_object_value(res, "coolant");
    result.coolant_mist = json_to_bool(json_object_value(coolant, "mist"));
    result.coolant_flood = json_to_bool(json_object_value(coolant, "flood"));
    const std::string lube = json_object_value(res, "lube");
    result.lube_axis_cycles_made = json_to_int(json_object_value(lube, "axis.cycles.made"));
    result.lube_axis_time_to_next_cycle = json_to_int(json_object_value(lube, "axis.time.to.next.cycle"));
    result.lube_spindle_cycles_made = json_to_int(json_object_value(lube, "spindle.cycles.made"));
    result.lube_spindle_time_to_next_cycle = json_to_int(json_object_value(lube, "spindle.time.to.next.cycle"));
    const std::string feed = json_object_value(res, "feed");
    result.feed_programmed = json_to_double(json_object_value(feed, "programmed"));
    result.feed_target = json_to_double(json_object_value(feed, "target"));
    result.feed_reference = json_to_double(json_object_value(feed, "reference"));
    const std::string spindle = json_object_value(res, "spindle");
#define SPINDLE_INT(member, key) result.spindle_##member = json_to_int(json_object_value(spindle, key))
    SPINDLE_INT(programmed, "programmed"); SPINDLE_INT(target, "target");
    SPINDLE_INT(actual, "actual"); SPINDLE_INT(load, "load"); SPINDLE_INT(torque, "torque");
    result.spindle_phase = json_to_double(json_object_value(spindle, "phase"));
    SPINDLE_INT(direction, "direction");
    result.spindle_not_ready = json_to_bool(json_object_value(spindle, "not.ready"));
    SPINDLE_INT(shaft, "shaft"); SPINDLE_INT(status, "status"); SPINDLE_INT(voltage, "voltage");
#undef SPINDLE_INT
    const std::string override_data = json_object_value(res, "override");
#define OVERRIDE_GROUP(member, key) \
    result.override_##member = json_to_int(json_object_value(override_data, key)); \
    result.override_##member##_min = json_to_int(json_object_value(override_data, key ".min")); \
    result.override_##member##_max = json_to_int(json_object_value(override_data, key ".max")); \
    result.override_##member##_enabled = json_to_bool(json_object_value(override_data, key ".enabled")); \
    result.override_##member##_locked = json_to_bool(json_object_value(override_data, key ".locked"))
    OVERRIDE_GROUP(jog, "jog"); OVERRIDE_GROUP(spindle, "spindle"); OVERRIDE_GROUP(fast, "fast");
    OVERRIDE_GROUP(feed, "feed"); OVERRIDE_GROUP(feed_custom_1, "feed.custom.1");
    OVERRIDE_GROUP(feed_custom_2, "feed.custom.2"); OVERRIDE_GROUP(plasma_power, "plasma.power");
    OVERRIDE_GROUP(plasma_voltage, "plasma.voltage");
#undef OVERRIDE_GROUP
    const std::string tool = json_object_value(res, "tool");
    result.tool_id = json_to_int(json_object_value(tool, "id"));
    result.tool_slot = json_to_int(json_object_value(tool, "slot"));
    result.tool_slot_enabled = json_to_bool(json_object_value(tool, "slot.enabled"));
    result.tool_type = json_to_int(json_object_value(tool, "type"));
    result.tool_diameter = json_to_double(json_object_value(tool, "diameter"));
    result.tool_offset_x = json_to_double(json_object_value(tool, "offset.x"));
    result.tool_offset_y = json_to_double(json_object_value(tool, "offset.y"));
    result.tool_offset_z = json_to_double(json_object_value(tool, "offset.z"));
    result.tool_param_1 = json_to_double(json_object_value(tool, "param.1"));
    result.tool_param_2 = json_to_double(json_object_value(tool, "param.2"));
    result.tool_param_3 = json_to_double(json_object_value(tool, "param.3"));
    result.tool_description = json_object_value(tool, "description");
    const std::string simulator = json_object_value(res, "simulator");
    result.simulator_available = json_to_bool(json_object_value(simulator, "available"));
    result.simulator_data_id = json_object_value(simulator, "data.id");
    result.simulator_state = json_to_int(json_object_value(simulator, "state"));
    result.simulator_planned_time_ms = json_to_int(json_object_value(simulator, "planned.time.ms"));
    result.simulator_current_time_ms = json_to_int(json_object_value(simulator, "current.time.ms"));
    result.simulator_speed_track = json_to_int(json_object_value(simulator, "speed.track"));
    
    return result;
}

APIEnabledCommands CncAPIClientCore::get_enabled_commands() {
    APIEnabledCommands result;
    result.has_data = false;
    
    std::map<std::string, std::string> data;
    data["get"] = "enabled.commands";
    std::string request = create_compact_json_request(data);
    std::string response = send_command(request);
    
    if (response.empty()) {
        return result;
    }
    
    // Check if response contains "res" field
    if (response.find("\"res\":") == std::string::npos) {
        return result;
    }
    
    // Check for null response
    if (response.find("\"res\":null") != std::string::npos) {
        return result;
    }
    
    result.has_data = true;
    
    // Parse boolean fields from res
    std::string cnc_start_str = SimpleJSON::Parser::get_nested_value(response, "res", "cnc.start");
    result.cnc_start = (cnc_start_str == "true");
    
    std::string cnc_pause_str = SimpleJSON::Parser::get_nested_value(response, "res", "cnc.pause");
    result.cnc_pause = (cnc_pause_str == "true");
    
    std::string cnc_resume_str = SimpleJSON::Parser::get_nested_value(response, "res", "cnc.resume");
    result.cnc_resume = (cnc_resume_str == "true");
    
    std::string cnc_stop_str = SimpleJSON::Parser::get_nested_value(response, "res", "cnc.stop");
    result.cnc_stop = (cnc_stop_str == "true");
    
    std::string cnc_continue_str = SimpleJSON::Parser::get_nested_value(response, "res", "cnc.continue");
    result.cnc_continue = (cnc_continue_str == "true");
    
    // Parse integer fields (bitmasks)
    std::string cnc_jog_command_str = SimpleJSON::Parser::get_nested_value(response, "res", "cnc.jog.command");
    if (!cnc_jog_command_str.empty()) {
        try { result.cnc_jog_command = std::stoi(cnc_jog_command_str); } catch (...) {}
    }
    
    std::string cnc_homing_str = SimpleJSON::Parser::get_nested_value(response, "res", "cnc.homing");
    if (!cnc_homing_str.empty()) {
        try { result.cnc_homing = std::stoi(cnc_homing_str); } catch (...) {}
    }

    const std::string res = SimpleJSON::Parser::get_value(response, "res");
#define ENABLED_BOOL(member, key) result.member = json_to_bool(json_object_value(res, key))
#define ENABLED_INT(member, key) result.member = json_to_int(json_object_value(res, key))
    ENABLED_INT(cnc_csfm_aux, "cnc.csfm.aux");
    ENABLED_BOOL(cnc_csfm_cooler_flood, "cnc.csfm.cooler.flood");
    ENABLED_BOOL(cnc_csfm_cooler_mist, "cnc.csfm.cooler.mist");
    ENABLED_BOOL(cnc_csfm_jog_mode, "cnc.csfm.jog.mode");
    ENABLED_BOOL(cnc_csfm_spindle_cw, "cnc.csfm.spindle.cw");
    ENABLED_BOOL(cnc_csfm_spindle_ccw, "cnc.csfm.spindle.ccw");
    ENABLED_BOOL(cnc_csfm_thc_disabled, "cnc.csfm.thc.disabled");
    ENABLED_BOOL(cnc_csfm_torch, "cnc.csfm.torch");
    ENABLED_BOOL(cnc_connection_close, "cnc.connection.close");
    ENABLED_BOOL(cnc_connection_open, "cnc.connection.open");
    ENABLED_BOOL(cnc_continue, "cnc.continue");
    ENABLED_INT(cnc_homing, "cnc.homing"); ENABLED_INT(cnc_jog_command, "cnc.jog.command");
    ENABLED_BOOL(cnc_mdi_command, "cnc.mdi.command"); ENABLED_BOOL(cnc_parameters, "cnc.parameters");
    ENABLED_BOOL(cnc_pause, "cnc.pause"); ENABLED_BOOL(cnc_resume, "cnc.resume");
    ENABLED_BOOL(cnc_resume_from_line, "cnc.resume.from.line");
    ENABLED_BOOL(cnc_resume_from_point, "cnc.resume.from.point");
    ENABLED_BOOL(cnc_start, "cnc.start"); ENABLED_BOOL(cnc_start_from_line, "cnc.start.from.line");
    ENABLED_BOOL(cnc_start_from_point, "cnc.start.from.point"); ENABLED_BOOL(cnc_stop, "cnc.stop");
    ENABLED_BOOL(program_analysis, "program.analysis");
    ENABLED_BOOL(program_analysis_abort, "program.analysis.abort");
    ENABLED_BOOL(program_gcode_add_text, "program.gcode.add.text");
    ENABLED_BOOL(program_gcode_clear, "program.gcode.clear");
    ENABLED_BOOL(program_gcode_modified, "program.gcode.modified");
    ENABLED_BOOL(program_gcode_set_text, "program.gcode.set.text");
    ENABLED_BOOL(program_load, "program.load"); ENABLED_BOOL(program_new, "program.new");
    ENABLED_BOOL(program_save, "program.save"); ENABLED_BOOL(program_save_as, "program.save.as");
    ENABLED_BOOL(reset_alarms, "reset.alarms"); ENABLED_BOOL(reset_alarms_history, "reset.alarms.history");
    ENABLED_BOOL(reset_warnings, "reset.warnings"); ENABLED_BOOL(reset_warnings_history, "reset.warnings.history");
    ENABLED_BOOL(set_compiler_settings, "set.compiler.settings");
    ENABLED_INT(set_dynamic_offsets, "set.dynamic.offsets"); ENABLED_BOOL(set_kinematics, "set.kinematics");
    ENABLED_INT(set_program_position, "set.program.position");
    ENABLED_BOOL(set_simulator_current_time_ms, "set.simulator.current.time.ms");
    ENABLED_BOOL(set_simulator_speed_track, "set.simulator.speed.track");
    ENABLED_BOOL(show_ui_dialog, "show.ui.dialog"); ENABLED_BOOL(simulator_continue, "simulator.continue");
    ENABLED_BOOL(simulator_pause, "simulator.pause"); ENABLED_BOOL(simulator_start, "simulator.start");
    ENABLED_BOOL(simulator_step_backward, "simulator.step.backward");
    ENABLED_BOOL(simulator_step_forward, "simulator.step.forward"); ENABLED_BOOL(simulator_stop, "simulator.stop");
    ENABLED_BOOL(tools_lib_write, "tools.lib.write");
#undef ENABLED_INT
#undef ENABLED_BOOL
    
    return result;
}

APICompileInfo CncAPIClientCore::get_compile_info() {
    APICompileInfo result;
    result.has_data = false;
    
    std::map<std::string, std::string> data;
    data["get"] = "compile.info";
    std::string request = create_compact_json_request(data);
    std::string response = send_command(request);
    
    if (response.empty()) {
        return result;
    }
    
    // Check if response contains "res" field
    if (response.find("\"res\":") == std::string::npos) {
        return result;
    }
    
    // Check for null response
    if (response.find("\"res\":null") != std::string::npos) {
        return result;
    }
    
    result.has_data = true;
    
    // Parse compile info fields from res
    std::string code_str = SimpleJSON::Parser::get_nested_value(response, "res", "code");
    if (!code_str.empty()) {
        try { result.code = std::stoi(code_str); } catch (...) {}
    }
    
    std::string code_line_str = SimpleJSON::Parser::get_nested_value(response, "res", "code.line");
    if (!code_line_str.empty()) {
        try { result.code_line = std::stoi(code_line_str); } catch (...) {}
    }
    
    std::string file_line_str = SimpleJSON::Parser::get_nested_value(response, "res", "file.line");
    if (!file_line_str.empty()) {
        try { result.file_line = std::stoi(file_line_str); } catch (...) {}
    }
    
    std::string file_name_str = SimpleJSON::Parser::get_nested_value(response, "res", "file.name");
    if (!file_name_str.empty()) {
        result.file_name = file_name_str;
    }
    
    std::string message_str = SimpleJSON::Parser::get_nested_value(response, "res", "message");
    if (!message_str.empty()) {
        result.message = message_str;
    }

    result.mode = json_to_int(SimpleJSON::Parser::get_nested_value(response, "res", "mode"), CM_NONE);
    
    std::string state_str = SimpleJSON::Parser::get_nested_value(response, "res", "state");
    if (!state_str.empty()) {
        try { result.state = std::stoi(state_str); } catch (...) {}
    }
    
    return result;
}

APIDigitalInputs CncAPIClientCore::get_digital_inputs() {
    APIDigitalInputs result;
    result.has_data = false;
    
    std::map<std::string, std::string> data;
    data["get"] = "digital.inputs";
    std::string request = create_compact_json_request(data);
    std::string response = send_command(request);
    
    if (response.empty()) {
        return result;
    }
    
    // Check if response contains "res" field
    if (response.find("\"res\":") == std::string::npos) {
        return result;
    }
    
    // Check for null response
    if (response.find("\"res\":null") != std::string::npos) {
        return result;
    }
    
    result.has_data = true;
    
    // Parse value array from res
    std::string value_str = SimpleJSON::Parser::get_nested_value(response, "res", "value");
    if (!value_str.empty()) {
        auto values = SimpleJSON::Parser::parse_int_array(value_str);
        for (size_t i = 0; i < values.size() && i < result.value.size(); ++i) {
            result.value[i] = values[i];
        }
    }
    
    return result;
}

APIDigitalOutputs CncAPIClientCore::get_digital_outputs() {
    APIDigitalOutputs result;
    result.has_data = false;
    
    std::map<std::string, std::string> data;
    data["get"] = "digital.outputs";
    std::string request = create_compact_json_request(data);
    std::string response = send_command(request);
    
    if (response.empty()) {
        return result;
    }
    
    // Check if response contains "res" field
    if (response.find("\"res\":") == std::string::npos) {
        return result;
    }
    
    // Check for null response
    if (response.find("\"res\":null") != std::string::npos) {
        return result;
    }
    
    result.has_data = true;
    
    // Parse value array from res
    std::string value_str = SimpleJSON::Parser::get_nested_value(response, "res", "value");
    if (!value_str.empty()) {
        auto values = SimpleJSON::Parser::parse_int_array(value_str);
        for (size_t i = 0; i < values.size() && i < result.value.size(); ++i) {
            result.value[i] = values[i];
        }
    }
    
    return result;
}

APIAlarmsWarningsList CncAPIClientCore::get_alarms_current_list() {
    APIAlarmsWarningsList result;
    result.has_data = false;
    
    std::map<std::string, std::string> data;
    data["get"] = "alarms.current.list";
    std::string request = create_compact_json_request(data);
    std::string response = send_command(request);
    
    if (response.empty()) {
        return result;
    }
    
    // Check if response contains "res" field
    if (response.find("\"res\":") == std::string::npos) {
        return result;
    }
    
    // Check for null response
    if (response.find("\"res\":null") != std::string::npos) {
        return result;
    }
    
    result.has_data = true;
    
    // Parse list array from res -> list
    std::string list_str = SimpleJSON::Parser::get_nested_value(response, "res", "list");
    
    if (!list_str.empty() && list_str != "[]") {
        // Parse array of alarm objects
        // Simple parsing: count objects by counting opening braces
        size_t pos = 0;
        while ((pos = list_str.find("{", pos)) != std::string::npos) {
            // Find the closing brace for this object
            size_t end_pos = list_str.find("}", pos);
            if (end_pos == std::string::npos) break;
            
            std::string obj_str = list_str.substr(pos, end_pos - pos + 1);
            
            // Parse individual alarm object
            APIAlarmsWarningsList::AlarmWarningData alarm;
            
            // Extract code
            std::string code_pattern = "\"code\":";
            size_t code_pos = obj_str.find(code_pattern);
            if (code_pos != std::string::npos) {
                code_pos += code_pattern.length();
                size_t code_end = obj_str.find_first_of(",}", code_pos);
                std::string code_str = obj_str.substr(code_pos, code_end - code_pos);
                try { alarm.code = std::stoi(SimpleJSON::Parser::trim(code_str)); } catch (...) {}
            }
            
            // Extract info.1
            std::string info1_pattern = "\"info.1\":";
            size_t info1_pos = obj_str.find(info1_pattern);
            if (info1_pos != std::string::npos) {
                info1_pos += info1_pattern.length();
                size_t info1_end = obj_str.find_first_of(",}", info1_pos);
                std::string info1_str = obj_str.substr(info1_pos, info1_end - info1_pos);
                try { alarm.info_1 = std::stoi(SimpleJSON::Parser::trim(info1_str)); } catch (...) {}
            }
            
            // Extract info.2
            std::string info2_pattern = "\"info.2\":";
            size_t info2_pos = obj_str.find(info2_pattern);
            if (info2_pos != std::string::npos) {
                info2_pos += info2_pattern.length();
                size_t info2_end = obj_str.find_first_of(",}", info2_pos);
                std::string info2_str = obj_str.substr(info2_pos, info2_end - info2_pos);
                try { alarm.info_2 = std::stoi(SimpleJSON::Parser::trim(info2_str)); } catch (...) {}
            }
            
            // Extract text
            std::string text_pattern = "\"text\":\"";
            size_t text_pos = obj_str.find(text_pattern);
            if (text_pos != std::string::npos) {
                text_pos += text_pattern.length();
                size_t text_end = obj_str.find("\"", text_pos);
                if (text_end != std::string::npos) {
                    alarm.text = obj_str.substr(text_pos, text_end - text_pos);
                }
            }
            
            result.list.push_back(alarm);
            pos = end_pos + 1;
        }
    }
    
    result.list = parse_alarm_warning_items(response);
    return result;
}

APISystemInfo CncAPIClientCore::get_system_info() {
    APISystemInfo result;
    result.has_data = false;
    
    std::map<std::string, std::string> data;
    data["get"] = "system.info";
    std::string request = create_compact_json_request(data);
    std::string response = send_command(request);
    
    if (response.empty()) {
        return result;
    }
    
    // Check if response contains "res" field
    if (response.find("\"res\":") == std::string::npos) {
        return result;
    }
    
    // Check for null response
    if (response.find("\"res\":null") != std::string::npos) {
        return result;
    }
    
    result.has_data = true;
    
    // Parse all system info fields
    std::string machine_name = SimpleJSON::Parser::get_nested_value(response, "res", "machine.name");
    if (!machine_name.empty()) {
        result.machine_name = machine_name;
    }
    
    std::string control_software_version = SimpleJSON::Parser::get_nested_value(response, "res", "control.software.version");
    if (!control_software_version.empty()) {
        result.control_software_version = control_software_version;
    }
    
    std::string core_version = SimpleJSON::Parser::get_nested_value(response, "res", "core.version");
    if (!core_version.empty()) {
        result.core_version = core_version;
    }
    
    std::string api_server_version = SimpleJSON::Parser::get_nested_value(response, "res", "api.server.version");
    if (!api_server_version.empty()) {
        result.api_server_version = api_server_version;
    }
    
    std::string firmware_version = SimpleJSON::Parser::get_nested_value(response, "res", "firmware.version");
    if (!firmware_version.empty()) {
        result.firmware_version = firmware_version;
    }
    
    std::string firmware_version_tag = SimpleJSON::Parser::get_nested_value(response, "res", "firmware.version.tag");
    if (!firmware_version_tag.empty()) {
        result.firmware_version_tag = firmware_version_tag;
    }
    
    std::string firmware_interface_level = SimpleJSON::Parser::get_nested_value(response, "res", "firmware.interface.level");
    if (!firmware_interface_level.empty()) {
        result.firmware_interface_level = firmware_interface_level;
    }
    
    std::string order_code = SimpleJSON::Parser::get_nested_value(response, "res", "order.code");
    if (!order_code.empty()) {
        result.order_code = order_code;
    }
    
    std::string customer_id = SimpleJSON::Parser::get_nested_value(response, "res", "customer.id");
    if (!customer_id.empty()) {
        result.customer_id = customer_id;
    }
    
    std::string serial_number = SimpleJSON::Parser::get_nested_value(response, "res", "serial.number");
    if (!serial_number.empty()) {
        result.serial_number = serial_number;
    }
    
    std::string part_number = SimpleJSON::Parser::get_nested_value(response, "res", "part.number");
    if (!part_number.empty()) {
        result.part_number = part_number;
    }
    
    std::string customization_number = SimpleJSON::Parser::get_nested_value(response, "res", "customization.number");
    if (!customization_number.empty()) {
        result.customization_number = customization_number;
    }
    
    std::string hardware_version = SimpleJSON::Parser::get_nested_value(response, "res", "hardware.version");
    if (!hardware_version.empty()) {
        result.hardware_version = hardware_version;
    }
    
    std::string operative_system = SimpleJSON::Parser::get_nested_value(response, "res", "operative.system");
    if (!operative_system.empty()) {
        result.operative_system = operative_system;
    }
    
    std::string operative_system_crc = SimpleJSON::Parser::get_nested_value(response, "res", "operative.system.crc");
    if (!operative_system_crc.empty()) {
        result.operative_system_crc = operative_system_crc;
    }
    
    std::string pld_version = SimpleJSON::Parser::get_nested_value(response, "res", "pld.version");
    if (!pld_version.empty()) {
        result.pld_version = pld_version;
    }
    const std::string licensed = SimpleJSON::Parser::get_nested_value(response, "res", "licensed.feature");
    result.licensed_feature_panel_pc = json_to_bool(json_object_value(licensed, "panel.pc"));
    result.licensed_feature_panel_pc_demo = json_to_bool(json_object_value(licensed, "panel.pc.demo"));
    result.licensed_feature_work_orders = json_to_bool(json_object_value(licensed, "work.orders"));
    result.licensed_feature_opc_ua_server = json_to_bool(json_object_value(licensed, "opc.ua.server"));
    result.licensed_feature_probe_sdk_g1 = json_to_bool(json_object_value(licensed, "probe.sdk.g1"));
    result.licensed_feature_probe_sdk_g2 = json_to_bool(json_object_value(licensed, "probe.sdk.g2"));
    result.licensed_feature_probe_sdk_g3 = json_to_bool(json_object_value(licensed, "probe.sdk.g3"));
    result.licensed_feature_probe_sdk_g4 = json_to_bool(json_object_value(licensed, "probe.sdk.g4"));
    result.licensed_feature_probe_sdk_g5 = json_to_bool(json_object_value(licensed, "probe.sdk.g5"));
    
    return result;
}

APIAnalogInputs CncAPIClientCore::get_analog_inputs() {
    APIAnalogInputs result;
    result.has_data = false;
    
    std::map<std::string, std::string> data;
    data["get"] = "analog.inputs";
    std::string request = create_compact_json_request(data);
    std::string response = send_command(request);
    
    if (response.empty()) {
        return result;
    }
    
    if (response.find("\"res\":") == std::string::npos) {
        return result;
    }
    
    if (response.find("\"res\":null") != std::string::npos) {
        return result;
    }
    
    result.has_data = true;
    
    // Parse value array from res
    std::string value_str = SimpleJSON::Parser::get_nested_value(response, "res", "value");
    if (!value_str.empty()) {
        auto values = SimpleJSON::Parser::parse_double_array(value_str);
        for (size_t i = 0; i < values.size() && i < result.value.size(); ++i) {
            result.value[i] = values[i];
        }
    }
    
    return result;
}

APIAnalogOutputs CncAPIClientCore::get_analog_outputs() {
    APIAnalogOutputs result;
    result.has_data = false;
    
    std::map<std::string, std::string> data;
    data["get"] = "analog.outputs";
    std::string request = create_compact_json_request(data);
    std::string response = send_command(request);
    
    if (response.empty()) {
        return result;
    }
    
    if (response.find("\"res\":") == std::string::npos) {
        return result;
    }
    
    if (response.find("\"res\":null") != std::string::npos) {
        return result;
    }
    
    result.has_data = true;
    
    // Parse value array from res
    std::string value_str = SimpleJSON::Parser::get_nested_value(response, "res", "value");
    if (!value_str.empty()) {
        auto values = SimpleJSON::Parser::parse_double_array(value_str);
        for (size_t i = 0; i < values.size() && i < result.value.size(); ++i) {
            result.value[i] = values[i];
        }
    }
    
    return result;
}

APIMachiningInfo CncAPIClientCore::get_machining_info() {
    APIMachiningInfo result;
    result.has_data = false;
    
    std::map<std::string, std::string> data;
    data["get"] = "machining.info";
    std::string request = create_compact_json_request(data);
    std::string response = send_command(request);
    
    if (response.empty()) {
        return result;
    }
    
    if (response.find("\"res\":") == std::string::npos) {
        return result;
    }
    
    if (response.find("\"res\":null") != std::string::npos) {
        return result;
    }
    
    result.has_data = true;
    
    // Parse tool.path fields
    std::string tool_path_in_fast = SimpleJSON::Parser::get_nested_value(response, "res", "tool.path", "in.fast");
    if (!tool_path_in_fast.empty()) {
        try { result.tool_path_in_fast = std::stod(tool_path_in_fast); } catch (...) {}
    }
    
    std::string tool_path_in_feed = SimpleJSON::Parser::get_nested_value(response, "res", "tool.path", "in.feed");
    if (!tool_path_in_feed.empty()) {
        try { result.tool_path_in_feed = std::stod(tool_path_in_feed); } catch (...) {}
    }
    
    std::string total_path = SimpleJSON::Parser::get_nested_value(response, "res", "tool.path", "total.path");
    if (!total_path.empty()) {
        try { result.total_path = std::stod(total_path); } catch (...) {}
    }
    
    std::string planned_time = SimpleJSON::Parser::get_nested_value(response, "res", "tool.path", "planned.time");
    if (!planned_time.empty()) {
        result.planned_time = planned_time;
    }
    
    const std::string res = SimpleJSON::Parser::get_value(response, "res");
    const std::string tool_path = json_object_value(res, "tool.path");
    for (const std::string& object : SimpleJSON::Parser::split_array_items(
             json_object_value(tool_path, "used.tool"))) {
        APIMachiningInfoUsedTool tool;
        tool.tool_id = json_to_int(json_object_value(object, "id"));
        tool.in_fast = json_to_double(json_object_value(object, "in.fast"));
        tool.in_feed = json_to_double(json_object_value(object, "in.feed"));
        result.used_tool.push_back(tool);
    }
#define EXTENTS3(group_key, prefix) do { \
    const std::string group = json_object_value(res, group_key); \
    result.prefix##_min_x = json_to_double(json_object_value(group, "min.x")); \
    result.prefix##_min_y = json_to_double(json_object_value(group, "min.y")); \
    result.prefix##_min_z = json_to_double(json_object_value(group, "min.z")); \
    result.prefix##_max_x = json_to_double(json_object_value(group, "max.x")); \
    result.prefix##_max_y = json_to_double(json_object_value(group, "max.y")); \
    result.prefix##_max_z = json_to_double(json_object_value(group, "max.z")); \
    result.prefix##_length_x = json_to_double(json_object_value(group, "length.x")); \
    result.prefix##_length_y = json_to_double(json_object_value(group, "length.y")); \
    result.prefix##_length_z = json_to_double(json_object_value(group, "length.z")); \
} while (false)
    EXTENTS3("tcp.extents.in.fast", tcp_extents_in_fast);
    EXTENTS3("tcp.extents.in.feed", tcp_extents_in_feed);
#undef EXTENTS3
#define EXTENTS6(group_key, prefix) do { \
    const std::string group = json_object_value(res, group_key); \
    result.prefix##_min_x = json_to_double(json_object_value(group, "min.x")); \
    result.prefix##_min_y = json_to_double(json_object_value(group, "min.y")); \
    result.prefix##_min_z = json_to_double(json_object_value(group, "min.z")); \
    result.prefix##_min_a = json_to_double(json_object_value(group, "min.a")); \
    result.prefix##_min_b = json_to_double(json_object_value(group, "min.b")); \
    result.prefix##_min_c = json_to_double(json_object_value(group, "min.c")); \
    result.prefix##_max_x = json_to_double(json_object_value(group, "max.x")); \
    result.prefix##_max_y = json_to_double(json_object_value(group, "max.y")); \
    result.prefix##_max_z = json_to_double(json_object_value(group, "max.z")); \
    result.prefix##_max_a = json_to_double(json_object_value(group, "max.a")); \
    result.prefix##_max_b = json_to_double(json_object_value(group, "max.b")); \
    result.prefix##_max_c = json_to_double(json_object_value(group, "max.c")); \
    result.prefix##_length_x = json_to_double(json_object_value(group, "length.x")); \
    result.prefix##_length_y = json_to_double(json_object_value(group, "length.y")); \
    result.prefix##_length_z = json_to_double(json_object_value(group, "length.z")); \
    result.prefix##_length_a = json_to_double(json_object_value(group, "length.a")); \
    result.prefix##_length_b = json_to_double(json_object_value(group, "length.b")); \
    result.prefix##_length_c = json_to_double(json_object_value(group, "length.c")); \
} while (false)
    EXTENTS6("joints.in.fast", joints_in_fast);
    EXTENTS6("joints.in.feed", joints_in_feed);
#undef EXTENTS6
    
    return result;
}

APIWorkInfo CncAPIClientCore::get_work_info() {
    APIWorkInfo result;
    result.has_data = false;
    
    std::map<std::string, std::string> data;
    data["get"] = "work.info";
    std::string request = create_compact_json_request(data);
    std::string response = send_command(request);
    
    if (response.empty()) {
        return result;
    }
    
    if (response.find("\"res\":") == std::string::npos) {
        return result;
    }
    
    if (response.find("\"res\":null") != std::string::npos) {
        return result;
    }
    
    result.has_data = true;
    
    // Parse work info fields
    std::string work_mode = SimpleJSON::Parser::get_nested_value(response, "res", "work.mode");
    if (!work_mode.empty()) {
        try { result.work_mode = std::stoi(work_mode); } catch (...) {}
    }
    
    std::string active_order_code = SimpleJSON::Parser::get_nested_value(response, "res", "active.work.order.code");
    if (!active_order_code.empty()) {
        result.active_work_order_code = active_order_code;
    }
    
    std::string active_file_index = SimpleJSON::Parser::get_nested_value(response, "res", "active.work.order.file.index");
    if (!active_file_index.empty()) {
        try { result.active_work_order_file_index = std::stoi(active_file_index); } catch (...) {}
    }
    
    std::string file_name = SimpleJSON::Parser::get_nested_value(response, "res", "file.name");
    if (!file_name.empty()) {
        result.file_name = file_name;
    }
    
    std::string planned_time = SimpleJSON::Parser::get_nested_value(response, "res", "planned.time");
    if (!planned_time.empty()) {
        result.planned_time = planned_time;
    }
    
    std::string worked_time = SimpleJSON::Parser::get_nested_value(response, "res", "worked.time");
    if (!worked_time.empty()) {
        result.worked_time = worked_time;
    }
    
    return result;
}

APIToolsLibInfo CncAPIClientCore::get_tools_lib_info(int index) {
    APIToolsLibInfo result;
    result.has_data = false;
    
    const std::string request = "{\"get\":\"tools.lib.info\",\"index\":" +
        std::to_string(index) + "}";
    std::string response = send_command(request);
    
    if (response.empty()) {
        return result;
    }
    
    if (response.find("\"res\":") == std::string::npos) {
        return result;
    }
    
    if (response.find("\"res\":null") != std::string::npos) {
        return result;
    }
    
    result.data = parse_tool_info(SimpleJSON::Parser::get_value(response, "res"));
    result.has_data = true;
    return result;
}

APIToolsLibInfos CncAPIClientCore::get_tools_lib_infos() {
    APIToolsLibInfos result;
    result.has_data = false;
    
    std::map<std::string, std::string> data;
    data["get"] = "tools.lib.infos";
    std::string request = create_compact_json_request(data);
    std::string response = send_command(request);
    
    if (response.empty()) {
        return result;
    }
    
    if (response.find("\"res\":") == std::string::npos) {
        return result;
    }
    
    if (response.find("\"res\":null") != std::string::npos) {
        return result;
    }
    
    result.has_data = true;
    
    // Parse slot.enabled
    std::string slot_enabled_str = SimpleJSON::Parser::get_nested_value(response, "res", "slot.enabled");
    if (!slot_enabled_str.empty()) {
        result.slot_enabled = (slot_enabled_str == "true" || slot_enabled_str == "1");
    }
    
    const std::string res = SimpleJSON::Parser::get_value(response, "res");
    const std::string tools = SimpleJSON::Parser::get_value(res, "tools");
    for (const std::string& item : SimpleJSON::Parser::split_array_items(tools)) {
        if (!item.empty()) result.data.push_back(parse_tool_info(item));
    }
    
    return result;
}

APIAlarmsWarningsList CncAPIClientCore::get_alarms_history_list() {
    APIAlarmsWarningsList result;
    result.has_data = false;
    
    std::map<std::string, std::string> data;
    data["get"] = "alarms.history.list";
    std::string request = create_compact_json_request(data);
    std::string response = send_command(request);
    
    if (response.empty() || response.find("\"res\":") == std::string::npos || response.find("\"res\":null") != std::string::npos) {
        return result;
    }
    
    result.has_data = true;
    
    // Parse list array - same logic as get_alarms_current_list
    std::string list_str = SimpleJSON::Parser::get_nested_value(response, "res", "list");
    if (!list_str.empty() && list_str != "[]") {
        size_t pos = 0;
        while ((pos = list_str.find("{", pos)) != std::string::npos) {
            size_t end_pos = list_str.find("}", pos);
            if (end_pos == std::string::npos) break;
            
            std::string obj_str = list_str.substr(pos, end_pos - pos + 1);
            APIAlarmsWarningsList::AlarmWarningData alarm;
            
            std::string code_pattern = "\"code\":";
            size_t code_pos = obj_str.find(code_pattern);
            if (code_pos != std::string::npos) {
                code_pos += code_pattern.length();
                size_t code_end = obj_str.find_first_of(",}", code_pos);
                std::string code_str = obj_str.substr(code_pos, code_end - code_pos);
                try { alarm.code = std::stoi(SimpleJSON::Parser::trim(code_str)); } catch (...) {}
            }
            
            std::string text_pattern = "\"text\":\"";
            size_t text_pos = obj_str.find(text_pattern);
            if (text_pos != std::string::npos) {
                text_pos += text_pattern.length();
                size_t text_end = obj_str.find("\"", text_pos);
                if (text_end != std::string::npos) {
                    alarm.text = obj_str.substr(text_pos, text_end - text_pos);
                }
            }
            
            result.list.push_back(alarm);
            pos = end_pos + 1;
        }
    }
    
    result.list = parse_alarm_warning_items(response);
    return result;
}

APIAlarmsWarningsList CncAPIClientCore::get_warnings_current_list() {
    APIAlarmsWarningsList result;
    result.has_data = false;
    
    std::map<std::string, std::string> data;
    data["get"] = "warnings.current.list";
    std::string request = create_compact_json_request(data);
    std::string response = send_command(request);
    
    if (response.empty() || response.find("\"res\":") == std::string::npos || response.find("\"res\":null") != std::string::npos) {
        return result;
    }
    
    result.has_data = true;
    
    // Parse list array - same logic as alarms
    std::string list_str = SimpleJSON::Parser::get_nested_value(response, "res", "list");
    if (!list_str.empty() && list_str != "[]") {
        size_t pos = 0;
        while ((pos = list_str.find("{", pos)) != std::string::npos) {
            size_t end_pos = list_str.find("}", pos);
            if (end_pos == std::string::npos) break;
            
            std::string obj_str = list_str.substr(pos, end_pos - pos + 1);
            APIAlarmsWarningsList::AlarmWarningData warning;
            
            std::string code_pattern = "\"code\":";
            size_t code_pos = obj_str.find(code_pattern);
            if (code_pos != std::string::npos) {
                code_pos += code_pattern.length();
                size_t code_end = obj_str.find_first_of(",}", code_pos);
                std::string code_str = obj_str.substr(code_pos, code_end - code_pos);
                try { warning.code = std::stoi(SimpleJSON::Parser::trim(code_str)); } catch (...) {}
            }
            
            std::string text_pattern = "\"text\":\"";
            size_t text_pos = obj_str.find(text_pattern);
            if (text_pos != std::string::npos) {
                text_pos += text_pattern.length();
                size_t text_end = obj_str.find("\"", text_pos);
                if (text_end != std::string::npos) {
                    warning.text = obj_str.substr(text_pos, text_end - text_pos);
                }
            }
            
            result.list.push_back(warning);
            pos = end_pos + 1;
        }
    }
    
    result.list = parse_alarm_warning_items(response);
    return result;
}

APIAlarmsWarningsList CncAPIClientCore::get_warnings_history_list() {
    APIAlarmsWarningsList result;
    result.has_data = false;
    
    std::map<std::string, std::string> data;
    data["get"] = "warnings.history.list";
    std::string request = create_compact_json_request(data);
    std::string response = send_command(request);
    
    if (response.empty() || response.find("\"res\":") == std::string::npos || response.find("\"res\":null") != std::string::npos) {
        return result;
    }
    
    result.has_data = true;
    
    // Parse list array - same logic as alarms
    std::string list_str = SimpleJSON::Parser::get_nested_value(response, "res", "list");
    if (!list_str.empty() && list_str != "[]") {
        size_t pos = 0;
        while ((pos = list_str.find("{", pos)) != std::string::npos) {
            size_t end_pos = list_str.find("}", pos);
            if (end_pos == std::string::npos) break;
            
            std::string obj_str = list_str.substr(pos, end_pos - pos + 1);
            APIAlarmsWarningsList::AlarmWarningData warning;
            
            std::string code_pattern = "\"code\":";
            size_t code_pos = obj_str.find(code_pattern);
            if (code_pos != std::string::npos) {
                code_pos += code_pattern.length();
                size_t code_end = obj_str.find_first_of(",}", code_pos);
                std::string code_str = obj_str.substr(code_pos, code_end - code_pos);
                try { warning.code = std::stoi(SimpleJSON::Parser::trim(code_str)); } catch (...) {}
            }
            
            std::string text_pattern = "\"text\":\"";
            size_t text_pos = obj_str.find(text_pattern);
            if (text_pos != std::string::npos) {
                text_pos += text_pattern.length();
                size_t text_end = obj_str.find("\"", text_pos);
                if (text_end != std::string::npos) {
                    warning.text = obj_str.substr(text_pos, text_end - text_pos);
                }
            }
            
            result.list.push_back(warning);
            pos = end_pos + 1;
        }
    }
    
    result.list = parse_alarm_warning_items(response);
    return result;
}

APIMachineSettings CncAPIClientCore::get_machine_settings() {
    APIMachineSettings result;
    result.has_data = false;
    
    std::map<std::string, std::string> data;
    data["get"] = "machine.settings";
    std::string request = create_compact_json_request(data);
    std::string response = send_command(request);
    
    if (response.empty() || response.find("\"res\":") == std::string::npos || response.find("\"res\":null") != std::string::npos) {
        return result;
    }
    
    const std::string axis = SimpleJSON::Parser::get_nested_value(response, "res", "axis");
    if (axis.empty()) return result;
    const auto integer = [&axis](const char* key) { return json_to_int(json_object_value(axis, key)); };
    const auto number = [&axis](const char* key) { return json_to_double(json_object_value(axis, key)); };
    result.axis_machine_type = integer("machine.type");
    result.machine_type = result.axis_machine_type; // Backward-compatible alias.
    result.axis_kinematics_model = integer("kinematics.model");
#define PARSE_AXIS(letter, member) \
    result.axis_##member##_type = integer(letter ".type"); \
    result.axis_##member##_max_vel = number(letter ".max.vel"); \
    result.axis_##member##_acc = number(letter ".acc"); \
    result.axis_##member##_min_lim = number(letter ".min.lim"); \
    result.axis_##member##_max_lim = number(letter ".max.lim")
    PARSE_AXIS("x", x); PARSE_AXIS("y", y); PARSE_AXIS("z", z);
    PARSE_AXIS("a", a); PARSE_AXIS("b", b); PARSE_AXIS("c", c);
#undef PARSE_AXIS
    result.kinematics_h_x = number("kinematics.h.x");
    result.kinematics_h_y = number("kinematics.h.y");
    result.kinematics_h_z = number("kinematics.h.z");
    result.kinematics_j_x = number("kinematics.j.x");
    result.kinematics_j_y = number("kinematics.j.y");
    result.kinematics_j_z = number("kinematics.j.z");
    result.has_data = true;
    
    return result;
}

APILocalizationInfo CncAPIClientCore::get_localization_info() {
    APILocalizationInfo result;
    result.has_data = false;
    
    std::map<std::string, std::string> data;
    data["get"] = "localization.info";
    std::string request = create_compact_json_request(data);
    std::string response = send_command(request);
    
    if (response.empty() || response.find("\"res\":") == std::string::npos || response.find("\"res\":null") != std::string::npos) {
        return result;
    }
    
    result.has_data = true;
    
    // Parse localization fields
    std::string units_mode_str = SimpleJSON::Parser::get_nested_value(response, "res", "units.mode");
    if (!units_mode_str.empty()) {
        try { result.units_mode = std::stoi(units_mode_str); } catch (...) {}
    }
    
    std::string locale_name = SimpleJSON::Parser::get_nested_value(response, "res", "locale.name");
    if (!locale_name.empty()) {
        result.locale_name = locale_name;
    }
    
    std::string description = SimpleJSON::Parser::get_nested_value(response, "res", "description");
    if (!description.empty()) {
        result.description = description;
    }
    
    std::string language = SimpleJSON::Parser::get_nested_value(response, "res", "language");
    if (!language.empty()) {
        result.language = language;
    }
    
    std::string language_list = SimpleJSON::Parser::get_nested_value(response, "res", "language.list");
    if (!language_list.empty()) {
        result.language_list = language_list;
    }
    const std::string res = SimpleJSON::Parser::get_value(response, "res");
    for (const std::string& object : SimpleJSON::Parser::split_array_items(json_object_value(res, "list"))) {
        APILocalizationInfo::LocalizationData item;
        item.locale_name = json_object_value(object, "locale.name");
        item.description = json_object_value(object, "description");
        item.owner = json_object_value(object, "owner");
        item.revisor = json_object_value(object, "revisor");
        item.version = json_object_value(object, "version");
        item.date = json_object_value(object, "date");
        item.program = json_object_value(object, "program");
        result.list.push_back(item);
    }
    
    return result;
}

APIScanningLaserInfo CncAPIClientCore::get_scanning_laser_info() {
    APIScanningLaserInfo result;
    result.has_data = false;
    
    std::map<std::string, std::string> data;
    data["get"] = "scanning.laser.info";
    std::string request = create_compact_json_request(data);
    std::string response = send_command(request);
    
    if (response.empty() || response.find("\"res\":") == std::string::npos || response.find("\"res\":null") != std::string::npos) {
        return result;
    }
    
    result.has_data = true;
    
    // Parse laser info fields
    result.laser_offset_x = json_to_double(
        SimpleJSON::Parser::get_nested_value(response, "res", "laser.offset.x"));
    result.laser_offset_y = json_to_double(
        SimpleJSON::Parser::get_nested_value(response, "res", "laser.offset.y"));
    result.laser_offset_z = json_to_double(
        SimpleJSON::Parser::get_nested_value(response, "res", "laser.offset.z"));

    std::string laser_out_bit = SimpleJSON::Parser::get_nested_value(response, "res", "laser.out.bit");
    if (!laser_out_bit.empty()) {
        try { result.laser_out_bit = std::stoi(laser_out_bit); } catch (...) {}
    }
    
    std::string laser_h_measure = SimpleJSON::Parser::get_nested_value(response, "res", "laser.h.measure");
    if (!laser_h_measure.empty()) {
        try { result.laser_h_measure = std::stod(laser_h_measure); } catch (...) {}
    }

    result.laser_out_umf = json_to_int(
        SimpleJSON::Parser::get_nested_value(response, "res", "laser.out.umf"));
    result.laser_mcs_x_position = json_to_double(
        SimpleJSON::Parser::get_nested_value(response, "res", "laser.mcs.x.position"));
    result.laser_mcs_y_position = json_to_double(
        SimpleJSON::Parser::get_nested_value(response, "res", "laser.mcs.y.position"));
    result.laser_mcs_z_position = json_to_double(
        SimpleJSON::Parser::get_nested_value(response, "res", "laser.mcs.z.position"));
    
    return result;
}

APIToolsLibCount CncAPIClientCore::get_tools_lib_count() {
    APIToolsLibCount result;
    result.has_data = false;
    
    std::map<std::string, std::string> data;
    data["get"] = "tools.lib.count";
    std::string request = create_compact_json_request(data);
    std::string response = send_command(request);
    
    if (response.empty() || response.find("\"res\":") == std::string::npos || response.find("\"res\":null") != std::string::npos) {
        return result;
    }
    
    result.has_data = true;
    
    // Parse count
    std::string count_str = SimpleJSON::Parser::get_nested_value(response, "res", "count");
    if (!count_str.empty()) {
        try { result.count = std::stoi(count_str); } catch (...) {}
    }
    
    return result;
}

APIToolsLibToolIndexFromId CncAPIClientCore::get_tools_lib_tool_index_from_id(int tool_id) {
    APIToolsLibToolIndexFromId result;
    result.has_data = false;
    
    const std::string request = "{\"get\":\"tools.lib.tool.index.from.id\",\"id\":" +
        std::to_string(tool_id) + "}";
    std::string response = send_command(request);
    
    if (response.empty() || response.find("\"res\":") == std::string::npos || response.find("\"res\":null") != std::string::npos) {
        return result;
    }
    
    result.has_data = true;
    
    // Parse index
    std::string index_str = SimpleJSON::Parser::get_nested_value(response, "res", "index");
    if (!index_str.empty()) {
        try { result.index = std::stoi(index_str); } catch (...) {}
    }
    
    return result;
}

APIWorkOrderCodeList CncAPIClientCore::get_work_order_code_list() {
    APIWorkOrderCodeList result;
    result.has_data = false;
    
    std::map<std::string, std::string> data;
    data["get"] = "work.order.code.list";
    std::string request = create_compact_json_request(data);
    std::string response = send_command(request);
    
    if (response.empty() || response.find("\"res\":") == std::string::npos || response.find("\"res\":null") != std::string::npos) {
        return result;
    }
    
    const std::string array = SimpleJSON::Parser::get_value(response, "res");
    for (const std::string& row : SimpleJSON::Parser::split_array_items(array)) {
        const std::vector<std::string> fields = SimpleJSON::Parser::split_array_items(row);
        if (fields.size() < 3) continue;
        APIWorkOrderCodeList::ListData item;
        item.order_code = SimpleJSON::Parser::unquote(fields[0]);
        item.order_state = json_to_int(fields[1]);
        item.revision_number = json_to_int(fields[2]);
        result.data.push_back(item);
    }
    result.has_data = true;
    
    return result;
}

APIWorkOrderDataForGet CncAPIClientCore::get_work_order_data(const std::string& order_code, int mode) {
    APIWorkOrderDataForGet result;
    result.has_data = false;
    
    std::string request = "{\"get\":\"work.order.data\",\"order.code\":\"" +
        escape_json_string(order_code) + "\"";
    if (mode == 1) request += ",\"mode\":1";
    request += "}";
    std::string response = send_command(request);
    
    if (response.empty() || response.find("\"res\":") == std::string::npos || response.find("\"res\":null") != std::string::npos) {
        return result;
    }
    
    const std::string res = SimpleJSON::Parser::get_value(response, "res");
    result.revision_number = json_to_int(json_object_value(res, "revision.number"));
    result.order_state = json_to_int(json_object_value(res, "order.state"));
    result.order_locked = json_to_bool(json_object_value(res, "order.locked"));
    result.order_code = json_object_value(res, "order.code");
    result.order_priority = json_to_int(json_object_value(res, "order.priority"));
    result.job_order_code = json_object_value(res, "job.order.code");
    result.customer_code = json_object_value(res, "customer.code");
    result.item_code = json_object_value(res, "item.code");
    result.material_code = json_object_value(res, "material.code");
    result.order_notes = json_object_value(res, "order.notes");
    result.files.clear();
    for (const std::string& object : SimpleJSON::Parser::split_array_items(json_object_value(res, "files"))) {
        APIWorkOrderDataForGet::FileData file;
        file.file_name = json_object_value(object, "file.name");
        file.file_state = json_to_int(json_object_value(object, "file.state"));
        file.pieces_per_file = json_to_int(json_object_value(object, "pieces.per.file"));
        file.requested_pieces = json_to_int(json_object_value(object, "requested.pieces"));
        file.produced_pieces = json_to_int(json_object_value(object, "produced.pieces"));
        file.discarded_pieces = json_to_int(json_object_value(object, "discarded.pieces"));
        result.files.push_back(file);
    }
    result.use_deadline_datetime = json_to_bool(json_object_value(res, "use.deadline.datetime"));
    result.creation_datetime = filetime_to_datetime(json_to_int64(json_object_value(res, "creation.datetime"), -1));
    result.deadline_datetime = filetime_to_datetime(json_to_int64(json_object_value(res, "deadline.datetime"), -1));
    result.reception_datetime = filetime_to_datetime(json_to_int64(json_object_value(res, "reception.datetime"), -1));
    result.acceptance_datetime = filetime_to_datetime(json_to_int64(json_object_value(res, "acceptance.datetime"), -1));
    result.begin_datetime = filetime_to_datetime(json_to_int64(json_object_value(res, "begin.datetime"), -1));
    result.end_datetime = filetime_to_datetime(json_to_int64(json_object_value(res, "end.datetime"), -1));
    result.archived_datetime = filetime_to_datetime(json_to_int64(json_object_value(res, "archived.datetime"), -1));
    result.time_for_setup = json_to_int(json_object_value(res, "time.for.setup"));
    result.time_for_idle = json_to_int(json_object_value(res, "time.for.idle"));
    result.time_for_work = json_to_int(json_object_value(res, "time.for.work"));
    result.time_total = json_to_int(json_object_value(res, "time.total"));
    result.operator_notes = json_object_value(res, "operator.notes");
    result.log_items.clear();
    for (const std::string& object : SimpleJSON::Parser::split_array_items(json_object_value(res, "log.items"))) {
        APIWorkOrderDataForGet::LogItemData item;
        item.log_id = json_to_int(json_object_value(object, "log.id"));
        item.log_datetime = filetime_to_datetime(json_to_int64(json_object_value(object, "log.datetime"), -1));
        item.log_info_1 = json_object_value(object, "log.info.1");
        item.log_info_2 = json_object_value(object, "log.info.2");
        result.log_items.push_back(item);
    }
    result.has_data = true;
    return result;
}

APIWorkOrderFileList CncAPIClientCore::get_work_order_file_list(const std::string& path, const std::string& file_filter) {
    APIWorkOrderFileList result;
    result.has_data = false;
    
    std::map<std::string, std::string> data;
    data["get"] = "work.order.file.list";
    if (!path.empty()) {
        data["path"] = path;
    }
    if (!file_filter.empty()) {
        data["file.filter"] = file_filter;
    }
    std::string request = create_compact_json_request(data);
    std::string response = send_command(request);
    
    if (response.empty() || response.find("\"res\":") == std::string::npos || response.find("\"res\":null") != std::string::npos) {
        return result;
    }
    
    const std::string array = SimpleJSON::Parser::get_value(response, "res");
    for (const std::string& object : SimpleJSON::Parser::split_array_items(array)) {
        APIWorkOrderFileList::FileData file;
        file.type = json_to_int(json_object_value(object, "type"));
        file.name = json_object_value(object, "name");
        file.size = json_to_int64(json_object_value(object, "size"));
        file.creation_datetime = filetime_to_datetime(json_to_int64(json_object_value(object, "creation.datetime"), -1));
        file.last_access_datetime = filetime_to_datetime(json_to_int64(json_object_value(object, "last.access.datetime"), -1));
        file.last_write_datetime = filetime_to_datetime(json_to_int64(json_object_value(object, "last.write.datetime"), -1));
        result.files.push_back(file);
    }
    result.has_data = true;
    
    return result;
}

APIProgrammedPoints CncAPIClientCore::get_programmed_points() {
    APIProgrammedPoints result;
    result.has_data = false;
    
    std::map<std::string, std::string> data;
    data["get"] = "programmed.points";
    std::string request = create_compact_json_request(data);
    std::string response = send_command(request);
    
    if (response.empty() || response.find("\"res\":") == std::string::npos || response.find("\"res\":null") != std::string::npos) {
        return result;
    }
    
    const std::string points = SimpleJSON::Parser::get_nested_value(response, "res", "points");
    for (const std::string& row : SimpleJSON::Parser::split_array_items(points)) {
        result.points.push_back(SimpleJSON::Parser::parse_double_array(row));
    }
    result.has_data = true;
    
    return result;
}

APICncParameters CncAPIClientCore::get_cnc_parameters(int address, int elements) {
    APICncParameters result;
    result.has_data = false;
    
    const std::string request = "{\"get\":\"cnc.parameters\",\"address\":" +
        std::to_string(address) + ",\"elements\":" + std::to_string(elements) + "}";
    std::string response = send_command(request);
    
    if (response.empty() || response.find("\"res\":") == std::string::npos || response.find("\"res\":null") != std::string::npos) {
        return result;
    }
    
    result.has_data = true;
    
    // Parse address
    std::string address_str = SimpleJSON::Parser::get_nested_value(response, "res", "address");
    if (!address_str.empty()) {
        try { result.address = std::stoi(address_str); } catch (...) {}
    }
    
    // Parse values array
    std::string values_str = SimpleJSON::Parser::get_nested_value(response, "res", "values");
    if (!values_str.empty()) {
        auto values = SimpleJSON::Parser::parse_double_array(values_str);
        result.values = values;
    }
    result.descriptions = SimpleJSON::Parser::parse_string_array(
        SimpleJSON::Parser::get_nested_value(response, "res", "descriptions"));
    
    return result;
}

APICompilerSettingsForGet CncAPIClientCore::get_compiler_settings() {
    APICompilerSettingsForGet result;
    if (!m_is_connected) return result;

    const std::string response = send_command("{\"get\":\"compiler.settings\"}");
    if (response.empty() || !SimpleJSON::Parser::has_key(response, "current.toolpath.mode")) return result;

    const auto value = [&response](const std::string& key) {
        return SimpleJSON::Parser::get_nested_value(response, "res", key);
    };

    result.current_toolpath_mode = json_to_int(value("current.toolpath.mode"));
    result.default_toolpath_mode = json_to_int(value("default.toolpath.mode"));
    result.modal_macro_motion_mode = json_to_int(value("modal.macro.motion.mode"));
    result.cutter_compensation_mode = json_to_int(value("cutter.compensation.mode"));
    result.cutter_compensation_gouging_threshold = json_to_int(value("cutter.compensation.gouging.threshold"));
    result.arc_radius_tolerance = json_to_double(value("arc.radius.tolerance"));
    result.infinite_loop_threshold = json_to_int(value("infinite.loop.threshold"));
    result.gcode_block_skip_enabled = json_to_bool(value("gcode.block.skip.enabled"));
    result.g43_persistent = json_to_bool(value("g43.persistent"));
    result.g52_independent = json_to_bool(value("g52.independent"));
    result.g92_persistent = json_to_bool(value("g92.persistent"));
    result.origin_offset_persistent = json_to_bool(value("origin.offset.persistent"));
    result.user_m_codes_arguments_enabled = json_to_bool(value("user.m.codes.arguments.enabled"));
    result.user_macro_path_mode = json_to_int(value("user.macro.path.mode"));
    result.user_macro_path = value("user.macro.path");
    result.jpdc_axis_x = json_to_double(value("jpdc.axis.x"));
    result.jpdc_axis_y = json_to_double(value("jpdc.axis.y"));
    result.jpdc_axis_z = json_to_double(value("jpdc.axis.z"));
    result.jpdc_axis_a = json_to_double(value("jpdc.axis.a"));
    result.jpdc_axis_b = json_to_double(value("jpdc.axis.b"));
    result.jpdc_axis_c = json_to_double(value("jpdc.axis.c"));
    result.restart_default_movement_mode = json_to_int(value("restart.default.movement.mode"));
    result.restart_first_movement_feed = json_to_double(value("restart.first.movement.feed"));
    result.restart_max_distance = json_to_double(value("restart.max.distance"));
    result.restart_force_tool_measurement = json_to_bool(value("restart.force.tool.measurement"));
    result.toolpath_resolution = json_to_double(value("toolpath.resolution"));
    result.use_points_per_block = json_to_bool(value("use.points.per.block"));
    result.points_per_block = json_to_int(value("points.per.block"));
    result.tool_xx0_color = json_to_int(value("tool.xx0.color"));
    result.tool_xx1_color = json_to_int(value("tool.xx1.color"));
    result.tool_xx2_color = json_to_int(value("tool.xx2.color"));
    result.tool_xx3_color = json_to_int(value("tool.xx3.color"));
    result.tool_xx4_color = json_to_int(value("tool.xx4.color"));
    result.tool_xx5_color = json_to_int(value("tool.xx5.color"));
    result.tool_xx6_color = json_to_int(value("tool.xx6.color"));
    result.tool_xx7_color = json_to_int(value("tool.xx7.color"));
    result.tool_xx8_color = json_to_int(value("tool.xx8.color"));
    result.tool_xx9_color = json_to_int(value("tool.xx9.color"));
    result.rapid_move_color = json_to_int(value("rapid.move.color"));
    result.rf_threshold = json_to_int(value("rf.threshold"));
    result.rf_threshold_color_lower = json_to_int(value("rf.threshold.color.lower"));
    result.rf_threshold_color_equal = json_to_int(value("rf.threshold.color.equal"));
    result.rf_threshold_color_upper = json_to_int(value("rf.threshold.color.upper"));
    result.rv_color_mode = json_to_int(value("rv.color.mode"));
    result.rv_wavelength_min = json_to_int(value("rv.wavelength.min"));
    result.rv_wavelength_max = json_to_int(value("rv.wavelength.max"));
    result.rv_gradient_color_min = json_to_int(value("rv.gradient.color.min"));
    result.rv_gradient_color_max = json_to_int(value("rv.gradient.color.max"));
    result.rz_color_mode = json_to_int(value("rz.color.mode"));
    result.rz_wavelength_min = json_to_int(value("rz.wavelength.min"));
    result.rz_wavelength_max = json_to_int(value("rz.wavelength.max"));
    result.rz_gradient_color_min = json_to_int(value("rz.gradient.color.min"));
    result.rz_gradient_color_max = json_to_int(value("rz.gradient.color.max"));
    result.has_data = true;
    return result;
}

APICoordinateSystemsInfo CncAPIClientCore::get_coordinate_systems_info() {
    APICoordinateSystemsInfo result;
    if (!m_is_connected) return result;

    const std::string response = send_command("{\"get\":\"coordinate.systems.info\"}");
    if (response.empty() || !SimpleJSON::Parser::has_key(response, "working.wcs")) return result;
    const auto value = [&response](const std::string& key) {
        return SimpleJSON::Parser::get_nested_value(response, "res", key);
    };

    result.working_wcs = json_to_int(value("working.wcs"));
    result.working_offset = SimpleJSON::Parser::parse_double_array(value("working.offset"));
    result.wcs_1 = SimpleJSON::Parser::parse_double_array(value("wcs.1"));
    result.wcs_2 = SimpleJSON::Parser::parse_double_array(value("wcs.2"));
    result.wcs_3 = SimpleJSON::Parser::parse_double_array(value("wcs.3"));
    result.wcs_4 = SimpleJSON::Parser::parse_double_array(value("wcs.4"));
    result.wcs_5 = SimpleJSON::Parser::parse_double_array(value("wcs.5"));
    result.wcs_6 = SimpleJSON::Parser::parse_double_array(value("wcs.6"));
    result.wcs_7 = SimpleJSON::Parser::parse_double_array(value("wcs.7"));
    result.wcs_8 = SimpleJSON::Parser::parse_double_array(value("wcs.8"));
    result.wcs_9 = SimpleJSON::Parser::parse_double_array(value("wcs.9"));
    result.has_data = true;
    return result;
}

APIMRUProgramsList CncAPIClientCore::get_mru_programs_list() {
    APIMRUProgramsList result;
    if (!m_is_connected) return result;
    const std::string response = send_command("{\"get\":\"mru.programs.list\"}");
    if (response.empty() || !SimpleJSON::Parser::has_key(response, "items")) return result;
    result.items = SimpleJSON::Parser::parse_string_array(
        SimpleJSON::Parser::get_nested_value(response, "res", "items"));
    result.has_data = true;
    return result;
}

APIOperatorRequest CncAPIClientCore::get_operator_request() {
    APIOperatorRequest result;
    if (!m_is_connected) return result;
    const std::string response = send_command("{\"get\":\"operator.request\"}");
    if (response.empty() || !SimpleJSON::Parser::has_key(response, "id") ||
        !SimpleJSON::Parser::has_key(response, "data")) return result;

    result.id = SimpleJSON::Parser::get_nested_value(response, "res", "id");
    result.type = json_to_int(SimpleJSON::Parser::get_nested_value(response, "res", "type"));
    result.media = SimpleJSON::Parser::get_nested_value(response, "res", "media");
    result.message = SimpleJSON::Parser::get_nested_value(response, "res", "message");
    result.external_continue_requested = json_to_bool(
        SimpleJSON::Parser::get_nested_value(response, "res", "external.continue.requested"));

    const std::string data_object =
        SimpleJSON::Parser::get_nested_value(response, "res", "data");
    result.data_elements = json_to_int(SimpleJSON::Parser::get_value(data_object, "elements"));
    const double no_value = std::numeric_limits<double>::quiet_NaN();
    result.data_d01 = json_to_double(SimpleJSON::Parser::get_value(data_object, "d01"), no_value);
    result.data_d02 = json_to_double(SimpleJSON::Parser::get_value(data_object, "d02"), no_value);
    result.data_d03 = json_to_double(SimpleJSON::Parser::get_value(data_object, "d03"), no_value);
    result.data_d04 = json_to_double(SimpleJSON::Parser::get_value(data_object, "d04"), no_value);
    result.data_d05 = json_to_double(SimpleJSON::Parser::get_value(data_object, "d05"), no_value);
    result.data_d06 = json_to_double(SimpleJSON::Parser::get_value(data_object, "d06"), no_value);
    result.data_d07 = json_to_double(SimpleJSON::Parser::get_value(data_object, "d07"), no_value);
    result.data_d08 = json_to_double(SimpleJSON::Parser::get_value(data_object, "d08"), no_value);
    result.data_d09 = json_to_double(SimpleJSON::Parser::get_value(data_object, "d09"), no_value);
    result.data_d10 = json_to_double(SimpleJSON::Parser::get_value(data_object, "d10"), no_value);
    result.data = {result.data_d01, result.data_d02, result.data_d03, result.data_d04,
                   result.data_d05, result.data_d06, result.data_d07, result.data_d08,
                   result.data_d09, result.data_d10};
    result.has_data = true;
    return result;
}

APIProgramInfo CncAPIClientCore::get_program_info() {
    APIProgramInfo result;
    if (!m_is_connected) return result;
    const std::string response = send_command("{\"get\":\"program.info\"}", 50000, 2000);
    if (response.empty() || !SimpleJSON::Parser::has_key(response, "file.name") ||
        !SimpleJSON::Parser::has_key(response, "code")) return result;
    result.file_name = SimpleJSON::Parser::get_nested_value(response, "res", "file.name");
    result.code = SimpleJSON::Parser::get_nested_value(response, "res", "code");
    result.has_data = true;
    return result;
}

APIRuntimeData CncAPIClientCore::get_runtime_data() {
    APIRuntimeData result;
    if (!m_is_connected) return result;
    const std::string response = send_command("{\"get\":\"runtime.data\"}");
    if (response.empty() || !SimpleJSON::Parser::has_key(response, "state") ||
        !SimpleJSON::Parser::has_key(response, "pending.item") ||
        !SimpleJSON::Parser::has_key(response, "acquired.items")) return result;

    result.state = json_to_int(SimpleJSON::Parser::get_nested_value(response, "res", "state"));
    const std::string pending =
        SimpleJSON::Parser::get_nested_value(response, "res", "pending.item");
    result.pending_item.gcode_line = json_to_int(SimpleJSON::Parser::get_value(pending, "gcode.line"));
    result.pending_item.canon_id = json_to_int(SimpleJSON::Parser::get_value(pending, "canon.id"));
    result.pending_item.canon_code = json_to_int(SimpleJSON::Parser::get_value(pending, "canon.code"));
    result.pending_item.canon_segment = json_to_int(SimpleJSON::Parser::get_value(pending, "canon.segment"));
    result.pending_item.text = SimpleJSON::Parser::get_value(pending, "text");

    const std::string acquired =
        SimpleJSON::Parser::get_nested_value(response, "res", "acquired.items");
    const std::vector<std::string> items = SimpleJSON::Parser::split_array_items(acquired);
    for (size_t i = 0; i < items.size(); ++i) {
        if (items[i].empty()) continue;
        APIRuntimeDataAcquiredItem item;
        item.datetime = filetime_to_datetime(json_to_int64(SimpleJSON::Parser::get_value(items[i], "datetime")));
        item.gcode_line = json_to_int(SimpleJSON::Parser::get_value(items[i], "gcode.line"));
        item.canon_id = json_to_int(SimpleJSON::Parser::get_value(items[i], "canon.id"));
        item.canon_code = json_to_int(SimpleJSON::Parser::get_value(items[i], "canon.code"));
        item.canon_segment = json_to_int(SimpleJSON::Parser::get_value(items[i], "canon.segment"));
        item.text = SimpleJSON::Parser::get_value(items[i], "text");
        item.data = SimpleJSON::Parser::parse_double_array(
            SimpleJSON::Parser::get_value(items[i], "data"));
        result.acquired_items.push_back(item);
    }
    result.has_data = true;
    return result;
}

APISimulatorData CncAPIClientCore::get_simulator_data(int data_type) {
    APISimulatorData result;
    if (!m_is_connected || (data_type != SDT_FULL && data_type != SDT_MINIMAL)) return result;
    result.data_type = data_type;
    const std::string request = std::string("{\"get\":\"simulator.data\",\"data.type\":") +
        std::to_string(data_type) + "}";
    if (!send_command_raw(request, result.data, 20000, 2000)) return result;
    result.has_data = !result.data.empty();
    return result;
}

APIToolpathData CncAPIClientCore::get_toolpath_data(int mode) {
    APIToolpathData result;
    if (!m_is_connected || (mode != 0 && mode != 1)) return result;

    if (mode == 0) {
        const std::string response = send_command("{\"get\":\"toolpath.data\"}");
        if (response.empty() || !SimpleJSON::Parser::has_key(response, "data")) return result;
        const std::string encoded =
            SimpleJSON::Parser::get_nested_value(response, "res", "data");
        if (!decode_base64(encoded, result.data)) return result;
        result.has_data = true;
        return result;
    }

    if (!send_command_raw("{\"get\":\"toolpath.data\",\"mode\":1}", result.data)) return result;
    result.has_data = true;
    return result;
}

std::vector<APIVMGeometryInfo> CncAPIClientCore::get_vm_geometry_info(
        const std::vector<std::string>& names) {
    std::vector<APIVMGeometryInfo> result;
    if (!m_is_connected || names.empty()) return result;

    std::string request = "{\"get\":\"vm.geometry.info\",\"name\":[";
    for (size_t i = 0; i < names.size(); ++i) {
        if (i > 0) request += ',';
        request += "\"" + escape_json_string(names[i]) + "\"";
    }
    request += "]}";

    const std::string response = send_command(request);
    if (response.empty()) return result;
    const std::string response_data = SimpleJSON::Parser::get_value(response, "res");
    if (response_data.empty() || response_data.front() != '[') return result;
    const std::vector<std::string> items =
        SimpleJSON::Parser::split_array_items(response_data);
    if (items.size() != names.size()) return result;

    result.reserve(items.size());
    for (size_t i = 0; i < items.size(); ++i) {
        APIVMGeometryInfo item;
        item.name = SimpleJSON::Parser::get_value(items[i], "name");
        item.x = json_to_double(SimpleJSON::Parser::get_value(items[i], "x"));
        item.y = json_to_double(SimpleJSON::Parser::get_value(items[i], "y"));
        item.z = json_to_double(SimpleJSON::Parser::get_value(items[i], "z"));
        item.color = json_to_int(SimpleJSON::Parser::get_value(items[i], "color"));
        item.scale = json_to_double(SimpleJSON::Parser::get_value(items[i], "scale"));
        item.visible = json_to_bool(SimpleJSON::Parser::get_value(items[i], "visible"));
        item.edges_angle = json_to_double(SimpleJSON::Parser::get_value(items[i], "edges.angle"));
        item.edges_visible = json_to_bool(SimpleJSON::Parser::get_value(items[i], "edges.visible"));
        item.has_data = !item.name.empty();
        result.push_back(item);
    }
    return result;
}

bool CncAPIClientCore::set_compiler_settings(const APICompilerSettingsForSet* data) {
    if (!m_is_connected || data == nullptr) return false;

    std::string request = "{";
    bool first = true;
    size_t settings_count = 0;
    append_json_string(request, first, "set", "compiler.settings");

#define APPEND_INT(field, key) if (data->field != nullptr) { \
    append_json_raw(request, first, key, std::to_string(*data->field)); ++settings_count; }
#define APPEND_BOOL(field, key) if (data->field != nullptr) { \
    append_json_raw(request, first, key, *data->field ? "true" : "false"); ++settings_count; }
#define APPEND_DOUBLE(field, key) if (data->field != nullptr) { \
    if (!std::isfinite(*data->field)) return false; \
    append_json_raw(request, first, key, json_number(*data->field)); ++settings_count; }

    APPEND_INT(current_toolpath_mode, "current.toolpath.mode");
    APPEND_INT(default_toolpath_mode, "default.toolpath.mode");
    APPEND_INT(modal_macro_motion_mode, "modal.macro.motion.mode");
    APPEND_INT(cutter_compensation_mode, "cutter.compensation.mode");
    APPEND_INT(cutter_compensation_gouging_threshold, "cutter.compensation.gouging.threshold");
    APPEND_DOUBLE(arc_radius_tolerance, "arc.radius.tolerance");
    APPEND_INT(infinite_loop_threshold, "infinite.loop.threshold");
    APPEND_BOOL(gcode_block_skip_enabled, "gcode.block.skip.enabled");
    APPEND_BOOL(g43_persistent, "g43.persistent");
    APPEND_BOOL(g52_independent, "g52.independent");
    APPEND_BOOL(g92_persistent, "g92.persistent");
    APPEND_BOOL(origin_offset_persistent, "origin.offset.persistent");
    APPEND_BOOL(user_m_codes_arguments_enabled, "user.m.codes.arguments.enabled");
    APPEND_INT(user_macro_path_mode, "user.macro.path.mode");
    if (data->user_macro_path != nullptr) {
        append_json_string(request, first, "user.macro.path", *data->user_macro_path);
        ++settings_count;
    }
    APPEND_DOUBLE(jpdc_axis_x, "jpdc.axis.x");
    APPEND_DOUBLE(jpdc_axis_y, "jpdc.axis.y");
    APPEND_DOUBLE(jpdc_axis_z, "jpdc.axis.z");
    APPEND_DOUBLE(jpdc_axis_a, "jpdc.axis.a");
    APPEND_DOUBLE(jpdc_axis_b, "jpdc.axis.b");
    APPEND_DOUBLE(jpdc_axis_c, "jpdc.axis.c");
    APPEND_INT(restart_default_movement_mode, "restart.default.movement.mode");
    APPEND_DOUBLE(restart_first_movement_feed, "restart.first.movement.feed");
    APPEND_DOUBLE(restart_max_distance, "restart.max.distance");
    APPEND_BOOL(restart_force_tool_measurement, "restart.force.tool.measurement");
    APPEND_DOUBLE(toolpath_resolution, "toolpath.resolution");
    APPEND_BOOL(use_points_per_block, "use.points.per.block");
    APPEND_INT(points_per_block, "points.per.block");
    APPEND_INT(tool_xx0_color, "tool.xx0.color");
    APPEND_INT(tool_xx1_color, "tool.xx1.color");
    APPEND_INT(tool_xx2_color, "tool.xx2.color");
    APPEND_INT(tool_xx3_color, "tool.xx3.color");
    APPEND_INT(tool_xx4_color, "tool.xx4.color");
    APPEND_INT(tool_xx5_color, "tool.xx5.color");
    APPEND_INT(tool_xx6_color, "tool.xx6.color");
    APPEND_INT(tool_xx7_color, "tool.xx7.color");
    APPEND_INT(tool_xx8_color, "tool.xx8.color");
    APPEND_INT(tool_xx9_color, "tool.xx9.color");
    APPEND_INT(rapid_move_color, "rapid.move.color");
    APPEND_INT(rf_threshold, "rf.threshold");
    APPEND_INT(rf_threshold_color_lower, "rf.threshold.color.lower");
    APPEND_INT(rf_threshold_color_equal, "rf.threshold.color.equal");
    APPEND_INT(rf_threshold_color_upper, "rf.threshold.color.upper");
    APPEND_INT(rv_color_mode, "rv.color.mode");
    APPEND_INT(rv_wavelength_min, "rv.wavelength.min");
    APPEND_INT(rv_wavelength_max, "rv.wavelength.max");
    APPEND_INT(rv_gradient_color_min, "rv.gradient.color.min");
    APPEND_INT(rv_gradient_color_max, "rv.gradient.color.max");
    APPEND_INT(rz_color_mode, "rz.color.mode");
    APPEND_INT(rz_wavelength_min, "rz.wavelength.min");
    APPEND_INT(rz_wavelength_max, "rz.wavelength.max");
    APPEND_INT(rz_gradient_color_min, "rz.gradient.color.min");
    APPEND_INT(rz_gradient_color_max, "rz.gradient.color.max");

#undef APPEND_INT
#undef APPEND_BOOL
#undef APPEND_DOUBLE

    if (settings_count == 0) return false;
    request += '}';
    return execute_request(request);
}

bool CncAPIClientCore::set_dynamic_offset_x(double value) {
    if (!m_is_connected || !std::isfinite(value)) return false;
    return execute_request("{\"set\":\"dynamic.offsets\",\"offset.x\":" +
                           json_number(value) + "}");
}

bool CncAPIClientCore::set_dynamic_offset_y(double value) {
    if (!m_is_connected || !std::isfinite(value)) return false;
    return execute_request("{\"set\":\"dynamic.offsets\",\"offset.y\":" +
                           json_number(value) + "}");
}

bool CncAPIClientCore::set_dynamic_offset_z(double value) {
    if (!m_is_connected || !std::isfinite(value)) return false;
    return execute_request("{\"set\":\"dynamic.offsets\",\"offset.z\":" +
                           json_number(value) + "}");
}

bool CncAPIClientCore::set_dynamic_offsets(const double* x, const double* y, const double* z) {
    if (!m_is_connected || (x == nullptr && y == nullptr && z == nullptr)) return false;
    std::string request = "{";
    bool first = true;
    append_json_string(request, first, "set", "dynamic.offsets");
    if (x != nullptr) {
        if (!std::isfinite(*x)) return false;
        append_json_raw(request, first, "offset.x", json_number(*x));
    }
    if (y != nullptr) {
        if (!std::isfinite(*y)) return false;
        append_json_raw(request, first, "offset.y", json_number(*y));
    }
    if (z != nullptr) {
        if (!std::isfinite(*z)) return false;
        append_json_raw(request, first, "offset.z", json_number(*z));
    }
    request += '}';
    return execute_request(request);
}

bool CncAPIClientCore::set_kinematics() {
    // The Python v1.5.3 reference intentionally has no protocol implementation.
    return false;
}

bool CncAPIClientCore::set_operator_response(const APIOperatorResponse* response) {
    if (!m_is_connected || response == nullptr) return false;
    if (response->type != ORPT_CONTINUE && response->type != ORPT_STOP) return false;
    if (response->data_elements < 0 || response->data_elements > 10) return false;

    const double values[10] = {
        response->data_d01, response->data_d02, response->data_d03, response->data_d04,
        response->data_d05, response->data_d06, response->data_d07, response->data_d08,
        response->data_d09, response->data_d10
    };

    std::string request = "{";
    bool first = true;
    append_json_string(request, first, "set", "operator.response");
    append_json_string(request, first, "id", response->id);
    append_json_raw(request, first, "type", std::to_string(response->type));
    if (!first) request += ',';
    request += "\"data\":{\"elements\":" + std::to_string(response->data_elements);
    for (int i = 0; i < response->data_elements; ++i) {
        const std::string name = "d" + std::string(i + 1 < 10 ? "0" : "") +
                                 std::to_string(i + 1);
        request += ",\"" + name + "\":";
        request += std::isfinite(values[i]) ? json_number(values[i]) : "null";
    }
    request += "}}";
    return execute_request(request);
}

bool CncAPIClientCore::set_program_position_x_with_laser_reference(double value) {
    if (!m_is_connected || !std::isfinite(value)) return false;
    const APIScanningLaserInfo laser = get_scanning_laser_info();
    if (!laser.has_data) return false;
    return set_program_position_x(value - laser.laser_mcs_x_position);
}

bool CncAPIClientCore::set_program_position_y_with_laser_reference(double value) {
    if (!m_is_connected || !std::isfinite(value)) return false;
    const APIScanningLaserInfo laser = get_scanning_laser_info();
    if (!laser.has_data) return false;
    return set_program_position_y(value - laser.laser_mcs_y_position);
}

bool CncAPIClientCore::set_program_position_z_with_laser_reference(double value,
                                                                    int sample_count) {
    if (!m_is_connected || !std::isfinite(value) || sample_count < 1 || sample_count > 10) {
        return false;
    }
    std::vector<double> samples;
    samples.reserve(static_cast<size_t>(sample_count));
    for (int i = 0; i < sample_count; ++i) {
        const APIScanningLaserInfo laser = get_scanning_laser_info();
        if (!laser.has_data) return false;
        samples.push_back(laser.laser_mcs_z_position);
        std::this_thread::sleep_for(std::chrono::milliseconds(200));
    }
    std::sort(samples.begin(), samples.end());
    const size_t middle = samples.size() / 2;
    const double median = (samples.size() % 2 != 0)
        ? samples[middle]
        : (samples[middle - 1] + samples[middle]) / 2.0;
    return set_program_position_z(-median - value);
}

bool CncAPIClientCore::set_simulator_current_time_ms(int value) {
    if (!m_is_connected) return false;
    return execute_request("{\"set\":\"simulator.current.time.ms\",\"value\":" +
                           std::to_string(value) + "}");
}

bool CncAPIClientCore::set_simulator_speed_track(int value) {
    if (!m_is_connected) return false;
    return execute_request("{\"set\":\"simulator.speed.track\",\"value\":" +
                           std::to_string(value) + "}");
}

bool CncAPIClientCore::set_tools_lib_info(const APIToolsLibInfoForSet* info) {
    if (!m_is_connected || info == nullptr || info->tool_index == nullptr) return false;
    std::string request = "{";
    bool first = true;
    append_json_string(request, first, "set", "tools.lib.info");
    append_json_raw(request, first, "index", std::to_string(*info->tool_index));

#define APPEND_TOOL_INT(field, key) if (info->field != nullptr) \
    append_json_raw(request, first, key, std::to_string(*info->field))
#define APPEND_TOOL_DOUBLE(field, key) if (info->field != nullptr) { \
    if (!std::isfinite(*info->field)) return false; \
    append_json_raw(request, first, key, json_number(*info->field)); }
    APPEND_TOOL_INT(tool_id, "id"); APPEND_TOOL_INT(tool_slot, "slot");
    APPEND_TOOL_INT(tool_type, "type"); APPEND_TOOL_DOUBLE(tool_diameter, "diameter");
    APPEND_TOOL_DOUBLE(tool_offset_x, "offset.x");
    APPEND_TOOL_DOUBLE(tool_offset_y, "offset.y");
    APPEND_TOOL_DOUBLE(tool_offset_z, "offset.z");
    APPEND_TOOL_DOUBLE(tool_param_1, "param.1"); APPEND_TOOL_DOUBLE(tool_param_2, "param.2");
    APPEND_TOOL_DOUBLE(tool_param_3, "param.3"); APPEND_TOOL_DOUBLE(tool_param_4, "param.4");
    APPEND_TOOL_DOUBLE(tool_param_5, "param.5"); APPEND_TOOL_DOUBLE(tool_param_6, "param.6");
    APPEND_TOOL_DOUBLE(tool_param_7, "param.7"); APPEND_TOOL_DOUBLE(tool_param_8, "param.8");
    APPEND_TOOL_DOUBLE(tool_param_9, "param.9"); APPEND_TOOL_DOUBLE(tool_param_10, "param.10");
    APPEND_TOOL_DOUBLE(tool_param_51, "param.51"); APPEND_TOOL_DOUBLE(tool_param_52, "param.52");
    APPEND_TOOL_DOUBLE(tool_param_53, "param.53"); APPEND_TOOL_DOUBLE(tool_param_54, "param.54");
    APPEND_TOOL_DOUBLE(tool_param_55, "param.55"); APPEND_TOOL_DOUBLE(tool_param_56, "param.56");
    APPEND_TOOL_DOUBLE(tool_param_57, "param.57"); APPEND_TOOL_DOUBLE(tool_param_58, "param.58");
    APPEND_TOOL_DOUBLE(tool_param_59, "param.59"); APPEND_TOOL_DOUBLE(tool_param_60, "param.60");
#undef APPEND_TOOL_INT
#undef APPEND_TOOL_DOUBLE
    if (info->tool_description != nullptr) {
        append_json_string(request, first, "description", *info->tool_description);
    }
    request += '}';
    return execute_request(request);
}

bool CncAPIClientCore::set_wcs_info(int wcs, const std::vector<double>& offset,
                                    bool activate) {
    if (!m_is_connected || wcs < 1 || wcs > 9 || offset.size() != 6) return false;
    const char* axes[6] = {"x", "y", "z", "a", "b", "c"};
    bool has_offset = false;
    std::string offset_data = "{";
    bool first_offset = true;
    for (size_t i = 0; i < offset.size(); ++i) {
        if (std::isnan(offset[i])) continue;
        if (!std::isfinite(offset[i])) return false;
        append_json_raw(offset_data, first_offset, axes[i], json_number(offset[i]));
        has_offset = true;
    }
    offset_data += '}';
    if (!has_offset && !activate) return false;

    std::string request = "{";
    bool first = true;
    append_json_string(request, first, "set", "wcs.info");
    append_json_raw(request, first, "wcs", std::to_string(wcs));
    if (activate) append_json_raw(request, first, "activate", "true");
    append_json_raw(request, first, "data", offset_data);
    request += '}';
    return execute_request(request);
}

bool CncAPIClientCore::set_vm_geometry_info(const std::vector<APIVMGeometryInfo>& values) {
    if (!m_is_connected || values.empty()) return false;
    std::string request = "{\"set\":\"vm.geometry.info\",\"data\":[";
    for (size_t i = 0; i < values.size(); ++i) {
        const APIVMGeometryInfo& value = values[i];
        if (!std::isfinite(value.x) || !std::isfinite(value.y) || !std::isfinite(value.z) ||
            !std::isfinite(value.scale) || !std::isfinite(value.edges_angle)) return false;
        if (i > 0) request += ',';
        request += "{\"name\":\"" + SimpleJSON::escape(value.name) + "\"";
        request += ",\"x\":" + json_number(value.x);
        request += ",\"y\":" + json_number(value.y);
        request += ",\"z\":" + json_number(value.z);
        request += ",\"color\":" + std::to_string(value.color);
        request += ",\"scale\":" + json_number(value.scale);
        request += std::string(",\"visible\":") + (value.visible ? "true" : "false");
        request += ",\"edges.angle\":" + json_number(value.edges_angle);
        request += std::string(",\"edges.visible\":") +
                   (value.edges_visible ? "true" : "false") + "}";
    }
    request += "]}";
    return execute_request(request);
}

bool CncAPIClientCore::set_work_order_data(const std::string& order_code,
                                           const APIWorkOrderDataForSet& data) {
    if (!m_is_connected) return false;
    if (data.order_state != nullptr &&
        (*data.order_state < WO_ST_DRAFT || *data.order_state > WO_ST_ARCHIVED)) return false;
    if (data.order_priority != nullptr &&
        (*data.order_priority < WO_PR_LOWEST || *data.order_priority > WO_PR_HIGHEST)) return false;

    std::string order_data = "{";
    bool first_data = true;
    if (data.order_state != nullptr)
        append_json_raw(order_data, first_data, "order.state", std::to_string(*data.order_state));
    if (data.order_locked != nullptr)
        append_json_raw(order_data, first_data, "order.locked", *data.order_locked ? "true" : "false");
    if (data.order_priority != nullptr)
        append_json_raw(order_data, first_data, "order.priority", std::to_string(*data.order_priority));
    if (data.job_order_code != nullptr)
        append_json_string(order_data, first_data, "job.order.code", *data.job_order_code);
    if (data.customer_code != nullptr)
        append_json_string(order_data, first_data, "customer.code", *data.customer_code);
    if (data.item_code != nullptr)
        append_json_string(order_data, first_data, "item.code", *data.item_code);
    if (data.material_code != nullptr)
        append_json_string(order_data, first_data, "material.code", *data.material_code);
    if (data.order_notes != nullptr)
        append_json_string(order_data, first_data, "order.notes", *data.order_notes);
    if (data.use_deadline_datetime != nullptr) {
        append_json_raw(order_data, first_data, "use.deadline.datetime",
                        *data.use_deadline_datetime ? "true" : "false");
        if (data.deadline_datetime != nullptr) {
            append_json_raw(order_data, first_data, "deadline.datetime",
                            std::to_string(datetime_to_filetime(*data.deadline_datetime)));
        }
    }

    if (!data.files.empty()) {
        std::string files = "[";
        for (size_t i = 0; i < data.files.size(); ++i) {
            if (i > 0) files += ',';
            files += '{';
            bool first_file = true;
            if (data.files[i].file_name != nullptr)
                append_json_string(files, first_file, "file.name", *data.files[i].file_name);
            if (data.files[i].pieces_per_file != nullptr)
                append_json_raw(files, first_file, "pieces.per.file",
                                std::to_string(*data.files[i].pieces_per_file));
            if (data.files[i].requested_pieces != nullptr)
                append_json_raw(files, first_file, "requested.pieces",
                                std::to_string(*data.files[i].requested_pieces));
            files += '}';
        }
        files += ']';
        append_json_raw(order_data, first_data, "files", files);
    }
    order_data += '}';

    std::string request = "{";
    bool first = true;
    append_json_string(request, first, "set", "work.order.data");
    append_json_string(request, first, "order.code", order_code);
    append_json_raw(request, first, "data", order_data);
    request += '}';
    return execute_request(request);
}

bool CncAPIClientCore::set_override_jog(int value) {
    const std::string request = "{\"set\":\"override\",\"name\":\"jog\",\"value\":" + std::to_string(value) + "}";
    std::string response = send_command(request);
    return evaluate_response(response);
}

bool CncAPIClientCore::set_override_fast(int value) {
    const std::string request = "{\"set\":\"override\",\"name\":\"fast\",\"value\":" + std::to_string(value) + "}";
    std::string response = send_command(request);
    return evaluate_response(response);
}

bool CncAPIClientCore::set_override_feed(int value) {
    const std::string request = "{\"set\":\"override\",\"name\":\"feed\",\"value\":" + std::to_string(value) + "}";
    std::string response = send_command(request);
    return evaluate_response(response);
}

bool CncAPIClientCore::set_override_feed_custom_1(int value) {
    const std::string request = "{\"set\":\"override\",\"name\":\"feed.custom.1\",\"value\":" + std::to_string(value) + "}";
    std::string response = send_command(request);
    return evaluate_response(response);
}

bool CncAPIClientCore::set_override_feed_custom_2(int value) {
    const std::string request = "{\"set\":\"override\",\"name\":\"feed.custom.2\",\"value\":" + std::to_string(value) + "}";
    std::string response = send_command(request);
    return evaluate_response(response);
}

bool CncAPIClientCore::set_override_plasma_power(int value) {
    const std::string request = "{\"set\":\"override\",\"name\":\"plasma.power\",\"value\":" + std::to_string(value) + "}";
    std::string response = send_command(request);
    return evaluate_response(response);
}

bool CncAPIClientCore::set_override_plasma_voltage(int value) {
    const std::string request = "{\"set\":\"override\",\"name\":\"plasma.voltage\",\"value\":" + std::to_string(value) + "}";
    std::string response = send_command(request);
    return evaluate_response(response);
}

bool CncAPIClientCore::set_override_spindle(int value) {
    const std::string request = "{\"set\":\"override\",\"name\":\"spindle\",\"value\":" + std::to_string(value) + "}";
    std::string response = send_command(request);
    return evaluate_response(response);
}

bool CncAPIClientCore::set_cnc_parameters(int address, const std::vector<double>* values,
                                          const std::vector<std::string>* descriptions) {
    if (values == nullptr && descriptions == nullptr) {
        return false;
    }
    
    size_t v_count = (values != nullptr) ? values->size() : 0;
    size_t d_count = (descriptions != nullptr) ? descriptions->size() : 0;
    
    if (v_count == 0 && d_count == 0) {
        return false;
    }
    
    if (v_count > 0 && d_count > 0 && v_count != d_count) {
        return false;
    }
    
    // Build JSON manually for complex structure
    std::string request = "{\"set\":\"cnc.parameters\",\"address\":" + std::to_string(address);
    
    if (v_count > 0) {
        request += ",\"values\":[";
        for (size_t i = 0; i < v_count; i++) {
            request += std::to_string((*values)[i]);
            if (i < v_count - 1) request += ",";
        }
        request += "]";
    }
    
    if (d_count > 0) {
        request += ",\"descriptions\":[";
        for (size_t i = 0; i < d_count; i++) {
            request += "\"" + (*descriptions)[i] + "\"";
            if (i < d_count - 1) request += ",";
        }
        request += "]";
    }
    
    request += "}";
    
    std::string response = send_command(request);
    return evaluate_response(response);
}

bool CncAPIClientCore::set_localization(int units_mode, const std::string& locale_name) {
    const std::string normalized_locale = SimpleJSON::Parser::trim(locale_name);
    if (units_mode == -1 && normalized_locale.empty()) {
        return false;
    }
    
    // Validate units_mode if provided
    if (units_mode != -1 && units_mode != UM_METRIC && units_mode != UM_IMPERIAL) {
        return false;
    }
    
    // Build JSON request
    std::string request = "{\"set\":\"localization\"";
    
    if (units_mode != -1) {
        request += ",\"units.mode\":" + std::to_string(units_mode);
    }
    
    if (!normalized_locale.empty()) {
        request += ",\"locale.name\":\"" + escape_json_string(normalized_locale) + "\"";
    }
    
    request += "}";
    
    std::string response = send_command(request);
    return evaluate_response(response);
}

bool CncAPIClientCore::set_program_position_a(double value) {
    std::string request = "{\"set\":\"program.position\",\"data\":{\"a\":" + std::to_string(value) + "}}";
    std::string response = send_command(request);
    return evaluate_response(response);
}

bool CncAPIClientCore::set_program_position_b(double value) {
    std::string request = "{\"set\":\"program.position\",\"data\":{\"b\":" + std::to_string(value) + "}}";
    std::string response = send_command(request);
    return evaluate_response(response);
}

bool CncAPIClientCore::set_program_position_c(double value) {
    std::string request = "{\"set\":\"program.position\",\"data\":{\"c\":" + std::to_string(value) + "}}";
    std::string response = send_command(request);
    return evaluate_response(response);
}

bool CncAPIClientCore::set_program_position_x(double value) {
    std::string request = "{\"set\":\"program.position\",\"data\":{\"x\":" + std::to_string(value) + "}}";
    std::string response = send_command(request);
    return evaluate_response(response);
}

bool CncAPIClientCore::set_program_position_y(double value) {
    std::string request = "{\"set\":\"program.position\",\"data\":{\"y\":" + std::to_string(value) + "}}";
    std::string response = send_command(request);
    return evaluate_response(response);
}

bool CncAPIClientCore::set_program_position_z(double value) {
    std::string request = "{\"set\":\"program.position\",\"data\":{\"z\":" + std::to_string(value) + "}}";
    std::string response = send_command(request);
    return evaluate_response(response);
}

// ========== CncAPIInfoContext Implementation ==========

CncAPIInfoContext::CncAPIInfoContext(CncAPIClientCore* api) : m_api(api) {
    // Initialize all info structures
    axes_info.has_data = false;
    cnc_info.has_data = false;
    compile_info.has_data = false;
    enabled_commands.has_data = false;
}

bool CncAPIInfoContext::update() {
    if (!m_api || !m_api->is_connected()) {
        return false;
    }
    
    try {
        // Update all info from API
        axes_info = m_api->get_axes_info();
        cnc_info = m_api->get_cnc_info();
        compile_info = m_api->get_compile_info();
        enabled_commands = m_api->get_enabled_commands();
        
        // Return true if at least one has data
        return axes_info.has_data || cnc_info.has_data || 
               compile_info.has_data || enabled_commands.has_data;
    } catch (...) {
        return false;
    }
}

// ========== Continued in Part 2... ==========
// Due to file size, implementation of remaining API methods follows...
// NOTE: This is Part 1 of the implementation file
// The complete file would include all remaining cmd, get, and set method implementations
// matching the Python original exactly.

} // namespace RosettaCNC
