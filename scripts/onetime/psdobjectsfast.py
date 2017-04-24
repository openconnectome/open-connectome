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
import annotation
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
   

  def inrange ( self, pt, corner, dim ):
    """Helper function.  Point in target area?"""

    return pt[0] >= corner[0] and pt[1] >= corner[1] and pt[2] >= corner[2] and pt[0] < corner[0]+dim[0] and pt[1] < corner[1]+dim[1] and pt[2] < corner[2]+dim[2]


  def process ( self, resolution, startid ):
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

    stride = 16

    # iterate over all cubes
    #for z in range(startslice,endslice,zcubedim):
    for z in range(startslice+16,endslice,zcubedim):
      for y in range(0,ylimit,stride):
        for x in range(0,xlimit,stride):

          # cutout a cube +/- 256 pixels in x and y +/- 8 pixels in z
          xlow = max ( 0, x*xcubedim-256 )
          ylow = max ( 0, y*ycubedim-256 )
          zlow = max ( 0, z-8 )
          xhigh = min ( ximagesz, (x+stride)*xcubedim+256 )
          yhigh = min ( yimagesz, (y+stride)*ycubedim+256 )
          zhigh = min ( endslice-1, z+zcubedim+8 )

          # perform the cutout
          cube = self.annoDB.cutout ( [xlow,ylow,zlow], [xhigh-xlow, yhigh-ylow, zhigh-zlow], resolution )
         
          nzoffs = np.nonzero(cube.data)
          # no elements?
          if len(nzoffs[0])==0:
            print "No data at {}".format((x,y,z))
            continue

          # Points are in xyz, voxels in zyx
          points = zip(nzoffs[2]+xlow,nzoffs[1]+ylow,nzoffs[0]+zlow+startslice)

          # for all points in the interior, let's grow the region
          while len(points) != 0:

            #grab the first psd
            seed = None
            for pt in points:
              if self.inrange ( pt, (x*xcubedim, y*ycubedim, z), (stride*xcubedim, stride*ycubedim, zcubedim) ):
                # only points that are not relabeled
                if (cube.data[pt[2]-zlow-startslice,pt[1]-ylow,pt[0]-xlow] < 100 ):
                  seed = pt
                  break

            if seed == None:
              break

            # We'll assume that there is non-intersectin bounding box around a PSD of at least 16 pixels in x y and 2 in z
            bbxlow = bbxhigh = seed[0]
            bbylow = bbyhigh = seed[1]
            bbzlow = bbzhigh = seed[2]

            inpoints=[]
        
            # loop control variable.  terminate when no new points were added
            somepoints = True

            while somepoints:
              outpoints=[]
              somepoints=False
              for pt in points:

                # put points in or out of PSD
                if pt[0] < bbxlow - 8 or pt[0] > bbxhigh + 8 or pt[1] < bbylow - 8 or pt[1] > bbyhigh + 8 or pt[2] < bbzlow - 2 or pt[2] > bbzhigh + 2:
                  outpoints.append(pt)
                else: 
                  inpoints.append(pt)
                  # somepoints
                  somepoints = True
                  # update bounding box
                  bbxlow = min(bbxlow,pt[0])
                  bbxhigh = max(bbxhigh,pt[0])
                  bbylow = min(bbylow,pt[1])
                  bbyhigh = max(bbyhigh,pt[1])
                  bbzlow = min(bbzlow,pt[2])
                  bbzhigh = max(bbzhigh,pt[2])

              points = outpoints              

            print "Found PSD id {} of length {}".format(startid,len(inpoints))

            # annotate the new object
            nppoints = np.array ( inpoints, dtype=np.uint32 )
            self.annoDB.annotate ( startid, resolution, nppoints )
            # create the RAMON object
            anno = annotation.Annotation()
            anno.annid = startid
            anno.kvpairs['vast_type']='PSD'
            anno.store ( self.annoDB )
            self.annoDB.commit()

            startid+=1

             


def main():

  parser = argparse.ArgumentParser(description='Break PSD labels into individual objects.')
  parser.add_argument('token', action="store", help='Token for the annotation project.')
  parser.add_argument('resolution', action="store", type=int, help='Resolution to process.')
  
  result = parser.parse_args()

  # Create the annotation stack
  psds = PSDObjectCreator ( result.token )

  # Iterate over the database creating the hierarchy
  psds.process ( result.resolution, 100000 )
  



if __name__ == "__main__":
  main()

