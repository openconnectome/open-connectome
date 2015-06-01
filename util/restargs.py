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

#
#  Check the formatting of RESTful arguments.
#  Shared by cutout and annotation services.
#

import sys
import re
import os
import numpy as np


#
# General rest argument processing exception
#
class RESTArgsError(Exception):
  """Illegal arguments"""
  def __init__(self, value):
    self.value = value
  def __str__(self):
    return repr(self.value)


class BrainRestArgs:

  # Accessors to get corner and dimensions
  def getCorner (self):
    return self.corner

  def getDim (self):
   return self.dim
   
  def getResolution (self):
   return self.resolution

  def getFilter ( self ):
    return self.filterlist

  def getWindow ( self ):
    return self.window
  
  def getTimeRange ( self ):
    return self.time
  
  def getZScaling ( self ):
    return self.zscaling


  def cutoutArgs ( self, imageargs, datasetcfg, channels=None ):
    """Process REST arguments for an cutout plane request"""

    try:
      # argument of format /resolution/x1,x2/y1,y2/z1,z2/rest(can include t1,t2)/
      #m = re.match("([0-9]+)/([0-9]+),([0-9]+)/([0-9]+),([0-9]+)/([0-9]+),([0-9]+)([/]*[\w+]*[/]*[\d,+]*[/]*)$", imageargs)
      m = re.match("([0-9]+)/([0-9]+),([0-9]+)/([0-9]+),([0-9]+)/([0-9]+),([0-9]+)([/]*[\d+,]*[\w+]*[/]*[\d,+]*[/]*)?$", imageargs)
      [self.resolution, x1, x2, y1, y2, z1, z2] = [int(i) for i in m.groups()[:-1]]
      rest = m.groups()[-1]

    except Exception, e:
      raise RESTArgsError("Incorrect cutout arguments {}. {}".format(imageargs, e))

    if self.resolution not in datasetcfg.getResolutions():
      raise RESTArgsError("Illegal scaling level {}".format(imageargs))

    # Convert cutout into 0 base in all dimensions
    (xoffset,yoffset,zoffset) = datasetcfg.getOffset()[self.resolution]

    (x1, x2) = (x1-xoffset, x2-xoffset)
    (y1, y2) = (y1-yoffset, y2-yoffset)
    (z1, z2) = (z1-zoffset, z2-zoffset)
    self.corner = [x1, y1, z1]
    self.dim = [x2-x1, y2-y1, z2-z1]

    # time arguments
    self.time = [0,0]
    result = re.match("/(\d+),(\d+)/", rest)
    if result is not None:
      self.time = [int(i) for i in result.groups()]


    # Check arguments for legal values
    try:
      if not ( datasetcfg.checkCube(self.resolution, self.corner, self.dim, self.time) ):
        raise RESTArgsError ( "Illegal range. Image size: {} at offset {}".format(str(datasetcfg.imageSize(self.resolution)),str(datasetcfg.getOffset()[self.resolution])))
    except Exception, e:
      # RBTODO make this error better.  How to print good information about e?
      #  it only prints 3, not KeyError 3, whereas print e in the debugger gives good info
      raise RESTArgsError ( "Illegal arguments to cutout. Check cube failed {}".format(e))

    # list of identifiers to keep
    result = re.match ("/filter/([\d/,]+)/", rest)
    if result != None:
      self.filterlist = np.array(result.group(1).split(','),dtype=np.uint32)
    else:
      self.filterlist = None
    
    
    # See if it is an isotropic cutout request
    self.zscaling = None
    result = re.match ("/iso/",rest)
    if result is not None:
      self.zscaling = 'isotropic'
     
    # See if it is an integral cutout request
    result = re.match ("/neariso/",rest)
    if result is not None:
      self.zscaling = 'nearisotropic'


# Unbound functions  not part of the class object

def voxel ( imageargs, datasetcfg ):
  """Process REST arguments for a single point"""

  try:
    [ resstr, xstr, ystr, zstr, rest ]  = imageargs.split('/',4)
  except:
    raise RESTArgsError ("Bad arguments to voxel %s" % imageargs)

  # expecting an argument of the form /resolution/x/y1,y2/z1,z2/
  # Check that the arguments are well formatted
  if not re.match ('[0-9]+$', resstr) or\
     not re.match ('[0-9]+$', xstr) or\
     not re.match ('[0-9]+$', ystr) or\
     not re.match ('[0-9]+$', zstr):
    raise RESTArgsError ("Non-numeric range argument %s" % imageargs)

  resolution = int(resstr)
  x = int(xstr)
  y = int(ystr)
  z = int(zstr)

  # Check arguments for legal values
  if not ( datasetcfg.checkCube ( resolution, [x,y,z], [x+1,y+1,z+1] )):
    raise RESTArgsError ( "Illegal range. Image size: {} at offset {}".format(str(datasetcfg.imageSize(self._resolution)),str(datasetcfg.offset[self._resolution])))

  return (resolution, [ x,y,z ])


#
#  Process cutout arguments
#
def conflictOption  ( imageargs ):
  """Parse the conflict resolution string"""

  restargs = imageargs.split('/')
  if len (restargs) > 0:
    if restargs[0] == 'preserve':
      return 'P'
    elif restargs[0] == 'except':
      return 'E'
    else:
      return 'O'

#                                                                                
#  Process annotation id for queries                                             
#                                                                               \
                                                                                 
def annotationId ( webargs, datasetcfg ):
  """Process REST arguments for a single"""

  rangeargs = webargs.split('/')
  # PYTODO: check validity of annotation id                                      
  return int(rangeargs[0])

