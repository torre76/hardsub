# -*- coding: utf-8 -*-

import os

import colorama
import pexpect
import progressbar

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
	   
def launch_process_with_progress_bar(command, progress_reg_exp, progress_bar_message="Working", verbose=False):
	"""
		Launch a process and show a progress bar with auto calculated ETA.
		:param command: Command to launch
		:type command: str
		:param progress_reg_exp: Regular Expression used to get process update percentage. It is applied on standard output
		:type progress_reg_exp: str
		:param progress_bar_message: Message shown on progress bar
		:type progress_bar_message: str
	"""
	if verbose:
		print command
	thread = pexpect.spawn(command)
	pl = thread.compile_pattern_list([
		pexpect.EOF,
		progress_reg_exp
		])
	widgets = [progress_bar_message, progressbar.Percentage(), ' ', progressbar.Bar(fill="-"),
               ' ', progressbar.AdaptiveETA(), ' ']
	pbar = progressbar.ProgressBar(widgets=widgets, maxval=100).start()
	while True:
		i = thread.expect_list(pl, timeout=None)
		if i == 0:  # EOF, Process exited
			pbar.finish()
			break
		if i == 1:  # Status
			progress = int(thread.match.group(1))
			pbar.update(progress)	
	thread.close()
        if thread.exitstatus != 0 :
		print (colorama.Fore.RED + "Error in execution of command. " + colorama.Fore.RESET + "Try again with -v switch to see the executed command.")
		quit()
