# -*- coding: utf-8 -*-
# Copyright (c) 2020-2023 Salvador E. Tropea
# Copyright (c) 2020-2023 Instituto Nacional de Tecnologïa Industrial
# License: Apache 2.0
# Project: KiAuto (formerly kicad-automation-scripts)
import configparser
from contextlib import contextmanager
import json
import os
import re
from subprocess import check_output, DEVNULL
from sys import exit, path

# Default W,H for recording
REC_W = 1366
REC_H = 960

# Return error codes
# Positive values are ERC/DRC errors
NO_SCHEMATIC = 1
WRONG_ARGUMENTS = 2   # This is what argsparse uses
EESCHEMA_CFG_PRESENT = 11
KICAD_CFG_PRESENT = 3
NO_PCB = 4
PCBNEW_CFG_PRESENT = 5
WRONG_LAYER_NAME = 6
WRONG_PCB_NAME = 7
WRONG_SCH_NAME = 8
PCBNEW_ERROR = 9
EESCHEMA_ERROR = 10
NO_PCBNEW_MODULE = 11
USER_HOTKEYS_PRESENT = 12
CORRUPTED_PCB = 13
NO_EN_LOCALE = 14
MISSING_TOOL = 15
KICAD_DIED = 16
READ_ONLY_PROBLEM = 17
WONT_OVERWRITE = 18
KICAD_CLI_ERROR = 19
CORRUPTED_CONFIG = 20
# Wait 60 s to pcbnew/eeschema window to be present
WAIT_START = 60
# Name for testing versions
NIGHTLY = 'nightly'
# Scale factor for the timeouts
TIME_OUT_MULT = 1.0

KICAD_VERSION_5_99 = 5099000
KICAD_VERSION_6_99 = 6099000
KICAD_VERSION_7_99 = 7099000
KICAD_VERSION_8_99 = 8099000
KICAD_VERSION_7_0_3 = 7000003
KICAD_VERSION_7_0_8 = 7000008
KICAD_VERSION_9_0_1 = 9000001
KICAD_SHARE = '/usr/share/kicad/'
KICAD_NIGHTLY_SHARE = '/usr/share/kicad-nightly/'
RULES_KEY = 'Ctrl+Shift+A'
# RULES_KEY = 'Alt+I'


@contextmanager
def hide_stderr():
    """ Low level stderr supression, used to hide KiCad bugs. """
    newstderr = os.dup(2)
    devnull = os.open('/dev/null', os.O_WRONLY)
    os.dup2(devnull, 2)
    os.close(devnull)
    yield
    os.dup2(newstderr, 2)


class Config(object):
    def __init__(self, logger, input_file=None, args=None, is_pcbnew=False):
        logger.debug(f'KiAuto v{__version__}')
        self.export_format = 'pdf'
        self.is_pcbnew = is_pcbnew
        if input_file:
            self.input_file = input_file
            self.input_no_ext = os.path.splitext(input_file)[0]
            #
            # As soon as we init pcbnew the following files are modified:
            #
            if os.path.isfile(self.input_no_ext+'.pro'):
                self.start_pro_stat = os.stat(self.input_no_ext+'.pro')
            else:
                self.start_pro_stat = None
            if os.path.isfile(self.input_no_ext+'.kicad_pro'):
                self.start_kicad_pro_stat = os.stat(self.input_no_ext+'.kicad_pro')
            else:
                self.start_kicad_pro_stat = None
            if os.path.isfile(self.input_no_ext+'.kicad_prl'):
                self.start_kicad_prl_stat = os.stat(self.input_no_ext+'.kicad_prl')
            else:
                self.start_kicad_prl_stat = None
        if args:
            # Session debug
            self.use_wm = args.use_wm  # Use a Window Manager, dialogs behaves in a different way
            self.start_x11vnc = args.start_x11vnc
            self.rec_width = args.rec_width
            self.rec_height = args.rec_height
            self.record = args.record
            self.video_dir = args.output_dir
            self.wait_for_key = args.wait_key
            self.time_out_scale = args.time_out_scale
            # Others
            if hasattr(args, 'file_format'):
                self.export_format = args.file_format.lower()
        else:
            # Session debug
            self.use_wm = False
            self.start_x11vnc = False
            self.rec_width = REC_W
            self.rec_height = REC_H
            self.record = False
            self.video_dir = None
            self.wait_for_key = False
            self.time_out_scale = 1.0
        self.colordepth = 24
        self.video_name = None
        self.video_dir = self.output_dir = ''
        # Executable and dirs
        self.eeschema = 'eeschema'
        self.pcbnew = 'pcbnew'
        self.kicad2step = 'kicad2step'
        self.kicad_cli = 'kicad-cli'
        self.kicad_conf_dir = 'kicad'
        ng_ver = os.environ.get('KIAUS_USE_NIGHTLY')
        if ng_ver:
            self.eeschema += '-'+NIGHTLY
            self.pcbnew += '-'+NIGHTLY
            self.kicad2step += '-'+NIGHTLY
            self.kicad_cli += '-'+NIGHTLY
            self.kicad_conf_dir += os.path.join(NIGHTLY, ng_ver)
            # Path to the Python module
            path.insert(0, '/usr/lib/kicad-nightly/lib/python3/dist-packages')
            os.environ['KICAD_PATH'] = '/usr/share/kicad-nightly'
        # Detect KiCad version
        try:
            import pcbnew
        except ImportError:
            logger.error("Failed to import pcbnew Python module."
                         " Is KiCad installed?"
                         " Do you need to add it to PYTHONPATH?")
            exit(NO_PCBNEW_MODULE)
        kicad_version = pcbnew.GetBuildVersion()
        try:
            # Debian sid may 2021 mess:
            really_index = kicad_version.index('really')
            kicad_version = kicad_version[really_index+6:]
        except ValueError:
            pass
        m = re.search(r'(\d+)\.(\d+)\.(\d+)', kicad_version)
        if m is None:
            logger.error("Unable to detect KiCad version, got: `{}`".format(kicad_version))
            exit(NO_PCBNEW_MODULE)
        self.kicad_version_major = int(m.group(1))
        self.kicad_version_minor = int(m.group(2))
        self.kicad_version_patch = int(m.group(3))
        self.kicad_version = self.kicad_version_major*1000000+self.kicad_version_minor*1000+self.kicad_version_patch
        logger.debug('Detected KiCad v{}.{}.{} ({} {})'.format(self.kicad_version_major, self.kicad_version_minor,
                     self.kicad_version_patch, kicad_version, self.kicad_version))
        self.ki5 = self.kicad_version < KICAD_VERSION_5_99
        self.ki6 = self.kicad_version >= KICAD_VERSION_5_99
        self.ki7 = self.kicad_version >= KICAD_VERSION_6_99
        self.ki8 = self.kicad_version >= KICAD_VERSION_7_99
        self.ki9 = self.kicad_version >= KICAD_VERSION_8_99
        if self.ki7:
            # Now part of the kicad-cli tool
            self.kicad2step = self.kicad_cli
            self.drc_dialog_name = 'Design Rules Checker'
        else:
            self.drc_dialog_name = 'DRC Control'
        # Config file names
        if not self.ki5:
            self.kicad_conf_path = pcbnew.GetSettingsManager().GetUserSettingsPath()
            # No longer needed for 202112021512+6.0.0+rc1+287+gbb08ef2f41+deb11
            # if ng_ver:
            #    self.kicad_conf_path = self.kicad_conf_path.replace('/kicad/', '/kicadnightly/')
        else:
            # Bug in KiCad (#6989), prints to stderr:
            # `../src/common/stdpbase.cpp(62): assert "traits" failed in Get(test_dir): create wxApp before calling this`
            # Found in KiCad 5.1.8, 5.1.9
            # So we temporarily supress stderr
            with hide_stderr():
                self.kicad_conf_path = pcbnew.GetKicadConfigPath()
        logger.debug('Config path {}'.format(self.kicad_conf_path))
        # First we solve kicad_common because it can redirect to another config dir
        self.conf_kicad = os.path.join(self.kicad_conf_path, 'kicad_common')
        self.conf_kicad_bkp = None
        if not self.ki5:
            self.conf_kicad += '.json'
            self.conf_kicad_json = True
        else:
            self.conf_kicad_json = False
        # Read the environment redefinitions used by KiCad
        self.env = {}
        if os.path.isfile(self.conf_kicad):
            self.load_kicad_environment(logger)
            if 'KICAD_CONFIG_HOME' in self.env and self.ki5:
                # The user is redirecting the configuration
                # KiCad 5 unintentionally allows it, is a bug, and won't be fixed:
                # https://forum.kicad.info/t/kicad-config-home-inconsistencies-and-detail/26875
                self.kicad_conf_path = self.env['KICAD_CONFIG_HOME']
                logger.debug('Redirecting KiCad config path to: '+self.kicad_conf_path)
        else:
            logger.warning('Missing KiCad main config file '+self.conf_kicad)
        # - eeschema config
        self.conf_eeschema = os.path.join(self.kicad_conf_path, 'eeschema')
        self.conf_eeschema_bkp = None
        # - pcbnew config
        self.conf_pcbnew = os.path.join(self.kicad_conf_path, 'pcbnew')
        self.conf_pcbnew_bkp = None
        # Config files that migrated to JSON
        # Note that they remain in the old format until saved
        if not self.ki5:
            self.conf_eeschema += '.json'
            self.conf_pcbnew += '.json'
            self.conf_eeschema_json = True
            self.conf_pcbnew_json = True
            self.pro_ext = 'kicad_pro'
            self.prl_ext = 'kicad_prl'
            self.conf_colors = os.path.join(self.kicad_conf_path, 'colors', 'user.json')
            self.conf_colors_bkp = None
            self.conf_3dview = os.path.join(self.kicad_conf_path, '3d_viewer.json')
            self.conf_3dview_bkp = None
        else:
            self.conf_eeschema_json = False
            self.conf_pcbnew_json = False
            self.pro_ext = 'pro'
            self.prl_ext = None
            self.conf_colors = self.conf_colors_bkp = None
            self.conf_3dview = self.conf_3dview_bkp = None
        # - hotkeys
        self.conf_hotkeys = os.path.join(self.kicad_conf_path, 'user.hotkeys')
        self.conf_hotkeys_bkp = None
        # share path
        kpath = os.environ.get('KICAD_PATH')
        if kpath is None and self.env:
            kpath = self.env.get('KICAD_PATH')
        if kpath is None:
            if os.path.isdir(KICAD_SHARE):
                kpath = KICAD_SHARE
            elif os.path.isdir(KICAD_NIGHTLY_SHARE):
                kpath = KICAD_NIGHTLY_SHARE
        if kpath is None:
            logger.warning('Missing KiCad share dir')
        else:
            logger.debug('KiCad share dir: '+kpath)
            vname = 'KICAD'+str(self.kicad_version_major)+'_FOOTPRINT_DIR'
            # KiCad 7.0.0 rc2 workaround (also 7.0.1 and 7.99 april 2023)
            # KiCad bug: https://gitlab.com/kicad/code/kicad/-/issues/13815
            if vname not in os.environ:
                # Footprint dir not defined, and needed for DRC
                if self.env and vname in self.env:
                    os.environ[vname] = self.env[vname]
                else:
                    os.environ[vname] = os.path.join(kpath, 'footprints')
                logger.debug('Defining {} = {}'.format(vname, os.environ[vname]))
        # - sym-lib-table
        self.user_sym_lib_table = os.path.join(self.kicad_conf_path, 'sym-lib-table')
        self.user_fp_lib_table = os.path.join(self.kicad_conf_path, 'fp-lib-table')
        self.sys_sym_lib_table = [KICAD_SHARE+'template/sym-lib-table']
        self.sys_fp_lib_table = [KICAD_SHARE+'template/fp-lib-table']
        if ng_ver:
            # 20200912: sym-lib-table is missing
            self.sys_sym_lib_table.insert(0, KICAD_NIGHTLY_SHARE+'template/sym-lib-table')
            self.sys_fp_lib_table.insert(0, KICAD_NIGHTLY_SHARE+'template/fp-lib-table')
        if kpath is not None:
            self.sys_sym_lib_table.insert(0, os.path.join(kpath, 'template/sym-lib-table'))
            self.sys_fp_lib_table.insert(0, os.path.join(kpath, 'template/fp-lib-table'))
        # Some details about the UI
        if not self.ki5:
            # KiCad 5.99.0
            # self.ee_window_title = r'\[.*\] — Eeschema$'  # "PROJECT [HIERARCHY_PATH] - Eeschema"
            if self.ki7:
                self.ee_window_title = r'.* — Schematic Editor$'  # "SHEET [HIERARCHY_PATH]? - Schematic Editor"
            else:
                # KiCad 6.x
                self.ee_window_title = r'\[.*\] — Schematic Editor$'  # "PROJECT [HIERARCHY_PATH] - Schematic Editor"
            self.pn_window_title = r'.* — PCB Editor$'  # "PROJECT - PCB Editor"
            self.pn_simple_window_title = 'PCB Editor'
            kind = 'PCB' if self.is_pcbnew else 'Schematic'
            self.window_title_end = ' — '+kind+' Editor'
        else:
            # KiCad 5.1.6
            self.ee_window_title = r'Eeschema.*\.sch'  # "Eeschema - file.sch"
            self.pn_window_title = r'^Pcbnew'
            self.pn_simple_window_title = 'Pcbnew'
        # Collected errors and unconnecteds (warnings)
        self.errs = []
        self.wrns = []
        # Error filters
        self.err_filters = []

    def load_kicad_environment(self, logger):
        self.env = {}
        if self.conf_kicad_json:
            env = self.get_config_vars_json(self.conf_kicad, logger)
            if env:
                self.env = env
        else:
            env = self.get_config_vars_ini(self.conf_kicad)
            if env:
                for k, v in env.items():
                    self.env[k.upper()] = v
        logger.debug('KiCad environment: '+str(self.env))

    @staticmethod
    def get_config_vars_json(file, logger):
        with open(file, "rt") as f:
            raw_data = f.read()
            try:
                data = json.loads(raw_data)
            except json.decoder.JSONDecodeError:
                logger.error(f"Corrupted KiCad config file `{file}`:\n{raw_data}")
                exit(CORRUPTED_CONFIG)
        if 'environment' in data and 'vars' in data['environment']:
            return data['environment']['vars']
        return None

    @staticmethod
    def get_config_vars_ini(file):
        config = configparser.ConfigParser()
        with open(file, "rt") as f:
            data = f.read()
        config.read_string('[Various]\n'+data)
        if 'EnvironmentVariables' in config:
            return config['EnvironmentVariables']
        return None


def get_en_locale(logger):
    ''' Looks for a usable locale with english as language '''
    try:
        res = check_output(['locale', '-a'], stderr=DEVNULL).decode('utf8')
    except FileNotFoundError:
        logger.warning("The `locale` command isn't installed. Guessing `C.UTF-8` is supported")
        res = 'C.UTF-8'
    found = re.search(r'en(.*)UTF-?8', res, re.I)
    if found:
        res = found.group(0)
    else:
        found = re.search(r'C\.UTF-?8', res, re.I)
        if found:
            res = found.group(0)
        else:
            logger.error("No suitable english locale found. Please add `en_US.utf8` to your system")
            exit(NO_EN_LOCALE)
    logger.debug('English locale: '+res)
    return res


__author__ = 'Salvador E. Tropea'
__copyright__ = 'Copyright 2018-2024, INTI/Productize SPRL'
__credits__ = ['Salvador E. Tropea', 'Seppe Stas', 'Jesse Vincent', 'Scott Bezek']
__license__ = 'Apache 2.0'
__email__ = 'stropea@inti.gob.ar'
__status__ = 'stable'
__url__ = 'https://github.com/INTI-CMNB/KiAuto/'
__version__ = '2.3.6'
