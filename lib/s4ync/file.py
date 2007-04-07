#!/usr/bin/env python

# Copyright 2007 Josh Bressers

# This file is part of s4ync.
#
# s4ync is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# any later version.
#
# s4ync is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Foobar; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301 USA

import os
import os.path
import S3
import config
import StringIO

class File:
    "Class to describe a file object"

    def __init__(self, filepath):

        self.config = config.get_config()
        self.fp = None
        self.name = filepath
        self.link = False
        if os.path.islink(self.name):
            self.link = os.readlink(self.name)
            os.lstat(filepath)
            self.mtime = os.lstat(filepath)[8]
            self.size = os.lstat(filepath)[6]
        elif os.path.exists(self.name):
            self.mtime = os.path.getmtime(filepath)
            self.size = os.path.getsize(filepath)
        else:
            self.mtime = -1
            self.size = -1

    def __del__(self):

        self.close()

    def get_fp(self):
        "Return the file pointer"

        if self.fp is None:
            if os.path.exists(self.name):
                if self.link:
                    self.fp = StringIO.StringIO()
                else:
                    self.fp = open(self.name, 'r+b')
            else:
                if self.link:
                    self.fp = StringIO.StringIO()
                    os.symlink(self.link, self.name)
                else:
                    self.fp = open(self.name, 'w+b')

        return self.fp

    def close(self):
        "Clean up the open file"

        if self.fp is None:
            return
        self.fp.close()
        self.fp = None

    def read(self, size = -1):

        fp = self.get_fp()
        return fp.read(size)

    def seek(self, seek_size):

        fp = self.get_fp()
        return fp.seek(seek_size)

    def tell(self):

        fp = self.get_fp()
        return fp.tell()

    def write(self, data):

        # We know if we're writing, it's encrypted data we're getting

        fp = self.get_fp()
        return fp.write(data)

    def encrypt(self):
        "Stream the data through an encryptor"

        # XXX: This looks horrible, We can fix it later

        (stdin, stdout) = os.popen2(self.config.encrypt_cmd % \
            (self.config.encrypt, self.name))

        new_fp = StringIO.StringIO()
        new_fp.write(stdout.read())
        stdout.close()
        new_fp.seek(0)
        self.fp = new_fp

    def decrypt(self):
        "Stream the data through a decryptor"

        fp = self.get_fp()
        fp.seek(0)

        (stdin, stdout) = os.popen2(self.config.decrypt_cmd % self.name)

        fp.seek(0)
        fp.write(stdout.read())
        fp.truncate()
        fp.seek(0)

    def set_mtime(self, mtime):
        "Set the file mtime"

        os.utime(self.name, (mtime, mtime))

def get_files(path):
    "Walk the directory tree, building our file list along the way"

    files = []

    os.path.walk(path, __walk_callback, files)

    return files

def sync_files(destination, source):
    "Sync the filelist with S3"

    if os.path.isdir(source) and source[-1] != os.path.sep:
        source = source + os.path.sep

    if destination[0:3] == 's3:':
        # This is a push to s3
        file_list = get_files(source)
        connection = S3.S3(destination[3:])
        connection.sync_filelist_to_s3(file_list, source)
    elif source[0:3] == 's3:':
        # We assume the user wants to pull from s3
        sources = source[3:].split(':', 1)
        bucket = sources[0]
        if len(sources) > 1:
            source = sources[1]
        else:
            source = ''
        connection = S3.S3(bucket)
        connection.sync_s3_filelist(source, destination)
    else:
        # This is probably an error
        raise Exception, "unknown source or destination error"

def __walk_callback(saved_files, path, names):
    "Build up our file list"

    for file in names:
        current_file = os.path.join(path, file)
        if os.path.islink(current_file):
            del(names[names.index(file)])
            saved_files.append(File(current_file))
        elif not os.path.isdir(current_file):
            saved_files.append(File(current_file))
