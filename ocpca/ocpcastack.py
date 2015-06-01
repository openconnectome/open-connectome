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

import sys
import os
import numpy as np
import urllib, urllib2
from contextlib import closing
import cStringIO
import logging
import MySQLdb
from PIL import Image
import zlib

from cube import Cube
import ocpcaproj
import ocpcadb
import ocplib
from ocpcaerror import OCPCAError
import logging
logger=logging.getLogger("ocp")

from ocpca_cy import addDataToZSliceStack_cy
from ocpca_cy import addDataToIsotropicStack_cy


#RBRM testing code
#
def getAnnValue ( value00, value01, value10, value11 ):
  """Determine the annotation value at the next level of the hierarchy from a 2x2.
      take the first non-zero element or take the first repeated element.
   """

  # The following block of code places the majority annotation into value
  # start with 00
  value = value00

  # put 01 in if not 00
  # if they are the same, that's fine
  if value == 0:
    value = value01

  if value10 != 0:
    if value == 0:
      value = value10
    # if this value matches a previous it is 2 out of 4
    elif value10 == value00 or value10 == value01:
      value = value10

  if value11 != 0:
    if value == 0:
      value = value10
    elif value11==value00 or value11==value01 or value11==value10:
      value = value11

  return value


def addDataToIsotropicStack ( cube, output, offset ):
    """Add the contribution of the input data to the next level at the given offset in the output cube"""

    for z in range (cube.data.shape[0]/2):
      for y in range (cube.data.shape[1]/2):
        for x in range (cube.data.shape[2]/2):

            # not perfect take a value from either slice.  Not a majority over all.
            value = getAnnValue (cube.data[z*2,y*2,x*2],cube.data[z*2,y*2,x*2+1],cube.data[z*2,y*2+1,x*2],cube.data[z*2,y*2+1,x*2+1])
            if value == 0:
              value = getAnnValue (cube.data[z*2+1,y*2,x*2],cube.data[z*2+1,y*2,x*2+1],cube.data[z*2+1,y*2+1,x*2],cube.data[z*2+1,y*2+1,x*2+1])

            try:
              output [ z+offset[2], y+offset[1], x+offset[0] ] = value
            except:
              import pdb; pdb.set_trace()


"""Construct a hierarchy off of a completed database."""

def buildStack(token, channel_name, resolution=None):
  """Wrapper for the different datatypes """

  with closing(ocpcaproj.OCPCAProjectsDB()) as projdb:
    proj = projdb.loadToken(token)
    ch = proj.getChannelObj(channel_name)
 
    try:
     
      if ch.getChannelType() in ocpcaproj.ANNOTATION_CHANNELS:
        #clearStack(token)
        buildAnnoStack(proj, ch, resolution)
      elif ch.getChannelType() in ocpcaproj.IMAGE_CHANNELS:
        buildImageStack(proj, ch, resolution)
      elif ch.getChannelType() in ocpcaproj.TIMESERIES_CHANNELS:
        print "Not Supported"
    
      ch.setPropagate(ocpcaproj.PROPAGATED)

    except MySQLdb.Error, e:
      proj.setPropagate(ocpcaproj.NOT_PROPAGATED)
      projdb.updatePropagate(proj)
      logger.error("Error in building image stack {}".format(token))
      raise OCPCAError("Error in the building image stack {}".format(token))


def clearStack ( token ):
  """ Clear a OCP stack for a given project """

  with closing(ocpcaproj.OCPCAProjectsDB()) as projdb:
    proj = projdb.loadToken(token)
  
  with closing(ocpcadb.OCPCADB(proj)) as db:
    
    # Clear the database
    for l in range(proj.getResolution(), proj.datasetcfg.resolutions[-1]):
      
        sql = "TRUNCATE table res{};".format(l+1)
        sql += "TRUNCATE table raw{};".format(l+1)
        sql += "TRUNCATE table idx{};".format(l+1)
        if proj.getExceptions == ocpcaproj.EXCEPTION_TRUE:
          sql += "TRUNCATE table exec{};".format(l+1)

        try:
          print sql
          db.conn.cursor().execute(sql)
          db.conn.commit()
        except MySQLdb.Error, e:
          logger.error ("Error truncating the table. {}".format(e))
          raise
        finally:
          db.conn.cursor().close()


def buildAnnoStack ( proj, ch, res=None ):
  """Build the hierarchy for annotations"""
  
  with closing(ocpcadb.OCPCADB (proj)) as db:

    # pick a resolution
    if res is None:
      res = 1
    
    high_res = proj.datasetcfg.scalinglevels
    scaling = proj.datasetcfg.scalingoption
  
    for cur_res in range(res, high_res+1):

      # Get the source database sizes
      [[ximagesz, yimagesz, zimagesz], timerange] = proj.datasetcfg.imageSize(cur_res)
      [xcubedim, ycubedim, zcubedim] = cubedim = proj.datasetcfg.getCubeDims()[cur_res]

      # Set the limits for iteration on the number of cubes in each dimension
      xlimit = (ximagesz-1) / xcubedim + 1
      ylimit = (yimagesz-1) / ycubedim + 1
      zlimit = (zimagesz-1) / zcubedim + 1

      #  Choose constants that work for all resolutions. recall that cube size changes from 128x128x16 to 64*64*64
      if scaling == ocpcaproj.ZSLICES:
        outdata = np.zeros ( [ zcubedim*4, ycubedim*2, xcubedim*2 ], dtype=ocpcaproj.OCP_dtypetonp.get(ch.getDataType()))
        outdata2 = np.zeros ( [ zcubedim*4, ycubedim*2, xcubedim*2 ], dtype=ocpcaproj.OCP_dtypetonp.get(ch.getDataType()))
      elif scaling == ocpcaproj.ISOTROPIC:
        outdata = np.zeros ( [ zcubedim*2,  ycubedim*2, xcubedim*2 ], dtype=ocpcaproj.OCP_dtypetonp.get(ch.getDataType()))
      else:
        logger.error ( "Invalid scaling option in project = {}".format(scaling) )
        raise OCPCAError ( "Invalid scaling option in project = {}".format(scaling)) 

      # Round up to the top of the range
      lastzindex = (ocplib.XYZMorton([xlimit,ylimit,zlimit])/64+1)*64

      # Iterate over the cubes in morton order
      for mortonidx in range(0, lastzindex, 64): 

        # call the range query
        cuboids = db.getCubes(ch, range(mortonidx,mortonidx+64), cur_res-1)
        cube = Cube.getCube(cubedim, ch.getChannelType(), ch.getDataType())

        # get the first cube
        for idx, datastring in cuboids:

          xyz = ocplib.MortonXYZ(idx)
          cube.fromNPZ(datastring)

          if scaling == ocpcaproj.ZSLICES:

            # Compute the offset in the output data cube 
            #  we are placing 4x4x4 input blocks into a 2x2x4 cube 
            offset = [(xyz[0]%4)*(xcubedim/2), (xyz[1]%4)*(ycubedim/2), (xyz[2]%4)*zcubedim]

            # add the contribution of the cube in the hierarchy
            #addDataToZSliceStack_cy(cube, outdata, offset)
            addDataToZSliceStack(cube, outdata, offset)
            #ocplib.addDataToZSliceStack_ctype(cube, outdata, offset)
            #if np.array_equal(outdata, outdata2) is False:
              #import pdb; pdb.set_trace()

          elif scaling == ocpcaproj.ISOTROPIC:

            # Compute the offset in the output data cube 
            #  we are placing 4x4x4 input blocks into a 2x2x2 cube 
            offset = [(xyz[0]%4)*(xcubedim/2), (xyz[1]%4)*(ycubedim/2), (xyz[2]%4)*(zcubedim/2)]

            # use python version for debugging
            addDataToIsotropicStack(cube, outdata, offset)

        #  Get the base location of this batch
        xyzout = ocplib.MortonXYZ (mortonidx)

        # adjust to output corner for scale.
        if scaling == ocpcaproj.ZSLICES:
          outcorner = [ xyzout[0]*xcubedim/2, xyzout[1]*ycubedim/2, xyzout[2]*zcubedim ]
        elif scaling == ocpcaproj.ISOTROPIC:
          outcorner = [ xyzout[0]*xcubedim/2, xyzout[1]*ycubedim/2, xyzout[2]*zcubedim/2 ]

        #  Data stored in z,y,x order dims in x,y,z
        outdim = outdata.shape[::-1]

        # Preserve annotations made at the specified level
        # KL check that the P option preserves annotations?  RB changed from O
        db.annotateDense(ch, outcorner, cur_res, outdata, 'O')
        db.conn.commit()
          
        # zero the output buffer
        outdata = np.zeros ([zcubedim*4, ycubedim*2, xcubedim*2], dtype=ocpcaproj.OCP_dtypetonp.get(ch.getDataType()))

def addDataToZSliceStack( cube, output, offset ):
  """Add the contribution of the input data to the next level at the given offset in the output cube"""
  for z in range (cube.data.shape[0]):
    for y in range (cube.data.shape[1]/2):
      for x in range (cube.data.shape[2]/2):
        try:
          value = getAnnValue (cube.data[z,y*2,x*2],cube.data[z,y*2,x*2+1],cube.data[z,y*2+1,x*2],cube.data[z,y*2+1,x*2+1])
          output [ z+offset[2], y+offset[1], x+offset[0] ] = value
        except Exception, e:
          import pdb; pdb.set_trace()


def buildImageStack(proj, ch, res=None):
  """Build the hierarchy of images"""

  with closing(ocpcadb.OCPCADB(proj)) as db:

    # pick a resolution
    if res is None:
      res = 1

    high_res = proj.datasetcfg.scalinglevels
    scaling = proj.datasetcfg.scalingoption

    for cur_res in range (res, high_res+1):

      # Get the source database sizes
      [[ximagesz, yimagesz, zimagesz], timerange] = proj.datasetcfg.imageSize(cur_res)
      [xcubedim, ycubedim, zcubedim] = cubedim = proj.datasetcfg.getCubeDims()[cur_res]

      if scaling == ocpcaproj.ZSLICES:
        (xscale, yscale, zscale) = (2, 2, 1)
      elif scaling == ocpcaproj.ISOTROPIC:
        (xscale, yscale, zscale) = (2, 2, 2)
      else:
        logger.error("Invalid scaling option in project = {}".format(scaling))
        raise OCPCAError("Invalid scaling option in project = {}".format(scaling)) 

      biggercubedim = [xcubedim*xscale,ycubedim*yscale,zcubedim*zscale]

      # Set the limits for iteration on the number of cubes in each dimension
      xlimit = (ximagesz-1) / xcubedim + 1
      ylimit = (yimagesz-1) / ycubedim + 1
      zlimit = (zimagesz-1) / zcubedim + 1


      for z in range(zlimit):
        for y in range(ylimit):
          for x in range(xlimit):

            # cutout the data at the resolution
            olddata = db.cutout(ch, [x*xscale*xcubedim, y*yscale*ycubedim, z*zscale*zcubedim ], biggercubedim, cur_res-1).data

            #olddata target array for the new data (z,y,x) order
            newdata = np.zeros([zcubedim,ycubedim,xcubedim], dtype=ocpcaproj.OCP_dtypetonp.get(ch.getDataType()))

            for sl in range(zcubedim):

              if scaling == ocpcaproj.ZSLICES:
                data = olddata[sl,:,:]
              elif scaling == ocpcaproj.ISOTROPIC:
                #vec_func = np.vectorize ( lambda a,b: a if b==0 else (b if a ==0 else np.uint8((a+b)/2))) 
                #mergedata = vec_func ( olddata[sl*2,:,:], olddata[sl*2+1,:,:] )
                data = ocplib.isotopicBuild_ctype(oldata[sl*2,:,:], olddata[sl*2+1,:,:])

              # Convert each slice to an image
              # 8-bit int option
              if olddata.dtype == np.uint8:
                slimage = Image.frombuffer('L', (xcubedim*2,ycubedim*2), olddata[sl,:,:].flatten(), 'raw', 'L', 0, 1)
              # 16-bit int option
              elif olddata.dtype == np.uint16:
                slimage = Image.frombuffer('I;16', (xcubedim*2,ycubedim*2), olddata[sl,:,:].flatten(), 'raw', 'I;16', 0, 1)
              # 32-bit float option
              elif olddata.dtype == np.float32:
                slimage = Image.frombuffer ( 'F', (xcubedim*2,ycubedim*2), olddata[sl,:,:].flatten(), 'raw', 'F', 0, 1 )

              # Resize the image and put in the new cube array
              newdata[sl, :, :] = np.asarray(slimage.resize([xcubedim,ycubedim]))

            zidx = ocplib.XYZMorton ([x,y,z])
            cube = Cube.getCube(cubedim, ch.getChannelType(), ch.getDataType())
            cube.zeros()

            cube.data = newdata
            db.putCube(ch, zidx, cur_res, cube, update=True)
