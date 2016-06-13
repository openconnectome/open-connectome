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

import sys
import os
import urllib
import urllib2
from contextlib import closing
import numpy as np
from PIL import Image
from operator import sub, add, mul, div
import boto3
import blosc

import django
django.setup()
from django.conf import settings

from cube import Cube
from ndtype import TIMESERIES_CHANNELS, IMAGE_CHANNELS, ANNOTATION_CHANNELS, ND_dtypetonp, UINT8, UINT16, UINT32, SUPERCUBESIZE
import ndwsrest
import spatialdb
import ndproj
import ndlib
from s3util import generateS3BucketName, generateS3Key
import s3io

from ndwserror import NDWSError
import logging
logger=logging.getLogger("neurodata")

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
    try:
      self.client = boto3.client('s3', aws_access_key_id=settings.AWS_ACCESS_KEY_ID, aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)
    except Exception, e:
      logger.error("Cannot connect to S3 backend")
      raise NDWSError("Cannot connect to S3 backend")

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
        key = '{}/{}/{}/{}'.format(self.token, self.channel, time_value, self.generateFileName(slice_number), ondisk=False)
      else:
        key = '{}/{}/{}'.format(self.token, self.channel, self.generateFileName(slice_number, ondisk=False))
      # making the request
      try:
        self.client.download_file(Bucket='neurodata-public', Key=key, Filename=self.path+self.generateFileName(slice_number))
      except botocore.exceptions.ClientError as e:
        continue

        # req = urllib2.Request(url)
        # resp = urllib2.urlopen(req, timeout=15)
      # except urllib2.URLError, e:
        # logger.warning("Failed to fetch url {}. File does not exist. {}".format(url, e))
        # continue
      
      # writing the file to scratch
      # try:
        # image_file = open('{}'.format(self.path+self.generateFileName(slice_number)),'w')
        # image_file.write(resp.read())
      # except IOError, e:
        # logger.warning("IOError. Could not open file {}. {}".format(self.path+self.generateFileName(slice_number), e))
      # finally:
        # image_file.close()


  def fetchCatmaidData(self, slice_list, xtile, ytile):
    """Fetch the next set of data from a remote source and place it locally"""
    
    # iterating over the slice number list
    for slice_number in slice_list:
      # generating the url based on some parameters
      url = '{}/{}/{}/{}/{}'.format(self.data_url, self.channel, slice_number, self.resolution, self.generateCatmaidFileName(slice_number, xtile, ytile, ondisk=False))
      
      # making the request
      try:
        req = urllib2.Request(url)
        resp = urllib2.urlopen(req, timeout=15)
      except urllib2.URLError, e:
        logger.warning("Failed to fetch url {}. File does not exist. {}".format(url, e))
        continue
        
      # writing the file to scratch
      try:
        catmaid_file = open('{}'.format(self.path+self.generateCatmaidFileName(slice_number, xtile, ytile)),'w')
        catmaid_file.write(resp.read())
      except IOError, e:
        logger.warning("IOError. Could not open file {}. {}".format(self.path+self.generateCatmaidFileName(slice_number, xtile, ytile), e))
      finally:
        catmaid_file.close()

  def cleanCatmaidData(self, slice_list, xtile, ytile):
    """Remove the slices at the local store"""

    for slice_number in slice_list:
      try:
        os.remove('{}{}'.format(self.path, self.generateCatmaidFileName(slice_number, xtile, ytile)))
      except OSError, e:
        logger.warning("File {} not found. {}".format(self.generateCatmaidFileName(slice_number, xtile, ytile), e))
 
  def cleanData(self, slice_list):
    """Remove the slices at the local store"""

    for slice_number in slice_list:
      try:
        os.remove('{}{}'.format(self.path, self.generateFileName(slice_number)))
      except OSError, e:
        logger.warning("File {} not found. {}".format(self.generateFileName(slice_number), e))

  def generateCatmaidFileName(self, slice_number, xtile, ytile, ondisk=True):
    """Generate a file name given the slice_number"""
    
    if ondisk:
      return '{}_{}_{}.{}'.format(slice_number, ytile, xtile, self.file_type)
    else:
      return '{}_{}.{}'.format(ytile, xtile, self.file_type)

  def generateFileName(self, slice_number, ondisk=True):
    """Generate a file name given the slice_number"""
    
    if ondisk:
      return '{}_{:0>4}.{}'.format(self.channel, slice_number, self.file_type)
    else:
      return '{:0>4}.{}'.format(slice_number, self.file_type)

  def createS3Bucket(self, project_name):
    """Create s s3 bucket"""
    
    # Creating a resource, similar to a client
    s3 = boto3.resource('s3', aws_access_key_id=settings.AWS_ACCESS_KEY_ID, aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)
    bucket = s3.Bucket(generateS3BucketName(project_name))
    
    # Creating a bucket
    try:
      logger.warning("Creating bucket {}.".format(generateS3BucketName(project_name)))
      bucket.create()
    except Exception as e:
      logger.error("There was an error in creating the bucket {}.".format(generateS3BucketName(project_name)))
      raise NDWSError("There was an error in creating the bucket {}.".format(generateS3BucketName(project_name)))


  def ingestCatmaidStack(self):
    """Ingest a CATMAID tile stack"""
    
    tilesz = 1024
    # Load a database
    proj = ndproj.NDProjectsDB().loadToken(self.token)
    db = spatialdb.SpatialDB(proj)
    s3db = s3io.S3IO(db)
    ch = proj.getChannelObj(self.channel)
    
    # creating bucket
    self.createS3Bucket(proj.getProjectName())

    # get the dataset configuration
    [[ximagesz, yimagesz, zimagesz],(starttime,endtime)] = proj.datasetcfg.imageSize(self.resolution)
    [xcubedim,ycubedim,zcubedim] = cubedim = proj.datasetcfg.getCubeDims()[self.resolution]
    [xoffset, yoffset, zoffset] = proj.datasetcfg.getOffset()[self.resolution]
    [xsupercubedim, ysupercubedim, zsupercubedim] = supercubedim = map(mul, cubedim, SUPERCUBESIZE)

    if ch.getChannelType() in TIMESERIES_CHANNELS:
      logger.error("Timeseries data not supported for CATMAID data. Error in {}".format(self.token))
      raise NDWSError("Timeseries data not supported for CATMAID data. Error in {}".format(self.token))
    
    num_xtiles = ximagesz / tilesz
    num_ytiles = yimagesz / tilesz
      
    # over all the tiles in the slice
    for ytile in range(0, num_ytiles, 1):
      for xtile in range(0, num_xtiles, 1):
          
        # Get a list of the files in the directories
        for slice_number in range (zoffset, zimagesz, zsupercubedim):
          # empty slab
          slab = np.zeros([zsupercubedim, tilesz, tilesz], dtype=ND_dtypetonp.get(ch.getDataType()))
          
          # prefetch data
          self.fetchCatmaidData(range(slice_number, slice_number+zsupercubedim) if slice_number+zsupercubedim<=zimagesz else range(slice_number, zimagesz), xtile, ytile)
          
          for b in range(zsupercubedim):
            if (slice_number + b < zimagesz):
              try:
                # reading the raw data
                file_name = "{}{}".format(self.path, self.generateCatmaidFileName(slice_number+b, xtile, ytile))
                logger.info("Open filename {}".format(file_name))
                # print "Open filename {}".format(file_name)
                slab[b,:,:] = np.asarray(Image.open(file_name, 'r'))[:,:,0]
              except IOError, e:
                logger.warning("IOError {}.".format(e))
                slab[b,:,:] = np.zeros((tilesz, tilesz), dtype=ND_dtypetonp.get(ch.getDataType()))

          for y in range (ytile*tilesz, (ytile+1)*tilesz, ysupercubedim):
            for x in range (xtile*tilesz, (xtile+1)*tilesz, xsupercubedim):

              # Getting a Cube id and ingesting the data one cube at a time
              zidx = ndlib.XYZMorton ( [(x-xoffset)/xsupercubedim, (y-yoffset)/ysupercubedim, (slice_number-zoffset)/zsupercubedim] )
              cube = Cube.getCube(supercubedim, ch.getChannelType(), ch.getDataType())
              cube.zeros()

              xmin = x % tilesz
              ymin = y % tilesz
              xmax = ( min(ximagesz-xoffset-1, x+xsupercubedim-1) % tilesz ) + 1
              ymax = ( min(yimagesz-yoffset-1, y+ysupercubedim-1) % tilesz ) + 1
              zmin = 0
              zmax = min(slice_number-zoffset+zsupercubedim, zimagesz+1)

              cube.data[0:zmax-zmin,0:ymax-ymin,0:xmax-xmin] = slab[zmin:zmax, ymin:ymax, xmin:xmax]
              if cube.isNotZeros():
                s3db.putCube(ch, self.resolution, zidx, cube.toBlosc())
      
          # clean up the slices fetched
          self.cleanCatmaidData(range(slice_number,slice_number+zsupercubedim) if slice_number+zsupercubedim<=zimagesz else range(slice_number,zimagesz), xtile, ytile)

  def ingestImageStack(self):
    """Ingest a TIF image stack"""

    # Load a database
    with closing (ndproj.NDProjectsDB()) as projdb:
      proj = projdb.loadToken(self.token)

    with closing (spatialdb.SpatialDB(proj)) as db:

      ch = proj.getChannelObj(self.channel)
      # get the dataset configuration
      [[ximagesz, yimagesz, zimagesz],(starttime,endtime)] = proj.datasetcfg.imageSize(self.resolution)
      [xcubedim, ycubedim, zcubedim] = cubedim = proj.datasetcfg.getCubeDims()[self.resolution]
      [xoffset, yoffset, zoffset] = proj.datasetcfg.getOffset()[self.resolution]
      
      if ch.getChannelType() in TIMESERIES_CHANNELS and (starttime == 0 and endtime == 0):
        logger.error("Timeseries Data cannot have timerange (0,0)")
        raise NDWSError("Timeseries Data cannot have timerange (0,0)")

      # Get a list of the files in the directories
      for timestamp in range(starttime, endtime+1):
        for slice_number in range (zoffset, zimagesz, zcubedim):
          slab = np.zeros([zcubedim, yimagesz, ximagesz ], dtype=ND_dtypetonp.get(ch.getDataType()))
          # fetch 16 slices at a time
          if ch.getChannelType() in TIMESERIES_CHANNELS:
            time_value = timestamp
          else:
            time_value = None
          self.fetchData(range(slice_number,slice_number+zcubedim) if slice_number+zcubedim<=zimagesz else range(slice_number,zimagesz), time_value=time_value)
          for b in range(zcubedim):
            if (slice_number + b < zimagesz):
              try:
                # reading the raw data
                file_name = "{}{}".format(self.path, self.generateFileName(slice_number+b))
                print "Open filename {}".format(file_name)
                logger.info("Open filename {}".format(file_name))
                
                if ch.getDataType() in [UINT8, UINT16] and ch.getChannelType() in IMAGE_CHANNELS:
                  image_data = np.asarray(Image.open(file_name, 'r'))
                  slab[b,:,:] = image_data
                elif ch.getDataType() in [UINT32] and ch.getChannelType() in IMAGE_CHANNELS:
                  image_data = np.asarray(Image.open(file_name, 'r').convert('RGBA'))
                  slab[b,:,:] = np.left_shift(image_data[:,:,3], 24, dtype=np.uint32) | np.left_shift(image_data[:,:,2], 16, dtype=np.uint32) | np.left_shift(image_data[:,:,1], 8, dtype=np.uint32) | np.uint32(image_data[:,:,0])
                elif ch.getChannelType() in ANNOTATION_CHANNELS:
                  image_data = np.asarray(Image.open(file_name, 'r'))
                  slab[b,:,:] = image_data
                else:
                  logger.error("Cannot ingest this data yet")
                  raise NDWSError("Cannot ingest this data yet")
              except IOError, e:
                logger.warning("IOError {}.".format(e))
                slab[b,:,:] = np.zeros((yimagesz, ximagesz), dtype=np.uint32)
          
          for y in range ( 0, yimagesz+1, ycubedim ):
            for x in range ( 0, ximagesz+1, xcubedim ):

              # Getting a Cube id and ingesting the data one cube at a time
              zidx = ndlib.XYZMorton ( [x/xcubedim, y/ycubedim, (slice_number-zoffset)/zcubedim] )
              cube = Cube.getCube(cubedim, ch.getChannelType(), ch.getDataType())
              cube.zeros()

              xmin,ymin = x,y
              xmax = min ( ximagesz, x+xcubedim )
              ymax = min ( yimagesz, y+ycubedim )
              zmin = 0
              zmax = min(slice_number+zcubedim, zimagesz+1)

              cube.data[0:zmax-zmin,0:ymax-ymin,0:xmax-xmin] = slab[zmin:zmax, ymin:ymax, xmin:xmax]
              if cube.isNotZeros():
                if ch.getChannelType() in IMAGE_CHANNELS:
                  db.putCube(ch, zidx, self.resolution, cube, update=True)
                elif ch.getChannelType() in TIMESERIES_CHANNELS:
                  db.putTimeCube(ch, zidx, timestamp, self.resolution, cube, update=True)
                elif ch.getChannelType() in ANNOTATION_CHANNELS:
                  corner = map(sub, [x,y,slice_number], [xoffset,yoffset,zoffset])
                  db.annotateDense(ch, corner, self.resolution, cube.data, 'O')
                else:
                  logger.error("Channel type {} not supported".format(ch.getChannelType()))
                  raise NDWSError("Channel type {} not supported".format(ch.getChannelType()))
          
          # clean up the slices fetched
          self.cleanData(range(slice_number,slice_number+zcubedim) if slice_number+zcubedim<=zimagesz else range(slice_number,zimagesz))
