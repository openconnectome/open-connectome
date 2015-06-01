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
from PIL import Image

from cube import Cube
import ocplib
from windowcutout import windowCutout

from ocpcaerror import OCPCAError
import logging
logger=logging.getLogger("ocp")


#
#  TimeCube8: manipulate the in-memory data representation of the 3-d cube of data
#    includes loading, export, read and write routines
#
#  All the interfaces to this class are in x,y,z order
#  Cube data goes in z,y,x order this is compatible with images and more efficient?
#
class TimeCube8(Cube):

  def __init__(self, cubesize=[64,64,64], timerange=[0,0]):
    """Create empty array of cubesize"""

    # call the base class constructor
    Cube.__init__(self,cubesize)
    # note that this is self.cubesize (which is transposed) in Cube
    self.timerange = timerange
    self.data = np.zeros ([self.timerange[1]-self.timerange[0]]+self.cubesize, dtype=np.uint8)

    # variable that describes when a cube is created from zeros rather than loaded from another source
    self._newcube = False

  def addData(self, other, index, time):
    """Add data to a larger cube from a smaller cube"""

    xoffset = index[0]*other.xdim
    yoffset = index[1]*other.ydim     
    zoffset = index[2]*other.zdim
    
    self.data [ time-self.timerange[0], zoffset:zoffset+other.zdim, yoffset:yoffset+other.ydim, xoffset:xoffset+other.xdim]\
        = other.data [:,:,:]

  def trim(self, xoffset, xsize, yoffset, ysize, zoffset, zsize):
    """Trim off the excess data"""
    self.data = self.data[:, zoffset:zoffset+zsize, yoffset:yoffset+ysize, xoffset:xoffset+xsize]

  def zeros(self):
    """Create a cube of all zeros"""
    self._newcube = True
    self.data = np.zeros(self.cubesize, np.uint8)

  def xyImage ( self ):
    """Create xy slice"""
    zdim,ydim,xdim = self.data.shape[1:]
    return Image.frombuffer ( 'L', (xdim,ydim), self.data[0,0,:,:].flatten(), 'raw', 'L', 0, 1 ) 

  def xzImage ( self, zscale ):
    """Create xz slice"""
    zdim,ydim,xdim = self.data.shape[1:]
    outimage = Image.frombuffer ( 'L', (xdim,zdim), self.data[0,:,0,:].flatten(), 'raw', 'L', 0, 1 ) 
    #if the image scales to 0 pixels it don't work
    return outimage.resize ( [xdim, int(zdim*zscale)] )

  def yzImage ( self, zscale ):
    """Create yz slice"""
    zdim,ydim,xdim = self.data.shape[1:]
    outimage = Image.frombuffer ( 'L', (ydim,zdim), self.data[0,:,:,0].flatten(), 'raw', 'L', 0, 1 ) 
    #if the image scales to 0 pixels it don't work
    return outimage.resize ( [ydim, int(zdim*zscale)] )


#
#  TimeCube16: manipulate the in-memory data representation of the 3-d cube 
#    includes loading, export, read and write routines
#
#  This sub-class is for 16 bit data 
#
#  All the interfaces to this class are in x,y,z order
#  Cube data goes in z,y,x order this is compatible with images and more efficient?
#
class TimeCube16(Cube):

  # Constructor 
  def __init__(self, cubesize=[64,64,64]):
    """Create empty array of cubesize"""

    # call the base class constructor
    Cube.__init__(self,cubesize)
    # note that this is self.cubesize (which is transposed) in Cube
    self.data = np.zeros ( self.cubesize, dtype=np.uint16 )

    # variable that describes when a cube is created from zeros
    #  rather than loaded from another source
    self._newcube = False

  def fromZeros ( self ):
    """Determine if the cube was created from all zeros?"""
    if self._newcube == True:
      return True
    else: 
      return False

  def zeros ( self ):
    """Create a cube of all 0"""
    self._newcube = True
    self.data = np.zeros ( self.cubesize, dtype=np.uint16 )

  def xyImage ( self ):
    """Create xy slice"""
    # This works for 16-> conversions
    zdim,ydim,xdim = self.data.shape
    if self.data.dtype == np.uint8:  
      return Image.frombuffer ( 'L', (xdim,ydim), self.data[0,:,:].flatten(), 'raw', 'L', 0, 1)
    else:
      outimage = Image.frombuffer ( 'I;16', (xdim,ydim), self.data[0,:,:].flatten(), 'raw', 'I;16', 0, 1)
      return outimage.point(lambda i:i*(1./256)).convert('L')


  def xzImage ( self, zscale ):
    """Create xz slice"""
    zdim,ydim,xdim = self.data.shape
    if self.data.dtype == np.uint8:  
      outimage = Image.frombuffer ( 'L', (xdim,zdim), self.data[:,0,:].flatten(), 'raw', 'L', 0, 1)
    else:
      outimage = Image.frombuffer ( 'I;16', (xdim,zdim), self.data[:,0,:].flatten(), 'raw', 'I;16', 0, 1)
      outimage = outimage.point(lambda i:i*(1./256)).convert('L')
    
    return  outimage.resize ( [xdim, int(zdim*zscale)] )


  def yzImage ( self, zscale ):
    """Create yz slice"""
    zdim,ydim,xdim = self.data.shape
    if self.data.dtype == np.uint8:  
      outimage = Image.frombuffer ( 'L', (ydim,zdim), self.data[:,:,0].flatten(), 'raw', 'L', 0, 1)
    else:
      outimage = Image.frombuffer ( 'I;16', (ydim,zdim), self.data[:,:,0].flatten(), 'raw', 'I;16', 0, 1)
      outimage = outimage.point(lambda i:i*(1./256)).convert('L')
    
    return outimage.resize ( [ydim, int(zdim*zscale)] )

# end BrainCube
