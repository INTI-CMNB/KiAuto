# -*- coding: utf-8 -*-
# Copyright (c) 2020-2021 Salvador E. Tropea
# Copyright (c) 2020-2021 Instituto Nacional de Tecnologïa Industrial
# License: Apache 2.0
# Project: KiAuto (formerly kicad-automation-scripts)
import os
import re
import json
import configparser
from contextlib import contextmanager
from sys import exit, path
from subprocess import check_output, DEVNULL

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
# Wait 40 s to pcbnew/eeschema window to be present
WAIT_START = 60
# Name for testing versions
NIGHTLY = 'nightly'
# Scale factor for the timeouts
TIME_OUT_MULT = 1.0

KICAD_VERSION_5_99 = 5099000
KICAD_SHARE = '/usr/share/kicad/'
KICAD_NIGHTLY_SHARE = '/usr/share/kicad-nightly/'


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
    def __init__(self, logger, input_file=None, args=None):
        self.export_format = 'pdf'
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
        self.kicad_conf_dir = 'kicad'
        ng_ver = os.environ.get('KIAUS_USE_NIGHTLY')
        if ng_ver:
            self.eeschema += '-'+NIGHTLY
            self.pcbnew += '-'+NIGHTLY
            self.kicad_conf_dir += os.path.join(NIGHTLY, ng_ver)
            # Path to the Python module
            path.insert(0, '/usr/lib/kicad-nightly/lib/python3/dist-packages')
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
        m = re.match(r'(\d+)\.(\d+)\.(\d+)', kicad_version)
        self.kicad_version_major = int(m.group(1))
        self.kicad_version_minor = int(m.group(2))
        self.kicad_version_patch = int(m.group(3))
        self.kicad_version = self.kicad_version_major*1000000+self.kicad_version_minor*1000+self.kicad_version_patch
        logger.debug('Detected KiCad v{}.{}.{} ({} {})'.format(self.kicad_version_major, self.kicad_version_minor,
                     self.kicad_version_patch, kicad_version, self.kicad_version))
        # Config file names
        if self.kicad_version >= KICAD_VERSION_5_99:
            self.kicad_conf_path = pcbnew.GetSettingsManager().GetUserSettingsPath()
            if ng_ver:
                self.kicad_conf_path = self.kicad_conf_path.replace('/kicad/', '/kicadnightly/')
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
        if self.kicad_version >= KICAD_VERSION_5_99:
            self.conf_kicad += '.json'
            self.conf_kicad_json = True
        else:
            self.conf_kicad_json = False
        # Read the environment redefinitions used by KiCad
        if os.path.isfile(self.conf_kicad):
            self.load_kicad_environment(logger)
            if 'KICAD_CONFIG_HOME' in self.env and self.kicad_version < KICAD_VERSION_5_99:
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
        if self.kicad_version >= KICAD_VERSION_5_99:
            self.conf_eeschema += '.json'
            self.conf_pcbnew += '.json'
            self.conf_eeschema_json = True
            self.conf_pcbnew_json = True
            self.pro_ext = 'kicad_pro'
            self.prl_ext = 'kicad_prl'
        else:
            self.conf_eeschema_json = False
            self.conf_pcbnew_json = False
            self.pro_ext = 'pro'
            self.prl_ext = None
        # - hotkeys
        self.conf_hotkeys = os.path.join(self.kicad_conf_path, 'user.hotkeys')
        self.conf_hotkeys_bkp = None
        # - sym-lib-table
        self.user_sym_lib_table = os.path.join(self.kicad_conf_path, 'sym-lib-table')
        self.user_fp_lib_table = os.path.join(self.kicad_conf_path, 'fp-lib-table')
        self.sys_sym_lib_table = [KICAD_SHARE+'template/sym-lib-table']
        self.sys_fp_lib_table = [KICAD_SHARE+'template/fp-lib-table']
        if ng_ver:
            # 20200912: sym-lib-table is missing
            self.sys_sym_lib_table.insert(0, KICAD_NIGHTLY_SHARE+'template/sym-lib-table')
            self.sys_fp_lib_table.insert(0, KICAD_NIGHTLY_SHARE+'template/fp-lib-table')
        # Some details about the UI
        if self.kicad_version >= KICAD_VERSION_5_99:
            # KiCad 5.99.0
            self.ee_window_title = r'\[.*\] — Eeschema$'  # "PROJECT [HIERARCHY_PATH] - Eeschema"
        else:
            # KiCad 5.1.6
            self.ee_window_title = r'Eeschema.*\.sch'  # "Eeschema - file.sch"
        # Collected errors and unconnecteds (warnings)
        self.errs = []
        self.wrns = []
        # Error filters
        self.err_filters = []

    def load_kicad_environment(self, logger):
        self.env = {}
        if self.conf_kicad_json:
            env = self.get_config_vars_json(self.conf_kicad)
            if env:
                self.env = env
        else:
            env = self.get_config_vars_ini(self.conf_kicad)
            if env:
                for k, v in env.items():
                    self.env[k.upper()] = v
        logger.debug('KiCad environment: '+str(self.env))

    @staticmethod
    def get_config_vars_json(file):
        with open(file, "rt") as f:
            data = json.load(f)
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
__copyright__ = 'Copyright 2018-2021, INTI/Productize SPRL'
__credits__ = ['Salvador E. Tropea', 'Seppe Stas', 'Jesse Vincent', 'Scott Bezek']
__license__ = 'Apache 2.0'
__email__ = 'stropea@inti.gob.ar'
__status__ = 'beta'
__url__ = 'https://github.com/INTI-CMNB/KiAuto/'
__version__ = '1.5.11'
