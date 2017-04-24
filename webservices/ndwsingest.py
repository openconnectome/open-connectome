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

import os
import urllib2
from contextlib import closing
import numpy as np
from PIL import Image
from operator import sub, add, mul, div
import boto3
import blosc
import botocore
import django
django.setup()
from django.conf import settings
from spdb.ndcube.cube import Cube
from ndlib.ndtype import *
import webservices.ndwsrest as ndwsrest
from spdb.spatialdb import SpatialDB
from ndproj.ndprojdb import NDProjectsDB
from ndlib.ndctypelib import XYZMorton
from spdb.ndkvio.s3io import S3IO
from ndingest.nddynamo.cuboidindexdb import CuboidIndexDB
from webservices.ndwserror import NDWSError
from ndingest.settings.settings import Settings
ndsettings = Settings.load()
import logging
logger = logging.getLogger("neurodata")

class IngestData:

  def __init__(self, token, channel, resolution, data_url, file_format, file_type):
    
    self.token = token
    self.channel = channel
    self.resolution = resolution
    self.data_url = data_url
    self.path = settings.TEMP_INGEST_PATH
    # identify which type of data this is
    self.file_format = file_format
    # set the file_type
    self.file_type = file_type

  def ingest(self):
    """Identify the data style and ingest accordingly"""
    
    if self.file_format in ['SLICE']:
      self.ingestImageStack()
    elif self.file_format in ['CATMAID']:
      self.ingestCatmaidStack()
    else:
      logger.error("Format {} not supported.".format(self.file_format))
      raise NDWSError("Format {} not supported.".format(self.file_format))

  def fetchData(self, slice_list, time_value):
    """Fetch the next set of data from a remote source and place it locally"""
    
    # iterating over the slice number list
    for slice_number in slice_list:
      # generating the url based on some parameters
      if time_value is not None:
        # key = '{}/{}/{}/{}/{}'.format(self.data_url, self.token, self.channel, time_value, self.generateFileName(slice_number), ondisk=False)
        key = '{}/{}/{}/{}'.format(self.data_url, self.token, self.channel, self.generateFileName(slice_number, ondisk=False))
      else:
        if self.data_url == '':
          key = '{}/{}/{}'.format(self.token, self.channel, self.generateFileName(slice_number, ondisk=False))
        else:
          key = '{}/{}/{}/{}'.format(self.data_url, self.token, self.channel, self.generateFileName(slice_number, ondisk=False))
      
      try:
        s3 = boto3.resource('s3', aws_access_key_id=ndsettings.AWS_ACCESS_KEY_ID, aws_secret_access_key=ndsettings.AWS_SECRET_ACCESS_KEY)
        s3.Object('neurodata-public', key).download_file(self.path+self.generateFileName(slice_number))
      except Exception as e:
        logger.warning("Image file not found {}. {}".format(self.generateFileName(slice_number) , e))


  def cleanData(self, slice_list):
    """Remove the slices at the local store"""

    for slice_number in slice_list:
      try:
        os.remove('{}{}'.format(self.path, self.generateFileName(slice_number)))
      except OSError, e:
        logger.warning("File {} not found. {}".format(self.generateFileName(slice_number), e))


  def generateFileName(self, slice_number, ondisk=True):
    """Generate a file name given the slice_number"""
    
    if ondisk:
      return '{}_{}_{:0>4}.{}'.format(self.token, self.channel, slice_number, self.file_type)
    else:
      return '{:0>4}.{}'.format(slice_number, self.file_type)


  def ingestImageStack(self):
    """Ingest a TIF image stack"""
    
    # Load a database
    with closing (NDProjectsDB()) as projdb:
      proj = projdb.loadToken(self.token)

    with closing (SpatialDB(proj)) as db:
      
      s3_io = S3IO(db)
      # cuboidindex_db = CuboidIndexDB(proj.project_name, endpoint_url=ndsettings.DYNAMO_ENDPOINT)
      
      ch = proj.getChannelObj(self.channel)
      # get the dataset configuration
      [ximagesz, yimagesz, zimagesz] = proj.datasetcfg.dataset_dim(self.resolution)
      [starttime, endtime] = ch.time_range
      [xcubedim, ycubedim, zcubedim] = cubedim = proj.datasetcfg.get_cubedim(self.resolution)
      [xsupercubedim, ysupercubedim, zsupercubedim] = supercubedim = proj.datasetcfg.get_supercubedim(self.resolution)
      [xoffset, yoffset, zoffset] = proj.datasetcfg.get_offset(self.resolution)
      
      if ch.channel_type in TIMESERIES_CHANNELS and (starttime == 0 and endtime == 0):
        logger.error("Timeseries Data cannot have timerange (0,0)")
        raise NDWSError("Timeseries Data cannot have timerange (0,0)")

      # Get a list of the files in the directories
      for timestamp in range(starttime, endtime):
        for slice_number in range (zoffset, zimagesz, zsupercubedim):
          slab = np.zeros([1, zsupercubedim, yimagesz, ximagesz ], dtype=ND_dtypetonp.get(ch.channel_datatype))
          # fetch 16 slices at a time
          if ch.channel_type in TIMESERIES_CHANNELS:
            time_value = timestamp
          else:
            time_value = None
          self.fetchData(range(slice_number, slice_number+zsupercubedim) if slice_number+zsupercubedim<=zimagesz else range(slice_number, zimagesz), time_value=time_value)
          for b in range(zsupercubedim):
            if (slice_number + b < zimagesz):
              try:
                # reading the raw data
                file_name = "{}{}".format(self.path, self.generateFileName(slice_number+b))
                # print "Open filename {}".format(file_name)
                logger.info("Open filename {}".format(file_name))
                
                if ch.channel_datatype in [UINT8, UINT16]:
                  try:
                    image_data = np.asarray(Image.open(file_name, 'r'))
                    slab[0,b,:,:] = image_data
                  except Exception as e:
                    slab[0,b,:,:] = np.zeros((yimagesz, ximagesz), dtype=ND_dtypetonp.get(ch.channel_datatype))
                    logger.warning("File corrupted. Cannot open file. {}".format(e))
                elif ch.channel_datatype in [UINT32]:
                  image_data = np.asarray(Image.open(file_name, 'r').convert('RGBA'))
                  slab[0,b,:,:] = np.left_shift(image_data[:,:,3], 24, dtype=np.uint32) | np.left_shift(image_data[:,:,2], 16, dtype=np.uint32) | np.left_shift(image_data[:,:,1], 8, dtype=np.uint32) | np.uint32(image_data[:,:,0])
                elif ch.channel_type in ANNOTATION_CHANNELS:
                  image_data = np.asarray(Image.open(file_name, 'r'))
                  slab[0,b,:,:] = image_data
                else:
                  logger.error("Cannot ingest this data yet")
                  raise NDWSError("Cannot ingest this data yet")
              except IOError, e:
                logger.warning("IOError {}.".format(e))
                slab[0,b,:,:] = np.zeros((yimagesz, ximagesz), dtype=ND_dtypetonp.get(ch.channel_datatype))
          
          for y in range ( 0, yimagesz+1, ysupercubedim ):
            for x in range ( 0, ximagesz+1, xsupercubedim ):

              # Getting a Cube id and ingesting the data one cube at a time
              zidx = XYZMorton ( [x/xsupercubedim, y/ysupercubedim, (slice_number-zoffset)/zsupercubedim] )
              cube = Cube.CubeFactory(supercubedim, ch.channel_type, ch.channel_datatype)
              cube.zeros()

              xmin,ymin = x,y
              xmax = min ( ximagesz, x+xsupercubedim )
              ymax = min ( yimagesz, y+ysupercubedim )
              zmin = 0
              zmax = min(slice_number+zsupercubedim, zimagesz+1)

              cube.data[0, 0:zmax-zmin,0:ymax-ymin,0:xmax-xmin] = slab[0, zmin:zmax, ymin:ymax, xmin:xmax]
              if cube.isNotZeros():
                # cuboidindex_db.putItem(ch.channel_name, self.resolution, x, y, slice_number, ch.time_range[0])
                # s3_io.putCube(ch, self.resolution, zidx, blosc.pack_array(cube.data))
                s3_io.putCube(ch, timestamp, zidx, self.resolution, blosc.pack_array(cube.data), neariso=False)
                
          # clean up the slices fetched
          self.cleanData(range(slice_number, slice_number+zsupercubedim) if slice_number + zsupercubedim<=zimagesz else range(slice_number, zimagesz))
