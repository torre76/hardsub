#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
	hardsub.py: Encode video with hard subtitles
"""

import argparse
import os
import platform
import re
import subprocess
import sys

import colorama
import magic
import pexpect
import progressbar

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

# List of magic signatures for video files
ALLOWED_MAGIC_SIG = [
	'AVI',
	'MPEG v4',
	'Matroska'
]

def which(name, flags=os.X_OK):
	    """Search PATH for executable files with the given name.
	   
	    On newer versions of MS-Windows, the PATHEXT environment variable will be
	    set to the list of file extensions for files considered executable. This
	    will normally include things like ".EXE". This fuction will also find files
	    with the given name ending with any of these extensions.
	
	    On MS-Windows the only flag that has any meaning is os.F_OK. Any other
	    flags will be ignored.
	   
	    @type name: C{str}
	    @param name: The name for which to search.
	   
	    @type flags: C{int}
	    @param flags: Arguments to L{os.access}.
	   
	    @rtype: C{list}
	    @param: A list of the full paths to files found, in the
	    order in which they were found.
	    """
	    result = []
	    exts = filter(None, os.environ.get('PATHEXT', '').split(os.pathsep))
	    path = os.environ.get('PATH', None)
	    if path is None:
	        return []
	    for p in os.environ.get('PATH', '').split(os.pathsep):
	        p = os.path.join(p, name)
	        if os.access(p, flags):
	            result.append(p)
	        for e in exts:
	            pext = p + e
	            if os.access(pext, flags):
	                result.append(pext)
	    return result

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
		if len(which(executable)) == 0:
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
	ap.add_argument("-s", "--subtitle-scale", default=2.5, help="Set the font scale (between 1 and 100)", metavar="<subtitle_scale>")
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
	candidates = []
	for f in os.listdir(directory):
		if os.path.isfile(directory + os.sep + f):
			for m in ALLOWED_MAGIC_SIG:
				if m in magic.from_file(directory + os.sep + f):
					candidates.append(directory + os.sep + f)
	# Check if there is a srt companion file, if not, remove element from candidates
	final_candidates = []
	for f in candidates:
		sub_file = os.path.splitext(f)[0] + ".srt"
		if os.path.isfile(sub_file):
			final_candidates.append(f)
	return final_candidates

def launch_process_with_progress_bar(command, progress_reg_exp, progress_bar_message="Working"):
	"""
		Launch a process and show a progress bar with auto calculated ETA.
		:param command: Command to launch
		:type command: str
		:param progress_reg_exp: Regular Expression used to get process update percentage. It is applied on standard output
		:type progress_reg_exp: str
		:param progress_bar_message: Message shown on progress bar
		:type progress_bar_message: str
	"""
	thread = pexpect.spawn(command)
	pl = thread.compile_pattern_list([
		pexpect.EOF,
		progress_reg_exp
		])
	widgets = [progress_bar_message, progressbar.Percentage(), ' ', progressbar.Bar(),
               ' ', progressbar.AdaptiveETA(), ' ']
	pbar = progressbar.ProgressBar(widgets=widgets, maxval=100).start()
	while True:
		i = thread.expect_list(pl, timeout=None)
		if i == 0: # EOF, Process exited
			pbar.finish()
			break
		if i == 1: # Status
			progress = int(thread.match.group(1))
			pbar.update(progress)	
	thread.close()

def hardsub_matroska_video(file_name, output_dir, scale):
	"""
		Hardsub a matroska video reencoding it using a .srt file for Subititles
		:param filename: Name of the file that had to be reencoded
		:type filename: str 
		:param output_dir: Directory where to place raw hardsubbed video
		:type output_dir: str
		:param scale: Subtitle font scale
		:type a: int
	"""
	# Build MEncoder command
	command = '{mencoder} -o {output_file} -nosound -noautosub -noskip -mc 0 -sub {sub_file} -subfont-text-scale {subtitle_scale} -ovc x264 -x264encopts crf=21:preset=slow:level_idc=31 {input_file}'.format(
		mencoder = which("mencoder")[0],
		output_file = "{}/{}.264".format(output_dir, os.path.splitext(os.path.basename(file_name))[0]),
		sub_file = os.path.splitext(f)[0] + ".srt",
		subtitle_scale = scale,
		input_file = file_name
	)
	launch_process_with_progress_bar(command, '.*\((.*)%\).*', 'Video Encoding: ')

def extract_matroska_audio(file_name, output_dir):
	"""
		Extract all audio tracks from a matroska container
		:param filename: Name of the file that contains audio track
		:type filename: str 
		:param output_dir: Directory where to place raw audio track
		:type output_dir: str	
	"""
	# detect how many audio track
	command = "{mkvmerge} -i {input_file}".format(mkvmerge=which('mkvmerge')[0], input_file=file_name)
	thread = pexpect.spawn(command)
	pl = thread.compile_pattern_list([
		pexpect.EOF,
		".*(\d): audio.*"
		])
	audio_tracks = []
	while True:
		i = thread.expect_list(pl, timeout=None)
		if i == 0: # EOF, Process exited
			break
		if i == 1: # Status
			audio_tracks.append(int(thread.match.group(1)))	
	thread.close()	 
	# Now extract each audio track
	for track in audio_tracks:
		t_command = "{mkvextract} tracks {input_file} {track}:{dest_file}".format(
			mkvextract = which("mkvextract")[0],
			input_file = file_name,
			track = track,
			dest_file = output_dir + os.sep + "{}".format(track) + ".audio"
		)
		launch_process_with_progress_bar(t_command, '.*(\d)%.*', 'Extract audio track {}: '.format(track))
		

def extract_audio(file_name, output_dir):
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
			kind = ms
			break
	if kind == "Matroska":
		extract_matroska_audio(file_name, output_dir)

def hardsub_video(file_name, output_dir, scale):
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
			kind = ms
			break
	if kind == "Matroska":
		hardsub_matroska_video(file_name, output_dir, scale)

def build_matroska_final_file(file_name, output_dir):
	"""
		Rebuild the matroska container for source file with hardsubbed video track
		:param filename: Name of the file that had to be reencoded
		:type filename: str 
		:param output_dir: Directory where to place raw hardsubbed video
		:type output_dir: str
	"""
	list_of_files = [f for f in os.listdir(output_dir)  if re.match(r'.*\.(264|audio)', f)]
	count = 0
	file_param = []
	for f in reversed(list_of_files):
		file_param.append(output_dir + os.sep + f + " --compression {}:none".format(count))
		count = count + 1
	command = "{mkvmerge} -o {dest_file} {files_opt}".format(mkvmerge=which('mkvmerge')[0], dest_file = output_dir + os.sep + os.path.basename(file_name), files_opt = " ".join(file_param))
	launch_process_with_progress_bar(command, '.*(\d)%.*', 'Rebuilding file: ')
	# Cleaning some mess
	for f in reversed(list_of_files):
		os.remove(output_dir + os.sep + f) 

def build_final_file(file_name, output_dir):
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
			kind = ms
			break
	if kind == "Matroska":
		build_matroska_final_file(file_name, output_dir)

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
		print ("\nStart work on " + colorama.Fore.GREEN + colorama.Style.BRIGHT + "{}".format(os.path.basename(f)) + colorama.Style.NORMAL + colorama.Fore.RESET + " ("  + colorama.Style.BRIGHT + "{}/{}".format(current_file, len(files_to_hardsub)) + colorama.Style.NORMAL + ").")
		print ("")
		hardsub_video(f, arguments.output, arguments.subtitle_scale)
		extract_audio(f, arguments.output)
		build_final_file(f, arguments.output)
		current_file = current_file + 1
