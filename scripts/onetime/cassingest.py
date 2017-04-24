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
#from cassandra.cluster import Cluster

sys.path += [os.path.abspath('../django')]
import OCP.settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'OCP.settings'
from django.conf import settings

import ocpcaproj
import ocpcadb
import zindex

"""Build a Cassandra DB from an existing MySQL DB"""

def main():

  parser = argparse.ArgumentParser(description='Build an aeropsike DB from mysql data.')
  parser.add_argument('intoken', action="store", help='Token for the project.')
  parser.add_argument('outtoken', action="store", help='Token for the project.')
  parser.add_argument('resolution', action="store", type=int)
  
  result = parser.parse_args()

  # cassandra database
  outprojdb = ocpcaproj.OCPCAProjectsDB()
  outproj = outprojdb.loadProject ( result.outtoken )

  # mysql database
  inprojdb = ocpcaproj.OCPCAProjectsDB()
  inproj = inprojdb.loadProject ( result.intoken )

  # Bind the databases
  inDB = ocpcadb.OCPCADB ( inproj )
  outDB = ocpcadb.OCPCADB ( outproj )

  # Get the source database sizes
  [ximagesz, yimagesz] = inproj.datasetcfg.imagesz [ result.resolution ]
  [xcubedim, ycubedim, zcubedim] = cubedim = inproj.datasetcfg.cubedim [ result.resolution ]

  # Get the slices
  [ startslice, endslice ] = inproj.datasetcfg.slicerange
  slices = endslice - startslice + 1

  # Set the limits for iteration on the number of cubes in each dimension
  # and the limits of iteration
  xlimit = (ximagesz-1) / xcubedim + 1
  ylimit = (yimagesz-1) / ycubedim + 1
  #  Round up the zlimit to the next larger
  zlimit = (((slices-1)/zcubedim+1)*zcubedim)/zcubedim 


  for z in range(zlimit):
    for y in range(ylimit):
      for x in range(xlimit):

        zidx = zindex.XYZMorton ( [x,y,z] )
        outDB.putCube ( zidx, result.resolution, inDB.getCube ( zidx, result.resolution )) 
        print "Ingesting {}".format(zidx)


if __name__ == "__main__":
  main()

