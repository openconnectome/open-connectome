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
import urllib, urllib2
import cStringIO
import zlib
import tempfile
import h5py

"""Construct an image hierarchy up from a given resolution"""

def main():

  url = 'http://neurodata.io/ocp/ca/kasthuri11/hdf5/3/1000,1500/1000,1500/1,100/' 
  # Get cube in question
  try:
    f = urllib2.urlopen ( url )
  except urllib2.URLError, e:
    print "Failed %s.  Exception %s." % (url,e)
    sys.exit(-1)

  # This feels like one more copy than is needed
  tmpfile = tempfile.NamedTemporaryFile ( )
  tmpfile.write ( f.read() )
  tmpfile.seek(0)
  h5f = h5py.File ( tmpfile.name, driver='core', backing_store=False )

  # RBTODO should be cutout
  othercube = np.array(h5f['cube'])

  # Here we have a Numpy array to upload.

  tmpfile = tempfile.NamedTemporaryFile ()
  h5w = h5py.File ( tmpfile.name ) 
  h5w.create_dataset ( "CUTOUT", tuple(othercube.shape), othercube.dtype,
                           compression='gzip',  data=othercube )
  h5w.close()
  tmpfile.seek(0)

  url = 'http://localhost:8000/ca/testupload/hdf5/0/0,500/0,500/0,99/' 
  # Get cube in question
  try:
    f = urllib2.urlopen ( url, tmpfile.read()  )
  except urllib2.URLError, e:
    print "Failed %s.  Exception %s." % (url,e)
    sys.exit(-1)

if __name__ == "__main__":
  main()

