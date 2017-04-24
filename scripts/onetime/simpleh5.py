# Copyright 2014 NeuroData (http://neurodata.io)
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import sys
import os
import numpy as np
import h5py
import tempfile
import urllib, urllib2
import cStringIO
from PIL import Image
import zlib
import MySQLdb
from cassandra.cluster import Cluster

sys.path += [os.path.abspath('../django')]
import OCP.settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'OCP.settings'
from django.conf import settings

import ocpcaproj
import ocpcadb
import zindex

"""Construct an image hierarchy up from a given resolution"""

def main():

  h5in = h5py.File ( "/tmp/test.h5" ) 
  print h5in.keys()
  fin = open ( "/tmp/test.h5", 'r' )

  import pdb; pdb.set_trace()

  tmpfile = tempfile.NamedTemporaryFile ()
  tmpfile.write ( fin.read() )
  tmpfile.seek ( 0 ) 
  h52 = h5py.File ( tmpfile.name, 'r' )

  h52.keys()

if __name__ == "__main__":
  main()

