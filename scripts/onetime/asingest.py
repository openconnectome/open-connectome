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
from PIL import Image
import zlib
import MySQLdb
import aerospike
import tempfile
import h5py

sys.path += [os.path.abspath('../django')]
import OCP.settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'OCP.settings'
from django.conf import settings

import ocpcaproj
import ocpcadb
import zindex

"""Construct an image hierarchy up from a given resolution"""

def main():

  parser = argparse.ArgumentParser(description='Build an aeropsike DB from mysql data.')
  parser.add_argument('token', action="store", help='Token for the project.')
  parser.add_argument('resolution', action="store", type=int)
  
  result = parser.parse_args()

  # as database
  ascfg = { 'hosts': [ ('127.0.0.1', 3000) ] }
  ascli = aerospike.client(ascfg).connect()

  # mysql database
  projdb = ocpcaproj.OCPCAProjectsDB()
  proj = projdb.loadProject ( result.token )

  # Bind the annotation database
  imgDB = ocpcadb.OCPCADB ( proj )

  # Get the source database sizes
  [ximagesz, yimagesz] = proj.datasetcfg.imagesz [ result.resolution ]
  [xcubedim, ycubedim, zcubedim] = cubedim = proj.datasetcfg.cubedim [ result.resolution ]

  # Get the slices
  [ startslice, endslice ] = proj.datasetcfg.slicerange
  slices = endslice - startslice + 1

  # Set the limits for iteration on the number of cubes in each dimension
  # RBTODO These limits may be wrong for even (see channelingest.py)
  xlimit = ximagesz / xcubedim
  ylimit = yimagesz / ycubedim
  #  Round up the zlimit to the next larger
  zlimit = (((slices-1)/zcubedim+1)*zcubedim)/zcubedim 

  cursor = imgDB.conn.cursor()

  for z in range(zlimit):
    for y in range(ylimit):
      for x in range(xlimit):

        mysqlcube = imgDB.cutout ( [ x*xcubedim, y*ycubedim, z*zcubedim ], cubedim, result.resolution )
        zidx = zindex.XYZMorton ( [x,y,z] )

        tmpfile = tempfile.NamedTemporaryFile ()
        h5tocass = h5py.File ( tmpfile.name ) 
        h5tocass.create_dataset ( "cuboid", tuple(mysqlcube.data.shape), mysqlcube.data.dtype,
                                 compression='gzip',  data=mysqlcube.data )
        h5tocass.close()
        tmpfile.seek(0)

        askey = ("ocp",str(result.token)+":"+str(result.resolution),str(zidx))

        print askey
        ascli.put ( askey, { 'cuboid' : tmpfile.read().encode('hex') } )

        try:
          ascli.get ( askey )
        except:
          print "Except"







if __name__ == "__main__":
  main()

