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

import math
from operator import add, sub, mul, div, mod
from django.http import Http404
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from ndproj.ndobject import NDObject
from ndlib.ndtype import *
from nduser.models import Dataset
from webservices.ndwserror import NDWSError
from ndproj.vector3d import Vector3D
import logging
logger=logging.getLogger("neurodata")

class NDDataset(NDObject):
  """Configuration for a dataset"""

  def __init__ (self, ds):
    """Construct a db configuration from the dataset parameters""" 
    
    self._ds = ds

    self._resolutions = []
    self._cubedim = {}
    self._supercubedim = {}
    self._image_size = {}
    self._offset = {}
    self._voxelres = {}
    self._scale = {}
    self._limit = {}
    self._scalinglevels = self._ds.scalinglevels
    # nearisotropic service for Stephan
    self.nearisoscaledown = {}
    self.neariso_voxelres = {}
    self.neariso_imagesz = {}
    self.neariso_offset = {}

    for i in range (self._ds.scalinglevels+1):
      """Populate the dictionaries"""

      # add this level to the resolutions
      self._resolutions.append( i )

      # set the image size
      #  the scaled down image rounded up to the nearest cube
      xpixels = ((self._ds.ximagesize-1)/2**i)+1
      ypixels = ((self._ds.yimagesize-1)/2**i)+1
      if self._ds.scalingoption == ZSLICES:
        zpixels = self._ds.zimagesize
      else:
        zpixels = ((self._ds.zimagesize-1)/2**i)+1
      self._image_size[i] = [ xpixels, ypixels, zpixels ]

      # set the offset
      xoffseti = 0 if self._ds.xoffset==0 else ((self._ds.xoffset)/2**i)
      yoffseti = 0 if self._ds.yoffset==0 else ((self._ds.yoffset)/2**i)
      if self._ds.zoffset == 0:
        zoffseti = 0
      else:
        if self._ds.scalingoption == ZSLICES:
          zoffseti = self._ds.zoffset
        else:
         zoffseti = ((self._ds.zoffset)/2**i)

      self._offset[i] = [ xoffseti, yoffseti, zoffseti ]

      # set the voxelresolution
      xvoxelresi = self._ds.xvoxelres*float(2**i)
      yvoxelresi = self._ds.yvoxelres*float(2**i)
      zvoxelresi = self._ds.zvoxelres if self._ds.scalingoption == ZSLICES else self._ds.zvoxelres*float(2**i)

      self._voxelres[i] = [ xvoxelresi, yvoxelresi, zvoxelresi ]
      self._scale[i] = { 'xy':xvoxelresi/yvoxelresi , 'yz':zvoxelresi/xvoxelresi, 'xz':zvoxelresi/yvoxelresi }
      
      # choose the cubedim as a function of the zscale
      if self._ds.scalingoption == ZSLICES:
        if float(self._ds.zvoxelres/self._ds.xvoxelres)/(2**i) >  0.5:
          self._cubedim[i] = [512, 512, 64]
        else: 
          self._cubedim[i] = [64, 64, 64]

        # Make an exception for bock11 data -- just an inconsistency in original ingest
        if self._ds.ximagesize == 135424 and i == 5:
          self._cubedim[i] = [512, 512, 64]
      else:
        self._cubedim[i] = [64, 64, 64]
      
      self._supercubedim[i] = map(mul, self._cubedim[i], SUPERCUBESIZE)

      if self._scale[i]['xz'] < 1.0:
        scalepixels = 1/self._scale[i]['xz']
        if ((math.ceil(scalepixels)-scalepixels)/scalepixels) <= ((scalepixels-math.floor(scalepixels))/scalepixels):
          self.nearisoscaledown[i] = int(math.ceil(scalepixels))
        else:
          self.nearisoscaledown[i] = int(math.floor(scalepixels))
      else:
        self.nearisoscaledown[i] = int(1)
      
      self.neariso_imagesz[i] = [ xpixels, ypixels, zpixels/self.nearisoscaledown[i] ]
      self.neariso_voxelres[i] = [ xvoxelresi, yvoxelresi, zvoxelresi*self.nearisoscaledown[i] ]
      self.neariso_offset[i] = [ float(xoffseti), float(yoffseti), float(zoffseti)/self.nearisoscaledown[i] ]
  
  def create(self):
    try:
      self._ds.save()
    except Exception as e:
      raise

  def delete(self):
    try:
      self._ds.delete()
    except Exception as e:
      raise

  @classmethod
  def fromName(cls, dataset_name):
    try:
      ds = Dataset.objects.get(dataset_name = dataset_name)
      return cls(ds)
    except Dataset.DoesNotExist as e:
      logger.error("Dataset {} does not exist. {}".format(dataset_name, e))
      raise Dataset.DoesNotExist
      # raise NDWSError("Dataset {} does not exist".format(dataset_name))

  @classmethod
  def fromJson(cls, dataset):
    ds = Dataset(**cls.deserialize(dataset))
    return cls(ds)
  
  @staticmethod
  def all_list():
    return Dataset.objects.all()

  @staticmethod
  def public_list():
    datasets  = Dataset.objects.filter(public = PUBLIC_TRUE)
    return [ds.dataset_name for ds in datasets]
    
  @staticmethod
  def user_list(user_id):
    return Dataset.objects.filter(user_id=user_id)
  
  def serialize(self):
    return NDObject.serialize(self._ds)

  @property
  def dataset_name(self):
    return self._ds.dataset_name
  
  @property
  def user_id(self):
    return self._ds.user_id

  @user_id.setter
  def user_id(self, value):
    self._ds.user_id = value

  @property
  def dataset_description(self):
    return self._ds.dataset_description

  @property
  def resolutions(self):
    return self._resolutions
  
  @property
  def public(self):
    return self._ds.public
  
  # RB use dataset_dim
  @property
  def image_size(self):
    return self._image_size
  
  @property
  def offset(self):
    return self._offset

  @property
  def voxelres(self):
    return self._voxelres
  
  @property
  def cubedim(self):
    return self._cubedim
  
  @property
  def supercubedim(self):
    return self._supercubedim

  def dataset_dim(self, res):
    return self._image_size[res]

  def get_imagesize(self, res):
    # return Vector3D(self._image_size[res][::-1])
    return self._image_size[res]
  
  def get_offset(self, res):
    # return Vector3D(self._offset[res])
    return self._offset[res]
  
  def get_voxelres(self, res):
    # return Vector3D(self._voxelres[res])
    return self._voxelres[res]
  
  def get_scale(self, res):
    return self._scale[res]

  def get_cubedim(self, res):
    # return Vector3D(self._cubedim[res])
    return self._cubedim[res]
  
  def get_supercubedim(self, res):
    # return Vector3D(self._supercubedim[res])
    return self._supercubedim[res]
  
  def cube_limit(self, res):
    return None

  def get_supercube_limit(self, res):
    # return Vector3D(map(add, map(div, map(sub, self._image_size[res][::-1], [1]*3), self._supercubedim[res]), [1]*3))
    return map(add, map(div, map(sub, self._image_size[res][::-1], [1]*3), self._supercubedim[res]), [1]*3)
  
  @property
  def scalingoption(self):
    return self._ds.scalingoption

  @property
  def scalinglevels(self):
    return self._scalinglevels

  @property
  def scale(self):
    return self._scale
  
  @property
  def supercube_size(self):
    return SUPERCUBESIZE
  
  def checkCube (self, resolution, corner, dim, neariso=False):
    """Return true if the specified range of values is inside the cube"""

    [xstart, ystart, zstart ] = corner

    [xend, yend, zend] = map(add, corner, dim) 
    
    if neariso:
      if ( ( xstart >= 0 ) and ( xstart < xend) and ( xend <= self.neariso_imagesz[resolution][0]) and\
          ( ystart >= 0 ) and ( ystart < yend) and ( yend <= self.neariso_imagesz[resolution][1]) and\
          ( zstart >= 0 ) and ( zstart < zend) and ( zend <= self.neariso_imagesz[resolution][2])):
        return True
    else:
      if ( ( xstart >= 0 ) and ( xstart < xend) and ( xend <= self._image_size[resolution][0]) and\
          ( ystart >= 0 ) and ( ystart < yend) and ( yend <= self._image_size[resolution][1]) and\
          ( zstart >= 0 ) and ( zstart < zend) and ( zend <= self._image_size[resolution][2])): 
        return True
      else:
        return False
