# -*- coding: utf-8 -*-

import os
import re

import pexpect

from utils import which, launch_process_with_progress_bar

def check_video(file_name, verbose=False):
	"""
		Checks if the file has a video track
		:param file_name: file to check
		:type fille_name: string
		:returns: boolean -- True if the file has a video track, False otherwise. 
	"""
	found = False
	# copyed from midentify
	command = '{mplayer} -noconfig all -cache-min 0 -vo null -ao null -frames 0 -identify "{input_file}" 2>/dev/null | grep ID_VIDEO_FORMAT'.format(mplayer=which('mplayer')[0], input_file=file_name)
	if verbose:
		print command
	thread = pexpect.spawn(command)
	pl = thread.compile_pattern_list([
		pexpect.EOF,
		".*ID_VIDEO_FORMAT.*"
		])
	while True:
		i = thread.expect_list(pl, timeout=None)
		if i == 0:  # EOF, Process exited
			break
		if i == 1:  # Status
			found = True	
	thread.close()	 
	return found

def hardsub_video(file_name, output_dir, scale, verbose=False, debug=False):
	"""
		Hardsub a AVI video reencoding it using a .srt file for Subititles
		:param filename: Name of the file that had to be reencoded
		:type filename: str 
		:param output_dir: Directory where to place raw hardsubbed video
		:type output_dir: str
		:param scale: Subtitle font scale
		:type a: int
	"""
	# Build MEncoder command
	command = '{mencoder} -o "{output_file}" -nosound -noautosub -noskip -mc 0 -sub "{sub_file}" -subfont-text-scale "{subtitle_scale}" -ovc xvid -xvidencopts fixed_quant=2 "{input_file}"'.format(
		mencoder=which("mencoder")[0],
		output_file="{}/{}.xvid".format(output_dir, os.path.splitext(os.path.basename(file_name))[0]),
		sub_file=os.path.splitext(file_name)[0] + ".srt",
		subtitle_scale=scale,
		input_file=file_name
	)
	launch_process_with_progress_bar(command, '.*\((.*)%\).*', 100, 'Video Encoding: ', verbose, debug)

def extract_audio(file_name, output_dir, verbose=False, debug=False):
	"""
		Extract all audio tracks from a AVI container
		:param filename: Name of the file that contains audio track
		:type filename: str 
		:param output_dir: Directory where to place raw audio track
		:type output_dir: str	
	"""
	# detect how many audio track
	command = '{mplayer} -noconfig all -cache-min 0 -vo null -ao null -frames 0 -identify "{input_file}" 2>/dev/null | grep ID_AUDIO_ID'.format(mplayer=which('mplayer')[0], input_file=file_name)
	if verbose:
		print command
	thread = pexpect.spawn(command)
	pl = thread.compile_pattern_list([
		pexpect.EOF,
		"ID_AUDIO_ID=(\d+).*"
		])
	audio_tracks = []
	while True:
		i = thread.expect_list(pl, timeout=None)
		if i == 0:  # EOF, Process exited
			break
		if i == 1:  # Status
			audio_tracks.append(int(thread.match.group(1)))	
	thread.close()	 
	# Now extract each audio track
	for track in audio_tracks:
		t_command = '{mplayer} -aid {track} -dumpaudio -dumpfile {dest_file} "{input_file}"'.format(
			mplayer=which("mplayer")[0],
			input_file=file_name,
			track=track,
			dest_file=output_dir + os.sep + "{}".format(track) + ".audio"
		)
		launch_process_with_progress_bar(t_command, '.*(\d+)%.*', 100, 'Extract audio track {}: '.format(track), verbose, debug)

def mux_audio_video(file_name, output_dir, verbose=False, debug=False):
	"""
		Rebuild the AVI container for source file with hardsubbed video track
		:param filename: Name of the file that had to be reencoded
		:type filename: str 
		:param output_dir: Directory where to place raw hardsubbed video
		:type output_dir: str
	"""
	list_of_files = [f for f in os.listdir(output_dir)  if re.match(r'.*\.(xvid|audio)', f)]
	input_param = []
	map_param = []
	count = 0
	for f in reversed(list_of_files):
		if f[-5:] == '.xvid':
			video_file = '-i "' + output_dir + os.sep + f + '"'
		else:
			count = count + 1
			input_param.append('-i "' + output_dir + os.sep + f + '"')
			map_param.append('-map ' + str(count) + ':0')

	# Gather data for the progress bar.
	# If you have ffmpeg you have ffprobe, so it is not checked in REQUIRED_EXECUTABLES
	command = '{ffprobe} -show_streams {video_input}'.format(
		ffprobe=which('ffprobe')[0],
                video_input=video_file,
	)
	thread = pexpect.spawn(command)
	pl = thread.compile_pattern_list([
		pexpect.EOF,
		"nb_frames=(\d+).*"
		])
	while True:
		i = thread.expect_list(pl, timeout=None)
		if i == 0:  # EOF, Process exited
			break
		if i == 1:  # Status
			tot_frames = int(thread.match.group(1))
	thread.close()	 

	command = '{ffmpeg} -y {video_input} {input_params} -c copy -map 0:0 {map_params} "{dest_file}"'.format(
		ffmpeg=which('ffmpeg')[0],
                video_input=video_file,
		input_params=' '.join(input_param),
		map_params=' '.join(map_param),
		dest_file=output_dir + os.sep + os.path.basename(file_name)
	)
	launch_process_with_progress_bar(command, '.*frame=(\d+).*', tot_frames, 'Rebuilding file: ', verbose, debug)
	# Cleaning some mess
	for f in reversed(list_of_files):
		os.remove(output_dir + os.sep + f) 
