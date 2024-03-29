# -*- coding: utf-8 -*-
# Copyright (c) 2020-2021 Salvador E. Tropea
# Copyright (c) 2020-2021 Instituto Nacional de Tecnologïa Industrial
# License: Apache 2.0
# Project: KiAuto (formerly kicad-automation-scripts)
"""
Tests for 'pcbnew_do export'

For debug information use:
pytest-3 --log-cli-level debug

"""

import os
import sys
import logging
# Look for the 'utils' module from where the script is running
script_dir = os.path.dirname(os.path.abspath(__file__))
prev_dir = os.path.dirname(script_dir)
sys.path.insert(0, prev_dir)
# Utils import
from utils import context
sys.path.insert(0, os.path.dirname(prev_dir))
from kiauto.misc import (WRONG_LAYER_NAME, WRONG_ARGUMENTS, Config)


PROG = 'pcbnew_do'
DEFAULT = 'printed.pdf'
CMD_OUT = 'output.txt'


def test_print_pcb_good_dwg_1(test_dir):
    ctx = context.TestContext(test_dir, 'Print_Good_with_Dwg', 'good-project')
    pdf = 'good_pcb_with_dwg.pdf'
    mtime1 = ctx.get_pro_mtime()
    mtime2 = ctx.get_prl_mtime()
    cmd = [PROG, '-vv', 'export', '--output_name', pdf]
    layers = ['F.Cu', 'F.SilkS', 'Dwgs.User', 'Edge.Cuts']
    ctx.run(cmd, extra=layers)
    ctx.expect_out_file(pdf)
    #ctx.compare_image(pdf)
    ctx.compare_pdf(pdf)
    assert mtime1 == ctx.get_pro_mtime()
    assert mtime2 == ctx.get_prl_mtime()
    ctx.clean_up()


def test_print_pcb_good_inner(test_dir):
    ctx = context.TestContext(test_dir, 'Print_Good_Inner', 'good-project')
    cmd = [PROG, '-r', '-vvv', 'export']
    layers = ['F.Cu', 'F.SilkS', 'GND.Cu', 'Signal1.Cu', 'Inner.3', 'Power.Cu', 'Edge.Cuts']
    ctx.run(cmd, extra=layers)
    ctx.expect_out_file(DEFAULT)
    ctx.compare_pdf(DEFAULT, 'good_pcb_inners.pdf')
    ctx.clean_up()


def test_print_pcb_layers(test_dir):
    ctx = context.TestContext(test_dir, 'Print_Layers', 'good-project')
    cmd = [PROG, 'export', '--list']
    ctx.run(cmd)
    ctx.compare_txt(CMD_OUT, 'good_pcb_layers.txt')
    ctx.clean_up()


def test_print_pcb_good_dwg_dism(test_dir):
    ctx = context.TestContext(test_dir, 'Print_Good_with_Dwg_Dism', 'good-project')
    pdf = 'good_pcb_with_dwg.pdf'
    # Create the output to force and overwrite
    with open(ctx.get_out_path(pdf), 'w') as f:
        f.write('dummy')
    cfg = Config(logging)
    # Run pcbnew in parallel to get 'Dismiss pcbnew already running' (KiCad 5) or 'Skipping already open dialog' (KiCad 6)
    if context.ki5:
        # Note: If we open the same file KiCad 5 will exit
        cmd = [cfg.pcbnew]
    else:
        # We open the same file, otherwise KiCad 6 won't have problems
        cmd = [cfg.pcbnew, ctx.board_file]
    with ctx.start_kicad(cmd, cfg):
        cmd = [PROG, '-vvv', '-r', '--wait_start', '5', 'export', '--output_name', pdf]
        layers = ['F.Cu', 'F.SilkS', 'Dwgs.User', 'Edge.Cuts']
        ctx.run(cmd, extra=layers)
        ctx.stop_kicad()
    ctx.expect_out_file(pdf)
    ctx.compare_image(pdf)
    if context.ki5:
        # Only KiCad 5 reports it as a problem
        assert ctx.search_err(r"already running") is not None
    else:
        # On KiCad 6 this is a problem only when we use the same file twice
        assert ctx.search_err(r"This file is already opened") is not None
    ctx.clean_up()


def test_wrong_layer_name_kiplot(test_dir):
    ctx = context.TestContext(test_dir, 'Wrong_Inner', 'good-project')
    cmd = [PROG, 'export']
    layers = ['F.Cu', 'Inner_1']
    ctx.run(cmd, WRONG_LAYER_NAME, extra=layers)
    m = ctx.search_err(r'Malformed inner layer name')
    assert m is not None
    ctx.clean_up()


def test_wrong_layer_big(test_dir):
    ctx = context.TestContext(test_dir, 'Wrong_Inner_Big', 'good-project')
    cmd = [PROG, 'export']
    layers = ['F.Cu', 'Inner.8']
    ctx.run(cmd, WRONG_LAYER_NAME, extra=layers)
    m = ctx.search_err(r"Inner.8 isn't a valid layer")
    assert m is not None
    ctx.clean_up()


def test_wrong_layer_bogus(test_dir):
    ctx = context.TestContext(test_dir, 'Wrong_Inner_Name', 'good-project')
    cmd = [PROG, 'export']
    layers = ['F.Cu', 'GND_Cu']
    ctx.run(cmd, WRONG_LAYER_NAME, extra=layers)
    m = ctx.search_err(r"Unknown layer GND_Cu")
    assert m is not None
    ctx.clean_up()


def test_print_pcb_good_wm(test_dir):
    """ Here we test the window manager """
    ctx = context.TestContext(test_dir, 'Print_Good_with_WM', 'good-project')
    pdf = 'good_pcb_with_dwg.pdf'
    cmd = [PROG, '-ms', 'export', '--output_name', pdf]
    layers = ['F.Cu', 'F.SilkS', 'Dwgs.User', 'Edge.Cuts']
    ctx.run(cmd, extra=layers)
    ctx.expect_out_file(pdf)
    ctx.compare_image(pdf)
    ctx.clean_up()


def test_print_pcb_refill(test_dir):
    ctx = context.TestContext(test_dir, 'Print_Refill', 'zone-refill')
    pdf = 'zone-refill.pdf'
    cmd = [PROG, '-vvv', 'export', '-f', '--output_name', pdf]
    layers = ['F.Cu', 'B.Cu', 'Edge.Cuts']
    ctx.run(cmd, extra=layers)
    ctx.expect_out_file(pdf)
    ctx.compare_image(pdf)
    ctx.clean_up()


def test_wrong_scaling(test_dir):
    ctx = context.TestContext(test_dir, 'wrong_scaling', 'good-project')
    cmd = [PROG, 'export', '--scaling', 'A']
    layers = ['F.Cu', 'GND_Cu']
    ctx.run(cmd, WRONG_ARGUMENTS, extra=layers)
    m = ctx.search_err(r"Scaling must be a floating point value")
    assert m is not None
    ctx.clean_up()


def test_wrong_pad_style_1(test_dir):
    ctx = context.TestContext(test_dir, 'wrong_pad_style_1', 'good-project')
    cmd = [PROG, 'export', '--pads', 'A']
    layers = ['F.Cu', 'GND_Cu']
    ctx.run(cmd, WRONG_ARGUMENTS, extra=layers)
    m = ctx.search_err(r"Pads style must be an integer value")
    assert m is not None
    ctx.clean_up()


def test_wrong_pad_style_2(test_dir):
    ctx = context.TestContext(test_dir, 'wrong_pad_style_2', 'good-project')
    cmd = [PROG, 'export', '--pads', '3']
    layers = ['F.Cu', 'GND_Cu']
    ctx.run(cmd, WRONG_ARGUMENTS, extra=layers)
    m = ctx.search_err(r"Pad style must be 0, 1 or 2")
    assert m is not None
    ctx.clean_up()


def test_print_pcb_good_dwg_2(test_dir):
    ctx = context.TestContext(test_dir, 'print_pcb_good_dwg_2', 'good-project')
    pdf = 'good_pcb_sep_bn.pdf'
    cmd = [PROG, 'export', '--mirror', '--scaling', '4', '--pads', '0', '--no-title', '--monochrome', '--separate',
           '--output_name', pdf]
    layers = ['F.Cu', 'F.SilkS', 'Dwgs.User', 'Edge.Cuts']
    ctx.run(cmd, extra=layers)
    ctx.expect_out_file(pdf)
    if context.ki5:
        assert ctx.search_err(r"KiCad 5 doesn't support setting mirror")
    ctx.compare_pdf(pdf)
    ctx.clean_up()


def test_print_pcb_good_dwg_3(test_dir):
    # Fit page
    ctx = context.TestContext(test_dir, 'print_pcb_good_dwg_3', 'good-project')
    pdf = 'good_pcb_sep_bn_fit.pdf'
    cmd = [PROG, 'export', '--mirror', '--scaling', '0', '--pads', '0', '--no-title', '--monochrome', '--separate',
           '--output_name', pdf]
    layers = ['F.Cu', 'F.SilkS', 'Dwgs.User', 'Edge.Cuts']
    ctx.run(cmd, extra=layers)
    ctx.expect_out_file(pdf)
    if context.ki5:
        assert ctx.search_err(r"KiCad 5 doesn't support setting mirror")
    ctx.compare_pdf(pdf)
    ctx.clean_up()
