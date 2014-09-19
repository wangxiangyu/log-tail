# -*- coding: utf-8 -*-
"""
@author: zhaolongbin@baidu.com
@date: Aug,2014
@summary: Pygtail
@version: 0.4.0
@copyright: Copyright (c) 2014 Baidu.com, Inc. All Rights Reserved
"""

import os, sys, time, sched, glob
from os import stat
from os.path import exists, getsize

from kafka.client import KafkaClient
from kafka.producer import SimpleProducer
from ub_conf import UbConfig 
from comlog import comlog

class PygtailSlice(object):
    """
    Creates an iterable object that returns only unread lines.

    Keyword arguments:
    offset_file   File to which offset data is written (default: <logfile>.offset).
    paranoid      Update the offset file every time we read a line (as opposed to
                  only when we reach the end of the file (default: False)
    copytruncate  Support copytruncate-style log rotation (default: True)
    """
    def __init__(self, filepath, filename, match_str, offset_file=None, paranoid=False, copytruncate=True):
        self.filepath = filepath
        self.filename = filepath + filename
        self.match_str = match_str
        self.cur_filename = self._check_rotated_filename_candidates()[-1]
        self.paranoid = paranoid
        self.copytruncate = copytruncate
        self._offset_file = offset_file or "%s%s.offset" % ("./../data/", filename)
        self._offset_file_inode = 0
        self._offset = 0
        self._fh = None
        self._rotated_logfile = None

        # if offset file exists and non-empty, open and parse it
        if exists(self._offset_file) and getsize(self._offset_file):
            offset_fh = open(self._offset_file, "r")
            (self._offset_file_inode, self._offset) = \
                [int(line.strip()) for line in offset_fh]
            offset_fh.close()
	  #  if self._offset_file_inode != stat(self.cur_filename).st_ino:
                # The inode has changed or filesize has reduced so the file
                # might have been rotated.
                # Look for the rotated file and process that if we find it.
        self._rotated_logfile = self._determine_rotated_logfile()
	self.filename = self._rotated_logfile
	
    def __del__(self):
        if self._filehandle():
            self._filehandle().close()

    def __iter__(self):
        return self

    def next(self):
        """
        Return the next line in the file, updating the offset.
        """
        try:
            line = next(self._filehandle())
        except StopIteration:
            # we've reached the end of the file; if we're processing the
            # rotated log file, we can continue with the actual file; otherwise
            # update the offset file
            if self._rotated_logfile:
                self._rotated_logfile = None
                self._fh.close()
                # open up current logfile and continue
                try:
		    if self._determine_rotated_logfile() != self.cur_filename:  
                        line = next(self._cur_filehandle())
                    else:
                        line = next(self._filehandle())
                except StopIteration:  # oops, empty file
                    self._update_offset_file()
                    raise
            else:
                self._update_offset_file()
                raise

        if self.paranoid:
            self._update_offset_file()

        return line

    def __next__(self):
        """`__next__` is the Python 3 version of `next`"""
        return self.next()

    def readlines(self):
        """
        Read in all unread lines and return them as a list.
        """
        return [line for line in self]

    def read(self):
        """
        Read in all unread lines and return them as a single string.
        """
        lines = self.readlines()
        if lines:
            return ''.join(lines)
        else:
            return None

    def _filehandle(self):
        """
        Return a filehandle to the file being tailed, with the position set
        to the current offset.
        """
        if not self._fh or self._fh.closed:
            filename = self.filename
            self._fh = open(filename, "r")
            self._fh.seek(self._offset)

        return self._fh


    def _cur_filehandle(self):
        """
        Return a filehandle to the file being tailed, with the position set
        to the current offset.
        """
        if not self._fh or self._fh.closed:
            filename = self.cur_filename
            self._fh = open(filename, "r")
            self._fh.seek(0)

        return self._fh

    def _update_offset_file(self):
        """
        Update the offset file with the current inode and offset.
        """
        self._offset = self._cur_filehandle().tell()
        inode = stat(self.cur_filename).st_ino
        fh = open(self._offset_file, "w")
        fh.write("%s\n%s\n" % (inode, self._offset))
        fh.close()

    def _determine_rotated_logfile(self):
        """
        We suspect the logfile has been rotated, so try to guess what the
        rotated filename is, and return it.
        """
	file_list = self._check_rotated_filename_candidates()
        rotated_filename = file_list[-1]
	if rotated_filename and exists(rotated_filename):
            if stat(rotated_filename).st_ino == self._offset_file_inode:
                return rotated_filename

            # if the inode hasn't changed, then the file shrank; this is expected with copytruncate,
            # otherwise print a warning
	    if len(file_list) < 2:
                old_rotated_filename = self._check_rotated_filename_candidates()[-1]
            else:
                old_rotated_filename = self._check_rotated_filename_candidates()[-2]
            if stat(old_rotated_filename).st_ino == self._offset_file_inode:
                if self.copytruncate:
                    return old_rotated_filename
                else:
                    print (
                        "[pygtail] [WARN] file size of %s shrank, and copytruncate support is "
                        "disabled (expected at least %d bytes, was %d bytes).\n" %
                        (self.filename, self._offset, stat(self.filename).st_size))

        return rotated_filename

    def _check_rotated_filename_candidates(self):
        """
        Check for various rotated logfile filename patterns and return the first
        match we find.
        """
        candidates = glob.glob(self.filepath + "/" + self.match_str)
 	if len(candidates) < 1:
            comlog.fatal("The log file is not exist:%s", self.filepath + "/" + self.match_str)
	    sys.exit()
        if candidates:
            candidates.sort()
            return candidates

        # no match
        return None

__version__ = '0.4.0'



