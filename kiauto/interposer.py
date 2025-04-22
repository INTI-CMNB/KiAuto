# -*- coding: utf-8 -*-
# Copyright (c) 2022-2024 Salvador E. Tropea
# Copyright (c) 2022-2024 Instituto Nacional de Tecnologïa Industrial
# License: Apache 2.0
# Project: KiAuto (formerly kicad-automation-scripts)
import atexit
import os
import platform
import psutil
from queue import Queue, Empty
import re
import shutil
from sys import exit, exc_info
from tempfile import mkdtemp
from time import sleep
from threading import Thread
import time
from traceback import extract_stack, format_list, print_tb
from kiauto.misc import KICAD_DIED, CORRUPTED_PCB, PCBNEW_ERROR, EESCHEMA_ERROR
from kiauto import log
from kiauto.ui_automation import xdotool, wait_for_window, wait_point, text_replace
from kiauto.file_util import wait_for_file_created_by_process

KICAD_EXIT_MSG = '>>exit<<'
INTERPOSER_OPS = 'interposer_options.txt'
IGNORED_DIALOG_MSGS = {'The quick brown fox jumps over the lazy dog.', '0123456789'}
BOGUS_FILENAME = '#'
KIKIT_HIDE = 'Specify which components to hide'
# These dialogs are asynchronous, they can pop-up at anytime.
# One example is when the .kicad_wks is missing, KiCad starts drawing and then detects it.
INFO_DIALOGS = {'KiCad PCB Editor Information', 'KiCad Schematic Editor Information'}
WARN_DIALOGS = {'KiCad PCB Editor Warning', 'KiCad Schematic Editor Warning'}
ASYNC_DIALOGS = INFO_DIALOGS | WARN_DIALOGS


def check_interposer(args, logger, cfg):
    # Name of the interposer library
    machine = platform.machine().lower()
    extra_name = '' if machine == 'x86_64' else '_'+machine
    interposer_lib = os.path.abspath(os.path.join(os.path.dirname(__file__), 'interposer', f'libinterposer{extra_name}.so'))
    logger.debug(f'Looking for interposer lib: {interposer_lib}')
    if (not os.path.isfile(interposer_lib) or  # The lib isn't there
       args.disable_interposer or              # The user disabled it
       os.environ.get('KIAUTO_INTERPOSER_DISABLE') or  # The user disabled it using the environment
       platform.system() != 'Linux'):  # Not Linux
        interposer_lib = None
    else:
        os.environ['LD_PRELOAD'] = interposer_lib
        logger.debug('** Interposer lib found')
    cfg.use_interposer = interposer_lib
    cfg.enable_interposer = interposer_lib or args.interposer_sniff
    cfg.logger = logger


def dump_interposer_dialog(cfg):
    cfg.logger.debug('Storing interposer dialog ({})'.format(cfg.flog_int.name))
    if cfg.enable_interposer and not cfg.use_interposer:
        try:
            while True:
                tm, line = cfg.kicad_q.get(timeout=.1)
                tm *= 1000
                diff = 0
                if cfg.last_msg_time:
                    diff = tm-cfg.last_msg_time
                cfg.last_msg_time = tm
                cfg.interposer_dialog.append('>>Interposer<<:{} (@{} D {})'.format(line[:-1], round(tm, 3), round(diff, 3)))
        except Empty:
            pass
    if hasattr(cfg, 'interposer_dialog'):
        for ln in cfg.interposer_dialog:
            cfg.flog_int.write(ln+'\n')
    cfg.flog_int.close()


def remove_interposer_print_dir(cfg):
    cfg.logger.debug('Removing temporal dir '+cfg.interposer_print_dir)
    shutil.rmtree(cfg.interposer_print_dir, ignore_errors=True)


def create_interposer_print_options_file(cfg):
    """ Creates a temporal holder for the print options """
    # We need a file to save the print options, make it unique to avoid collisions
    cfg.interposer_print_dir = mkdtemp()
    cfg.interposer_print_file = os.path.join(cfg.interposer_print_dir, INTERPOSER_OPS)
    cfg.logger.debug('Using temporal file {} for interposer print options'.format(cfg.interposer_print_file))
    os.environ['KIAUTO_INTERPOSER_PRINT'] = cfg.interposer_print_file
    atexit.register(remove_interposer_print_dir, cfg)


def save_interposer_print_data(cfg, tmpdir, fn, ext):
    """ Write the print options to the created file """
    with open(cfg.interposer_print_file, 'wt') as f:
        f.write(tmpdir+'\n')
        f.write(fn+'\n')
        f.write(ext+'\n')
    return os.path.join(tmpdir, fn+'.'+ext)


# def flush_queue():
#     """ Thread safe queue flush """
#     with cfg.kicad_q.mutex:
#         cfg.kicad_q.queue.clear()


def enqueue_output(out, queue):
    """ Read 1 line from the interposer and add it to the queue.
        Notes:
        * The queue is thread safe.
        * When we get an empty string we finish, this is the case for KiCad finished """
    tm_start = time.time()
    for line in iter(out.readline, ''):
        if (line.startswith('PANGO:') or line.startswith('GTK:') or line.startswith('IO:') or line.startswith('GLX:') or
           line.startswith('* ')):
            queue.put((time.time()-tm_start, line))
        # logger.error((time.time()-tm_start, line))
    out.close()


# https://stackoverflow.com/questions/375427/a-non-blocking-read-on-a-subprocess-pipe-in-python
def start_queue(cfg):
    """ Create a communication queue in a separated thread.
        It will collect all messages from the interposer. """
    if not cfg.enable_interposer:
        return
    cfg.logger.debug('Starting queue thread')
    cfg.kicad_q = Queue()
    # Avoid crashes when KiCad 5 sends an invalid Unicode sequence
    cfg.popen_obj.stdout.reconfigure(errors='ignore')
    cfg.kicad_t = Thread(target=enqueue_output, args=(cfg.popen_obj.stdout, cfg.kicad_q))
    cfg.kicad_t.daemon = True   # thread dies with the program
    cfg.kicad_t.start()
    cfg.collecting_io = False
    cfg.last_msg_time = 0
    cfg.interposer_dialog = []


def collect_io_from_queue(cfg):
    cfg.collected_io = set()
    cfg.collecting_io = True


def wait_queue(cfg, strs='', starts=False, times=1, timeout=300, do_to=True, kicad_can_exit=False, with_windows=False,
               dialog_interrupts=False):
    """ Wait for a string in the queue """
    if not cfg.use_interposer:
        return None
    if isinstance(strs, str):
        strs = [strs]
    end_time = time.time()+timeout*cfg.time_out_scale
    msg = 'Waiting for `{}` starts={} times={}'.format(strs, starts, times)
    cfg.interposer_dialog.append('KiAuto:'+msg)
    if cfg.verbose > 1:
        cfg.logger.debug(msg)
    while time.time() < end_time:
        try:
            tm, line = cfg.kicad_q.get(timeout=.1)
            line = line[:-1]
            if cfg.verbose > 1:
                tm *= 1000
                diff = 0
                if cfg.last_msg_time:
                    diff = tm-cfg.last_msg_time
                cfg.last_msg_time = tm
                cfg.logger.debug('>>Interposer<<:{} (@{} D {})'.format(line, round(tm, 3), round(diff, 3)))
            cfg.interposer_dialog.append(line)
            # The I/O can be in parallel to the UI
            if cfg.collecting_io and line.startswith('IO:'):
                cfg.collected_io.add(line)
        except Empty:
            line = ''
        if line == '' and cfg.popen_obj.poll() is not None:
            if kicad_can_exit:
                return KICAD_EXIT_MSG
            cfg.logger.error('KiCad unexpectedly died (error level {})'.format(cfg.popen_obj.poll()))
            exit(KICAD_DIED)
        old_times = times
        for s in strs:
            if s == '':
                # Waiting for anything ... but not for nothing
                if line != '':
                    return line
                continue
            if starts:
                if line.startswith(s):
                    times -= 1
                    break
            elif line == s:
                times -= 1
                break
        if times == 0:
            cfg.interposer_dialog.append('KiAuto:match')
            cfg.logger.debug('Interposer match: '+line)
            return line
        if old_times != times:
            cfg.interposer_dialog.append('KiAuto:times '+str(times))
            cfg.logger.debug('Interposer match, times='+str(times))
        if (not with_windows and not kicad_can_exit and line.startswith('GTK:Window Title:') and
            # The change in the unsaved status is ignored here
           not (not cfg.ki5 and line.endswith(cfg.window_title_end))):
            # We aren't expecting a window, but something seems to be there
            # Note that window title change is normal when we expect KiCad exiting
            title = line[17:]
            if title in INFO_DIALOGS:
                # Async dialogs
                dismiss_pcb_info(cfg, title)
            elif title == 'pcbnew Warning' or title in WARN_DIALOGS:
                # KiCad 5 error during post-load, before releasing the CPU
                # KiCad 7 missing fonts
                dismiss_pcbnew_warning(cfg, title)
            elif cfg.ki8 and title == 'KiCad PCB Editor Error':
                dismiss_pcbnew_error(cfg, title)
            elif title.startswith(KIKIT_HIDE):
                # Buggy KiKit plugin creating a dialog at start-up (many times)
                pass
            else:
                unknown_dialog(cfg, title)
            if dialog_interrupts:
                raise InterruptedError()
    if do_to:
        raise RuntimeError('Timed out waiting for `{}`'.format(strs))


def wait_swap(cfg, times=1, kicad_can_exit=False):
    """ Wait an OpenGL draw (buffer swap) """
    if not cfg.use_interposer or not times:
        return None
    return wait_queue(cfg, 'GLX:Swap', starts=True, times=times, kicad_can_exit=kicad_can_exit)


def set_kicad_process(cfg, pid):
    """ Translates the PID into a psutil object, stores it in cfg """
    for process in psutil.process_iter():
        if process.pid == pid:
            cfg.kicad_process = process
            break
    else:
        cfg.logger.error('Unable to map KiCad PID to a process')
        exit(1)


def wait_kicad_ready_i(cfg, swaps=0, kicad_can_exit=False):
    res = wait_swap(cfg, swaps, kicad_can_exit=kicad_can_exit)
    # KiCad 5 takes 0 to 2 extra swaps (is random) so here we ensure KiCad is sleeping
    status = cfg.kicad_process.status()
    if status != psutil.STATUS_SLEEPING:
        if swaps:
            cfg.logger.debug('= KiCad still running after {} swaps, waiting more'.format(swaps))
        else:
            cfg.logger.debug('= KiCad still running, waiting more')
        try:
            while cfg.kicad_process.status() != psutil.STATUS_SLEEPING:
                new_res = wait_queue(cfg, 'GLX:Swap', starts=True, timeout=0.1, do_to=False, kicad_can_exit=kicad_can_exit)
                if new_res is not None:
                    res = new_res
        except psutil.NoSuchProcess:
            cfg.logger.debug('= KiCad died')
            return KICAD_EXIT_MSG
        cfg.logger.debug('= KiCad finally sleeping')
    else:
        cfg.logger.debug('= KiCad already sleeping ({})'.format(status))
    return res


def open_dialog_i(cfg, name, keys, no_show=False, no_wait=False, no_main=False, extra_msg=None, raise_if=None):
    wait_point(cfg)
    # Wait for KiCad to be sleeping
    wait_kicad_ready_i(cfg)
    cfg.logger.info('Opening dialog `{}` {}'.format(name, '('+extra_msg+')' if extra_msg is not None else ''))
    # cfg.logger.error('Durmiendo')
    # time.sleep(4)
    # cfg.logger.error('Despertando')
    if isinstance(keys, str):
        keys = ['key', keys]
    xdotool(keys)
    pre_gtk_title = 'GTK:Window Title:'
    pre_gtk = pre_gtk_title if no_show else 'GTK:Window Show:'
    if isinstance(name, str):
        name = [name]
    name_w_pre = [pre_gtk+f for f in name]
    if raise_if is not None:
        name_w_pre.extend(raise_if)
    # Add the async dialogs
    for t in ASYNC_DIALOGS:
        name_w_pre.append(pre_gtk_title+t)
    # Wait for our dialog or any async dialog
    # Note: wait_queue won't dismiss them because we use "with_windows=True"
    while True:
        res = wait_queue(cfg, name_w_pre, with_windows=True)
        if raise_if is not None and res in raise_if:
            raise InterruptedError()
        title = res[len(pre_gtk_title):]
        if title not in ASYNC_DIALOGS:
            break
        if title in INFO_DIALOGS:
            # Get rid of the info dialog
            dismiss_pcb_info(cfg, title)
        else:
            dismiss_pcbnew_warning(cfg, title)
        # Send the keys again
        xdotool(keys)
    name = res[len(pre_gtk):]
    if no_wait:
        return name, None
    if not no_main:
        wait_queue(cfg, 'GTK:Main:In')
    # Wait for KiCad to be sleeping
    wait_kicad_ready_i(cfg)
    # The dialog is there, just make sure it has the focus
    return name, wait_for_window(name, name, 1)[0]


def check_text_replace(cfg, name):
    """ Wait until we get the file name """
    wait_queue(cfg, 'PANGO:'+name, dialog_interrupts=True)


def paste_text_i(cfg, msg, text):
    """ Paste some text and check the echo from KiCad, then wait for sleep """
    # Paste the name
    cfg.logger.info('{} ({})'.format(msg, text))
    wait_point(cfg)
    retry = True
    while retry:
        retry = False
        text_replace(text)
        try:
            # Look for the echo
            check_text_replace(cfg, text)
        except InterruptedError:
            cfg.logger.debug('Interrupted by a dialog while waiting echo, retrying')
            retry = True
    # Wait for KiCad to be sleeping
    wait_kicad_ready_i(cfg)


def paste_output_file_i(cfg, use_dir=False):
    """ Paste the output file/dir and check the echo from KiCad, then wait for sleep """
    name = cfg.output_dir if use_dir else cfg.output_file
    paste_text_i(cfg, 'Pasting output file', name)


def paste_bogus_filename(cfg):
    # We paste a bogus name that will be replaced
    paste_text_i(cfg, 'Paste bogus short name', BOGUS_FILENAME)


def setup_interposer_filename(cfg, fn=None):
    """ Defines the file name used by the interposer to fake the file choosers """
    if not cfg.use_interposer:
        return
    if fn is None:
        fn = cfg.output_file
    os.environ['KIAUTO_INTERPOSER_FILENAME'] = fn
    if os.path.isfile(BOGUS_FILENAME):
        cfg.logger.warning('Removing bogus file `{}`'.format(BOGUS_FILENAME))
        os.remove(BOGUS_FILENAME)


def send_keys(cfg, msg, keys, closes=None, delay_io=False, no_destroy=False):
    cfg.logger.info(msg)
    wait_point(cfg)
    if isinstance(keys, str):
        keys = ['key', keys]
    if delay_io:
        collect_io_from_queue(cfg)
    xdotool(keys)
    if closes is not None:
        if no_destroy:
            wait_close_dialog_i(cfg)
        else:
            if isinstance(closes, str):
                closes = [closes]
            for w in closes:
                try:
                    wait_queue(cfg, 'GTK:Window Destroy:'+w, dialog_interrupts=True)
                except InterruptedError:
                    # KiCad 7.99
                    xdotool(keys)
        wait_kicad_ready_i(cfg)


def wait_create_i(cfg, name, fn=None, forced_ext=None):
    """ Wait for open+close of the file.
        Also look for them in the collected_io messages.
        And if we just get close forget about the open. """
    cfg.logger.info('Wait for '+name+' file creation')
    wait_point(cfg)
    if fn is None:
        fn = cfg.output_file
    fn_kicad = fn+'.'+forced_ext if forced_ext and cfg.ki8 else fn
    # Experimental option to use the PID approach
    # Could help for VirtioFS where the close seems to be somehow bypassed
    use_pid = os.environ.get('KIAUTO_USE_PID_FOR_CREATE')
    if use_pid is not None and use_pid != '0':
        pid = cfg.pcbnew_pid if hasattr(cfg, 'pcbnew_pid') else cfg.eeschema_pid
        return wait_for_file_created_by_process(pid, fn_kicad)
    # Normal mechanism using the interposer
    open_msg = 'IO:open:'+fn_kicad
    close_msg = 'IO:close:'+fn_kicad
    if cfg.collecting_io:
        cfg.collecting_io = False
        got_open = open_msg in cfg.collected_io
        got_close = close_msg in cfg.collected_io
    else:
        got_open = False
        got_close = False
    if got_open or got_close:
        if got_open:
            cfg.logger.debug('Found IO '+open_msg)
    else:
        msg = wait_queue(cfg, [open_msg, close_msg], starts=True)
        got_close = msg.startswith(close_msg)
    if got_close:
        cfg.logger.debug('Found IO '+close_msg)
    else:
        wait_queue(cfg, close_msg, starts=True)
    wait_kicad_ready_i(cfg)
    if forced_ext and cfg.ki8 and os.path.isfile(fn_kicad):
        os.rename(fn_kicad, fn)


def collect_dialog_messages(cfg, title):
    cfg.logger.info(title+' dialog found ...')
    cfg.logger.debug('Gathering potential dialog content')
    msgs = set()
    for msg in range(12):
        res = wait_queue(cfg, 'PANGO:', starts=True, timeout=0.1, do_to=False)
        if res is None:
            # Some dialogs has less messages
            continue
        res = res[6:]
        if res not in IGNORED_DIALOG_MSGS:
            msgs.add(res)
    cfg.logger.debug('Messages: '+str(msgs))
    return msgs


def exit_pcb_ees_error(cfg):
    exit(PCBNEW_ERROR if cfg.is_pcbnew else EESCHEMA_ERROR)


def trace_dump(cfg):
    cfg.logger.error('Trace stack:')
    (type, value, traceback) = exc_info()
    if traceback is None:
        print(''.join(format_list(extract_stack()[:-2])))
    else:
        print_tb(traceback)


def unknown_dialog(cfg, title, msgs=None, fatal=True):
    if msgs is None:
        msgs = collect_dialog_messages(cfg, title)
    msg_unk = 'Unknown KiCad dialog: '+title
    msg_msgs = 'Potential dialog messages: '+str(msgs)
    if fatal:
        cfg.logger.error(msg_unk)
        cfg.logger.error(msg_msgs)
        trace_dump(cfg)
        exit_pcb_ees_error(cfg)
    cfg.logger.warning(msg_unk)
    cfg.logger.warning(msg_msgs)


def dismiss_dialog(cfg, title, keys):
    cfg.logger.debug('Dismissing dialog `{}` using {}'.format(title, keys))
    try:
        wait_for_window(title, title, 2)
    except RuntimeError:
        # The window was already closed
        return
    if isinstance(keys, str):
        keys = [keys]
    xdotool(['key']+keys)


def dismiss_error(cfg, title):
    """ KiCad 6/7: Corrupted PCB/Schematic
        KiCad 5: Newer KiCad needed  for PCB, missing sch lib """
    msgs = collect_dialog_messages(cfg, title)
    if "Error loading PCB '"+cfg.input_file+"'." in msgs:
        # KiCad 6 PCB loading error
        cfg.logger.error('Error loading PCB file. Corrupted?')
        exit(CORRUPTED_PCB)
    if "Error loading schematic '"+cfg.input_file+"'." in msgs:
        # KiCad 6 schematic loading error
        cfg.logger.error('Error loading schematic file. Corrupted?')
        exit(EESCHEMA_ERROR)
    if 'KiCad was unable to open this file, as it was created with' in msgs:
        # KiCad 5 PCBnew loading a KiCad 6 file
        cfg.logger.error('Error loading PCB file. Needs KiCad 6?')
        exit(CORRUPTED_PCB)
    if 'Use the Manage Symbol Libraries dialog to fix the path (or remove the library).' in msgs:
        # KiCad 5 Eeschema missing lib. Should be a warning, not an error dialog
        cfg.logger.warning('Missing libraries, please fix it')
        dismiss_dialog(cfg, title, 'Return')
        return
    if 'The entire schematic could not be loaded.  Errors occurred attempting to load hierarchical sheets.' in msgs:
        # KiCad 6 loading a sheet, but sub-sheets are missing
        cfg.logger.error('Error loading schematic file. Missing schematic files?')
        exit(EESCHEMA_ERROR)
    if ("Failed to inspect the lock file '/tmp/org.kicad.kicad/instances/pcbnew-8.0' (error 2: No such file or directory)"
       in msgs):
        # KiCad 8.0.0RC2 glitch
        cfg.logger.warning('KiCad 8 lock glitch')
        dismiss_dialog(cfg, title, 'Return')
        return
    for msg in msgs:
        if msg.startswith("Error loading schematic '"+cfg.input_file+"'."):
            # KiCad 7 schematic loading error
            cfg.logger.error('Error loading schematic file. Corrupted?')
            exit(EESCHEMA_ERROR)
    unknown_dialog(cfg, title, msgs)


def dismiss_file_open_error(cfg, title):
    """ KiCad 6: File is already opened """
    msgs = collect_dialog_messages(cfg, title)
    kind = 'PCB' if cfg.is_pcbnew else 'Schematic'
    fname = os.path.basename(cfg.input_file)
    # KiCad 6.x and <7.0.7: PCB 'xxxx' is already open.
    # KiCad 7.0.7: PCB 'xxxx' is already open by 'user' at 'host'
    # KiCad 8.0.1: PCB 'ABSOLUTE/xxxx' is already open by 'user' at 'host'
    start = kind+" '"
    follow = "' is already open"
    found = False
    cfg.logger.error(start)
    for msg in msgs:
        if msg.startswith(start) and follow in msg and msg.endswith("."):
            found = True
            fname = msg
            break
    if 'Open Anyway' in msgs and found:
        cfg.logger.warning('This file is already opened ({})'.format(fname))
        dismiss_dialog(cfg, title, ['Left', 'Return'])
        return
    unknown_dialog(cfg, title, msgs)


def dismiss_already_running(cfg, title):
    """ KiCad 5: Program already running """
    msgs = collect_dialog_messages(cfg, title)
    kind = 'pcbnew' if cfg.is_pcbnew else 'eeschema'
    if kind+' is already running. Continue?' in msgs:
        cfg.logger.warning(kind+' is already running')
        dismiss_dialog(cfg, title, 'Return')
        return
    unknown_dialog(cfg, title, msgs)


def dismiss_warning(cfg, title):
    """ KiCad 5 when already open file (PCB/SCH)
        KiCad 5 with bogus SCH files """
    msgs = collect_dialog_messages(cfg, title)
    kind = 'PCB' if cfg.is_pcbnew else 'Schematic'
    if kind+' file "'+cfg.input_file+'" is already open.' in msgs:
        cfg.logger.error('File already opened by another KiCad instance')
        exit_pcb_ees_error(cfg)
    if 'Error loading schematic file "'+os.path.abspath(cfg.input_file)+'".' in msgs:
        cfg.logger.error('eeschema reported an error while loading the schematic')
        exit(EESCHEMA_ERROR)
    unknown_dialog(cfg, title, msgs)


def dismiss_pcbnew_warning(cfg, title):
    """ Pad in invalid layer
        Missing font """
    msgs = collect_dialog_messages(cfg, title)
    # More generic cases
    for msg in msgs:
        # Warning about pad using an invalid layer
        # Missing font
        if msg.endswith("could not find valid layer for pad") or \
           re.search(r"Font '(.*)' not found; substituting '(.*)'", msg) or \
           msg.startswith("Altium layer"):
            cfg.logger.warning(msg)
            dismiss_dialog(cfg, title, 'Return')
            return
    unknown_dialog(cfg, title, msgs)


def dismiss_pcbnew_error(cfg, title):
    """ lock glitch in 8.0.0RC2 """
    msgs = collect_dialog_messages(cfg, title)
    # More generic cases
    for msg in msgs:
        if msg.startswith("Failed to inspect the lock file"):
            cfg.logger.warning(msg)
            dismiss_dialog(cfg, title, 'Return')
            return
    unknown_dialog(cfg, title, msgs)


def dismiss_remap_symbols(cfg, title):
    """ KiCad 5 opening an old file """
    msgs = collect_dialog_messages(cfg, title)
    if "Output Messages" in msgs and "Close" in msgs:
        cfg.logger.warning('Schematic needs update')
        dismiss_dialog(cfg, title, ['Escape'])
        return
    unknown_dialog(cfg, title, msgs)


def dismiss_remap_layers(cfg, title):
    """ KiCad 9 importing Altium files """
    wait_queue(cfg, 'GTK:Main:In')
    dismiss_dialog(cfg, title, ['alt+l'])
    time.sleep(1)
    dismiss_dialog(cfg, title, ['alt+l', 'alt+o'])


def dismiss_save_changes(cfg, title):
    """ KiCad 5/6 asking for save changes to disk """
    msgs = collect_dialog_messages(cfg, title)
    if ("Save changes to '"+os.path.basename(cfg.input_file)+"' before closing?" in msgs or   # KiCad 6
       "If you don't save, all your changes will be permanently lost." in msgs):  # KiCad 5
        dismiss_dialog(cfg, title, ['Left', 'Left', 'Return'])
        return
    cfg.logger.error('Save dialog without correct messages')
    exit_pcb_ees_error(cfg)


def dismiss_pcb_info(cfg, title):
    """ KiCad 6 information, we know about missing worksheet style """
    msgs = collect_dialog_messages(cfg, title)
    found = False
    for msg in msgs:
        if msg.startswith("Drawing sheet ") and msg.endswith(" not found."):
            cfg.logger.warning("Missing worksheet file (.kicad_wks)")
            cfg.logger.warning(msg)
            found = True
            break
        else:
            ma = re.search(r"Font '(.*)' not found; substituting '(.*)'", msg)
            if ma:
                cfg.logger.warning(f"Missing '{ma.group(1)}' font")
                cfg.logger.warning("KiCad message: "+msg)
                found = True
                break
    if not found:
        unknown_dialog(cfg, title, msgs, fatal=False)
    dismiss_dialog(cfg, title, 'Return')


def exit_kicad_i(cfg):
    wait_kicad_ready_i(cfg)
    send_keys(cfg, 'Exiting KiCad', 'ctrl+q')
    pre = 'GTK:Window Title:'
    pre_l = len(pre)
    retries = 3
    while True:
        # Wait for any window
        res = wait_queue(cfg, pre, starts=True, timeout=2, kicad_can_exit=True, do_to=False, with_windows=True)
        known_dialog = False
        if res is not None:
            cfg.logger.debug('exit_kicad_i got '+res)
            if res == KICAD_EXIT_MSG:
                return
            title = res[pre_l:]
            if title == 'Save Changes?' or title == '':  # KiCad 5 without title!!!!
                dismiss_save_changes(cfg, title)
                known_dialog = True
            elif title == 'Pcbnew —  [Unsaved]':
                # KiCad 5 does it
                known_dialog = True
            else:
                unknown_dialog(cfg, title)
        retries -= 1
        if not retries:
            cfg.logger.error("Can't exit KiCad")
            return
        if not known_dialog:
            cfg.logger.warning("Retrying KiCad exit")
        # Wait until KiCad is sleeping again
        wait_kicad_ready_i(cfg, kicad_can_exit=True)
        # Retry the exit
        xdotool(['key', 'ctrl+q'])


def wait_close_dialog_i(cfg):
    """ Wait for the end of the main loop for the dialog.
        Then the main loop for the parent exits and enters again. """
    wait_queue(cfg, 'GTK:Main:Out')
    wait_queue(cfg, 'GTK:Main:In')


def wait_and_show_progress(cfg, msg, regex_str, trigger, msg_reg, skip_match=None, with_windows=False):
    """ msg: The message we are waiting
        regex_str: A regex to extract the progress message (text after PANGO:)
        trigger: A text that must be start at the beginning to test using the regex (PANGO:trigger)
        msg_reg: Message to print before the info (msg_reg: MATCH)
        skip_match: A match that we will skip
        with_windows: KiCad could pop-up a window """
    pres = [msg, 'PANGO:'+trigger]
    regex = re.compile(regex_str)
    with_info = False
    padding = 80*' '
    while True:
        res = wait_queue(cfg, pres, starts=True, with_windows=with_windows)
        if res.startswith(msg):
            # End of process detected
            if with_info:
                log.flush_info()
            wait_kicad_ready_i(cfg)
            return
        # Check if this message contains progress information
        if cfg.verbose and res.startswith('PANGO:'):
            res = res[6:]
            match = regex.match(res)
            if match is not None:
                m = match.group(1)
                if skip_match is None or m != skip_match:
                    m = msg_reg+': '+m+padding
                    log.info_progress(m[:80])
                    with_info = True


def wait_start_by_msg(cfg):
    if cfg.is_pcbnew:
        kind = 'PCB'
        prg_name = 'Pcbnew'
        unsaved = '  [Unsaved]'
    else:
        kind = 'Schematic'
        prg_name = 'Eeschema'
        unsaved = ' noname.sch'
    cfg.logger.info('Waiting for {} window ...'.format(prg_name))
    pre1 = 'GTK:Window Title:'
    pre1_l = len(pre1)
    pre2 = 'GTK:Window Set Modal:'
    pre2_l = len(pre2)
    cfg.logger.debug('Waiting {} to start and load the {}'.format(prg_name, kind))
    # Inform the elapsed time for slow loads
    pres = [pre1, pre2, 'PANGO:0:']
    elapsed_r = re.compile(r'PANGO:(\d:\d\d:\d\d)')
    loading_msg = 'Loading '+kind
    prg_msg = prg_name+' —'
    with_elapsed = False
    modals = []
    while True:
        # Wait for any window
        res = wait_queue(cfg, pres, starts=True, timeout=cfg.wait_start, with_windows=True)
        cfg.logger.debug('wait_start_by_msg got '+res)
        match = elapsed_r.match(res)
        title = res[pre1_l:]
        # The following code deals with the elusive "Report" dialog
        # This dialog is always created, but if filled it becomes modal
        if res.startswith(pre2):
            modal = res[pre2_l:]
            cfg.logger.debug(f"Detected window changing modal status: `{modal}`")
            if modal[-1] == '1':
                modals.append(modal[:-2])
            elif modal[-1] == '0' and modal[:-2] in modals:
                modals.remove(modal[:-2])
                if len(modals):
                    name = modals[-1]
                    cfg.logger.error(f'Insisting with nested modal `{name}`')
                    dismiss_dialog(cfg, modals[-1], ['Tab', 'Return'] if name == 'Report' else 'Return')
            if modal == 'Report 1':
                # Return is not enough, OK is not the default
                dismiss_dialog(cfg, 'Report', ['Tab', 'Return'])
            elif modal == 'Edit Mapping of Imported Layers 1':
                dismiss_remap_layers(cfg, modal[:-2])
            continue
        if not match and with_elapsed:
            log.flush_info()
        if not cfg.ki5 and title.endswith(cfg.window_title_end):
            # KiCad 6
            if title.startswith('[no schematic loaded]'):
                # False alarma, nothing loaded
                continue
            # KiCad finished the load process
            if title[0] == '*':
                # This is an old format file that will be saved in the new format
                cfg.logger.warning('Old file format detected, please convert it to KiCad 6 if experimenting problems')
            wait_queue(cfg, 'GTK:Main:In')
            return
        elif cfg.ki5 and title.startswith(prg_msg):
            # KiCad 5 title
            if not title.endswith(unsaved):
                # KiCad 5 name is "Pcbnew — PCB_NAME" or "Eeschema — SCH_NAME [HIERARCHY] — SCH_FILE_NAME"
                # wait_pcbnew()
                wait_queue(cfg, ['GTK:Window Show:'+title, 'GTK:Main:In'], starts=True, timeout=cfg.wait_start, times=2,
                           with_windows=True)
                return
            # The "  [Unsaved]" is changed before the final load, ignore it
        elif title == '' or title == cfg.pn_simple_window_title or title == 'Eeschema':
            # This is the main window before loading anything
            # Note that KiCad 5 can create dialogs BEFORE this
            pass
        elif title == loading_msg:
            # This is the dialog for the loading progress, wait
            pass
        elif match is not None:
            msg = match.group(1)
            if msg != '0:00:00':
                log.info_progress('Elapsed time: '+msg)
                with_elapsed = True
        elif title == 'Error' or (cfg.ki7 and title == 'KiCad Schematic Editor Error'):
            dismiss_error(cfg, title)
        elif title == 'File Open Error':
            dismiss_file_open_error(cfg, title)
        elif cfg.ki7 and title == 'File Open Warning':
            dismiss_file_open_error(cfg, title)
        elif title == 'Confirmation':
            dismiss_already_running(cfg, title)
        elif title == 'Warning':
            dismiss_warning(cfg, title)
        elif title == 'pcbnew Warning' or title in WARN_DIALOGS:
            dismiss_pcbnew_warning(cfg, title)
        elif title == 'Remap Symbols':
            dismiss_remap_symbols(cfg, title)
        elif title in INFO_DIALOGS:
            dismiss_pcb_info(cfg, title)
        elif title.startswith(KIKIT_HIDE):
            # Buggy KiKit plugin creating a dialog at start-up (many times)
            pass
        elif title == 'Report':
            # KiCad 8.0.3 bogus hidden dialog
            pass
        elif title == 'Edit Mapping of Imported Layers':
            # KiCad 9 import, we handle it on modal 1
            pass
        else:
            unknown_dialog(cfg, title)
