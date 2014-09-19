# -*- coding: utf-8 -*-
"""
@author: wangxiangyu@baidu.com
@date: Aug,2014
@summary: Pygtail
@version: 0.4.0
@copyright: Copyright (c) 2014 Baidu.com, Inc. All Rights Reserved
"""

import os, sys, time, sched, glob, re
from os import stat
from os.path import exists, getsize

from kafka.client import KafkaClient
from kafka.producer import SimpleProducer
from ub_conf import UbConfig 
from comlog import comlog

class PygtailMtime(object):
    """
    Creates an iterable object that returns only unread lines.

    Keyword arguments:
    filepath      The path where to search log files
    filename_pattern  The regular expressions to match log files
    offset_file   File to which offset data is written (default: <logfile>.offset).
    paranoid      Update the offset file every time we read a line (as opposed to
                  only when we reach the end of the file (default: False)
    copytruncate  Support copytruncate-style log rotation (default: True)
    """
    def __init__(self, filepath, filename_pattern, offset_file=None, paranoid=False, copytruncate=True):
        self.filepath = filepath
        self.filename_pattern = filename_pattern
        self.paranoid = paranoid
        self.copytruncate = copytruncate
        self._offset_file = offset_file or "%s%s" % ("./../data/", "offset")
        self._offset_file_inode = 0
        self._offset = 0
        self._fh = None
        self._rotated_logfile = None
        self.filename=self._determine_filename()

        # if offset file exists and non-empty, open and parse it
        if exists(self._offset_file) and getsize(self._offset_file):
            offset_fh = open(self._offset_file, "r")
            (self._offset_file_inode, self._offset) = \
                [int(line.strip()) for line in offset_fh]
            offset_fh.close()
            # the file might have been rotated
            if self._offset_file_inode != stat(self.filename).st_ino:
                self._rotated_logfile = self._determine_rotated_logfile()
                if self._rotated_logfile and exists(self._rotated_logfile):
                    if stat(self._rotated_logfile).st_ino != self._offset_file_inode:
                          #can't  get the right rotated file, just ignore
                        self._rotated_logfile=None
                        self._offset = 0
                        
            # truncate happeded
            if self._offset_file_inode == stat(self.filename).st_ino and stat(self.filename).st_size < self._offset:
                if self.copytruncate:
                    self._offset = 0
                else:
                    print (
                        "[pygtail] [WARN] file size of %s shrank, and copytruncate support is "
                        "disabled (expected at least %d bytes, was %d bytes).\n" %
                        (self.filename, self._offset, stat(self.filename).st_size))
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
	    filebandle = self._filehandle()
            line = next(self._filehandle())
        except StopIteration:
            # we've reached the end of the file; if we're processing the
            # rotated log file, we can continue with the actual file; otherwise
            # update the offset file
            if self._rotated_logfile:
                self._rotated_logfile = None
                self._fh.close()
                self._offset = 0
                # open up current logfile and continue
                try:
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
            filename = self._rotated_logfile or self.filename
            self._fh = open(filename, "r")
            self._fh.seek(self._offset)

        return self._fh

    def _update_offset_file(self):
        """
        Update the offset file with the current inode and offset.
        """
        offset = self._filehandle().tell()
        inode = stat(self.filename).st_ino
        fh = open(self._offset_file, "w")
        fh.write("%s\n%s\n" % (inode, offset))
        fh.close()
    def _determine_filename(self):
        """
        Return the second newest filename
        """
        FileList=self._get_filelist_sortby_mtime()
        if len(FileList)<1:
            return None
        else:
            return FileList[-1]

    def _determine_rotated_logfile(self):
        """
        We suspect the logfile has been rotated, so try to guess what the
        rotated filename is, and return it.  Return the second newest filename
        """
        FileList=self._get_filelist_sortby_mtime()
        if len(FileList)<2:
            return None
        else:
            return FileList[-2]

    def _get_filelist_sortby_mtime(self):
        """
        Find the file list matched by the filename pattern and sort them by mtime.
        """
        FileList = []
        FileList_withtime = []
        for root, subFolders, files in os.walk(self.filepath):
            for f in files:
                if re.search(self.filename_pattern,f):
                    file_path=os.path.join(root, f)
                    mtime=time.localtime(os.stat(file_path)[8])
                    file_tuple=mtime, file_path
                    FileList_withtime.append(file_tuple)

        FileList_withtime.sort()
        for item in FileList_withtime:
            FileList.append(item[1])
        return FileList

__version__ = '0.4.0'



