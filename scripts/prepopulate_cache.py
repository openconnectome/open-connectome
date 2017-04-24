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
import argparse
sys.path.append(os.path.abspath('../django/'))
import ND.settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'ND.settings'
from django.conf import settings
import django
django.setup()
from scripts_helper import *
from ndlib.ndctypelib import *
from spdb.spatialdb import SpatialDB
HOST_NAME = 'localhost:8080'

class Cache(object):

  def __init__(self, token_name, host_name):
    
    self.info_interface = InfoInterface(host_name, token_name)
    self.resource_interface = ResourceInterface(self.info_interface.dataset_name, self.info_interface.project_name, host_name)
  

  def populate(self, channel_name, resolution, start_values, end_values, time_limit, neariso=False):
    proj = self.resource_interface.getProject()
    ch = NDChannel.fromName(proj, channel_name)
    cubedim = proj.datasetcfg.get_cubedim(resolution)
    image_size = proj.datasetcfg.get_imagesize(resolution)
  
    if time_limit is None:
      time_limit = ch.time_range[1]

    if end_values == [0,0,0]:
      end_values = image_size

    [x_start, y_start, z_start] = map(div, start_values, cubedim)
    x_end = (end_values[0] - 1) / cubedim[0] + 1
    y_end = (end_values[1] - 1) / cubedim[1] + 1
    z_end = (end_values[2] - 1) / cubedim[2] + 1

    db = SpatialDB(proj)
  
    for time_index in range(ch.time_range[0], time_limit, 1):
      for z_index in range(z_start, z_end, 1):
        for y_index in range(y_start, y_end, 1):
          for x_index in range(x_start, x_end, 1):
            
            print("Populating Cache with T:{},X:{},Y:{},Z:{}".format(time_index, x_index*cubedim[0], y_index*cubedim[1], z_index*cubedim[2]))
            zidx = XYZMorton([x_index, y_index, z_index])
            db.getCubes(ch, [time_index], [zidx], resolution, neariso=neariso)

def main():

  parser = argparse.ArgumentParser(description="Populate the cache for ndstore")
  parser.add_argument('token_name', action='store', type=str, help="Token Name")
  parser.add_argument('channel_name', action='store', type=str, help="Channel Name")
  parser.add_argument('resolution', action='store', type=int, help="Resolution")
  parser.add_argument('--start', dest='start_values', action='store', type=int, nargs=3, metavar=('X', 'Y','Z'), default=[0, 0, 0], help='Start co-ordinates')
  parser.add_argument('--end', dest='end_values', action='store', type=int, nargs=3, metavar=('X', 'Y','Z'), default=[0, 0, 0], help='End co-ordinates')
  parser.add_argument('--time', dest='time_limit', action='store', default=None, type=int, help="Time Index")
  parser.add_argument('--host', dest='host_name', action='store', default=HOST_NAME, type=str, help="Host Name")
  result = parser.parse_args()
  
  cache = Cache(result.token_name, result.host_name)
  cache.populate(result.channel_name, result.resolution, result.start_values, result.end_values, result.time_limit)

if __name__ == '__main__':
  main()
