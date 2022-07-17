KiAuto
======

[![Regression tests](https://img.shields.io/github/workflow/status/INTI-CMNB/KiAuto/Regression%20tests?style=plastic)](https://github.com/INTI-CMNB/KiAuto/actions)
[![Coverage Status](https://img.shields.io/coveralls/github/INTI-CMNB/KiAuto?style=plastic)](https://coveralls.io/github/INTI-CMNB/KiAuto?branch=master)
[![PyPI version](https://img.shields.io/pypi/v/kiauto?style=plastic)](https://pypi.org/project/kiauto/)
[![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg?style=plastic)](https://www.paypal.com/donate/?hosted_button_id=K2T86GDTTMRPL)

KiCad automation scripts.
In particular to automate tasks that can't be done using the KiCad native Python interface.
The automation is carried out emulating the user interaction.

## Index

* [Introduction](#introduction)
* [Installation](#installation)
  * [Dependencies](#dependencies)
  * [No installation](#no-installation)
  * [Installation using pip](#installation-using-pip)
  * [Python style installation](#python-style-installation)
  * [Installation on Ubuntu/Debian](#installation-on-debian)
* [Usage](#usage)
  * [Export a schematic to PDF or SVG](#export-a-schematic-to-pdf-or-svg)
  * [Run ERC](#run-erc)
  * [Generate netlist](#generate-netlist)
  * [Update BoM XML or basic BoM generation](#update-bom-xml-or-basic-bom-generation)
  * [Run DRC](#run-drc)
  * [Export layout as PDF](#export-layout-as-pdf)
  * [Refilling copper zones](#refilling-copper-zones)
  * [Common options](#common-options)
  * [Ignoring warnings and errors from ERC or DRC](#ignoring-warnings-and-errors-from-erc-or-drc)
  * [Running on GitLab CI](#running-on-gitlab-ci)
* [History](#history)

## Introduction

Current implementation uses a virtual X server ([xvfb](https://www.x.org/releases/X11R7.6/doc/man/man1/Xvfb.1.xhtml)),
sends key events and detects which window is focused using [xdotool](https://github.com/jordansissel/xdotool/).
This means it works for Linux. KiCad is also available for Windows and MacOSX, help to port the scripts will be appreciated.

Currently tested and working:

- Exporting schematics to PDF, SVG, PS, DXF and HPGL
- Exporting layouts (PCBs) to PDF
- Running ERC on schematics
- Running DRC on layouts
- Netlist generation (including IPC-D-356 format)
- Basic BoM generation (mainly the XML needed for [KiBoM](https://github.com/SchrodingersGat/KiBoM))
- PCB 3D render
- Export PCB in Gencad format

If you are looking for Gerbers, Drill, Position, STEP and more take a look at [KiBot](https://github.com/INTI-CMNB/KiBot).

This project started as a fork of [kicad-automation-scripts](https://github.com/obra/kicad-automation-scripts) for more information read the [history](#History) section.

A docker image containg the scripts and other tools can be found at [DockerHub](https://hub.docker.com/repository/docker/setsoft/kicad_auto).

## Installation

### Dependencies

If you are installing from a Debian package you don't need to worry about dependencies, otherwise you need to install:

- **Python 3.4** or newer
- [**KiCad**](http://kicad.org/) 5.1.x or newer, KiCad 6.x is supported
- [**Xvfb**](https://www.x.org/releases/X11R7.6/doc/man/man1/Xvfb.1.xhtml) This is the X Virtual Frame Buffer, part of X, but usually available as a separated package (i.e. `xvfb`)
- [**xdotool**](https://github.com/jordansissel/xdotool)
- [**xsltproc**](http://xmlsoft.org/xslt/) (usually installed as a KiCad dependency). Only needed for BoMs.
- [**import**](https://imagemagick.org/) from Image Magick. Also provided by Graphics Magick. Only needed for ERC with KiCad 6.
- [**xclip**](https://github.com/astrand/xclip). Only needed by kicad2step_do when using KiCad 6.

The following Python modules are also needed, they are installed by the Debian package and `pip`:

- [**xvfbwrapper**](https://pypi.org/project/xvfbwrapper/)
- [**psutil**](https://pypi.org/project/psutil/)

If you want to debug problems you could also need:

- [**recordmydesktop**](http://recordmydesktop.sourceforge.net/about.php), to create a video of the KiCad session.
- [**x11vnc**](http://www.karlrunge.com/x11vnc/) and a client like [**ssvnc**](http://www.karlrunge.com/x11vnc/ssvnc.html), to see the KiCad live interaction.
- [**fluxbox**](http://fluxbox.org/) and [**wmctrl**](http://tripie.sweb.cz/utils/wmctrl/) if you want to have a window manager when using **x11vnc**. Othewise windows can't be moved.

### Installation using pip

```shell
pip3 install kiauto
```

Note: the `pip` command is usually installed as `pip3` on modern systems. To avoid confusing it with Python 2 version.
You can also install the current git code running:


```shell
pip3 install .
```

In the root of the repo.

### Python style installation

Just run the setup, like with any other Python tool:

```
sudo python3 setup.py install
```

### No installation

You can use the scripts without installing. The scripts are located at the *src/* directory.

You can also define bash aliases:

```
alias pcbnew_do=PATH_TO_REPO/src/pcbnew_do
alias eeschema_do=PATH_TO_REPO/src/eeschema_do
```

Note that the following Python 3 packages must be installed:

- [**xvfbwrapper**](https://pypi.org/project/xvfbwrapper/)
- [**psutil**](https://pypi.org/project/psutil/)

Also note that this won't work if you plan to call the scripts from KiBot or other tool.
Aliases are good for direct command line use, but are restricted to the shell where the aliases are declared.
You can add the aliases to the bash configuration, but if the tool doesn't use bash or don't even use a shell this won't work.

### Installation on Debian

Get the Debian package from the [releases section](https://github.com/INTI-CMNB/KiAuto/releases) and run:
```
sudo apt install ./kiauto_*_all.deb
```

## Usage

Two scripts are provided:

- **eeschema_do**: interacts with KiCad's eeschema (schematic editor)
- **pcbnew_do**: interacts with KiCad's pcbnew (PCB editor)

You can get detailed help using the *--help* command line option. Here I include some basic usage.

### Export a schematic to PDF or SVG

```
eeschema_do export -a YOUR_SCHEMATIC.sch DESTINATION/
```
This will create *DESTINATION/YOUR_SCHEMATIC.pdf* file containing all the schematic pages. If you want just one page remove the *-a* option. If you want an SVG file just use *-f svg* like this:
```
eeschema_do export -a -f svg YOUR_SCHEMATIC.sch DESTINATION/
```
In this case you'll get one SVG for each page in your schematic.

### Run ERC

To run the Electrical Rules Check:
```
eeschema_do run_erc YOUR_SCHEMATIC.sch DESTINATION/
```
If an error is detected you'll get a message and the script will return a negative error level. Additionally you'll get *DESTINATION/YOUR_SCHEMATIC.erc* containing KiCad's report.

### Generate netlist

To generate or update the netlist, needed by other tools:
``` 
eeschema_do netlist YOUR_SCHEMATIC.sch DESTINATION/
```
You'll get *DESTINATION/YOUR_SCHEMATIC.net*

### Update BoM XML or basic BoM generation:

Tools like [KiBoM](https://github.com/SchrodingersGat/KiBoM) can generate a nice BoM, but in order to run them from the command line you need to be sure that the project's XML BoM is updated. You can do it running:
``` 
eeschema_do bom_xml YOUR_SCHEMATIC.sch DESTINATION/
```
After running it *./YOUR_SCHEMATIC.xml* will be updated. You'll also get *DESTINATION/YOUR_SCHEMATIC.csv* contain a very basic BoM generated using KiCad's *bom2grouped_csv.xsl* template.

### Run DRC

To run the Distance Rules Check:
```
pcbnew_do run_drc YOUR_PCB.kicad_pcb DESTINATION/
```
If an error is detected you'll get a message and the script will return a negative error level. Additionally you'll get *DESTINATION/drc_result.rpt* containing KiCad's report. You can select the name of the report using *--output_name* and you can ignore unconneted nets using *--ignore_unconnected*.

### Export layout as PDF

This is useful to complement your gerber files including some extra information in the *Dwgs.User* or *Cmts.User* layer.
```
pcbnew_do export YOUR_PCB.kicad_pcb DESTINATION/ LAYER1 LAYER2
```
Will generate *DESTINATION/printed.pdf* containing LAYER1 and LAYER2 overlapped. You can list as many layers as you want. I use things like ```F.Cu Dwgs.User```. The name of the layers is the same you see in the GUI, if your first inner layer is GND you just need to use ```GND.Cu```.

If you need to get a list of valid layers run:

```
pcbnew_do export --list YOUR_PCB.kicad_pcb
```

If you would like to export PDFs containing different layers in parallel to fully utilize multi-core CPUs:

```
pcbnew_do config -b
while ...; do
    pcbnew_do -b export YOUR_PCB.kicad_pcb DESTINATION/ LAYERs... & # background process
    sleep $delay # ensure configs are loaded before the next launch
done
wait
pcbnew_do config -r
```

This will run multiple instances in parallel with quite little overhead for ensuring configs are loaded, and wait until all export processes are exited. Then, restore the configs with the ones that are backed up in the beginning.

### Refilling copper zones

When you run the DRC KiCad will refill all zones. If you didn't do it before saving it could lead to a situation where the PCB that passes DRC isn't the one saved to disk. To solve you can use *-s* option to save the PCB after DRC:

```
pcbnew_do run_drc -s YOUR_PCB.kicad_pcb DESTINATION/
```

Another option could be to avoid changing the file on disk, but fill the zones before printing. To achieve it you can invoke the export command like this:

```
pcbnew_do export -f YOUR_PCB.kicad_pcb DESTINATION/ LAYERs...
```

### Common options

By default all the scripts run very quiet. If you want to get some information about what's going on use *-v*. 

The nature of these scripts make them very fragile. In particular when you run them in your every day desktop. You must avoid having *eeschema* and/or *pcbnew* windows opened while running the scripts. If you need to debug a problem you can:
1. Use the *-vv* option to get debug information
2. Use the *-r* option to record a video (OGV format) containing the GUI session. The file will be stored in the output directory and its name will begin with the name of the requested command.
3. Use the *-s* and *-w* options to start **x11vnc**. The execution will stop asking for a keypress. At this time you can start a VNC client like this: ```ssvncviewer :0```. You'll be able to see KiCad running and also interact with it.
4. Same as 3 but also using *-m*, in this case you'll get a window manager to move the windows and other stuff.

### Ignoring warnings and errors from ERC or DRC

Sometimes we need to ignore some warnings and/or errors reported during the ERC and/or DRC test.

To achieve it you need to create a *filters file*. Each line contains a rule to exclude one or more matching errors. The syntax is:

```
ERROR_ID,REGULAR_EXPRESSION
```

The regular expression must follow the Python syntax. In the simplest case this can be just the text that the error must contain.

The error id is just the KiCad internal number for the error you want to ignore. For KiCad 6 this is a string, not a number.

Here is an example, suppose our report says:

```
** Created on 2020-06-05 11:16:21 **

** Found 2 DRC errors **
ErrType(45): Courtyards overlap
    @(144.361 mm, 101.752 mm): Footprint C16 on F.Cu
    @(144.825 mm, 101.244 mm): Footprint C19 on F.Cu
ErrType(45): Courtyards overlap
    @(159.885 mm, 97.663 mm): Footprint R4 on F.Cu
    @(160.393 mm, 97.191 mm): Footprint C21 on F.Cu

** Found 0 unconnected pads **

** End of Report **
```

Here we have two errors, both number 45. So lets suppose we want to ignore the first error, we could use the following filter:

```
45,Footprint C16
```

This will ignore any error of type 45 (Courtyards overlap) related to *Footprint C16*. To use
it you just need mto use the *-f* command line option:


```
pcbnew_do run_drc -f FILTER_FILE YOUR_PCB.kicad_pcb DESTINATION/
```

Note that when using KiCad 6 the errors are strings enclosed by brackets, use only the text, not the brackets.

### Running on GitLab CI

If you want to use KiAuto in GitLab CI servers I'll recommend always using the `-r` option.

The scripts runs very well locally and using GitHub CI servers.
It also worked well on april 25 2020 on GitLab CI.
Tests on august 25 2020 on GitLab CI started to fail.
The v1.5.8 implements a workaround that is working on february 22 2021, but you must enable recording.

In case you are interested the misterious problem is related with the use Xvfb.
After starting Xvfb process we start polling it to ensure the server is up and running.
We use the `setxkbmap -query` command to know if Xvfb finished its start-up and is working.
After we can successfully run `setxkbmap -query` we assume Xvfb is fully functional.
For some reason this isn't true on GitLab CI servers, if we don't wait some time after the test the X server doesn't respond.
What is even more misterious is that we must run `recordmydesktop` or KiCad will fail to initialize GTK+.
I don't have any idea of why, but it works.

## History

I saw a presentation of Jesse Vincent ([@obra](https://github.com/obra)) in the [KiCon 2019](https://2019.kicad-kicon.com/) about automating KiCad tasks.

The presentation used [kicad-automation-scripts](https://github.com/obra/kicad-automation-scripts) as base for the tasks that needs to emulate the user interaction.
So I forked this repo.

But this wasn't the original repo, Jesse's repo is a fork of Productize SPRL's [scripts](https://github.com/productize/kicad-automation-scripts).
These scripts were created by Seppe Stas ([@seppestas](https://github.com/seppestas)).

According to Seppe he took many ideas from the [split-flap display project](https://scottbez1.github.io/splitflap/).
In particular from the files [here](https://github.com/scottbez1/splitflap/tree/master/electronics/scripts).
The author of split-flap is Scott Bezek ([@scottbez1](https://github.com/scottbez1)).
Scott explained the idea in his [blog](https://scottbezek.blogspot.be/2016/04/scripting-kicad-pcbnew-exports.html)

So this is the history of the scripts, at least what I know. In short: Scott Bezek had the original idea and used it for his project, but not as a separated tool.
Seppe Stas from Productize SPRL took the scripts and created a tool from them.
Then Jesse Vincent used the scripts to create a bigger set of tools and presented it on KiCon 2019.
And finally I (Salvador E. Tropea) took Jesse's scripts and adapted them to the needs of [KiBot](https://github.com/INTI-CMNB/KiBot).


