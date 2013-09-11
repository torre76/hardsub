# -*- coding: utf-8 -*-

import os
import re

import colorama
import pexpect

from utils import which, launch_process_with_progress_bar, get_base_file_name

def check_video(file_name, verbose=False):
	"""
		Checks if the file has a video track
		:param file_name: file to check
		:type fille_name: string
		:returns: boolean -- True if the file has a video track, False otherwise. 
	"""
	found = False
	command = '{mp4info} "{input_file}"'.format(mp4info=which('mp4info')[0], input_file=file_name)
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

def hardsub_video(file_name, output_dir, scale, verbose=False, debug=False):
	"""
		Hardsub a MP4 video reencoding it using a .srt file for Subititles
		:param filename: Name of the file that had to be reencoded
		:type filename: str 
		:param output_dir: Directory where to place raw hardsubbed video
		:type output_dir: str
		:param scale: Subtitle font scale
		:type a: int
	"""
        base_file_name = get_base_file_name(file_name)
	# Build MEncoder command
	command = '{mencoder} -o "{output_file}" -of rawvideo -nosound -noautosub -noskip -mc 0 -sub "{sub_file}" -subfont-text-scale "{subtitle_scale}" -ovc x264 -x264encopts crf=21:preset=slow:level_idc=31 "{input_file}"'.format(
		mencoder = which("mencoder")[0],
		output_file = "{}/{}.264".format(output_dir, base_file_name),
		sub_file = os.path.splitext(file_name)[0] + ".srt",
		subtitle_scale = scale,
		input_file = file_name
	)
	launch_process_with_progress_bar(command, '.*\((.*)%\).*', 'Video Encoding: ', verbose, debug)

def extract_audio(file_name, output_dir, verbose=False, debug=False):
	"""
		Extract all audio tracks from a MP4 container
		:param filename: Name of the file that contains audio track
		:type filename: str 
		:param output_dir: Directory where to place raw audio track
		:type output_dir: str	
	"""
	# detect how many audio tracks
	command = '{mp4info} "{input_file}"'.format(mp4info=which('mp4info')[0], input_file=file_name)
	if verbose:
		print command
	thread = pexpect.spawn(command)
	pl = thread.compile_pattern_list([
		pexpect.EOF,
		"(\d+)\s+audio\s+(.*)"
		])
	audio_tracks = {}
	while True:
		i = thread.expect_list(pl, timeout=None)
		if i == 0: # EOF, Process exited
			break
		if i == 1: # Status
			# MP4Box gets the type of the audio track from the extension
			# TODO(gquadro): handle types other than AAC
			if 'AAC' in thread.match.group(2):
				audio_tracks[int(thread.match.group(1))] = 'aac'
			else:
				audio_tracks[int(thread.match.group(1))] = 'audio'
	thread.close()
        base_file_name = get_base_file_name(file_name)
	# Now extract each audio track
	for track in audio_tracks:
		# If the destination file already exists, MP4Box adds the new track to it
		output_file = output_dir + os.sep + base_file_name + '_' + "{}".format(track) + "." + audio_tracks[track]
		if os.path.isfile(output_file):
			os.remove(output_file)
		t_command = '{mp4box} -out "{dest_file}" -raw {track} "{input_file}"'.format(
			mp4box = which("MP4Box")[0],
			input_file = file_name,
			track = track,
			dest_file = output_file
		)
		launch_process_with_progress_bar(t_command, '.*(\d+)%.*', 'Extract audio track {}: '.format(track), verbose, debug)

def mux_audio_video(file_name, output_dir, verbose=False, debug=False):
	"""
		Rebuild the MP4 container for source file with hardsubbed video track
		:param filename: Name of the file that had to be reencoded
		:type filename: str 
		:param output_dir: Directory where to place raw hardsubbed video
		:type output_dir: str
	"""
        base_file_name = get_base_file_name(file_name)
	#list_of_files = [f for f in os.listdir(output_dir) if re.match(r'.*\.(264|aac|audio)', f)]
	list_of_files = [f for f in os.listdir(output_dir) if re.match(base_file_name + r'.*\.(264|aac|audio)', f)]
	file_param = []
	for f in reversed(list_of_files):
		file_param.append('-add "' + output_dir + os.sep + f + '"')

	# If the destination file already exists, MP4Box adds the new tracks to it
	output_file = output_dir + os.sep + os.path.basename(file_name)
	index_out = 0
	while os.path.isfile(output_file):
		print (colorama.Style.BRIGHT + 'File ' + output_file + ' already exists' + colorama.Style.NORMAL);
		index_out = index_out + 1
		output_file = output_dir + os.sep + os.path.basename(file_name) + '_' + str(index_out)

	command = '{MP4Box} -quiet {add_audio_opts} "{dest_file}"'.format(
		MP4Box = which('MP4Box')[0],
		add_audio_opts = ' '.join(file_param),
		dest_file = output_file
	)
	launch_process_with_progress_bar(command, '.*(\d+)%.*', 'Rebuilding file: ', verbose, debug)
	# Cleaning some mess
	for f in reversed(list_of_files):
		os.remove(output_dir + os.sep + f) 
