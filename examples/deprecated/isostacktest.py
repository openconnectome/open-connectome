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

import numpy as np
from PIL import Image
import urllib2
import zlib
import StringIO

#
#  makePNGs
#
#  First RESTful client program.
#  Download a cube and write out PNGs.
#

#
# Extract data from the cube and write out PNG files.
#
def cubeToPNGs ( nparray, prefix ):
  """Convert a numpy array into PNG files"""  

  # Note the data order is z then y then x
  zdim,ydim,xdim = nparray.shape

  # One file per xz plane
  for j in range(ydim):
    outimage = Image.frombuffer ( 'L', (xdim,zdim), nparray[:,j,:].flatten(), 'raw', 'L', 0, 1 ) 
    outimage.save ( prefix + str(j) + ".png", "PNG" )
    t = nparray[:,j,:]
    print (np.unique(t))


# Get cube in question
try:

#  url = "http://openconnecto.me/ocp/ocpca/kasthuri11/npz/5/100,300/200,448/1,400/neariso/"
#  url = "http://openconnecto.me/ocp/ocpca/kasthuri11/npz/5/100,700/200,500/1,500/neariso/"
#  url = "http://openconnecto.me:8000/ocpca/kasthuri11/npz/5/0,672/0,832/1,500/neariso/"
  url = "http://openconnecto.me/ocp/ocpca/kasthuri11/npz/5/0,672/0,832/1,500/neariso/"
#  url = "http://openconnecto.me/ocp/ocpca/bock11/npz/7/0,1058/0,936/2917,3013/neariso/"
#  url = "http://openconnecto.me:8000/ocpca/bock11/npz/7/0,1058/0,936/2917,3013/neariso/"
#  url = "http://localhost/ocp/ocpca/bock11/npz/0/18000,19000/18000,19000/2917,2920/neariso/"
#  url = "http://openconnecto.me/ocp/ocpca/bock11/npz/0/18000,19000/18000,19000/2917,2920/neariso/"
  f = urllib2.urlopen ( url )
except urllib2.URLError, e:
  print "Failed to open url ", url, e
  assert 0

zdata = f.read ()

# get the data out of the compressed blob
pagestr = zlib.decompress ( zdata[:] )
pagefobj = StringIO.StringIO ( pagestr )
cube = np.load ( pagefobj )

# Write out the cube as files
cubeToPNGs ( cube, "/tmp/npz" )
