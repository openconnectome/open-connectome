#D Copyright 2014 NeuroData (http://neurodata.io)
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
from contextlib import closing

sys.path += [os.path.abspath('../../django')]
import OCP.settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'OCP.settings'
from django.conf import settings

import ocpcaproj
import ocpcadb
import zindex
import restargs
from ocpcaerror import OCPCAError

# RBTDOD This doesn't work because of channel interfaces to cutout.  Try and reimplement with cassandra branch.

"""Extract all points above a threshhold for a specific channel and resolution."""

class ThreshholdStack:

  def __init__(self, token, cutout):
    """Load the annotation database and project"""

    projdb = ocpcaproj.OCPCAProjectsDB()
    self.proj = projdb.loadProject ( token )

    # Bind the annotation database
    self.annoDB = ocpcadb.OCPCADB ( self.proj )

    # Perform argument processing
    try:
      args = restargs.BrainRestArgs ();
      args.cutoutArgs ( cutout+"/", self.proj.datasetcfg )
    except restargs.RESTArgsError, e:
      raise OCPCAError(e.value)
      
    # Extract the relevant values
    self.corner = args.getCorner()
    self.dim = args.getDim() 


  def countLocations ( self, channel, resolution, threshhold ):
    """Build the hierarchy of annotations"""
     
    # Get the source database sizes
    [ximagesz, yimagesz] = self.proj.datasetcfg.imagesz [ resolution ]
    [xcubedim, ycubedim, zcubedim] = self.proj.datasetcfg.cubedim [ resolution ]

    # Get the slices
    [ startslice, endslice ] = self.corner[2],self.corner[2]+self.dim[2]
    slices = endslice - startslice + 1

    # Set the limits for iteration on the number of cubes in each dimension
    xstart = self.corner[0] / xcubedim
    ystart = self.corner[1] / ycubedim
    xend = (self.corner[0]+self.dim[0]-1) / xcubedim + 1
    yend = (self.corner[1]+self.dim[1]-1) / ycubedim + 1

    #  Round up the zlimit to the next larger
    zstart = startslice/zcubedim
    zend = (endslice+1-1)/zcubedim+1

    count = 0

    for z in (zstart,zend):
      for y in (ystart,yend):
        for x in (xstart,xend):

          mortonidx = zindex.XYZMorton((x,y,z)) 

          print "Working on batch %s at %s" % (mortonidx, zindex.MortonXYZ(mortonidx))
          
          #  get the cube
          import pdb; pdb.set_trace() 
          cube = self.annoDB.getCube ( mortonidx, resolution, channel );

          # Flag to indicate no data.  No update query
          somedata = False

          # get the first cube
          [key,cube]  = self.annoDB.getNextCube ()

          #  if there's a cube, there's data
          if key != None:
            somedata = True

          xyz = (x,y,z)

          # Compute the offset in the output data cube 
          #  we are placing 4x4x4 input blocks into a 2x2x4 cube 
          offset = [xyz[0]*xcubedim, xyz[1]*ycubedim, xyz[2]*zcubedim]

          nzlocs = np.nonzero ( cube.data > threshhold )

          count += len(nzlocs[1]) 
             
    return countt

def main():

  parser = argparse.ArgumentParser(description='Find all points above a threshhold for a specific channel and resolution')
  parser.add_argument('token', action="store", help='Token for the annotation project.')
  parser.add_argument('channel', action="store", help='Channel.')
  parser.add_argument('resolution', action="store", type=int, help='Resolution')
  parser.add_argument('threshhold', action="store", type=int, help='Minimum value')
  parser.add_argument('cutout', action="store", help="Data regions in format r/x1,x2/y1,y2/z1,z2")
  
  result = parser.parse_args()

  # Create the annotation stack
  tholder = ThreshholdStack ( result.token, result.cutout )

  # Iterate over the database creating the hierarchy
  count = tholder.countLocations ( result.channel, result.resolution, result.threshhold )
  
  print "Found {} locations greater than {} in {} voxels at {}".format(count,threshhold,dim[0]*dim[1]*dim[2], result.cutout)

if __name__ == "__main__":
  main()

