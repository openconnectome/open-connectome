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

import os
import sys

sys.path += [os.path.abspath('../django')]
import OCP.settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'OCP.settings'
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()


from django.contrib.auth.models import User
from ocpuser.models import Project
from ocpuser.models import Dataset
from ocpuser.models import Token
from ocpuser.models import Channel

import ocpcaproj
import site_to_test
import kvengine_to_test

def createTestDB ( project_name, channel_list=['unit_anno'], channel_type='annotation', channel_datatype='uint32', public=0, ximagesize=10000, yimagesize=10000, zimagesize=1000, scalingoption=ocpcaproj.ZSLICES, scalinglevels=5, readonly=0, window=[0,0], time=[0,0], default=False, ocp_version=0.6 ):
  """Create a unit test data base on the specified sit and name"""

  unituser = User.objects.get(username='brain')

  ds = Dataset ( dataset_name="unittest", user=unituser, ximagesize=ximagesize, yimagesize=yimagesize, zimagesize=zimagesize,  xoffset=0, yoffset=0, zoffset=0, xvoxelres=4.0, yvoxelres=4.0, zvoxelres=3.0, scalingoption=scalingoption, scalinglevels=scalinglevels, starttime=time[0], endtime=time[1], dataset_description="Unit test" ) 
  ds.save()


  # RBTODO need to add a window and a project

  # make the project entry
  pr = Project (project_name=project_name, project_description='Unit test', user=unituser, dataset=ds, ocp_version=ocp_version)
  pr.save()

  # and create the database
  pd = ocpcaproj.OCPCAProjectsDB()

  # create a token
  tk = Token (token_name = project_name, user=unituser, token_description = 'Unit test token', project_id=pr, public=public)
  tk.save()

  pd.newOCPCAProject( pr.project_name )
  try:
    for channel_name in channel_list:
      ch = Channel (channel_name=channel_name, channel_type=channel_type, channel_datatype=channel_datatype, channel_description='Unit test channel', project_id=pr, readonly=readonly, resolution=0, exceptions=1,startwindow=window[0], endwindow=window[1], default=default)
      ch.save()
      pd.newOCPCAChannel(pr.project_name, ch.channel_name)
  except Exception, e:
    pass


def deleteTestDB ( project_name ):

  try:
    tk = Token.objects.get(token_name=project_name)
    pr = Project.objects.get(project_name=project_name)
    ds = Dataset.objects.get(dataset_name=pr.dataset_id)
    channel_list = Channel.objects.filter(project_id=pr)
    pd = ocpcaproj.OCPCAProjectsDB()
    pd.deleteOCPCADB ( pr.project_name )
    for ch in channel_list:
      ch.delete()
    tk.delete()
    pr.delete()
    ds.delete()
  except Exception, e:
    pass
