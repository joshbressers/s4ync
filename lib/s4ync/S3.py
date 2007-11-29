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
import time

class S3:

    def __init__(self, bucket = None):

        self.configuration = config.get_config()

        self.access_key = self.configuration.access_key
        self.secret_key = self.configuration.secret_key

        self.__connect()

        if bucket:
            self.bucket = Bucket(self.conn, bucket)
        else:
            self.bucket = None

    def __connect(self):
        "Open the S3 connection"

        self.conn = boto.s3.connection.S3Connection(self.access_key,
            self.secret_key)

    def create_bucket(self, bucket):
        "Create a new bucket"

        s3_bucket = try_again(self.conn.create_bucket, bucket)
        self.bucket = Bucket(self.conn, bucket)

    def delete_bucket(self):
        "Delete the current bucket"

        self.bucket.delete()
        self.bucket = None

    def sync_file_to_s3(self, file, base):
        "Sync a single file to S3"

        filepath = re.sub(base, '', file.name)
        key = self.bucket.get_key(filepath, True)

        # The file exists, let's see if it needs to be updated
        if file.size == key.size and file.mtime == key.mtime:
            # Nothing has changed, no need to update this file
            if self.configuration.verbose > 1:
                print file.name + " ... Skipping"
            return

        key.size = file.size
        key.mtime = file.mtime

        if file.link:
            key.link = str(file.link)

        if self.configuration.verbose:
            print file.name

        key.upload(file)
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
                if i is None:
                    continue
                if not local_filelist.has_key(i):
                    self.delete_s3_file(i)

    def sync_s3_to_file(self, s3_filename, local_file):
        "Sync from S3 to a local file"

        key = self.bucket.get_key(s3_filename)
        if key is None:
            # This file doesn't exist
            raise Exception, "Key doesn't exist"

        directory = os.path.dirname(local_file)
        if not os.path.exists(directory):
            os.makedirs(directory)
        file_object = file.File(local_file)

        if file_object.size == key.size and \
                file_object.mtime == key.mtime:
            # Nothing has changed, no need to update this file
            return

        if self.configuration.verbose:
            print file_object.name

        if key.link:
            file_object.link = key.link;
            file_object.get_fp()
        else:
            key.download(file_object)
            file_object.decrypt()
            file_object.set_mtime(key.mtime)
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
        key = self.bucket.get_key(filename)
        key.delete()

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
        keys = self.bucket.get_all_keys(prefix)
        for i in keys:
            filenames.append(i.filename)

        return filenames

class Bucket:

    def __init__(self, connection, name):
        self.connection = connection
        self.name = name
        self.real_bucket = try_again(self.connection.get_bucket, self.name)

    def get_all_keys(self, prefix=''):
        "Return a list of all key objects"

        keys = try_again(self.real_bucket.list, prefix=prefix)

        return keys

    def get_key(self, filename, create=False):
        "Return a single key"

        key = try_again(self.real_bucket.lookup, filename)

        if key is None and create:
            # This file doesn't exist, let's create it
            key = try_again(self.real_bucket.new_key)
            key.key = filename

        return Key(self.real_bucket, key)

    def delete(self):
        "Delete this bucket and all its contents from S3"

        files = self.get_all_keys()
        for i in files:
            i.delete()
        try_again(self.connection.delete_bucket, self.real_bucket)

class Key:

    def __init__(self, bucket, key):
        self.bucket = bucket
        self.real_key = key
        self.link = False

        self.filename = key.key

        if key.metadata.has_key('size'):
            self.size = int(key.get_metadata('size'))
        else:
            self.size = 0
        if key.metadata.has_key('mtime'):
            self.mtime = int(key.get_metadata('mtime'))
        else:
            self.mtime = 0

        if key.metadata.has_key('symlink'):
            self.link = key.get_metadata('symlink')

    def upload(self, file):
        "Sync the contents to S3"

        self.real_key.set_metadata('size', str(self.size))
        self.real_key.set_metadata('mtime', str(self.mtime))

        if self.link:
            self.real_key.set_metadata('symlink', self.link)

            try_again(self.real_key.set_contents_from_string, "")
        else:
            try_again(self.real_key.set_contents_from_file, file)

    def download(self, file):
        "Write the S3 contents into a file object"
        try_again(self.real_key.get_contents_to_file, file)

    def delete(self):
        "Delete the key from S3"

        try_again(self.bucket.delete_key, self.real_key.key)

def try_again(function, *args, **keywords):
    "Try to execute a function a number of times"

    times = 10
    while(True):
        try:
            return apply(function, args, keywords)
        except KeyboardInterrupt, e:
            raise e
        except Exception, e:
            time.sleep(10)
            times = times - 1
            if times == 0:
                raise e
