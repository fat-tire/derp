#!/usr/bin/env python
#
# DERP- Device Environment Replacement Program
# Copyright (C) 2013 fattire <f4ttire@gmail.com> (not the beer!)
# 
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; version 2
# of the License.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

from distutils.core import setup

import platform

# For OS X

if platform.system() == "Darwin":
      import py2app
      import shutil
      shutil.copyfile("bin/derp","bin/derp.py")
      options = dict(
          py2app=dict(
              compressed=1,
              optimize=2,
              argv_emulation=True,
              iconfile="res/drawables/derp.icns",
              packages=['src'],
              site_packages=True,
              resources=['LICENSE', 'README', "src", "res", "scripts"],
              plist=dict(
                  CFBundleName                  = "Derp",
                  CFBundleTypeExtensions        = ["derp"],
                  CFBundleGetInfoString         = "Derp",
                  CFBundleTypeRole              = "Viewer",
                  CFBundleTypeName              = "Derp Script",
                  CFBundletypeIconFile          = "derp.icns",
              ),
          ),
      )
      osOptions=dict(setup_requires = ['py2app'], app=['bin/derp.py'])
else:
      options  = {}
      osOptions = {}

dataFiles = [(".", ["derp.desktop"]), \
             (".", ["derp-derp.xml"])]

setup(name="derp",
      author="fattire",
      author_email="f4ttire@gmail.com",
      url="n/a",
      version="0.001",
      packages=["src"],
      package_data = {"src": ["../scripts/*/*/*", "../res/*/*", "../README", "../LICENSE"]},
      scripts=["bin/derp"],
      options=options,
      data_files = dataFiles,
      **osOptions)
