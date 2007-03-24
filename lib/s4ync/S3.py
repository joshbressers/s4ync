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

import boto
import boto.s3
import boto.s3.connection
import config
import os.path
import re
import file

class S3:

    def __init__(self, bucket = None):

        self.configuration = config.get_config()

        self.access_key = self.configuration.access_key
        self.secret_key = self.configuration.secret_key
        self.bucket = bucket

        self.__connect()
        self.__set_bucket()

    def __connect(self):
        "Open the S3 connection"

        self.conn = boto.s3.connection.S3Connection(self.access_key,
            self.secret_key)

    def __set_bucket(self):
        "Set the bucket we want to use"

        if self.bucket is None:
            # A bucket of None means we don't want to open a bucket
            return

        self.bucket = try_again(self.conn.get_bucket, self.bucket)

    def create_bucket(self, bucket):
        "Create a new bucket"

        self.bucket = try_again(self.conn.create_bucket, bucket)

    def delete_bucket(self):
        "Delete the current bucket"

        files = self.get_s3_filelist()
        while(files):
            for i in files:
                self.delete_s3_file(i)
            files = self.get_s3_filelist()

        try_again(self.conn.delete_bucket, self.bucket)
        self.bucket = None

    def sync_file_to_s3(self, file, base):
        "Sync a single file to S3"

        filepath = re.sub(base, '', file.name)

        key = try_again(self.bucket.lookup, filepath)
        if key is None:
            # This file doesn't exist
            key = try_again(self.bucket.new_key)
            key.key = filepath
        else:
            # The file exists, let's see if it needs to be updated
            size = key.get_metadata('size')
            mtime = key.get_metadata('mtime')
            if str(file.size) == size and str(file.mtime) == mtime:
                # Nothing has changed, no need to update this file
                if self.configuration.verbose > 1:
                    print file.name + " ... Skipping"
                return

        key.set_metadata('size', str(file.size))
        key.set_metadata('mtime', str(file.mtime))

        if file.link:
            key.set_metadata('symlink', str(file.link))

        if self.configuration.verbose:
            print file.name

        if file.link:
            try_again(key.set_contents_from_string, "")
        else:
            file.encrypt()
            try_again(key.set_contents_from_file, file)
            file.close()

    def sync_filelist_to_s3(self, filelist, base):
        "Sync an array of files to S3"

        s3_filelist = self.get_s3_filelist()
        local_filelist = {}

        for i in filelist:
            local_filelist[re.sub(base, '', i.name)] = 1
            self.sync_file_to_s3(i, base)

        # Delete files no longer tracked on the local filesystem
        # XXX: Use a set here
        if self.configuration.delete:
            for i in s3_filelist:
                if not local_filelist.has_key(i):
                    self.delete_s3_file(i)

    def sync_s3_to_file(self, s3_filename, local_file):
        "Sync from S3 to a local file"

        key = try_again(self.bucket.lookup, s3_filename)
        if key is None:
            # This file doesn't exist
            raise Exception, "Key doesn't exist"

        directory = os.path.dirname(local_file)
        if not os.path.exists(directory):
            os.makedirs(directory)
        file_object = file.File(local_file)

        size = key.get_metadata('size')
        mtime = key.get_metadata('mtime')
        if str(file_object.size) == size and str(file_object.mtime) == mtime:
            # Nothing has changed, no need to update this file
            return

        if self.configuration.verbose:
            print file_object.name

        if key.metadata.has_key('symlink'):
            file_object.link = key.get_metadata('symlink')
            file_object.get_fp()
        else:
            try_again(key.get_contents_to_file, file_object)
            file_object.decrypt()
            file_object.set_mtime(int(key.get_metadata('mtime')))
            file_object.close()

    def sync_s3_filelist(self, source, destination):
        "Write the s3 files into a local directory"

        filelist = self.get_s3_filelist(source)
        for file in filelist:
            file_path = destination
            file_path = os.path.join(destination, re.sub(r'^[/.]', '', file))
            self.sync_s3_to_file(file, file_path)

    def delete_s3_file(self, filename):
        "Delete a file from S3"

        if self.configuration.verbose:
            print "Deleting " + filename
        try_again(self.bucket.delete_key, filename)

    def get_buckets(self):
        "Return a list of all buckets"

        names = []
        buckets = self.conn.get_all_buckets()

        for i in buckets:
            names.append(i.name)

        return names

    def get_s3_filelist(self, prefix=''):
        "Return an array of filenames"

        filenames = []

        keys = self.get_s3_keys(prefix)

        for i in keys:
            filenames.append(i.key)

        return filenames

    def get_s3_keys(self, prefix = ''):
        "Return an array of S3 key objects"

        keys = try_again(self.bucket.get_all_keys, prefix=prefix)
        if len(keys) > 0:
            while True:
                last = keys[-1]
                rs = try_again(self.bucket.get_all_keys, marker=last.key,
                    prefix=prefix)
                if len(rs) < 1:
                    break
                keys._results.extend(rs._results)

        return keys

def try_again(function, *args, **keywords):
    "Try to execute a function a number of times"

    times = 10
    while(True):
        try:
            return apply(function, args, keywords)
        except KeyboardInterrupt, e:
            raise e
        except Exception, e:
            times = times - 1
            if times == 0:
                raise e
