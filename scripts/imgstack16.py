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

import argparse
import sys
import os
import numpy as np
import urllib, urllib2
import cStringIO
from contextlib import closing
from PIL import Image
import zlib

sys.path += [os.path.abspath('../django')]
import OCP.settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'OCP.settings'
from django.conf import settings

import django
django.setup()

from cube import Cube
import ocpcarest
import ocplib
import ocpcaproj
import ocpcadb

"""Construct an image hierarchy up from a given resolution for 16-bit images"""

def buildStack(token, channel, res):
  """Build the hierarchy of images"""

  with closing (ocpcaproj.OCPCAProjectsDB()) as projdb:
    proj = projdb.loadToken(token)
  
  with closing (ocpcadb.OCPCADB(proj)) as db:

    ch = proj.getChannelObj(channel)
    high_res = proj.datasetcfg.scalinglevels
    for cur_res in range(res, high_res+1):

      # Get the source database sizes
      [[ximagesz, yimagesz, zimagesz], timerange] = proj.datasetcfg.imageSize(cur_res)
      [xcubedim, ycubedim, zcubedim] = cubedim = proj.datasetcfg.getCubeDims()[cur_res]
      [xoffset, yoffset, zoffset] = proj.datasetcfg.getOffset()[cur_res]

      biggercubedim = [xcubedim*2,ycubedim*2,zcubedim]

      # Set the limits for iteration on the number of cubes in each dimension
      xlimit = (ximagesz-1) / xcubedim + 1
      ylimit = (yimagesz-1) / ycubedim + 1
      zlimit = (zimagesz-1) / zcubedim + 1

      for z in range(zlimit):
        for y in range(ylimit):
          for x in range(xlimit):

            # cutout the data at the -1 resolution
            olddata = db.cutout(ch, [ x*2*xcubedim, y*2*ycubedim, z*zcubedim], biggercubedim, cur_res-1 ).data
            # target array for the new data (z,y,x) order
            newdata = np.zeros([zcubedim,ycubedim,xcubedim], dtype=np.uint16)

            for sl in range(zcubedim):

              # Convert each slice to an image
              slimage = Image.frombuffer ( 'I;16', (xcubedim*2,ycubedim*2), olddata[sl,:,:].flatten(), 'raw', 'I;16', 0, 1 )

              # Resize the image
              newimage = slimage.resize ( [xcubedim,ycubedim] )
              
              # Put to a new cube
              newdata[sl,:,:] = np.asarray ( newimage )

            zidx = ocplib.XYZMorton ( [x,y,z] )
            cube = Cube.getCube(cubedim, ch.getChannelType(), ch.getDataType())
            cube.zeros()

            cube.data = newdata
            print "Inserting Cube {} at res {}".format(zidx, cur_res)
            db.putCube(ch, zidx, cur_res, cube, update=True)
            

def main():

  parser = argparse.ArgumentParser(description='Build an image stack')
  parser.add_argument('token', action="store", help='Token for the project.')
  parser.add_argument('channel', action="store", help='Channel for the project.')
  parser.add_argument('resolution', action="store", type=int, help='Start (highest) resolution to build')
  
  result = parser.parse_args()

  buildStack(result.token, result.channel, result.resolution)

  
if __name__ == "__main__":
  main()
