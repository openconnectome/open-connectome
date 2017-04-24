# -*- coding: utf-8 -*-

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

from __future__ import absolute_import
import os
import sys
import json
from contextlib import closing
import argparse
import csv
import blosc
from operator import div
import numpy as np
from PIL import Image
sys.path.append(os.path.abspath('../django'))
import ND.settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'ND.settings'
from ndingest.settings.settings import Settings
ndingest_settings = Settings.load()
import django
django.setup()
from django.forms.models import model_to_dict
from django.conf import settings
from ndlib.ndctypelib import *
from ndcube.cube import Cube
from ndlib.ndtype import *
from ndlib.restutil import *
from ndproj.nddataset import NDDataset
from ndproj.ndchannel import NDChannel
from ndproj.ndproject import NDProject
from ndproj.ndtoken import NDToken
from ndingest.nddynamo.cuboidindexdb import CuboidIndexDB
from ndingest.ndbucket.cuboidbucket import CuboidBucket
from scripts_helper import *
from ingest.core.config import Configuration
import logging
HOST_NAME = 'localhost:8080'



class AwsInterface:

  def __init__(self, token_name, host_name=HOST_NAME):
    """Create the bucket and intialize values"""
  
    # configuring the logger based on the dataset we are uploading
    self.logger = logging.getLogger(token_name)
    self.logger.setLevel(logging.INFO)
    fh = logging.FileHandler('{}.log'.format(token_name))
    self.logger.addHandler(fh)
    # setting up the project metadata
    self.info_interface = InfoInterface(host_name, token_name)
    # creating the resource interface to the remote server
    # self.resource_interface = ResourceInterface(self.info_interface.dataset_name, self.info_interface.project_name, host_name, logger=self.logger)
    # self.proj = self.resource_interface.getProject()
    # create the s3 I/O and index objects
    self.cuboidindex_db = CuboidIndexDB(self.info_interface.project_name)
    self.cuboid_bucket = CuboidBucket(self.info_interface.project_name)
  

  
  # def setupNewProject(self):
    # """Setup a new project if it does not exist"""
    
    # self.resource_interface.createDataset()
    # self.resource_interface.createProject()
    # self.resource_interface.createToken()
  

  def uploadExistingProject(self, channel_name, resolution, start_values, neariso=False):
    """Upload an existing project to S3"""
      
    self.setupNewProject()
    db = SpatialDB(self.proj)
    # checking for channels
    if channel_name is None:
      channel_list = None
    else:
      channel_list = [channel_name]
    
    # iterating over channels in a project
    for ch in self.proj.projectChannels(channel_list):
      
      # creating the channel resource
      self.resource_interface.createChannel(ch.channel_name)
      # ingest 1 or more resolutions based on user input
      if resolution is None:
        start_res = self.proj.datasetcfg.scalinglevels
        stop_res = ch.resolution - 1
      else:
        start_res = resolution
        stop_res = resolution - 1
      
      # iterating over resolution
      for cur_res in range(start_res, stop_res, -1):
        
        # get the source database sizes
        [image_size, time_range] = self.proj.datasetcfg.dataset_dim(cur_res)
        [xcubedim, ycubedim, zcubedim] = cubedim = self.proj.datasetcfg.get_cubedim(cur_res)
        offset = self.proj.datasetcfg.get_offset(cur_res)
        [xsupercubedim, ysupercubedim, zsupercubedim] = supercubedim = self.proj.datasetcfg.get_supercubedim(cur_res)
        # set the limits for iteration on the number of cubes in each dimension
        xlimit = (image_size[0]-1) / (xsupercubedim) + 1
        ylimit = (image_size[1]-1) / (ysupercubedim) + 1
        zlimit = (image_size[2]-1) / (zsupercubedim) + 1
        # [xlimit, ylimit, zlimit] = limit = self.proj.datasetcfg.get_supercube_limit(cur_res)
        [x_start, y_start, z_start] = map(div, start_values, supercubedim)
        for z in range(z_start, zlimit, 1):
          for y in range(y_start, ylimit, 1):
            for x in range(x_start, xlimit, 1):

              try:
                # cutout the data at the current resolution
                data = db.cutout(ch, [x*xsupercubedim, y*ysupercubedim, z*zsupercubedim], [xsupercubedim, ysupercubedim, zsupercubedim], cur_res).data
                # generate the morton index
                morton_index = XYZMorton([x, y, z])

                self.logger.info("[{},{},{}] at res {}".format(x*xsupercubedim, y*ysupercubedim, z*zsupercubedim, cur_res))
                # updating the index
                # self.cuboidindex_db.putItem(ch.channel_name, cur_res, x, y, z, ch.time_range[0])
                # inserting the cube
                self.s3_io.putCube(ch, ch.time_stamp[0], morton_index, cur_res, blosc.pack_array(data), neariso=neariso)
              
              except Exception as e:
                # checkpoint the ingest
                self.logger.error(e)
                self.checkpoint_ingest(ch.channel_name, cur_res, x, y, z, e)
                raise e
  
  
  def uploadNewProject(self, config_file, start_values, neariso=False):
    """Upload a new project"""
    
    # loading the config file and assdociated params and processors
    config = Configuration()
    config.load(json.loads(open(config_file, 'rt').read()))
    config.load_plugins()
    path_processor = config.path_processor_class
    path_processor.setup(config.get_path_processor_params())
    tile_processor = config.tile_processor_class
    tile_processor.setup(config.get_tile_processor_params())
    tile_params = config.get_tile_processor_params()
    path_params = config.get_path_processor_params()
    
    # creating the channel object from resource service
    channel_name = config.config_data['database']['channel']
    channel_datatype = self.info_interface.get_channel_datatype(channel_name)
    cur_res = tile_params['ingest_job']['resolution']
    
    # loading all the parameters for image-sizes, tile-sizes, and iteration limits
    [xsupercubedim, ysupercubedim, zsupercubedim] = supercubedim = SUPER_CUBOID_SIZE
    [x_start, x_end] = tile_params['ingest_job']['extent']['x']
    [y_start, y_end] = tile_params['ingest_job']['extent']['y']
    [z_start, z_end] = tile_params['ingest_job']['extent']['z']
    [t_start, t_end] = tile_params['ingest_job']['extent']['t']
    x_tilesz = tile_params['ingest_job']['tile_size']['x']
    y_tilesz = tile_params['ingest_job']['tile_size']['y']
    z_tilesz = tile_params['ingest_job']['tile_size']['z']
    t_tilesz = tile_params['ingest_job']['tile_size']['t']
    x_limit = (x_end-1) / (x_tilesz) + 1
    y_limit = (y_end-1) / (y_tilesz) + 1
    z_limit = (z_end-1) / (z_tilesz) + 1
    t_limit = (t_end-1) / (t_tilesz) + 1
    
    if start_values != [0, 0, 0]:
      [x_start, y_start, z_start] = map(div, start_values, [x_tilesz, y_tilesz, z_tilesz])
    # iterate over t,z,y,x to ingest the data
    for t in range(t_start, t_limit, 1):  
      for z in range(z_start, z_limit, zsupercubedim):
        for y in range(y_start, y_limit, 1):
          for x in range(x_start, x_limit, 1):
            
            data = np.zeros([zsupercubedim, y_tilesz, x_tilesz], dtype=ND_dtypetonp[channel_datatype])
            for b in range(0, zsupercubedim, 1):
              if z + b > z_end - 1:
                break
              # generate file name
              file_name = path_processor.process(x, y, z+b, t)
              # read the file, handle expection if the file is missing
              try:
                tile_handle = tile_processor.process(file_name, x, y, z+b, t)
                tile_handle.seek(0)
                data[b,:,:] = np.asarray(Image.open(tile_handle))
              except IOError as e:
                pass
                # print "missing file", file_name
            # iterate over the tile if it is larger then supercuboid size
            for y_index in range(0, y_tilesz/ysupercubedim):
              for x_index in range(0, x_tilesz/xsupercubedim):
                # calculate the morton index 
                insert_data = data[:, y_index*ysupercubedim:(y_index+1)*ysupercubedim, x_index*xsupercubedim:(x_index+1)*xsupercubedim]
                if np.any(insert_data):
                  morton_index = XYZMorton([x_index+(x*x_tilesz/xsupercubedim), y_index+(y*y_tilesz/ysupercubedim), z/zsupercubedim])
                  [s3_x, s3_y, s3_z] = MortonXYZ(morton_index)
                  print "Morton Index {}".format(morton_index)
                  self.logger.info("[{},{},{}]".format((x_index+x)*x_tilesz, (y_index+y)*y_tilesz, z))
                  self.cuboidindex_db.putItem(channel_name, cur_res, s3_x, s3_y, s3_z, t, neariso=neariso)
                  self.cuboid_bucket.putObject(channel_name, cur_res, morton_index, t, blosc.pack_array(insert_data), neariso=neariso)
                  # self.s3_io.putCube(ch, t, morton_index, cur_res, blosc.pack_array(insert_data), update=False, neariso=False)


  def checkpoint_ingest(self, channel_name, resolution, x, y, z, e, time=0):
    """Checkpoint the progress to file"""
    
    with closing(open('checkpoint_ingest.csv', 'wb')) as csv_file:
      field_names = ['project_name', 'channel_name', 'resolution', 'x', 'y', 'z', 'time', 'exception']
      csv_writer = csv.DictWriter(csv_file, delimiter=',', fieldnames=field_names)
      csv_writer.writeheader()
      csv_writer.writerow({'project_name' : self.proj.project_name, 'channel_name' : channel_name, 'resolution' : resolution, 'x' : x, 'y' : y, 'z' : z, 'time' : time, 'exception' : e.message})

  
  def load_checkpoint(self):
    """Load from a checkpoint file"""
    return NotImplemented

def main():
  
  parser = argparse.ArgumentParser(description="Upload an existing project of NeuroData to s3")
  parser.add_argument('token', action='store', help='Token for the project')
  parser.add_argument('--channel', dest='channel_name', action='store', type=str, default=None, help='Channel Name in the project')
  parser.add_argument('--res', dest='resolution', action='store', type=int, default=None, help='Resolution to upload')
  parser.add_argument('--action', dest='action', action='store', choices=['upload-existing', 'upload-new', 'delete-channel', 'delete-res', 'delete-project'], default='upload', help='Specify action for the given project')
  parser.add_argument('--host', dest='host_name', action='store', type=str, default='localhost:8080', help='Server host name')
  parser.add_argument('--start', dest='start_values', action='store', type=int, nargs=3, metavar=('X', 'Y', 'Z'), default=[0, 0, 0], help='Resume upload from co-ordinates')
  parser.add_argument('--data', dest='data_location', action='store', type=str, default=None, help='Data Location')
  parser.add_argument('--config', dest='config_file', action='store', default=None, help='Config file name')
  # Unwanted field which might be useful in the future
  # parser.add_argument('--dry-run', dest='dry_run', action='store', type=bool, default=False, help='Try a dry run without uploading data')
  # parser.add_argument('--new', dest='new_project', action='store', choices=['slice', 'catmaid'], default='slice', help='New Project')
  # parser.add_argument('--tilesz', dest='tile_size', action='store', type=int, default=512, help='Tile Size')
  # parser.add_argument('--url', dest='url', action='store', type=str, help='Http URL')
  result = parser.parse_args()
  
  aws_interface = AwsInterface(result.token, result.host_name)
  if result.action == 'upload-new':
    if result.config_file is None:
      raise ValueError("Error: data location or config file location cannot be empty for uploading new project")
    aws_interface.uploadNewProject(result.config_file, result.start_values)
  elif result.action == 'upload-existing':
    if result.channel_name is None and result.resolution is not None:
      raise ValueError("Error: channel cannot be empty if resolution is not empty")
    aws_interface.uploadExistingProject(result.channel_name, result.resolution, result.start_values)
  elif result.action == 'delete-project':
    aws_interface.deleteProject()
  elif result.action == 'delete-channel':
    if result.channel_name is None:
      raise ValueError("Error: channel cannot be empty")
    aws_interface.deleteChannel(result.channel_name)
  elif result.action == 'delete-res':
    if result.channel_name is None or result.resolution is None:
      raise ValueError("Error: channel or resolution cannot be empty")
    aws_interface.deleteResolution(result.channel_name, result.resolution)
  else:
    raise ValueError("Error: Invalid action {}".format(result.action))


if __name__ == '__main__':
  main()
