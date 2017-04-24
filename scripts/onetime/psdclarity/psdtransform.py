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
from contextlib import closing
import cv2

sys.path += [os.path.abspath('../../django')]
import OCP.settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'OCP.settings'
from django.conf import settings

import ocpcaproj
import ndlib
import ocpcarest
import ocpcadb
import imagecube

"""Build a Cassandra DB from an existing MySQL DB"""

def main():

  parser = argparse.ArgumentParser(description='Build a transform DB for Kwame.')
  parser.add_argument('outtoken', action="store", help='Token for the Output project.')
  parser.add_argument('path', action="store", help='Path to data')
  parser.add_argument('resolution', action="store", type=int)
  
  result = parser.parse_args()

  with closing ( ocpcaproj.OCPCAProjectsDB() ) as outprojdb:
    outproj = outprojdb.loadProject (result.outtoken)

  with closing ( ocpcadb.OCPCADB(outproj) ) as outDB:   
    
    # Get the source database sizes
    (ximagesz, yimagesz) = outproj.datasetcfg.imagesz [ result.resolution ]
    (xcubedim, ycubedim, zcubedim) = cubedims = outproj.datasetcfg.cubedim [ result.resolution ]
    (startslice, endslice) = outproj.datasetcfg.slicerange
    batchsz = zcubedim

    # Get the slices
    slices = endslice - startslice + 1

    # Set the limits for iteration on the number of cubes in each dimension and the limits of iteration
    xlimit = (ximagesz-1) / xcubedim + 1
    ylimit = (yimagesz-1) / ycubedim + 1
    #  Round up the zlimit to the next larger
    zlimit = (((slices-1)/zcubedim+1)*zcubedim)/zcubedim 
    zscale = int(outproj.datasetcfg.zscale[result.resolution])
    channel = "Grayscale"
    
    outDB.putChannel(channel,1)

    for sl in range( startslice, endslice, batchsz ):

      slab = np.zeros ( (batchsz,yimagesz,ximagesz), dtype=np.uint16 )
      
      for b in range (batchsz):

        if ( sl + b <= endslice ):
            
          filename = '{}00-164_00-152_{:0>6}.tif'.format(result.path,(sl+b)*80)
          #filename = '{}00-111_000-29_{:0>6}.tif'.format(result.path,(sl+b)*50)
          #filename = '{}00-199_000000_{:0>6}.tif'.format(result.path,(sl+b)*60)
          #filename = '{}00-462_000000_{:0>6}.tif'.format(result.path,(sl+b)*50)
          #filename = '{}00-427_000000_{:0>6}.tif'.format(result.path,(sl+b)*60)
          #filename = '{}00-222_000000_{:0>6}.tif'.format(result.path,(sl+b)*50)
          #filename = '{}00-415_000000_{:0>6}.tif'.format(result.path,(sl+b)*50)
          #filename = '{}00-117_000000_{:0>6}.tif'.format(result.path,(sl+b)*50)
          #filename = '{}00-298_000000_{:0>6}.tif'.format(result.path,(sl+b)*50)
          #filename = '{}00-398_000000_{:0>6}.tif'.format(result.path,(sl+b)*60)
          #filename = '{}00-532_000000_{:0>6}.tif'.format(result.path,(sl+b)*60)
          #filename = '{}00-199_000000_{:0>6}.tif'.format(result.path,(sl+b)*50)
          #filename = '{}00-544_000-53_{:0>6}.tif'.format(result.path,(sl+b)*50)
          #imageurl = 'Grayscale/{}/{},{}/{},{}/{}/'.format(result.resolution,0,ximagesz,0,yimagesz,sl+b)
          print "slice {}".format(sl+b)

          try:
            #imgdata = ocpcarest.cutout( imageurl, outproj, outDB )
            imgdata = cv2.imread(filename,-1) 
            if imgdata != None:
              img = Image.frombuffer( 'I;16', (imgdata.shape[::-1]), imgdata.flatten(), 'raw', 'I;16', 0, 1)
              slab[b,:,:] = np.asarray(img.resize( [ximagesz,yimagesz]))
              img = None
            else:
              slab[b,:,:] = np.zeros((yimagesz,ximagesz),dtype=np.uint16)
          except IOError, e:
            print "Failed to get Cutout. {}".format(e)

      for y in range ( 0, yimagesz+1, ycubedim ):
        for x in range ( 0, ximagesz+1, xcubedim ):

          zidx = ndlib.XYZMorton ( [x/xcubedim,y/ycubedim,(sl-startslice)/zcubedim] )
          cubedata = np.zeros ( (zcubedim,ycubedim,xcubedim), dtype=np.uint16 )

          xmin = x 
          ymin = y
          xmax = ((min(ximagesz-1,x+xcubedim-1)))+1
          ymax = ((min(yimagesz-1,y+ycubedim-1)))+1
          zmin = 0
          zmax = min(sl+zcubedim,endslice+1)

          cubedata[0:zmax-zmin,0:ymax-ymin,0:xmax-xmin] = slab[zmin:zmax, ymin:ymax, xmin:xmax]

          cube = imagecube.ImageCube16 ( cubedims )
          cube.zeros()
          cube.data = cubedata
          if np.count_nonzero ( cube.data) != 0:
            outDB.putChannelCube ( zidx, 1, result.resolution, cube )

        print "Commiting at x:{},y:{},z{}".format(x,y,sl)
      outDB.conn.commit()

if __name__ == "__main__":
  main()

