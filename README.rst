====================================
HS - Hardsub video file on GNU/Linux
====================================

HS is a *python* script that simplifies re-encoding a video with subtitles irreversibly merged into its frames. 

It starts from a video source file and its `SubRip text file format <http://en.wikipedia.org/wiki/.srt#SubRip_text_file_format>`_ (at this moment only *srt* files are supported) and it will produce a new video file of the same type of the source but with subtitles merged into video track.

What video containers this script supports? 
-------------------------------------------

It supports `AVI <http://en.wikipedia.org/wiki/Audio_Video_Interleave>`_,  `Matroska <http://en.wikipedia.org/wiki/Matroska>`_ and `MPEG-4 <http://en.wikipedia.org/wiki/MP4>`_ containers.

Why I should use this script?
-----------------------------

This script is useful if you have an old video decoder which does not support external *srt* files or if you prefer that subtitles for your video have to be immutable.

Installation
------------

*This page is intentionally left blank.*

*At least until* `#3 <https://github.com/torre76/hardsub/issues/3>`_ *will be resolved.*

Usage
----- 

Once installed, the command syntax is:

.. code:: bash

	hs -o <output_dir> source_dir

where:

- *output_dir* is the directory where reencoded video will be placed
- *source_dir* is the directory where video file(s) and relatives subititle file(s) has been placed. **Please note that the srt file and video file must have the same name otherwhise the script will not consider this video as a source file**.

Additional parameters
_____________________

*HS* has also additional paramteres:

- *-h* that shows an inline help
- *-v* that displays the underliying command that will be used for reencoding
- *-s* that states the size of subtitle text (1 - normal, 4 - blinded, any value inside this range is accepted).

Examples
________

.. code:: bash

	hs -o out/ in/

will encode any video file present in *in* folder that has an *srt* file with the same name of video file and will output the new files in *out* folder.

.. code:: bash

	hs -s 4 -o out/ in/

same as above but the subtitle text will be gigantic.
