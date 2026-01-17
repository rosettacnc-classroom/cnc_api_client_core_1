import time
import cnc_api_client_core as api

# constant things
AUX_FUNCS = [
    api.FS_NM_AUX_01, api.FS_NM_AUX_02, api.FS_NM_AUX_03, api.FS_NM_AUX_04,
    api.FS_NM_AUX_05, api.FS_NM_AUX_06, api.FS_NM_AUX_07, api.FS_NM_AUX_08,
    api.FS_NM_AUX_09, api.FS_NM_AUX_10, api.FS_NM_AUX_11, api.FS_NM_AUX_12,
    api.FS_NM_AUX_13, api.FS_NM_AUX_14, api.FS_NM_AUX_15, api.FS_NM_AUX_16,
    api.FS_NM_AUX_17, api.FS_NM_AUX_18, api.FS_NM_AUX_19, api.FS_NM_AUX_20,
    api.FS_NM_AUX_21, api.FS_NM_AUX_22, api.FS_NM_AUX_23, api.FS_NM_AUX_24,
    api.FS_NM_AUX_25, api.FS_NM_AUX_26, api.FS_NM_AUX_27, api.FS_NM_AUX_28,
    api.FS_NM_AUX_29, api.FS_NM_AUX_30, api.FS_NM_AUX_31, api.FS_NM_AUX_32,
]

AUX_HEADER = (
    "                      1 1 1 1 1 1 1 1 1 1 2 2 2 2 2 2 2 2 2 2 3 3 3\n"
    "    1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2\n"
    "   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+\n"
)

AUX_FOOTER = "   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+"

# connect with API server
core = api.CncAPIClientCore()
if not core.connect('127.0.0.1', 8000):
    print('ERROR: connection not possible')
    quit()

def slice_time(value: float = None):
    if isinstance(value, float):
        time.sleep(value)
    else:
        time.sleep(0.5)

def show_aux_outputs(text: str = None, add_new_line: bool = False):
    slice_time(0.1) # settle time to have aux.outputs refreshed state from NC Board
    res = core.get_cnc_info()
    if not res.has_data:
        return
    if add_new_line:
        print()
    if text is not None:
        print(text)
    bits = res.aux_outputs
    row = "   |" + "|".join(str((bits >> i) & 1) for i in range(32)) + "|"
    print(AUX_HEADER + row + "\n" + AUX_FOOTER)

# initial state with all to OFF or DEFAULT
core.cnc_change_function_state_mode(api.FS_NM_SPINDLE_CW, api.FS_MD_OFF)
core.cnc_change_function_state_mode(api.FS_NM_SPINDLE_CCW, api.FS_MD_OFF)
core.cnc_change_function_state_mode(api.FS_NM_TORCH, api.FS_MD_OFF)
core.cnc_change_function_state_mode(api.FS_NM_THC_DISABLED, api.FS_MD_OFF)
core.cnc_change_function_state_mode(api.FS_NM_MIST, api.FS_MD_OFF)
core.cnc_change_function_state_mode(api.FS_NM_FLOOD, api.FS_MD_OFF)
core.cnc_change_function_state_mode(api.FS_NM_JOG_MODE, api.FS_MD_JOG_MODE_DEFAULT)
for idx, aux_id in enumerate(AUX_FUNCS, start=1):
    core.cnc_change_function_state_mode(aux_id, api.FS_MD_OFF)
show_aux_outputs('- initial state with all to OFF or DEFAULT')
slice_time()

# forever loop
while True:
    # SPINDLE_CW -> ON -> slice time -> OFF
    # to be changed requires an active tool of type different than PROBE or PLASMA
    core.cnc_change_function_state_mode(api.FS_NM_SPINDLE_CW, api.FS_MD_ON)
    slice_time(2.0)
    core.cnc_change_function_state_mode(api.FS_NM_SPINDLE_CW, api.FS_MD_OFF)

    # SPINDLE_CCW -> ON -> slice time -> OFF
    # to be changed requires an active tool of type different than PROBE or PLASMA
    core.cnc_change_function_state_mode(api.FS_NM_SPINDLE_CCW, api.FS_MD_ON)
    slice_time(2.0)
    core.cnc_change_function_state_mode(api.FS_NM_SPINDLE_CCW, api.FS_MD_OFF)

    # TORCH -> ON -> slice time -> OFF
    # to be changed requires an active tool of type PLASMA
    core.cnc_change_function_state_mode(api.FS_NM_TORCH, api.FS_MD_ON)
    slice_time()
    core.cnc_change_function_state_mode(api.FS_NM_TORCH, api.FS_MD_OFF)

    # THC_DISABLED -> ON -> slice time -> OFF
    core.cnc_change_function_state_mode(api.FS_NM_THC_DISABLED, api.FS_MD_ON)
    slice_time()
    core.cnc_change_function_state_mode(api.FS_NM_THC_DISABLED, api.FS_MD_OFF)

    # MIST  -> ON -> slice time -> OFF
    core.cnc_change_function_state_mode(api.FS_NM_MIST, api.FS_MD_ON)
    slice_time()
    core.cnc_change_function_state_mode(api.FS_NM_MIST, api.FS_MD_OFF)

    # FLOOD  -> ON -> slice time -> OFF
    core.cnc_change_function_state_mode(api.FS_NM_FLOOD, api.FS_MD_ON)
    slice_time()
    core.cnc_change_function_state_mode(api.FS_NM_FLOOD, api.FS_MD_OFF)

    # JOG_MODE -> ALONG_TOOL -> slice time -> DEFAULT
    # to be chanced requires a kinematics with at least an HEAD axis and NC Feature "Jog Mode Selector" set to "None"
    core.cnc_change_function_state_mode(api.FS_NM_JOG_MODE, api.FS_MD_JOG_MODE_ALONG_TOOL)
    slice_time()
    core.cnc_change_function_state_mode(api.FS_NM_JOG_MODE, api.FS_MD_JOG_MODE_DEFAULT)

    # cycle of ON -> slice time > OFF for all aux digital outputs from AUX_01 to AUX_32
    for idx, aux_id in enumerate(AUX_FUNCS, start=1):
        core.cnc_change_function_state_mode(aux_id, api.FS_MD_ON)
        show_aux_outputs(f'- AUX_{idx:02d} -> ON:', True)
        slice_time()
        core.cnc_change_function_state_mode(aux_id, api.FS_MD_OFF)
        show_aux_outputs(f'  AUX_{idx:02d} -> OFF:')
