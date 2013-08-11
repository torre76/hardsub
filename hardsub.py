#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
	hardsub.py: Encode video with hard subtitles
"""

import argparse
import os
import platform
import shutil
import sys

import colorama

__author__ = "Gian Luca Dalla Torre"
__copyright__ = "Copyright 2013, Gian Luca Dalla Torre"
__credits__ = []
__license__ = "GPL v.3"
__version__ = "0.1"
__maintainer__ = "Gian Luca Dalla Torre"
__email__ = "gianluca.dallatorre@gmail.com"
__status__ = "Alpha"

# List of required executables on a Linux Box used to accomplish
# hard subbing
REQUIRED_EXECUTABLES = (
	'file',
	'mencoder',
	'mplayer',
	'mkvextract',
	'mkvmerge',
	'MP4Box'
	
)

def header():
	"""
		Print Script Header
	"""
	print(colorama.Style.BRIGHT + "HardSub " + colorama.Style.NORMAL + "v." + colorama.Style.BRIGHT+ " {}".format(__version__) + colorama.Style.NORMAL)
	print (__copyright__)
	print ("Licensed under " + colorama.Style.BRIGHT+ "{}".format(__license__) + colorama.Style.NORMAL + " license.\n")

def check_platform():
	"""
		Check if the platform is Linux
		:returns: boolean - True if the platform is Linux, False otherwise
	"""
	return platform.system() == "Linux"

def check_prerequisites():
	"""
		Check if all executables required by this script
		are present on the Linux Box.
		:returns: (Boolean, tuple) -- True if all required executables are present, False otherwhise. Second tuple value contains all missing executables
	"""
	missing_executables = []
	for executable in REQUIRED_EXECUTABLES:
		if shutil.which(executable) is None:
			missing_executables.append(executable)
	return (len(missing_executables) == 0, tuple(missing_executables))

def build_argument_parser():
	"""
		Build an ArgumentParser instance suitable for this script
		:returns: ArgumentParser -- ArgumentParser for this script
	"""
	ap = argparse.ArgumentParser(
		prog="hardsub",
		description="Encode video with hardsubs"
	)
	ap.add_argument("source_dir", help="Directory that contains video files to hardsub. This directory also had to hold srt files with the same name of video file")
	ap.add_argument("-o", "--output", required=True, help="States the output directory for hardsubbed video.", metavar="<output_dir>")
	return ap

def check_arguments(args):
	"""
		Check if passed arguments are coherent to the script
		:param args: arguments to check
		:type args: dict
		:returns: (boolean, tuple) -- True if the parameters are correct, False otherwhise. If parameters are not correct, tuple contains error messages 
	"""
	errors = []
	if not os.path.isdir(args['output']):
		errors.append( colorama.Style.BRIGHT + "output directory" +  colorama.Style.NORMAL + " is not a valid directory");
	if not os.path.isdir(args['source_dir']):
		errors.append( colorama.Style.BRIGHT + "source directory" +  colorama.Style.NORMAL + " is not a valid directory");
	return (len(errors) == 0, errors)

if __name__ == "__main__":
	colorama.init()
	header()
	# First check platform and, if it is not OK, programm will exit
	if not check_platform():
		print ("Sorry but, for now, only" + colorama.Style.BRIGHT + " Linux " + colorama.Style.NORMAL + "platform is supported.")
		sys.exit(1)
	# Second, check for all executables that are required by this script
	executables_found, missing_executables = check_prerequisites()
	if not executables_found:
		print ( colorama.Style.BRIGHT + "Some dependencies for this script are missing. "  + colorama.Style.NORMAL + "Please check that the following packages are installed on this Linux Box:")
		for me in missing_executables:
			print ("\t- "  + colorama.Style.BRIGHT + "{}".format(me)  + colorama.Style.NORMAL);
		sys.exit(2)
	# Check for script parameters
	ap = build_argument_parser()
	arguments = ap.parse_args(sys.argv[1:])
	parameter_checks, param_errors = check_arguments(vars(arguments))
	if not parameter_checks:
		print ( "Some parameters are inconsistent:")
		for pe in param_errors:
			print ("\t- {}".format(pe) );
		sys.exit(3)
	
