# -*- coding: utf-8 -*-

"""
.. currentmodule: hardsub

    :synopsis: Module that contains function and classes to hardsub videos
"""

import argparse
import os
import platform
import re
import subprocess
import sys

import colorama
import magic

from utils import which

__author__ = "Gian Luca Dalla Torre, Luigi Bellagotti"
__copyright__ = "Copyright 2013, Gian Luca Dalla Torre and Luigi Bellagotti"
__credits__ = []
__license__ = "GPL v.3"
__version__ = "0.0.1"
__maintainer__ = "Gian Luca Dalla Torre"
__email__ = "gianluca.dallatorre@gmail.com"
__status__ = "Alpha"

# List of magic signatures for video files
ALLOWED_MAGIC_SIG = {
	'AVI': 'avi',
	'MPEG v4': 'mp4',
	#'ISO Media, MPEG v4 system, version 1': 'mp4',
	#'ISO Media, MPEG v4 system, version 2': 'mp4',
	'Matroska': 'matroska' 
}

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

def check_prerequisites(file_name):
	"""
		Check if all executables required by this script
		are present on the Linux Box.
		:returns: (Boolean, tuple) -- True if all required executables are present, False otherwhise. Second tuple value contains all missing executables
	"""
	missing_executables = []
	magic_sig = magic.from_file(file_name)
	kind = None
	for ms in ALLOWED_MAGIC_SIG:
		if ms in magic_sig:  
			kind = ALLOWED_MAGIC_SIG[ms]
			break
	if kind is not None:
		movie_type = __import__('hardsub.'+kind, fromlist=["x"])
		for executable in movie_type.REQUIRED_EXECUTABLES:
			if len(which(executable)) == 0:
				missing_executables.append(executable)
	return (len(missing_executables) == 0, tuple(missing_executables))

def build_argument_parser():
	"""
		Build an ArgumentParser instance suitable for this script
		:returns: ArgumentParser -- ArgumentParser for this script
	"""
	ap = argparse.ArgumentParser(
		prog="hs",
		description="Encode video with hardsubs"
	)
	ap.add_argument("source_dir", help="Directory that contains video files to hardsub. This directory also had to hold srt files with the same name of video file")
	ap.add_argument("-o", "--output", required=True, help="States the output directory for hardsubbed video.", metavar="<output_dir>")
	ap.add_argument("-s", "--subtitle-scale", default=2.5, help="Set the font scale (between 1 and 100)", metavar="<subtitle_scale>")
	ap.add_argument("-v", "--verbose", help="increase output verbosity", action="store_true")
	ap.add_argument("-f", "--force", help="write to output directory even if it is not empty", action="store_true")
	ap.add_argument("--debug", help="save stdout and stderr on /tmp/hs.log", action="store_true")
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

def find_candidates(directory):
	"""
		Find all video container file that have an srt associated for hardsubbing
		:param directory: Directory where to find candidates
		:type directory: str
		:returns: list -- list of file that hat to be hardsubbed
	"""
	candidates = {}
	for f in os.listdir(directory):
		if os.path.isfile(directory + os.sep + f):
			for m in ALLOWED_MAGIC_SIG:
				if m in magic.from_file(directory + os.sep + f):
					candidates[directory + os.sep + f] = ALLOWED_MAGIC_SIG[m]
	# Check if there is a srt companion file, if not, remove element from candidates
	final_candidates = []
	for f in candidates:
		sub_file = os.path.splitext(f)[0] + ".srt"
		if os.path.isfile(sub_file):
			movie_type = __import__('hardsub.'+candidates[f], fromlist=["x"])
			if movie_type.check_video(f):
				final_candidates.append(f)
	final_candidates.sort()
	return final_candidates

def extract_audio(file_name, output_dir, verbose=False, debug=False):
	"""
		Extract all audio tracks from a container
		:param filename: Name of the file that contains audio track
		:type filename: str 
		:param output_dir: Directory where to place raw audio track
		:type output_dir: str	
	"""
	magic_sig = magic.from_file(file_name)
	kind = None
	for ms in ALLOWED_MAGIC_SIG:
		if ms in magic_sig:  
			kind = ALLOWED_MAGIC_SIG[ms]
			break
	if kind is not None:
		movie_type = __import__('hardsub.'+kind, fromlist=["x"])
		movie_type.verbose = verbose
		movie_type.debug = debug
		movie_type.extract_audio(file_name, output_dir)

def hardsub_video(file_name, output_dir, scale, verbose=False, debug=False):
	"""
		Hardsub a video reencoding it using a .srt file for Subititles
		:param filename: Name of the file that had to be reencoded
		:type filename: str 
		:param output_dir: Directory where to place raw hardsubbed video
		:type output_dir: str
		:param scale: Subtitle font scale
		:type a: int
	"""
	magic_sig = magic.from_file(file_name)
	kind = None
	for ms in ALLOWED_MAGIC_SIG:
		if ms in magic_sig:  
			kind = ALLOWED_MAGIC_SIG[ms]
			break
	if kind is not None:
		movie_type = __import__('hardsub.'+kind, fromlist=["x"])
		movie_type.verbose = verbose
		movie_type.debug = debug
		movie_type.hardsub_video(file_name, output_dir, scale)

def build_final_file(file_name, output_dir, verbose=False, debug=False):
	"""
		Rebuild the container for source file with hardsubbed video track
		:param filename: Name of the file that had to be reencoded
		:type filename: str 
		:param output_dir: Directory where to place raw hardsubbed video
		:type output_dir: str
	"""
	magic_sig = magic.from_file(file_name)
	kind = None
	for ms in ALLOWED_MAGIC_SIG:
		if ms in magic_sig:  
			kind = ALLOWED_MAGIC_SIG[ms]
			break
	if kind is not None:
		movie_type = __import__('hardsub.'+kind, fromlist=["x"])
		movie_type.verbose = verbose
		movie_type.debug = debug
		movie_type.mux_audio_video(file_name, output_dir)

def hardsub_main():
	"""
		Hardsub files specified on standard input
	"""
	colorama.init()
	header()
	# First check platform and, if it is not OK, programm will exit
	if not check_platform():
		print ("Sorry but, for now, only" + colorama.Style.BRIGHT + " Linux " + colorama.Style.NORMAL + "platform is supported.")
		sys.exit(1)
	# Check for script parameters
	ap = build_argument_parser()
	arguments = ap.parse_args(sys.argv[1:])
	parameter_checks, param_errors = check_arguments(vars(arguments))
	if not parameter_checks:
		print ( "Some parameters are inconsistent:")
		for pe in param_errors:
			print ("\t- {}".format(pe) );
		sys.exit(3)
	# Check if dest dir is empty or force was specified
	if os.listdir(arguments.output) == [] or arguments.force :
		if os.listdir(arguments.output) != [] and arguments.verbose :
			print "Output directory not empty. Proceeding because -f was specified"
	else :
		print (colorama.Style.BRIGHT + "The output directory is not empty." + colorama.Style.NORMAL + 
			" If you still want to proceed use the " + colorama.Style.BRIGHT + "-f" + colorama.Style.NORMAL + " parameter")
		sys.exit(5)
	# Get Files to hardsub
	files_to_hardsub = find_candidates(arguments.source_dir)
	if len(files_to_hardsub) == 0:
		print ("There are no video files to hardsub on the source directory.")
		sys.exit(4)
	print ("Those files will be hardsubbed (i.e. they are video file and they have a corresponding .srt file):")	
	for f in files_to_hardsub:
		print ("\t- "  + colorama.Fore.GREEN + colorama.Style.BRIGHT + "{}".format(os.path.basename(f)) + colorama.Style.NORMAL + colorama.Fore.RESET)
	current_file = 1
	for f in files_to_hardsub:
		print ("\nStart work on " + colorama.Fore.GREEN + colorama.Style.BRIGHT + "{}".format(os.path.basename(f)) + colorama.Style.NORMAL + colorama.Fore.RESET + 
			" ("  + colorama.Style.BRIGHT + "{}/{}".format(current_file, len(files_to_hardsub)) + colorama.Style.NORMAL + ").")
		print ("")
		# Check for all executables that are required by this script
		executables_found, missing_executables = check_prerequisites(f)
		if not executables_found:
			print (colorama.Style.BRIGHT + "Some dependencies for this script are missing. "  + colorama.Style.NORMAL + 
				"Please check that the following packages are installed on this Linux Box:")
			for me in missing_executables:
				print ("\t- "  + colorama.Style.BRIGHT + "{}".format(me)  + colorama.Style.NORMAL);
			sys.exit(2)
		hardsub_video(f, arguments.output, arguments.subtitle_scale, arguments.verbose, arguments.debug)
		extract_audio(f, arguments.output, arguments.verbose, arguments.debug)
		build_final_file(f, arguments.output, arguments.verbose, arguments.debug)
		current_file = current_file + 1
