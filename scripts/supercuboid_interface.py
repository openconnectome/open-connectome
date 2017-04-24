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
import sys
import numpy as np
import blosc
import argparse
sys.path.append('../')
# sys.path.append(os.path.abspath('../django'))
# import ND.settings
# os.environ['DJANGO_SETTINGS_MODULE'] = 'ND.settings'
from ndingest.nddynamo.cuboidindexdb import CuboidIndexDB
from ndingest.ndbucket.cuboidbucket import CuboidBucket
from ndlib.restutil import *
from ndlib.ndctypelib import *
from scripts_helper import *
import logging
HOST_NAME = 'localhost:8080'

class S3Cuboid(object):

  def __init__(self, token_name, host_name=HOST_NAME):
    # configuring the logger based on the dataset we are uploading
    self.logger = logging.getLogger(token_name)
    self.logger.setLevel(logging.INFO)
    fh = logging.FileHandler('{}_upload.log'.format(token_name))
    self.logger.addHandler(fh)

    self.info_interface = InfoInterface(host_name, token_name)
    self.project_name = self.info_interface.project_name
    self.cuboidindex_db = CuboidIndexDB(self.project_name)
    self.cuboid_bucket = CuboidBucket(self.project_name)


  def upload(self, file_name, channel_name, resolution, x_index, y_index, z_index, dimensions=[1, 64, 512,512], time_index=0, neariso=False):
    """Upload a 4D supercuboid directly to dynamo and s3"""
    cuboid_data = np.fromfile(file_name, dtype=self.info_interface.get_channel_datatype(channel_name))
    cuboid_data = cuboid_data.reshape(dimensions)
    super_zidx = XYZMorton([x_index, y_index, z_index])
    self.logger.info("Inserting cube {},{},{}".format(x_index, y_index, z_index))
    self.cuboidindex_db.putItem(channel_name, resolution, x_index, y_index, z_index, time_index, neariso=neariso)
    self.cuboid_bucket.putObject(channel_name, resolution, super_zidx, time_index, blosc.pack_array(cuboid_data), neariso=neariso)


def main():

  parser = argparse.ArgumentParser(description="Upload a supercuboid to S3")
  parser.add_argument('file_name', action='store', type=str, help='File Name')
  parser.add_argument('token_name', action='store', type=str, help='Token Name')
  parser.add_argument('channel_name', action='store', type=str, help='Channel Name')
  parser.add_argument('resolution', action='store', type=int, help='Resolution')
  parser.add_argument('indexes', action='store', type=int, nargs=3, metavar=('X', 'Y', 'Z'), default=[0, 0, 0], help='X, Y, Z co-ordinates of the supercuboid')
  parser.add_argument('--time', dest='time_index', action='store', type=int, default=0, help='Time index')
  parser.add_argument('--dims', dest='dimensions', action='store', type=int, nargs=3, metavar=('X', 'Y', 'Z'), default=[1, 64, 512, 512], help='Supercuboid dimensions')
  parser.add_argument('--neariso', dest='neariso', action='store', type=bool, default=False, help='Neariso')
  parser.add_argument('--host', dest='host_name', action='store', type=str, default=HOST_NAME, help='Server host name')
  parser.add_argument('--supercube', dest='super_cube', action='store_true', default=False, help='Return supercube dimension')
  result = parser.parse_args()
  
  s3_cuboid = S3Cuboid(result.token_name, result.host_name)
  if result.super_cube:
    print (s3_cuboid.info.supercuboid_dimension(result.resolution))
  else:
    s3_cuboid.upload(result.file_name, result.channel_name, result.resolution, result.indexes[0], result.indexes[1], result.indexes[2], result.dimensions, result.time_index, result.neariso)

if __name__ == '__main__':
  main()
