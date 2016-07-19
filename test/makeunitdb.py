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

sys.path += [os.path.abspath('../django')]
import ND.settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'ND.settings'
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()


from django.contrib.auth.models import User
from nduser.models import Project
from nduser.models import Dataset
from nduser.models import Token
from nduser.models import Channel

from ndproj import NDProjectsDB
from ndtype import ZSLICES, ANNOTATION, NOT_PROPAGATED, READONLY_FALSE, UINT32, ND_VERSION, MYSQL, CASSANDRA, RIAK, PUBLIC_TRUE

import site_to_test
import kvengine_to_test

def createTestDB ( project_name, channel_list=['unit_anno'], channel_type=ANNOTATION, channel_datatype=UINT32, public=0, ximagesize=10000, yimagesize=10000, zimagesize=1000, xvoxelres=4.0, yvoxelres=4.0, zvoxelres=3.0, scalingoption=ZSLICES, scalinglevels=5, readonly=READONLY_FALSE, propagate=NOT_PROPAGATED, window=[0,0], time=[0,0], default=False, nd_version=ND_VERSION ):
  """Create a unit test data base on the specified sit and name"""
  
  unituser = User.objects.get(username='neurodata')

  ds = Dataset ( dataset_name="unittest", user=unituser, ximagesize=ximagesize, yimagesize=yimagesize, zimagesize=zimagesize,  xoffset=0, yoffset=0, zoffset=1, xvoxelres=xvoxelres, yvoxelres=yvoxelres, zvoxelres=zvoxelres, scalingoption=scalingoption, scalinglevels=scalinglevels, starttime=time[0], endtime=time[1], public=PUBLIC_TRUE, dataset_description="Unit test" ) 
  ds.save()

  # make the project entry
  pr = Project (project_name=project_name, project_description='Unit test', user=unituser, dataset=ds, nd_version=nd_version, host='localhost', kvengine=kvengine_to_test.kvengine, kvserver=kvengine_to_test.kvserver)
  pr.save()

  # create a token
  tk = Token (token_name = project_name, user = unituser, token_description = 'Unit test token', project_id = pr, public = public)
  tk.save()
  
  # get the correct object for the kvengine
  pd = NDProjectsDB.getProjDB(project_name)
  # create the database
  pd.newNDProject()

  try:
    for channel_name in channel_list:
      ch = Channel (channel_name=channel_name, channel_type=channel_type, channel_datatype=channel_datatype, channel_description='Unit test channel', project_id=pr, readonly=readonly, propagate=propagate, resolution=0, exceptions=1,startwindow=window[0], endwindow=window[1], default=default)
      # create a channel
      ch.save()
      # create the channel table
      pd.newNDChannel(ch.channel_name)
  except Exception, e:
      print(e)
      raise e


def deleteTestDB ( project_name ):
  
  try:
    # get the objects
    tk = Token.objects.get(token_name=project_name)
    pr = Project.objects.get(project_name=project_name)
    ds = Dataset.objects.get(dataset_name=pr.dataset_id)
    
    # get the channel list
    channel_list = Channel.objects.filter(project_id=pr)
    
    # get the correct object for the kvengine
    pd = NDProjectsDB.getProjDB(pr.project_name)
    
    for ch in channel_list:
      # delete the channel table
      pd.deleteNDChannel(ch.channel_name)
      # delete the channel
      ch.delete()
    # delete the project database
    pd.deleteNDProject()
    # delete the objects
    tk.delete()
    pr.delete()
    ds.delete()
  except Exception, e:
    print(e)
    raise e
    

def deleteTestDBList(project_name_list):
  
  # TODO KL Will cascade work across different django versions?
  try:
    for project_name in project_name_list:
      pr = Project.objects.get(project_name=project_name)
      pd = NDProjectsDB.getProjDB(pr.project_name)
      # delete the project database
      pd.deleteNDProject()
    ds = Dataset.objects.get(dataset_name=pr.dataset_id)
    # deleting the dataset works in django1.9 as it does a cascaded delete
    ds.delete()
  except Exception, e:
    print(e)
    raise e
