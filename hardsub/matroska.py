# -*- coding: utf-8 -*-

import os
import re

import pexpect

from utils import which, launch_process_with_progress_bar, get_base_file_name

# List of required executables on a Linux Box used to accomplish
# hard subbing
REQUIRED_EXECUTABLES = {
	'mencoder'   : '.*\((.*)%\).*',
	'mkvextract' : '.*: (\d+)%.*',
	'mkvmerge'   : '.*: (\d+)%.*',
}

verbose = False

debug = False

def check_video(file_name):
	"""
		Checks if the file has a video track
		:param file_name: file to check
		:type fille_name: string
		:returns: boolean -- True if the file has a video track, False otherwise. 
	"""
	found = False
	command = '{mkvmerge} -i "{input_file}"'.format(mkvmerge=which('mkvmerge')[0], input_file=file_name)
	if verbose:
		print command
	thread = pexpect.spawn(command)
	pl = thread.compile_pattern_list([
		pexpect.EOF,
		".*video.*"
		])
	while True:
		i = thread.expect_list(pl, timeout=None)
		if i == 0: # EOF, Process exited
			break
		if i == 1: # Status
			found = True	
	thread.close()	 
	return found

def hardsub_video(file_name, output_dir, scale):
	"""
		Hardsub a matroska video reencoding it using a .srt file for Subititles
		:param filename: Name of the file that had to be reencoded
		:type filename: str 
		:param output_dir: Directory where to place raw hardsubbed video
		:type output_dir: str
		:param scale: Subtitle font scale
		:type a: int
	"""
        base_file_name = get_base_file_name(file_name)
	# Build MEncoder command
	command = '{mencoder} -o "{output_file}" -nosound -noautosub -noskip -mc 0 -sub "{sub_file}" -subfont-text-scale "{subtitle_scale}" -ovc x264 -x264encopts crf=21:preset=slow:level_idc=31 "{input_file}"'.format(
		mencoder = which("mencoder")[0],
		output_file = "{}/{}.264".format(output_dir, base_file_name),
		sub_file = os.path.splitext(file_name)[0] + ".srt",
		subtitle_scale = scale,
		input_file = file_name
	)
	launch_process_with_progress_bar(command, REQUIRED_EXECUTABLES['mencoder'], 100, 'Video Encoding: ', verbose, debug)

def extract_audio(file_name, output_dir):
	"""
		Extract all audio tracks from a matroska container
		:param filename: Name of the file that contains audio track
		:type filename: str 
		:param output_dir: Directory where to place raw audio track
		:type output_dir: str	
	"""
	# detect how many audio track
	command = '{mkvmerge} -i "{input_file}"'.format(mkvmerge=which('mkvmerge')[0], input_file=file_name)
	if verbose:
		print command
	thread = pexpect.spawn(command)
	pl = thread.compile_pattern_list([
		pexpect.EOF,
		".*(\d+): audio.* \((.*)\)"
		])
	audio_tracks = {}
	while True:
		i = thread.expect_list(pl, timeout=None)
		if i == 0: # EOF, Process exited
			break
		if i == 1: # Status
			# TODO(gquadro): handle types other than AAC
			if 'A_AAC' in thread.match.group(2):
				audio_tracks[int(thread.match.group(1))] = 'aac'
			else:
				audio_tracks[int(thread.match.group(1))] = 'audio'
	thread.close()
        base_file_name = get_base_file_name(file_name)
	# Now extract each audio track
	for track in audio_tracks:
		output_file = output_dir + os.sep + base_file_name + '_' + "{}".format(track) + "." + audio_tracks[track]
		t_command = '{mkvextract} tracks "{input_file}" {track}:"{dest_file}"'.format(
			mkvextract = which("mkvextract")[0],
			input_file = file_name,
			track = track,
			dest_file = output_file
		)
		launch_process_with_progress_bar(t_command, REQUIRED_EXECUTABLES['mkvextract'], 100, 'Extract audio track {}: '.format(track), verbose, debug)
		
def mux_audio_video(file_name, output_dir):
	"""
		Rebuild the matroska container for source file with hardsubbed video track
		:param filename: Name of the file that had to be reencoded
		:type filename: str 
		:param output_dir: Directory where to place raw hardsubbed video
		:type output_dir: str
	"""
        base_file_name = get_base_file_name(file_name)
	list_of_files = [f for f in os.listdir(output_dir) if re.match(base_file_name + r'.*\.(264|audio)', f)]
	count = 0
	file_param = []
	for f in reversed(list_of_files):
		file_param.append('"' + output_dir + os.sep + f + "\" --compression {}:none".format(count))
		count = count + 1
	output_file = output_dir + os.sep + os.path.basename(file_name)
	command = '{mkvmerge} -o "{dest_file}" {files_opt}'.format(mkvmerge=which('mkvmerge')[0], dest_file = output_file, files_opt = " ".join(file_param))
	launch_process_with_progress_bar(command, REQUIRED_EXECUTABLES['mkvmerge'], 100, 'Rebuilding file: ', verbose, debug, (0, 1))
	# Cleaning some mess
	for f in reversed(list_of_files):
		os.remove(output_dir + os.sep + f) 

