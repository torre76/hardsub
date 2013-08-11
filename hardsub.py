#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
	hardsub.py: Encode video with hard subtitles
"""

import shutil

__author__ = "Gian Luca Dalla Torre"
__copyright__ = "Copyright 2013, Gian Luca Dalla Torre"
__credits__ = []
__license__ = "GPL"
__version__ = "0.1"
__maintainer__ = "Gian Luca Dalla Torre"
__email__ = "gianluca.dallatorre@gmail.com"
__status__ = "Alpha"

# List of required executables on a Linux Box used to accomplish
# hard subbing
REQUIRED_EXECUTABLES = (
	'mencoder',
	'mplayer',
	'mkvextract',
	'mkvmerge',
	'MP4Box'
	
)

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

if __name__ == "__main__":
	print (check_prerequisites())
