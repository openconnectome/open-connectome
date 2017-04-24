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

sys.path += [os.path.abspath('../django')]
import OCP.settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'OCP.settings'
from django.conf import settings

import ocpcaproj
import ocpcadb
import zindex

from ocpca_cy import addData_cy

"""Construct an annotation hierarchy off of a completed annotation database."""

class PSDObjectCreator:
  """Stack of annotations."""

  def __init__(self, token):
    """Load the annotation database and project"""

    projdb = ocpcaproj.OCPCAProjectsDB()
    self.proj = projdb.loadProject ( token )

    # Bind the annotation database
    self.annoDB = ocpcadb.OCPCADB ( self.proj )
   

  def process ( self, resolution ):
    """Build the hierarchy of annotations"""

      # Get the source database sizes
    [ximagesz, yimagesz] = self.proj.datasetcfg.imagesz [ resolution ]
    [xcubedim, ycubedim, zcubedim] = self.proj.datasetcfg.cubedim [ resolution ]

    # Get the slices
    [ startslice, endslice ] = self.proj.datasetcfg.slicerange
    slices = endslice - startslice + 1

    # Set the limits for iteration on the number of cubes in each dimension
    xlimit = (ximagesz-1)/xcubedim+1
    ylimit = (yimagesz-1)/ycubedim+1
    #  Round up the zlimit to the next larger
    zlimit = (((slices-1)/zcubedim+1)*zcubedim)/zcubedim 

    stride = 1

    # iterate over all cubes
    for z in range(startslice,endslice,zcubedim):
      for y in range(0,ylimit,stride):
        for x in range(0,xlimit,stride):

          # start where there is data
          if x == 0 and y==0 and z==1:
            x=29; y=13; z=1

          # cutout a cube +/- 256 pixels in x and y +/- 8 pixels in z
          xlow = max ( 0, x*xcubedim-256 )
          ylow = max ( 0, y*ycubedim-256 )
          zlow = max ( 0, (z-startslice)*zcubedim-8 ) 
          xhigh = min ( ximagesz, (x+stride)*xcubedim+256 )
          yhigh = min ( yimagesz, (y+stride)*xcubedim+256 )
          zhigh = min ( endslice-1, (z+1)*zcubedim+8 )

          # perform the cutout
          cube = self.annoDB.cutout ( [xlow,ylow,zlow], [xhigh-xlow, yhigh-ylow, zhigh-zlow], resolution )
          print "Cutout {} {}".format([xlow,ylow,zlow], [xhigh-xlow, yhigh-ylow, zhigh-zlow])
         
          nzoffs = np.nonzero(cube.data)
          # no elements?
          if len(nzoffs[0])==0:
            print "No data at {}".format((x,y,z))
            continue

          points = zip(nzoffs[0],nzoffs[1],nzoffs[2])

          print "Len points {}".format(len(points))

          continue


          # for all points in the interior, let's grow the region
          while len(points) != 0:

            # working lists
            psdels=[]
            psd=[]
  
            #grab the first point
            firstindex = points.pop()

            #remove zero'ed elements
            while firstindex == (0,0,0) and len(points)!=0:
              firstindex = points.pop()

            if firstindex == (0,0,0):
              break

            psdels.append(firstindex)

            while(len(psdels) != 0):
              cur = psdels.pop()
              psd.append(cur)
              # grow the region
              for idx in range(len(points)-1,-1,-1):
                 
                if abs(points[idx][0]-cur[0] + points[idx][1]-cur[1] + points[idx][2]-cur[2]) == 1:
                  psdels.append(points[idx]) 
                  points[idx]=(0,0,0)

            print "PSD {}".format(psd)
             


def main():

  parser = argparse.ArgumentParser(description='Break PSD labels into individual objects.')
  parser.add_argument('token', action="store", help='Token for the annotation project.')
  parser.add_argument('resolution', action="store", type=int, help='Resolution to process.')
  
  result = parser.parse_args()

  # Create the annotation stack
  psds = PSDObjectCreator ( result.token )

  # Iterate over the database creating the hierarchy
  psds.process ( result.resolution )
  



if __name__ == "__main__":
  main()

