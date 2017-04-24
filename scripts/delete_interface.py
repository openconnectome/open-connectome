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
import argparse
sys.path.append(os.path.abspath('../django/'))
import ND.settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'ND.settings'
from django.conf import settings
from scripts_helper import *
from ndingest.nddynamo.cuboidindexdb import CuboidIndexDB
from ndingest.ndbucket.cuboidbucket import CuboidBucket
HOST_NAME = 'localhost:8080'

class Interface(object):

  def __init__(self, dataset_name, project_name, host_name=HOST_NAME):
    # self.resource_interface = ResourceInterface(dataset_name, project_name, host_name)
    self.cuboid_bucket = CuboidBucket(project_name)
    self.cuboidindex_db = CuboidIndexDB(project_name)

  # def deleteToken(self):
    # """Delete the Token"""
    # self.resource_interface.deleteToken()
    # print 'Delete successful for token {}'.format(self.token)

  def deleteProject(self):
    """Delete the project"""
    return NotImplemented 
    # delete the project from s3 and dynamo
    # self.s3_projdb.deleteNDProject()
    # deleting the meta-data via resource interface
    # self.resource_interface.deleteToken()
    # self.resource_interface.deleteProject()
    # print 'Delete successful for project {}'.format(self.project_name)
  
  
  def deleteChannel(self, channel_name):
    """Delete the channel"""
    
    try:
      for item in self.cuboidindex_db.queryChannelItems(channel_name):
        self.cuboid_bucket.deleteObject(item['supercuboid_key'])
        self.cuboidindex_db.deleteItem(item['supercuboid_key'])
    except Exception as e:
      print (e)
      
    # delete the channel from s3 and dynamo
    # self.s3_projdb.deleteNDChannel(channel_name)
    # deleting the meta-data via resource interface
    # self.resource_interface.deleteChannel(channel_name)
    # print 'Delete successful for channel {}'.format(channel_name)


  def deleteResolution(self, channel_name, resolution):
    """Delete an existing resolution"""
    
    try:
      for item in self.cuboidindex_db.queryResolutionItems(channel_name, resolution):
        self.cuboid_bucket.deleteObject(item['supercuboid_key'])
        self.cuboidindex_db.deleteItem(item['supercuboid_key'])
    except Exception as e:
      print (e)

    # delete the project from s3 and dynamo
    # self.s3_projdb.deleteNDResolution(channel_name, resolution)
    # print 'Delete successful for resolution {} for channel {}'.format(resolution, channel_name)

def main():

  dataset_name = 'synaptomesberlin'
  project_name = 'bigalign2'
  channel_name = 'MBP'
  resolution = 6
  import pdb; pdb.set_trace()
  interface = Interface(dataset_name, project_name)
  interface.deleteResolution(channel_name, resolution)

if __name__ == '__main__':
  main()
