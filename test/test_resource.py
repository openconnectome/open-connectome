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
import pytest
sys.path += [os.path.abspath('../django')]
import ND.settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'ND.settings'
from ndlib.ndtype import TIMESERIES, UINT8, MYSQL
from params import Params
from ndlib.restutil import getJson, postJson, deleteJson
from test_settings import *

p = Params()
p.token = 'unittest'
p.project = 'unittest'
p.resolution = 0
p.channels = ['CHAN1', 'CHAN2']
p.channel_type = TIMESERIES
p.datatype = UINT8
p.dataset = 'unittest'

@pytest.mark.skipif(DEV_MODE, reason='Test not necessary for dev mode')
class Test_Resource():

  def setup_class(self):
    """Setup Parameters"""
    # makeunitdb.createTestDB(p.project, channel_list=p.channels, ximagesize=2000, yimagesize=2000, zimagesize=1000, xvoxelres=1.0, yvoxelres=1.0, zvoxelres=5.0, token_name=p.token)
    pass
  
  def teardown_class(self):
    """Teardown Parameters"""
    try:
      makeunitdb.deleteTestDB(p.project, token_name=p.token)
    except Exception as e:
      pass
  
  def test_post_dataset(self):
    dataset = {
        'dataset_name' : p.dataset,
        'ximagesize': 2000,
        'yimagesize' : 2000,
        'zimagesize' : 100,
        'xvoxelres' : 1.0,
        'yvoxelres' : 2.0,
        'zvoxelres' : 1.0,
        'public' : 1
    }
    response = postJson('https://{}/resource/dataset/{}/'.format(SITE_HOST, p.dataset), dataset)
    assert(response.status_code == 201)

  def test_post_project(self):
    project = {
        'project_name' : p.project,
        'host' : 'localhost',
        's3backend' : 0,
        'public' : 1,
        'kvserver' : 'localhost',
        'kvengine' : MYSQL
    }
    response = postJson('https://{}/resource/dataset/{}/project/{}'.format(SITE_HOST, p.dataset, p.project), project)
    assert(response.status_code == 201)
  
  def test_post_channel(self):
    channel = {
        'channel_name' : p.channels[0],
        'channel_type' : p.channel_type,
        'channel_datatype' : p.datatype,
        'startwindow' : 0,
        'endwindow': 500
    }
    response = postJson('https://{}/resource/dataset/{}/project/{}/channel/{}/'.format(SITE_HOST, p.dataset, p.project, p.channels[0]), channel)
    assert(response.status_code == 201)
  
  def test_post_token(self):
    token = {
        'token_name' : p.token,
        'public' : 1
    }
    response = postJson('https://{}/resource/dataset/{}/project/{}/token/{}/'.format(SITE_HOST, p.dataset, p.project, p.token), token)
    assert(response.status_code == 201)
  
  def test_public_dataset(self):
    response = getJson('https://{}/resource/public/dataset/'.format(SITE_HOST))
    assert(p.dataset in response.json())
  
  def test_list_dataset(self):
    response = getJson('https://{}/resource/dataset/'.format(SITE_HOST))
    assert(p.dataset in response.json())
  
  def test_list_project(self):
    response = getJson('https://{}/resource/dataset/{}/project/'.format(SITE_HOST, p.dataset))
    assert(p.project in response.json())
  
  def test_public_token(self):
    response = getJson('https://{}/resource/public/token/'.format(SITE_HOST))
    assert(p.token in response.json())
  
  def test_get_dataset(self):
    response = getJson('https://{}/resource/dataset/{}/'.format(SITE_HOST, p.dataset))
    assert(response.status_code == 200)
    assert(response.json()['dataset_name'] == p.dataset)
    assert(response.json()['ximagesize'] == 2000)
    assert(response.json()['xvoxelres'] == 1.0)
  
  def test_get_dataset_error(self):
    response = getJson('https://{}/resource/dataset/{}/'.format(SITE_HOST, 'foo'))
    assert(response.status_code == 404)

  def test_get_project(self):
    response = getJson('https://{}/resource/dataset/{}/project/{}/'.format(SITE_HOST, p.dataset, p.project))
    assert(response.status_code == 200)
    assert(response.json()['project_name'] == p.project)
    assert(response.json()['host'] == 'localhost')
    assert(response.json()['kvengine'] == MYSQL)
  
  def test_get_project_error(self):
    response = getJson('https://{}/resource/dataset/{}/project/{}/'.format(SITE_HOST, p.dataset, 'foo'))
    assert(response.status_code == 404)
  
  def test_get_channel(self):
    response = getJson('https://{}/resource/dataset/{}/project/{}/channel/{}/'.format(SITE_HOST, p.dataset, p.project, p.channels[0]))
    assert(response.status_code == 200)
    assert(response.json()['channel_name'] == p.channels[0])
    assert(response.json()['channel_type'] == p.channel_type)
    assert(response.json()['channel_datatype'] == p.datatype)
    assert(response.json()['startwindow'] == 0)
    assert(response.json()['endwindow'] == 500)
  
  def test_get_channel_error(self):
    response = getJson('https://{}/resource/dataset/{}/project/{}/channel/{}/'.format(SITE_HOST, p.dataset, p.project, 'foo'))
    assert(response.status_code == 404)
  
  def test_get_token(self):
    response = getJson('https://{}/resource/dataset/{}/project/{}/token/{}/'.format(SITE_HOST, p.dataset, p.project, p.token))
    assert(response.status_code == 200)
    assert(response.json()['token_name'] == p.token)
  
  def test_get_token(self):
    response = getJson('https://{}/resource/dataset/{}/project/{}/token/{}/'.format(SITE_HOST, p.dataset, p.project, 'foo'))
    assert(response.status_code == 404)

  def test_delete_token(self):
    response = deleteJson('https://{}/resource/dataset/{}/project/{}/token/{}/'.format(SITE_HOST, p.dataset, p.project, p.token))
    assert(response.status_code == 204)

  def test_delete_channel(self):
    response = deleteJson('https://{}/resource/dataset/{}/project/{}/channel/{}/'.format(SITE_HOST, p.dataset, p.project, p.channels[0]))
    assert(response.status_code == 204)
  
  def test_delete_project(self):
    response = deleteJson('https://{}/resource/dataset/{}/project/{}/'.format(SITE_HOST, p.dataset, p.project))
    assert(response.status_code == 204)
  
  def test_delete_dataset(self):
    response = deleteJson('https://{}/resource/dataset/{}/'.format(SITE_HOST, p.dataset))
    assert(response.status_code == 204)
