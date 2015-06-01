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
import cStringIO
from PIL import Image
import zlib

import ocpcaproj
import ocplib

import logging
logger=logging.getLogger("ocp")

#
#  AnnotateCube: manipulate the in-memory data representation of the 3-d cube of data
#    that contains annotations.  
#

class Cube:

  #  Express cubesize in [ x,y,z ]
  def __init__(self, cubesize):
    """Create empty array of cubesize"""

    # cubesize is in z,y,x for interactions with tile/image data
    self.zdim, self.ydim, self.xdim = self.cubesize = [ cubesize[2],cubesize[1],cubesize[0] ]
    self.data = np.empty ( self.cubesize )


  def addData ( self, other, index ):
    """Add data to a larger cube from a smaller cube"""

    xoffset = index[0]*other.xdim
    yoffset = index[1]*other.ydim
    zoffset = index[2]*other.zdim

    self.data [ zoffset:zoffset+other.zdim,\
                yoffset:yoffset+other.ydim,\
                xoffset:xoffset+other.xdim]\
            = other.data [:,:,:]

  def addData_new ( self, other, index ):
    """Add data to a larger cube from a smaller cube"""

    xoffset = index[0]*other.xdim
    yoffset = index[1]*other.ydim
    zoffset = index[2]*other.zdim

    np.copyto ( self.data[zoffset:zoffset+other.zdim,yoffset:yoffset+other.ydim,xoffset:xoffset+other.xdim],other.data [:,:,:] )
  
  def trim ( self, xoffset, xsize, yoffset, ysize, zoffset, zsize ):
    """Trim off the excess data"""
    self.data = self.data [ zoffset:zoffset+zsize, yoffset:yoffset+ysize, xoffset:xoffset+xsize ]

  def fromNPZ ( self, pandz ):
    """Load the cube from a pickled and zipped blob"""
    try:
      self.data = np.load ( cStringIO.StringIO ( zlib.decompress ( pandz[:] ) ) )
    except:
      logger.error ("Failed to decompress database cube.  Data integrity concern.")
      raise

    self._newcube = False


  def toNPZ ( self ):
    """Pickle and zip the object"""
    try:
      # Create the compressed cube
      fileobj = cStringIO.StringIO ()
      np.save ( fileobj, self.data )
      return  zlib.compress (fileobj.getvalue())
    except:
      logger.error ("Failed to compress database cube.  Data integrity concern.")
      raise
 
  def overwrite ( self, writedata ):
    """Get's a dense voxel region and overwrites all non-zero values"""
    if (self.data.dtype != writedata.dtype ):
      logger.error("Conflicting data types for overwrite")
      raise OCPCAError ("Conflicting data types for overwrite")
    self.data = ocplib.overwriteDense_ctype ( self.data, writedata )
  
  def RGBAChannel(self):
    """Return a RGBAChannel Method definition"""
    pass

  def isNotZeros(self):
    """Check if the cube has any data"""
    return np.any(self.data)


  # factory method for cube
  @staticmethod
  def getCube(cubedim, channel_type, datatype, timerange=None):

    if channel_type in ocpcaproj.ANNOTATION_CHANNELS and datatype in ocpcaproj.DTYPE_uint32:
      return anncube.AnnotateCube (cubedim)
    elif channel_type in ocpcaproj.TIMESERIES_CHANNELS and timerange is not None:
      if datatype in ocpcaproj.DTYPE_uint8:
        return timecube.TimeCube8(cubedim, timerange)
      elif datatype in ocpcaproj.DTYPE_uint16:
        return timecube.TimeCube16(cubedim, timerange)
    elif datatype in ocpcaproj.DTYPE_uint8:
      return imagecube.ImageCube8 (cubedim)
    elif datatype in ocpcaproj.DTYPE_uint16:
      return imagecube.ImageCube16 (cubedim)
    elif datatype in ocpcaproj.DTYPE_uint32:
      return imagecube.ImageCube32 (cubedim)
    elif datatype in ocpcaproj.DTYPE_uint64:
      return imagecube.ImageCube64 (cubedim)
    elif datatype in ocpcaproj.DTYPE_float32:
      return probmapcube.ProbMapCube32 (cubedim)
    else:
      return Cube(cubedim)


# end cube

import imagecube
import anncube
import probmapcube
import timecube
