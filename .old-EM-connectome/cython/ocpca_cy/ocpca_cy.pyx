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

# setup ocplib
import sys
sys.path.append('../../ocplib')

import numpy as np
cimport numpy as np
import ocplib 

DTYPE = np.uint32
ctypedef np.uint32_t DTYPE_t

#######################   Annotate -- list processing optimized ##########################

def annotate_cy ( np.ndarray[DTYPE_t, ndim=3] data, unsigned int annid, offset, np.ndarray[DTYPE_t, ndim=2] locations, conflictopt ):
  """Add annotation by a list of locations"""

  cdef unsigned int xoffset
  cdef unsigned int yoffset
  cdef unsigned int zoffset

  xoffset, yoffset, zoffset = offset

  exceptions = []


  # xyz coordinates get stored as zyx to be more
  #  efficient when converting to images
  for i in range (len(locations)):
    voxel = locations[i]

#    if xoffset<voxel[0] or yoffset<voxel[1] or zoffset<voxel[2]:
#      raise Exception( '{},{},{}{}'.format(xoffset, yoffset, zoffset, voxel))

    #  label unlabeled voxels
    if ( data [ voxel[2]-zoffset, voxel[1]-yoffset, voxel[0]-xoffset] == 0 ):
         data [ voxel[2]-zoffset, voxel[1]-yoffset, voxel[0]-xoffset ] = annid

    # already labelled voxels are exceptions, unless they are the same value
    elif (data [ voxel[2]-zoffset, voxel[1]-yoffset, voxel[0]-xoffset] != annid ):
      # O is for overwrite
      if conflictopt == 'O':
        data [ voxel[2]-zoffset, voxel[1]-yoffset, voxel[0]-xoffset ] = annid
      # P preserves the existing content
      elif conflictopt == 'P':
        pass
      # E creates exceptions
      elif conflictopt == 'E':
        exceptions.append ([voxel[0]-xoffset, voxel[1]-yoffset, voxel[2]-zoffset])
      else:
        print ( "Improper conflict option selected.  Option = ", conflictopt  )
        assert 0

  return exceptions


####################  shave -- remove a list of voxels from an annotation   ############################

def shave_cy ( np.ndarray[DTYPE_t, ndim=3] data, int annid, offset, np.ndarray[DTYPE_t, ndim=2] locations ):
  """Remove annotation by a list of locations"""

  cdef int xoffset
  cdef int yoffset
  cdef int zoffset

  xoffset, yoffset, zoffset = offset

  exceptions = []
  zeroed = []              # candidates for promotion

  # xyz coordinates get stored as zyx to be more
  #  efficient when converting to images
  for i in range (len(locations)):

    voxel = locations[i]
    #  if it's labeled, remove the label
    if ( data [ voxel[2]-offset[2], voxel[1]-offset[1], voxel[0]-offset[0]] == annid ):
         data [ voxel[2]-offset[2], voxel[1]-offset[1], voxel[0]-offset[0] ] = 0
         zeroed.append ( [voxel[0]-offset[0], voxel[1]-offset[1], voxel[2]-offset[2]] )

    # already labelled voxels may be in the exceptions list
    elif (data [ voxel[2]-offset[2], voxel[1]-offset[1], voxel[0]-offset[0]] != 0 ):
      exceptions.append ([voxel[0]-offset[0], voxel[1]-offset[1], voxel[2]-offset[2]])

  return exceptions, zeroed


#################  Annotation recoloring function   ##################

# 256 categorical colors from onetime/colorgen.py
pcolors = (
(127, 243, 121),
(243, 121, 163),
(121, 198, 243),
(234, 243, 121),
(216, 121, 243),
(121, 243, 181),
(243, 145, 121),
(121, 132, 243),
(168, 243, 121),
(243, 121, 203),
(121, 239, 243),
(243, 211, 121),
(176, 121, 243),
(121, 243, 140),
(243, 121, 138),
(121, 173, 243),
(209, 243, 121),
(241, 121, 243),
(121, 243, 206),
(243, 170, 121),
(135, 121, 243),
(143, 243, 121),
(243, 121, 178),
(121, 214, 243),
(243, 236, 121),
(201, 121, 243),
(121, 243, 165),
(243, 130, 121),
(121, 148, 243),
(183, 243, 121),
(243, 121, 219),
(121, 243, 231),
(243, 196, 121),
(160, 121, 243),
(121, 243, 125),
(243, 121, 153),
(121, 189, 243),
(224, 243, 121),
(226, 121, 243),
(121, 243, 190),
(243, 155, 121),
(121, 123, 243),
(158, 243, 121),
(243, 121, 194),
(121, 229, 243),
(243, 221, 121),
(185, 121, 243),
(121, 243, 150),
(243, 121, 128),
(121, 163, 243),
(199, 243, 121),
(243, 121, 234),
(121, 243, 216),
(243, 180, 121),
(145, 121, 243),
(133, 243, 121),
(243, 121, 169),
(121, 204, 243),
(240, 243, 121),
(210, 121, 243),
(121, 243, 175),
(243, 139, 121),
(121, 138, 243),
(174, 243, 121),
(243, 121, 209),
(121, 243, 241),
(243, 205, 121),
(170, 121, 243),
(121, 243, 134),
(243, 121, 143),
(121, 179, 243),
(214, 243, 121),
(235, 121, 243),
(121, 243, 200),
(243, 165, 121),
(129, 121, 243),
(149, 243, 121),
(243, 121, 184),
(121, 220, 243),
(243, 230, 121),
(195, 121, 243),
(121, 243, 159),
(243, 124, 121),
(121, 154, 243),
(189, 243, 121),
(243, 121, 225),
(121, 243, 225),
(243, 190, 121),
(154, 121, 243),
(124, 243, 121),
(243, 121, 159),
(121, 195, 243),
(230, 243, 121),
(220, 121, 243),
(121, 243, 184),
(243, 149, 121),
(121, 129, 243),
(164, 243, 121),
(243, 121, 200),
(121, 235, 243),
(243, 215, 121),
(179, 121, 243),
(121, 243, 144),
(243, 121, 134),
(121, 169, 243),
(205, 243, 121),
(243, 121, 240),
(121, 243, 210),
(243, 174, 121),
(139, 121, 243),
(139, 243, 121),
(243, 121, 175),
(121, 210, 243),
(243, 240, 121),
(204, 121, 243),
(121, 243, 169),
(243, 133, 121),
(121, 144, 243),
(180, 243, 121),
(243, 121, 215),
(121, 243, 235),
(243, 199, 121),
(164, 121, 243),
(121, 243, 128),
(243, 121, 149),
(121, 185, 243),
(220, 243, 121),
(230, 121, 243),
(121, 243, 194),
(243, 159, 121),
(123, 121, 243),
(155, 243, 121),
(243, 121, 190),
(121, 226, 243),
(243, 224, 121),
(189, 121, 243),
(121, 243, 153),
(243, 121, 124),
(121, 160, 243),
(195, 243, 121),
(243, 121, 231),
(121, 243, 219),
(243, 184, 121),
(148, 121, 243),
(129, 243, 121),
(243, 121, 165),
(121, 200, 243),
(236, 243, 121),
(214, 121, 243),
(121, 243, 179),
(243, 143, 121),
(121, 135, 243),
(170, 243, 121),
(243, 121, 206),
(121, 241, 243),
(243, 209, 121),
(173, 121, 243),
(121, 243, 138),
(243, 121, 140),
(121, 175, 243),
(211, 243, 121),
(239, 121, 243),
(121, 243, 204),
(243, 168, 121),
(133, 121, 243),
(145, 243, 121),
(243, 121, 180),
(121, 216, 243),
(243, 234, 121),
(198, 121, 243),
(121, 243, 163),
(243, 128, 121),
(121, 150, 243),
(186, 243, 121),
(243, 121, 221),
(121, 243, 229),
(243, 193, 121),
(158, 121, 243),
(121, 243, 122),
(243, 121, 155),
(121, 191, 243),
(226, 243, 121),
(224, 121, 243),
(121, 243, 188),
(243, 153, 121),
(121, 125, 243),
(161, 243, 121),
(243, 121, 196),
(121, 231, 243),
(243, 218, 121),
(183, 121, 243),
(121, 243, 147),
(243, 121, 130),
(121, 166, 243),
(201, 243, 121),
(243, 121, 237),
(121, 243, 213),
(243, 178, 121),
(142, 121, 243),
(135, 243, 121),
(243, 121, 171),
(121, 206, 243),
(242, 243, 121),
(208, 121, 243),
(121, 243, 173),
(243, 137, 121),
(121, 141, 243),
(176, 243, 121),
(243, 121, 212),
(121, 243, 238),
(243, 203, 121),
(167, 121, 243),
(121, 243, 132),
(243, 121, 146),
(121, 181, 243),
(217, 243, 121),
(233, 121, 243),
(121, 243, 198),
(243, 162, 121),
(127, 121, 243),
(151, 243, 121),
(243, 121, 186),
(121, 222, 243),
(243, 228, 121),
(193, 121, 243),
(121, 243, 157),
(243, 122, 121),
(121, 156, 243),
(192, 243, 121),
(243, 121, 227),
(121, 243, 223),
(243, 187, 121),
(152, 121, 243),
(126, 243, 121),
(243, 121, 161),
(121, 197, 243),
(232, 243, 121),
(218, 121, 243),
(121, 243, 182),
(243, 147, 121),
(121, 131, 243),
(166, 243, 121),
(243, 121, 202),
(121, 237, 243),
(243, 212, 121),
(177, 121, 243),
(121, 243, 142),
(243, 121, 136),
(121, 172, 243),
(207, 243, 121),
(243, 121, 243),
(121, 243, 207),
(243, 172, 121),
(136, 121, 243),
(141, 243, 121),
(243, 121, 177),
)

rgbcolor=[]
for pc in pcolors:
  rgbcolor.append((0xFF<<24)+(pc[0]<<16)+(pc[1]<<8)+pc[2])
#  for will temporary
#  rgbcolor.append((0xA0<<24)+(pc[0]<<16)+(pc[1]<<8)+pc[2])

def recolor_cy ( np.ndarray[np.uint32_t, ndim=2] cutout, np.ndarray[np.uint32_t, ndim=2] imagemap ):
  """Annotation recoloring function."""

  cdef int i
  cdef int j
  for j in range ( cutout.shape[0] ):
    for i in range ( cutout.shape[1] ):
      if cutout[j,i]!=0:
        imagemap[j,i] = rgbcolor[cutout[j,i]%217]


#################  Tight cutout function ##################

def assignVoxels_cy ( np.ndarray[np.uint32_t, ndim=2] voxarray, np.ndarray[np.uint32_t, ndim=3] cutout, int annoid, int xmin, int ymin, int zmin):
  """Set the voxels specified in voxarray to annoid in the cutout data"""

  cdef int a
  cdef int b
  cdef int c
  for (a,b,c) in voxarray:
    cutout[c-zmin,b-ymin,a-xmin] = annoid 


#################  Loop  for uploading voxels function ##################

def cubeLocs_cy ( np.ndarray[np.uint32_t, ndim=2] locations, cubedim ):

  cdef int i

  cubelocs = np.zeros ( [len(locations),4], dtype=np.uint32 )

  #  construct a list of the voxels in each cube using arrays
  for i in range(len(locations)):
    loc = locations[i]
    cubeno = loc[0]/cubedim[0], loc[1]/cubedim[1], loc[2]/cubedim[2]
#    cubekey = zindex.XYZMorton(cubeno)
    cubekey = ocplib.XYZMorton(cubeno)
    cubelocs[i]=[cubekey,loc[0],loc[1],loc[2]]

  return cubelocs



####  RB? Maybe these need to go elsewhere?


cdef int getAnnValue ( int value00, int value01, int value10, int value11 ):
  """Determine the annotation value at the next level of the hierarchy from a 2x2"""

  # The following block of code places the majority annotation into value
  # start with 00
  cdef int value = value00

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


def addDataToZSliceStack_cy ( cube, output, offset ):
    """Add the contribution of the input data to the next level at the given offset in the output cube"""

    for z in range (cube.data.shape[0]):
      for y in range (cube.data.shape[1]/2):
        for x in range (cube.data.shape[2]/2):
           
            value = getAnnValue (cube.data[z,y*2,x*2],cube.data[z,y*2,x*2+1],cube.data[z,y*2+1,x*2],cube.data[z,y*2+1,x*2+1])
            output [ z+offset[2], y+offset[1], x+offset[0] ] = value

def addDataToIsotropicStack_cy ( cube, output, offset ):
    """Add the contribution of the input data to the next level at the given offset in the output cube"""

    for z in range (cube.data.shape[0]/2):
      for y in range (cube.data.shape[1]/2):
        for x in range (cube.data.shape[2]/2):
  
            # not perfect take a value from either slice.  Not a majority over all.
            # this whole rooutine getAnnValue needs to be replaced.
            value = getAnnValue (cube.data[z*2,y*2,x*2],cube.data[z*2,y*2,x*2+1],cube.data[z*2,y*2+1,x*2],cube.data[z*2,y*2+1,x*2+1])          
            if value == 0:
              value = getAnnValue (cube.data[z*2+1,y*2,x*2],cube.data[z*2+1,y*2,x*2+1],cube.data[z*2+1,y*2+1,x*2],cube.data[z*2+1,y*2+1,x*2+1])          
  
            output [ z+offset[2], y+offset[1], x+offset[0] ] = value



def zoomData_cy ( np.ndarray[np.uint32_t, ndim=3] olddata, np.ndarray[np.uint32_t, ndim=3] newdata, int factor ):
    """Add the contribution of the input data to the next level at the given offset in the output cube"""

    cdef int z
    cdef int y
    cdef int x
    for z in range (newdata.shape[0]):
      for y in range (newdata.shape[1]):
        for x in range (newdata.shape[2]):
          newdata[z,y,x] = olddata[z,y/(2**factor),x/(2**factor)]

#######################   Annotate -- list processing optimized ##########################

def mergeCube_cy ( np.ndarray[DTYPE_t, ndim=3] data, unsigned int newid, unsigned int oldid):
    """Relabel voxels in cuve from oldid to newid"""
    cdef int z
    cdef int y
    cdef int x
    for z in range (data.shape[0]):
      for y in range (data.shape[1]):
        for x in range (data.shape[2]):
          if data[z,y,x]== oldid:
            data[z,y,x]=newid
	      




  
