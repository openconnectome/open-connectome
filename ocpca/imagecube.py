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
#  ImageCube: manipulate the in-memory data representation of the 3-d cube of data
#    includes loading, export, read and write routines
#
#  All the interfaces to this class are in x,y,z order
#  Cube data goes in z,y,x order this is compatible with images and more efficient?
#
class ImageCube8(Cube):

  def __init__(self, cubesize=[64,64,64]):
    """Create empty array of cubesize"""

    # call the base class constructor
    Cube.__init__(self,cubesize)
    # note that this is self.cubesize (which is transposed) in Cube
    self.data = np.zeros ( self.cubesize, dtype=np.uint8 )

    # variable that describes when a cube is created from zeros rather than loaded from another source
    self._newcube = False

  def fromZeros ( self ):
    """Determine if the cube was created from all zeros?"""
    if self._newcube == True:
      return True
    else: 
      return False

  def zeros ( self ):
    """Create a cube of all zeros"""
    self._newcube = True
    self.data = np.zeros ( self.cubesize, dtype=np.uint8 )

  def xyImage ( self ):
    """Create xy slice"""
    zdim,ydim,xdim = self.data.shape
    return Image.frombuffer ( 'L', (xdim,ydim), self.data[0,:,:].flatten(), 'raw', 'L', 0, 1 ) 

  def xzImage ( self, zscale ):
    """Create xz slice"""
    zdim,ydim,xdim = self.data.shape
    outimage = Image.frombuffer ( 'L', (xdim,zdim), self.data[:,0,:].flatten(), 'raw', 'L', 0, 1 ) 
    #if the image scales to 0 pixels it don't work
    return outimage.resize ( [xdim, int(zdim*zscale)] )

  def yzImage ( self, zscale ):
    """Create yz slice"""
    zdim,ydim,xdim = self.data.shape
    outimage = Image.frombuffer ( 'L', (ydim,zdim), self.data[:,:,0].flatten(), 'raw', 'L', 0, 1 ) 
    #if the image scales to 0 pixels it don't work
    return outimage.resize ( [ydim, int(zdim*zscale)] )



#
#  ImageCube16: manipulate the in-memory data representation of the 3-d cube 
#    includes loading, export, read and write routines
#
#  This sub-class is for 16 bit data 
#
#  All the interfaces to this class are in x,y,z order
#  Cube data goes in z,y,x order this is compatible with images and more efficient?
#
class ImageCube16(Cube):

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

#
#  ImageCube32: manipulate the in-memory data representation of the 3-d cube 
#    includes loading, export, read and write routines
#
#  This sub-class is for 32 bit data. The data is 4x8bit RGBA channels.
#
#  All the interfaces to this class are in x,y,z order
#  Cube data goes in z,y,x order this is compatible with images and more efficient?
#
class ImageCube32(Cube):

  def __init__(self, cubesize=[64,64,64]):
    """Create empty array of cubesize"""

    # call the base class constructor
    Cube.__init__(self,cubesize)
    # note that this is self.cubesize (which is transposed) in Cube
    self.data = np.zeros ( self.cubesize, dtype=np.uint32 )
    # variable that describes when a cube is created from zeros rather than loaded from another source
    self._newcube = False

  def fromZeros ( self ):
    """Determine if the cube was created from all zeros"""
    if self._newcube == True:
      return True
    else: 
      return False

  def zeros ( self ):
    """Create a cube of all 0"""
    self._newcube = True
    self.data = np.zeros ( self.cubesize, dtype=np.uint32 )

  #
  # Create the specified slice (index) 
  #
  def xyImage ( self ):

    zdim,ydim,xdim = self.data.shape
    return Image.fromarray( self.data[0,:,:], "RGBA")


  #
  # Create the specified slice (index) 
  #
  def xzImage ( self, zscale ):

    zdim,ydim,xdim = self.data.shape
    outimage = Image.fromarray( self.data[:,0,:], "RGBA")
    return outimage.resize ( [xdim, int(zdim*zscale)] )


  #
  # Create the specified slice (index) 
  #
  def yzImage ( self, zscale ):

    zdim,ydim,xdim = self.data.shape
    outimage = Image.fromarray( self.data[:,:,0], "RGBA")
    return outimage.resize ( [ydim, int(zdim*zscale)] )


  def RGBAChannel ( self ):
    """Convert the uint32 back into 4x8 bit channels"""

    zdim, ydim, xdim = self.data.shape
    newcube = np.zeros( (4, zdim, ydim, xdim), dtype=np.uint8 )
    newcube[0,:,:,:] = np.bitwise_and(self.data, 0xff, dtype=np.uint8)
    newcube[1,:,:,:] = np.uint8 ( np.right_shift( self.data, 8) & 0xff )
    newcube[2,:,:,:] = np.uint8 ( np.right_shift( self.data, 16) & 0xff )
    newcube[3,:,:,:] = np.uint8 ( np.right_shift (self.data, 24) )
    self.data = newcube


#
#  ImageCube64: manipulate the in-memory data representation of the 3-d cube 
#    includes loading, export, read and write routines
#
#  This sub-class is for 64 bit data. The data is 4x8bit RGBA channels.
#
#  All the interfaces to this class are in x,y,z order
#  Cube data goes in z,y,x order this is compatible with images and more efficient?
#
class ImageCube64(Cube):

  def __init__(self, cubesize=[64,64,64]):
    """Create empty array of cubesize"""

    # call the base class constructor
    Cube.__init__(self,cubesize)
    # note that this is self.cubesize (which is transposed) in Cube
    self.data = np.zeros ( self.cubesize, dtype=np.uint64 )
    # variable that describes when a cube is created from zeros rather than loaded from another source
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
    self.data = np.zeros ( self.cubesize, dtype=np.uint64 )

  def xyImage ( self ):
    """Create xy slice"""

#RB I think this does nothing
#    channels,ydim,xdim = self.data.shape
    self.extractChannel()
    return Image.fromarray( self.data, "RGBA")

  def xzImage ( self, zscale ):
    """Create xz slice"""

    zdim,ydim,xdim = self.data.shape
    self.extractChannel()
    outimage = Image.fromarray( self.data, "RGBA")
    return outimage.resize ( [xdim, int(zdim*zscale)] )

  def yzImage ( self, zscale ):
    """Create yz slice"""

    zdim,ydim,xdim = self.data.shape
    self.extractChannel()
    outimage = Image.fromarray( self.data, "RGBA")
    return outimage.resize ( [ydim, int(zdim*zscale)] )
  
  def extractChannel ( self ):
    """Convert the uint32 back into 4x8 bit channels"""

    zdim, ydim, xdim = self.data.shape
    newcube = np.zeros( (ydim, xdim, 4), dtype=np.uint8 )
    newcube[:,:,0] = np.bitwise_and(self.data, 0xffff, dtype=np.uint8)
    newcube[:,:,1] = np.uint8 ( np.right_shift( self.data, 16) & 0xffff )
    newcube[:,:,2] = np.uint8 ( np.right_shift( self.data, 32) & 0xffff )
    newcube[:,:,3] = np.uint8 ( np.right_shift (self.data, 48) )
    self.data = newcube

  def RGBAChannel ( self ):
    """Convert the uint32 back into 4x8 bit channels"""

    zdim, ydim, xdim = self.data.shape
    newcube = np.zeros( (4, zdim, ydim, xdim), dtype=np.uint16 )
    newcube[0,:,:,:] = np.bitwise_and(self.data, 0xffff, dtype=np.uint16)
    newcube[1,:,:,:] = np.uint16 ( np.right_shift( self.data, 16) & 0xffff )
    newcube[2,:,:,:] = np.uint16 ( np.right_shift( self.data, 32) & 0xffff )
    newcube[3,:,:,:] = np.uint16 ( np.right_shift (self.data, 48) )
    self.data = newcube
