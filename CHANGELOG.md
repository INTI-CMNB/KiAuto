# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.1.0] - 2022-10-17
### Added
- VRML Export (INTI-CMNB/KiBot#349)


## [2.0.6] - 2022-10-11
### Fixed
- Problems with GTK 3.24.34 and recycled DRC dialog
- ERC exclusions not detected (#31)


## [2.0.5] - 2022-09-22
### Added
- Support for KiCad 5 "could not find valid layer for pad" warning
  (See INTI-CMNB/KiBot#299)


## [2.0.4] - 2022-09-12
### Added
- 3D render options to control:
 - Hide the silkscreen layers
 - Hide the solder mask layers
 - Hide the solder paste layers
 - Hide filled areas in zones
 - Don't clip silkscreen at solder mask edges
 - Don't clip silkscreen at via annuli

### Changed
- The 3D render now enables silkscreen clips by default


## [2.0.3] - 2022-09-02
### Added
- Support for the asynchronous "Info" dialogs found in KiCad 6.
  Example: missing .kicad_wks (See INTI-CMNB/KiBot#264)

### Fixed
- Project files are now restored using binary mode. So we preserve the
  original end of line.


## [2.0.2] - 2022-08-26
### Fixed
- Problems when the output directory doesn't exist.


## [2.0.1] - 2022-08-22
### Added
- Support for the error dialog we get when sub-sheets are missing.

### Fixed
- Problems when using `--output_name` and the system temporal dir isn't in the
  same file system as the selected name.


## [2.0.0] - 2022-08-11
### Added
- New interporser mechanism for Linux x86_64.
  - Faster and more reliable
- `--separate_info` command line option to send information to stdout
  (separated from debug in stderr)
- `--info` command line option to debug installation issues
- Now all eeschema_do commands supports `--output_name`


## [1.6.15] - 2022-07-13
### Fixed
- DRC unconnected and warnings count (KiCad 6) (#25)

## [1.6.14] - 2022-07-01
### Added
- Support for partially saved projects (KiCad 6). (See INTI-CMNB/kicad_auto#11)
- The typing delay of pasted text is now scaled by the time-out scale.
- Delay before trying to paste the filename in the 3D render.
- Discard DRC errors explicitly excluded by KiCad 6 configuration. (#25)

### Fixed
- Problems to parse some KiCad 6 DRC messages. (#25)


## [1.6.13] - 2022-06-06
### Added
- Force Mesa GL to use sofware render. Helps on some setups. (#22)
- Support missing fp/sym-lib-table template. (#24)
- Better pcbnew window available mechanism. (See #21)
- An option to use the ray trace end detection with regular (OpenGL) renders
  (See #23)

### Changed
- Increased some timeouts, specially when waiting for the file creation (See #23)

### Fixed
- Problems when using PCBs in a read-only dir


## [1.6.12] - 2022-06-02
### Fixed
- kicad2step: very small wait on exit (#21)
- kicad2step: output dir option ignored

## [1.6.11] - 2022-05-17
### Added
- Added IPC-D-356 netlist generation

## [1.6.10] - 2022-04-18
### Fixed
- eeschema_do fails when loading the schematics took more than 3 seconds.

### Changed
- Time-outs when waiting for the PCB print dialog. Should make things faster.

## [1.6.9] - 2022-04-10
### Fixed
- `--list` option was limited to layer IDs upto 50. Now isn't limited.
- Problems with xclip messages for the version found on Fedora 35.

## [1.6.8] - 2022-03-29
### Added
- 3D View: support for X, Y, Z rotation in steps (KiCad 6 only)

## [1.6.7] - 2022-03-26
### Added
- PCB export: support for KiCad 6 color theme selection

## [1.6.6] - 2022-03-26
### Added
- 3D View: support for alpha channel (KiCad 6)
- 3D View: support for solder mask and silk screen bottom colors (KiCad 6)

### Fixed
- KiCad 6: 3D View axis not disabled

## [1.6.5] - 2022-03-08
### Added
- 3D View support for KiCad 6 (now that bug 9890 is fixed)
- Gencad export (#17)

## [1.6.4] - 2022-03-03
### Added
- pcbnew_do SVG export

## [1.6.3] - 2022-01-18
### Fixed
- KiCad 6: pcbnew_do problems when KiCad isn't configured.

## [1.6.2] - 2022-01-18
### Added
- Error message when the `import` tool isn't installed.

## [1.6.1] - 2022-01-13
### Added
- Support for `--subst-models` option

## [1.6.0] - 2021-12-28
### Added
- `kicad2step_do` a wrapper for `kicad2step`, a GUI tool in KiCad 6

### Changed
- Better support for KiCad 6 DRC errors.
- Better support for KiCad 6 error dialog at start-up.

## [1.5.14] - 2021-12-02
### Added
- Added experimental mechanism to detect the ray tracing end (#12)

### Fixed
- 3D View zoom issues on some systems (#13)

## [1.5.13] - 2021-11-30
### Fixed
- Problems with xdotool failing to match strings on some locales.

## [1.5.12] - 2021-11-25
### Added
- Monochrome schematic print.

### Fixed
- pcbnew_do export problems when the PCB name contained "print" and we asked
  to fill zones.

## [1.5.11] - 2021-11-18
### Added
- PCB 3D view capture.

## [1.5.10] - 2021-11-16
### Fixed
- pcbnew_do export problems when the PCB name contained "print".

## [1.5.9] - 2021-11-16
### Changed
- Now the time-out scale also affects the time we wait for a file creation.

### Fixed
- pcbnew_do export scaling for the "fit page" case.
- Locale problems for some Linux distros (i.e. Arch)
- Problems with wrong KiCad version in unstable Debian.

## [1.5.8] - 2021-02-22
### Added
- Verbosity level 3 enables logs for: KiCad, check for Xvfb and
  recordmydesktop.
- GitLab CI workaround:
  - Retries when we detect KiCad prematurely dies (before creating a
    window).
  - Delay after detecting Xvfb is running (increased exponentially on
    retries).

## [1.5.7] - 2021-02-17
### Added
- Call to `vmstat` and `uptime` after time-out.
- KiCad bug #6989 message supression.

## [1.5.6] - 2021-02-08
### Added
- Command line option to scale all the time-outs.

## [1.5.5] - 2021-01-12
### Added
- KiCad environment variables preservation in eeschema_do
- Support for KICAD_CONFIG_HOME defined from inside KiCad
- ERC report name can be configured

### Fixed
- No KiCad config assumed, now we ask KiCad

## [1.5.3] - 2020-10-15
### Added
- Support for KiCad 5.99 DRC/ERC reports.

### Fixed
- Problems when using KiCad 5.99 and projects from KiCad 5.

## [1.5.2] - 2020-10-12
### Added
- Option to pcbnew_do export:
  - `--mirror/-M`      Mirror printing (KiCad 6 only!)

## [1.5.1] - 2020-10-08
### Added
- Options to pcbnew_do export:
  - `--scaling/-s`     Scale factor (0 fit page)
  - `--pads/-p`        Pads style (0 none, 1 small, 2 full)
  - `--no-title/-t`    Remove the title-block
  - `--monochrome/-m`  Print in blanck and white
  - `--separate/-S`    Layers in separated sheets

## [1.5.0] - 2020-10-05
### Added
- Support for KiCad Nightly
  - Just define the environment variable: `KIAUS_USE_NIGHTLY=5.99`

## [1.4.2] - 2020-09-10
### Fixed
- Crash when no arguments.
- Crash when no x11vnc and it was requested.
- Lost warning messages when using --warnings_as_errors

## [1.4.1] - 2020-06-14
### Added
- --fill_zones/-f option to 'pcbnew_do export' to fill zones before printing.

### Changed
- Filtered errors are displayed as warnings, but ignored.
- Filtered warnings are displayed as information.
- When an error/warning is filtered a debug message informs which regex matched.

## [1.4.0] - 2020-06-08
### Added
- --errors_filter/-f option to provide a file containing errors to ignore from DRC/ERC.

### Fixed
- Sometimes when using a WM the "pcbnew_do export" failed to open the Printer dialog.
- Sometimes when exiting xdotool didn't find any window and reported error.
- When the filled zones changed during DRC the PCB could be saved even when we didn't
  specify --save

## [1.3.1] - 2020-05-19
### Fixed
- Under some situations the EEschema plot dialog failed to clear the old file path
  and we pasted concatenated. Was introduced when fixing the browse button selected.

## [1.3.0] - 2020-05-18
### Added
- --wait_key/-w option to send the commands step by step (debug)
- --start_x11vnc/-s option to start a server so we can monitor what's going on (debug)
- --use_wm/-m option to start a window manager (fluxbox) so we can interact better (debug)

### Changed
- Now we exit eeschema and pcbnew without killing the application.
- Default record height now is 960.

### Fixed
- Error and Warning dialog detection. Now we use more specific regular expressions.
- Sometimes the 'Plot Schematic Options' starts with the browse button selected and we
must move left.
- Sometimes the netlist dialog starts with the generation button selected and we move to
the plugin button instead. Now we detect it and go back to the generate button.

## [1.2.0] - 2020-05-13
### Added
- Support for PS, DXF and HPGL to the schematic export.
- Support for eeschema already running.
- Support for loading KiCad 4 schematics (asking for Remap symbols)

### Changed
- pcbnew_print_layers to "pcbnew_do export" to be coherent with "eeschema_do"
- pcbnew_run_drc to "pcbnew_do run_drc" ditto

### Fixed
- --ignore_unconnected of pcbnew_run_drc wasn't implemented.
- ERC omitted warnings if errors were detected.
- The project file could be altered, or even lost, during schematic export.

## [1.1.6] - 2020-04-23
### Changed
- Now we use setxkbmap instead of xset to test X is working.
If setxkbmap isn't available we default to xset.

## [1.1.5] - 2020-04-20
### Added
- More support for docker environment in the pcbnew scripts

### Changed
- Now eeschema_do reports ERC warnings as warning messages

## [1.1.4] - 2020-04-20
### Added
- Support missing *-lib-table in user config
- Create the KiCad config dir if it doesn't exist

### Fixed
- Two missing dependences.

## [1.1.3] - 2020-03-30
### Changed
- Debug and info colors.

## [1.1.2] - 2020-03-21
### Added
- Support for the names used by kiplot for the inner layers.

## [1.1.1] - 2020-03-18
### Fixed
- Supressed eeschema stdout to avoid printing the ERC report.
- ERC errors now reported as negative values.

## [1.1.0] - 2020-03-16
### Added
- --save to save the PCB after DRC (updating filled zones)

### Changed
- Sorted command line options

### Fixed
- Give more priority to the local module instead of the system wide installed.

## [1.0.0] - 2020-03-10
### Added
- Option to list all layers to pcbnew_print_layers.
- Documentation for the new scripts.
- Debian package files.
- Different error levels.
- --version and --verbose.
- Unified the loggers and made it coloured.
- Width and height config for the record function.
- --output_name option to the DRC.
- Netlist generation
- Simple BoM (XML) generation
- Print a PDF containing one or more layers.

### Changed
- Error level of src/pcbnew_run_drc to negative to be more coherent with the
run_erc command.
- Interpreter to Python 3.
- Renamed the main scripts so they don't include .py in the name.
- Renamed the "util" package to "kicad_auto" (less generic).
- Moved the eeschema/export_bom.py functionality to the bom_xml command of
src/eeschema_do.
- eeschema/schematic.py -> src/eeschema_do.py (more descriptive name).
- Now we keep only the last recorded video.
- Added creation of a suitable eeschema config, instead of editing the current.
- Made schematic and output_dir position args (always used).
- Removed --screencast_dir in favor of --record (+ size).
- _pcbnew/print_layers.py to src/pcbnew_print_layers.
- Renamed _pcbnew/run_drc.py to src/pcbnew_run_drc.
- Made some debug/info message classification to make it cleaner.
- Supressed the recordmydesktop output.
- Now the screencast files are named according to the recorded task.
- Suppressed the pcbnew stderr (noissy).
- Disabled long waits to test for old errors.
- Adapted to KiCad 5.1.x.
- Saves the current pcbnew/eeschema config and creates one usable.
The originals are restored.

### Removed
- Custom configs. Now they are generated on-the-fly.
- _pcbnew/generate_svg.py, its functionality can be achieved using pcbnew_print_layers.
- _pcbnew/generate_gerber.py, kiplot project has a better solution.

### Fixed
- Simplified the copy/paste mechanism used for run_erc. The old one could fail.
- src/pcbnew* always recorded the session.
- Adjusted the pcbnew first time-out, for some reason I'm getting huge delays.
- A test (and wait) for the Xvfb, sometimes is slow and xclip runs before it.
- clipboard_store rewrite, the old version ignored any errors
- Made stronger the eeschema config parser.
- Language set as english + UTF-8 (to run outside docker).


