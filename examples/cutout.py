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
import numpy as np
import urllib, urllib2
import cStringIO
import sys

import zlib

def main():

  parser = argparse.ArgumentParser(description='Cutout a small region of the database and print the contents')
  parser.add_argument('baseurl', action="store" )
  parser.add_argument('token', action="store" )
  parser.add_argument('cutout', action="store", help='Cutout arguments of the form resolution/x1,x2/y1,y2/z1,z2.' )

  result = parser.parse_args()

  url = 'http://{}/sd/{}/npz/{}/'.format( result.baseurl, result.token, result.cutout )

  # Get cube in question
  try:
    f = urllib2.urlopen ( url )
  except urllib2.URLError, e:
    print "Failed {}. Exception {}.".format(url, e) 
    sys.exit(-1)

  zdata = f.read ()

  # get the data out of the compressed blob
  pagestr = zlib.decompress ( zdata[:] )
  pagefobj = cStringIO.StringIO ( pagestr )
  cube = np.load ( pagefobj )

  print cube

  cube.tostring()

if __name__ == "__main__":
  main()
