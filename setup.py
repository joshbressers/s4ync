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

from distutils.core import setup

setup(  name='s4ync',
        version='0.0.1',
        description='Amazon s3 sync tool',
        author='Josh Bressers',
        author_email='josh@bress.net',
        url='http://www.bress.net',
        package_dir = {"": "lib"},
        packages=['s4ync'],
        scripts=['bin/s4ync', 'bin/s3tool'],
        data_files=[('share/man/man1', ['doc/s4ync.1', 'doc/s3tool.1'])]
)
