# Copyright 2014 Open Connectome Project (http://openconnecto.me)
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

import os
import sys
import argparse
import h5py
import urllib2
import tempfile
import numpy as np
import cStringIO
import zlib

def postH5 ( host, token, channel="Grayscale" ):
  """ Post a HDF5 File """
  
  # Create a temp file
  tmpfile = tempfile.NamedTemporaryFile()

  # Your data goes into imageData
  # IMPORTANT : Do ensure that the posted data numpy type matches your dataset numpy type
  # Image 8 bit / Channel 8 bit = np.uint8
  # Image 16 bit / Channel 16 bit = np.uint.16
  
  # Here I create a 10x10x2 cube of Image data
  imageData = np.uint16(range(0,400)).reshape(2,2,10,10)

  # Create the compressed cube
  fileobj = cStringIO.StringIO ()
  np.save ( fileobj, imageData )
  cdz = zlib.compress (fileobj.getvalue())
     
  # Package the object as a Web readable file handle
  fileobj = cStringIO.StringIO ( cdz )
  fileobj.seek(0)

  # Sample url
  # url = http://<hostname>/ocpca/<token>/hdf5/1/<x1>,<x2>/<y1>,<y2>/<z1>,<z2>/
  # IMPORTANT : You can only post to a project which is NOT read-only. Do ensure that when you create a token, it is not set to read-only.

  # Here I post the 10x10x2 cube to of data to 3000,3010/4000,4010/500,502 volume
  url = 'http://{}/ocpca/{}/npz/Grayscale,Blue/1/3000,3010/4000,4010/500,502/'.format( host, token )
  
  # Opening the url and verifying if it connects or else exit the program
  try:
    req = urllib2.Request ( url, fileobj.read() )
    response = urllib2.urlopen(req)
    print url 
  except urllib2.URLError, e:
    print "Failed URL {}".format(url)
    print "Error {}".format(e)


def main():
  
  parser = argparse.ArgumentParser(description="Run the Load Test script")
  parser.add_argument('host', action="store", help='HostName')
  parser.add_argument('token', action="store", help='Project Token')
 
  global result

  result = parser.parse_args()
  postH5 ( result.host, result.token )

if __name__ == "__main__":
  main()
