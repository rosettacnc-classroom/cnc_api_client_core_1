"""
    API cmd/get/set added with 1.5.2:

        cmd     tools.lib.add           add a new element in tools library with optional tool info
        cmd     tools.lib.clear         clear tools library
        cmd     tools.lib.delete        delete an element in tools library
        cmd     tools.lib.insert        insert a new elment in tools library with optional tool info

        get     tools.lib.count         get tools library elments count
        get     tools.lib.info          get tool info from tools library
        get     tools.lib.infos         get all tools infos from tools library
        get     tools.lib.tool.index    get index for a tool from tools library

        set     tools.lib.info          change indexed tool info in the tools library
"""
import cnc_api_client_core as api


# == BEG: log attributes
#
def log_command(command: str):
    print()
    print(command)
    print("=" * len(command))
#
# == END: log attributes


# == BEG: eval attributes
#
def eval_cmd_tools_lib_add(prefix: str = '', tool_info: api.APIToolsLibInfoForSet = api.APIToolsLibInfoForSet()) -> bool:
    log_command(f'{prefix}CMD: TOOLS LIB ADD')
    return core.tools_lib_add(tool_info)

def eval_cmd_tools_lib_clear(prefix: str = ''):
    log_command(f'{prefix}CMD: TOOLS LIB CLEAR')
    return core.tools_lib_clear()

def eval_cmd_tools_lib_delete(prefix: str = '', index: int = 0):
    log_command(f'{prefix}CMD: TOOLS LIB DELETE')
    return core.tools_lib_delete(index)

def eval_cmd_tools_lib_insert(prefix: str = '', tool_info: api.APIToolsLibInfoForSet = api.APIToolsLibInfoForSet()) -> bool:
    log_command(f'{prefix}CMD: TOOLS LIB INSERT')
    return core.tools_lib_insert(tool_info)

def eval_get_tools_lib_count(prefix: str = '') -> bool:
    log_command(f'{prefix}GET: TOOLS LIB COUNT')
    res = core.get_tools_lib_count()
    if not res.has_data:
        print("No data available")
        return False
    else:
        print('tools library elements count      =', res.count)
    return True

def eval_get_tools_lib_info(prefix: str = '', index: int = 0):
    log_command(f'{prefix}GET: TOOLS LIB INFO')
    res = core.get_tools_lib_info(index)
    if not res.has_data:
        print("No data available")
    else:
        print('  +======+======+======+======+======+=========+==========================================+')
        print('  |    # |  TID |  SID | TYPE | DIAM |  LENGHT |                              DESCRIPTION |')
        print('  +======+======+======+======+======+=========+==========================================+')
        s = (
            '  '
            f'| {res.data.tool_index:>4} '
            f'| {res.data.tool_id:>4} '
            f'| {res.data.tool_slot:>4} '
            f'| {res.data.tool_type:>4} '
            f'| {res.data.tool_diameter:>4} '
            f'| {res.data.tool_offset_z:>7} '
            f'| {res.data.tool_description:>40} '
            '|'
        )
        print(s)
        print('  +------+------+------+------+------+---------+------------------------------------------+')
        return True

def eval_get_tools_lib_infos(prefix: str = '') -> bool:
    log_command(f'{prefix}GET: TOOLS LIB INFOS')
    res = core.get_tools_lib_infos()
    if not res.has_data:
        print("No data available")
    else:
        print('slot_enabled                      =', res.slot_enabled)
        print('tools                             =', len(res.data))
        if res.data:
            print('  +======+======+======+======+======+=========+==========================================+')
            print('  |    # |  TID |  SID | TYPE | DIAM |  LENGHT |                              DESCRIPTION |')
            print('  +======+======+======+======+======+=========+==========================================+')
            for tool_info in res.data:
                s = (
                    '  '
                    f'| {tool_info.tool_index:>4} '
                    f'| {tool_info.tool_id:>4} '
                    f'| {tool_info.tool_slot:>4} '
                    f'| {tool_info.tool_type:>4} '
                    f'| {tool_info.tool_diameter:>4} '
                    f'| {tool_info.tool_offset_z:>7} '
                    f'| {tool_info.tool_description:>40} '
                    '|'
                )
                print(s)
                print('  +------+------+------+------+------+---------+------------------------------------------+')
    return True

def eval_get_tools_lib_tool_index_from_id(prefix: str = '', tool_id: int = None) -> bool:
    log_command(f'{prefix}GET: TOOLS LIB TOOL INDEX FROM ID')
    res = core.get_tools_lib_tool_index_from_id(tool_id)
    if not res.has_data:
        print("No data available")
        return False
    else:
        print('tools library index of tool id is =', res.index)
    return True

def eval_set_tools_lib_info(prefix: str = '', tool_info: api.APIToolsLibInfoForSet = api.APIToolsLibInfoForSet()) -> bool:
    log_command(f'{prefix}SET: TOOLS LIB INFO')
    return core.set_tools_lib_info(tool_info)
#
# == END: eval attributes


# connect with API server
core = api.CncAPIClientCore()
if not core.connect('127.0.0.1', 8000):
    print('ERROR: connection not possible')
    quit()

# evaluate logger
core.log_add("CONNECTED with API ( Unicode char for alpha α )")

# evaluate get tools.lib.infos
if not eval_get_tools_lib_infos('01]   '):
    print('Error: get tools.lib.infos')
    quit()

# evaluate cmd tools.lib.clear
if not eval_cmd_tools_lib_clear('02]   '):
    print('Error: cmd tools.lib.clear')
    quit()

# evaluate get tools.lib.infos
if not eval_get_tools_lib_infos('03]   '):
    print('Error: get tools.lib.infos')
    quit()

# evaluate cmd tools.lib.add (add 3 empty items in tools library)
if not eval_cmd_tools_lib_add('04.1] '):
    print('Error: cmd tools.lib.add')
    quit()
if not eval_cmd_tools_lib_add('04.2] '):
    print('Error: cmd tools.lib.add')
    quit()
if not eval_cmd_tools_lib_add('04.3] '):
    print('Error: cmd tools.lib.add')
    quit()

# evaluate get tools.lib.infos
if not eval_get_tools_lib_infos('05]   '):
    print('Error: get tools.lib.infos')
    quit()

# evaluate cmd tools.lib.add (add 1 item with info in tools library)
tool_info = api.APIToolsLibInfoForSet()
tool_info.tool_id = 2
tool_info.tool_slot = 5
tool_info.tool_type = 2
tool_info.tool_diameter = 6.0
tool_info.tool_offset_z = 135.871
tool_info.tool_description = 'Ball End Mill 6.0 mm'
if not eval_cmd_tools_lib_add('06]   ', tool_info):
    print('Error: cmd tools.lib.add')
    quit()

# evaluate get tools.lib.infos
if not eval_get_tools_lib_infos('07]   '):
    print('Error: get tools.lib.infos')
    quit()

# evaluate cmd tools.lib.insert (inset one item in 2nd position with info in tools library)
tool_info = api.APIToolsLibInfoForSet()
tool_info.tool_index = 1    # 0-based list so 1 = 2nd position
tool_info.tool_id = 1
tool_info.tool_slot = 4
tool_info.tool_type = 1
tool_info.tool_diameter = 20.0
tool_info.tool_offset_z = 50.12
tool_info.tool_description = 'Raw End Mill 20.0 mm'
if not eval_cmd_tools_lib_insert('08]   ', tool_info):
    print('Error: cmd tools.lib.insert')
    quit()

# evaluate get tools.lib.infos
if not eval_get_tools_lib_infos('08]   '):
    print('Error: get tools.lib.infos')
    quit()

# evaluate cmd tools.lib.delete (remove item from 3rd position)
if not eval_cmd_tools_lib_delete('09]   '):
    print('Error: cmd tools.lib.delete')
    quit()

# evaluate get tools.lib.infos
if not eval_get_tools_lib_infos('10]   '):
    print('Error: get tools.lib.infos')
    quit()

# evaluate set tools.lib.info
tool_info = api.APIToolsLibInfoForSet()
tool_info.tool_index = 1    # 0-based list so 1 = 2nd position
tool_info.tool_id = 3
tool_info.tool_slot = 2
tool_info.tool_type = 1
tool_info.tool_diameter = 10.0
tool_info.tool_offset_z = 150.323
tool_info.tool_description = 'Raw End Mill 10.0 mm'
if not eval_set_tools_lib_info('11]   ', tool_info):
    print('Error: set tools.lib.info')
    quit()

# evaluate get tools.lib.infos
if not eval_get_tools_lib_infos('12]   '):
    print('Error: get tools.lib.infos')
    quit()

if not eval_get_tools_lib_count('13]   '):
    print('Error: get tools.lib.count')
    quit()

# evaluate get tools.lib.info (get element 0)
if not eval_get_tools_lib_info('13]   ', 0):
    print('Error: get tools.lib.info')
    quit()

# evaluate get tools.lib.info (get element 3)
if not eval_get_tools_lib_info('14]   ', 3):
    print('Error: get tools.lib.info')
    quit()

# evaluate index of a tool (id) in a tools library list
if not eval_get_tools_lib_tool_index_from_id('15]   ', 3):
    print('Error: get tools.lib.tool_index_from_id')
    quit()
