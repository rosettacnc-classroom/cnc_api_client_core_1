import time
import threading
import cnc_api_client_core as api

thread_job_enabled = False

def cnc_info_thread(core, stop_event):
    """Thread che richiama continuamente get_cnc_info()."""
    global thread_job_enabled
    while not stop_event.is_set():
        try:
            if thread_job_enabled:
                core.get_cnc_info()
                time.sleep(0.1)
                core.get_axes_info()
                time.sleep(0.1)
                core.get_digital_inputs()
            time.sleep(0.1)
        except Exception as e:
            print(f"Error in cnc_info_thread: {e}")
            #break

def main():
    # connect with API server
    global thread_job_enabled
    core = api.CncAPIClientCore()
    if not core.connect('127.0.0.1', 8000):
        print('ERROR: connection not possible')
        quit()

    # Crea evento per fermare il thread
    stop_event = threading.Event()

    # Avvia il thread per get_cnc_info()
    info_thread = threading.Thread(
        target=cnc_info_thread,
        args=(core, stop_event),
        daemon=True
    )
    info_thread.start()

    # define menu options
    MENU_OPTIONS = {
        "X": ("Connection Open", ""),   # this is not an UI Dialog but we use menu mechanism
        "Y": ("Connection Close", ""),  # this is not an UI Dialog but we use menu mechanism
        "T": ("Toogle Thread JOB", ""), # this is not an UI Dialog but we use menu mechanism
        "1": ("Program Settings", api.UID_PROGRAM_SETTINGS),
        "2": ("Work Coordinates", api.UID_WORK_COORDINATES),
        "3": ("Parameters Library", api.UID_PARAMETERS_LIBRARY),
        "4": ("Tools Library", api.UID_TOOLS_LIBRARY),
        "5": ("Board Monitor", api.UID_BOARD_MONITOR),
        "6": ("Board Settings", api.UID_BOARD_SETTINGS),
        "7": ("Board EtherCAT Monitor", api.UID_BOARD_ETHERCAT_MONITOR),
        "8": ("Change Board IP", api.UID_CHANGE_BOARD_IP),
        "9": ("Board Firmware Manager", api.UID_BOARD_FIRMWARE_MANAGER),
        "A": ("ATC Management", api.UID_ATC_MANAGEMENT),
        "B": ("Macros Management", api.UID_MACROS_MANAGEMENT),
        "C": ("About", api.UID_ABOUT),
    }

    # menu loop
    while True:
        # create dynamically the menu
        menu_text = "Choose which dialog UI to display:\n" + "=" * 34 + "\n\n"
        for key, (description, _) in MENU_OPTIONS.items():
            menu_text += f"{key} = {description}\n"
        menu_text += "0 = Exit\n\nInput: "

        # ask dialog to show
        try:
            s = input(menu_text).strip()
        except KeyboardInterrupt:
            s = 'q'

        if s.lower() == "q" or s == "0":
            print("Exit.")

            # Ferma il thread
            stop_event.set()
            info_thread.join(timeout=2)  # Attendi max 2 secondi
            break

        if s.lower() in ['x', 'y', 't']:
            if s == 'x':
                core.cnc_connection_open()
            elif s == 'y':
                core.cnc_connection_close()
            else:
                thread_job_enabled = not thread_job_enabled
        else:
            if s in MENU_OPTIONS:
                _, dialog_id = MENU_OPTIONS[s]
                core.show_ui_dialog(dialog_id)
            else:
                print(f"Invalid value. Enter a number between 1 and {len(MENU_OPTIONS)} or 0 to exit.")

if __name__ == '__main__':
    main()
