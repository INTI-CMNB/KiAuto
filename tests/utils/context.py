
import os
import shutil
import tempfile
import logging
import subprocess
import re

KICAD_PCB_EXT = '.kicad_pcb'
REF_DIR = 'tests/reference'


class TestContext(object):

    def __init__(self, test_name, board_name, test_dir):
        # The name used for the test output dirs and other logging
        self.test_name = test_name
        # The name of the PCB board file
        self.board_name = board_name
        # The actual board file that will be loaded
        self._get_board_name()
        # The actual output dir for this run
        self._set_up_output_dir(test_dir)
        # stdout and stderr from the run
        self.out = None
        self.err = None

    def _get_board_cfg_dir(self):
        this_dir = os.path.dirname(os.path.realpath(__file__))
        return os.path.join(this_dir, '../kicad5')

    def _get_board_name(self):
        self.board_file = os.path.join(self._get_board_cfg_dir(),
                                       self.board_name,
                                       self.board_name + KICAD_PCB_EXT)
        logging.info('PCB file: '+self.board_file)
        assert os.path.isfile(self.board_file)

    def _set_up_output_dir(self, test_dir):
        if test_dir:
            self.output_dir = os.path.join(test_dir, self.test_name)
            os.makedirs(self.output_dir)
            self._del_dir_after = False
        else:
            # create a tmp dir
            self.output_dir = tempfile.mkdtemp(prefix='tmp-kicad_auto-'+self.test_name+'-')
            self._del_dir_after = True
        logging.info('Output dir: '+self.output_dir)

    def clean_up(self):
        logging.debug('Clean-up')
        if self._del_dir_after:
            logging.debug('Removing dir')
            shutil.rmtree(self.output_dir)

    def expect_out_file(self, filename):
        file = os.path.join(self.output_dir, filename)
        assert os.path.isfile(file)
        assert os.path.getsize(file) > 0
        return file

    def run(self, cmd, ret_val=None, extra=None):
        logging.debug('Running '+self.test_name)
        # Change the command to be local and add the board and output arguments
        cmd[0] = os.path.abspath(os.path.dirname(os.path.abspath(__file__))+'/../../src/'+cmd[0])
        cmd.append(self.board_file)
        cmd.append(self.output_dir)
        if extra is not None:
            cmd = cmd+extra
        logging.debug(cmd)
        # Redirect stdout and stderr to files
        out_filename = os.path.join(self.output_dir, 'output.txt')
        f_out = os.open(out_filename, os.O_RDWR | os.O_CREAT)
        err_filename = os.path.join(self.output_dir, 'error.txt')
        f_err = os.open(err_filename, os.O_RDWR | os.O_CREAT)
        # Run the process
        process = subprocess.Popen(cmd, stdout=f_out, stderr=f_err)
        ret_code = process.wait()
        logging.debug('ret_code '+str(ret_code))
        exp_ret = 0 if ret_val is None else ret_val
        assert ret_code == exp_ret
        # Read stdout
        os.lseek(f_out, 0, os.SEEK_SET)
        self.out = os.read(f_out, 10000)
        os.close(f_out)
        self.out = self.out.decode()
        # Read stderr
        os.lseek(f_err, 0, os.SEEK_SET)
        self.err = os.read(f_err, 10000)
        os.close(f_err)
        self.err = self.err.decode()

    def search_out(self, text):
        m = re.search(text, self.out, re.MULTILINE)
        return m

    def search_err(self, text):
        m = re.search(text, self.err, re.MULTILINE)
        return m

    def compare_image(self, image, reference=None, diff='diff.png'):
        if reference is None:
            reference = image
        cmd = ['compare', '-metric', 'MSE',
               os.path.join(self.output_dir, image),
               os.path.join(REF_DIR, reference),
               os.path.join(self.output_dir, diff)]
        logging.debug('Comparing images with: '+str(cmd))
        res = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        m = re.match(r'([\d\.]+) \(([\d\.]+)\)', res.decode())
        assert m
        logging.debug('MSE={} ({})'.format(m.group(1), m.group(2)))
        assert float(m.group(2)) == 0.0

    def compare_txt(self, text, reference=None, diff='diff.txt'):
        if reference is None:
            reference = text
        cmd = ['/bin/sh', '-c', 'diff -ub '+os.path.join(REF_DIR, reference)+' ' +
               os.path.join(self.output_dir, text)+' > '+os.path.join(self.output_dir, diff)]
        logging.debug('Comparing texts with: '+str(cmd))
        res = subprocess.call(cmd)
        assert res == 0
