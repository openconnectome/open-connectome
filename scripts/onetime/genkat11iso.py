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

import numpy as np
import urllib, urllib2
import cStringIO
import sys
import zlib
from PIL import Image
import zindex
import MySQLdb

#_startslice = 1089 # 15*64+1
#_endslice = 1537  # 24*64+1
_startslice = 1793 # 15*64+1
#_startslice = 129 # 15*64+1
_endslice = 1850  # 24*64+1

conn = MySQLdb.connect (host = 'localhost',
                            user = 'brain',
                            passwd = '88brain88',
                            db = 'kat11isodata')

cursor = conn.cursor ()

# It's a 64^3 cube
for z in range (_startslice, _endslice, 64):
  for y in range (0,((2579-1)/64+1)*64, 64):
    conn.commit()
    for x in range (0,((2150-1)/64+1)*64, 64):

      zmax = min(z+64,1850+1)

      xmax = min((x+64)*5,10752)
      ymax = min((y+64)*5,13312)

      # Cutout the data from the kasthuri11 data set at resolution 1
      url = "http://rio.cs.jhu.edu/EM/emca/kasthuri11/npz/1/%s,%s/%s,%s/%s,%s/" % (x*5, xmax, y*5, ymax, z, zmax)
      
      print url

      # Get cube in question
      try:
        f = urllib2.urlopen ( url )
      except urllib2.URLError, e:
        print "Failed %s.  Exception %s." % (url,e)

      zdatain = f.read ()

      # get the data out of the compressed blob
      instr = zlib.decompress ( zdatain[:] )
      infobj = cStringIO.StringIO ( instr )
      cube = np.load ( infobj )
      infobj.close()


      # Put the cutout into the array
      olddata = np.zeros( [ 64,320,320 ], dtype=np.uint8 )
      olddata[0:cube.shape[0],0:cube.shape[1],0:cube.shape[2]] = cube

      # target cube
      newdata = np.zeros ( [64, 64, 64], dtype=np.uint8 )

      # Rescale the data to be one fifth the size 
      for s in range(64):

        # Convert each slice to an image
        simage = Image.frombuffer ( 'L', (320,320), olddata[s,:,:].flatten(), 'raw', 'L', 0, 1 )

        # Resize the image
        newimage = simage.resize ( [64, 64] )

        # Put to a new cube
        newdata[s,:,:] = np.asarray ( newimage )

      # Compress the data
      outfobj = cStringIO.StringIO ()
      np.save ( outfobj, newdata )
      zdataout = zlib.compress (outfobj.getvalue())
      outfobj.close()

      key = zindex.XYZMorton ( [x/64,y/64,z/64] )

      # Put in the database
      sql = "DELETE FROM res0 where zindex=%s" % key
      print sql
      cursor.execute ( sql )
      sql = "INSERT INTO res0 (zindex, cube) VALUES (%s, %s)"
      try:
        cursor.execute ( sql, (key,zdataout))
      except MySQLdb.Error, e:
        print "Failed insert %d: %s. sql=%s" % (e.args[0], e.args[1], sql)


