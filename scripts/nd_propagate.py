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
import json
sys.path.append(os.path.abspath('../django/'))
import ND.settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'ND.settings'
from django.conf import settings
import django
django.setup()
from webservices.ndstack import *
from ndlib.ndtype import *
from ndproj.ndproject import NDProject
from ndproj.ndchannel import NDChannel
from scripts_helper import *
HOST_NAME = 'localhost:8080'

def main():
  """Take arguments from user"""
  
  parser = argparse.ArgumentParser(description="Run the propagate script for neurodata")
  parser.add_argument('token_name', action='store', type=str, help="Token Name")
  parser.add_argument('--channel', dest='channel_name', action='store', default=None, type=str, help="Channel Name")
  parser.add_argument('--host', dest='host_name', action='store', default=HOST_NAME, type=str, help="Host Name")
  parser.add_argument('--neariso', dest='neariso', action='store_true', default=False, help="Only propagate neariso")
  parser.add_argument('--old', dest='old', action='store_true', default=False, help="For old annotation projects. Creates neariso tables.")
  result = parser.parse_args()
  info_interface = InfoInterface(result.host_name, result.token_name)
  resource_interface = ResourceInterface(info_interface.dataset_name, info_interface.project_name, result.host_name)

  proj = resource_interface.getProject()
  
  # if single channel passed then only propagate that channel
  if result.channel_name:
    channel_list = [result.channel_name]
  else:
    channel_list = None
  for ch in proj.projectChannels(channel_list=channel_list):
    
    # create neariso tables for old annotation projects
    if result.old:
      try:
        ch.db.updateNDChannel(ch.channel_name)
      except:
        pass

    print ("Propagating channel {}".format(ch.channel_name))
    ch.propagate = UNDER_PROPAGATION

    try:
      if result.neariso:
        # build only neariso
        buildImageStack(proj, ch, neariso=result.neariso, direct=False)
      else:
        # build stack twice, once for zslice and once for neariso
        buildImageStack(proj, ch, neariso=False, direct=True)
        buildImageStack(proj, ch, neariso=True, direct=True)
      # set to propagate when done
      ch.propagate = PROPAGATED
    except Exception as e:
      ch.propagate = NOT_PROPAGATED
      raise e

if __name__ == '__main__':
  main()
