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

import json
from ndlib.restutil import *
try:
  from ndproj.ndproject import NDProject
  from ndproj.nddataset import NDDataset
  from ndproj.ndchannel import NDChannel
except:
  pass

class InfoInterface(object):

  def __init__(self, host_name, project_name):
    
    # self._host_name = host_name
    # self._project_name = project_name

    try:
      # setting up the project info
      response = getJson('https://{}/sd/{}/info/'.format(host_name, project_name))
      if response.status_code != 200:
        raise ValueError("Error. The server returned status code {}".response.status_code)
      self._info = response.json()
    except Exception as e:
      raise e

  @property
  def info(self):
    return self._info
  
  @property
  def dataset_name(self):
    return self._info['dataset']['name']
  
  @property
  def project_name(self):
    return self._info['project']['name']

  def supercuboid_dimension(self, resolution):
    return self._info['dataset']['supercube_dimension'][str(resolution)]

  def cuboid_dimension(self, resolution):
    return self._info['dataset']['cube_dimension'][str(resolution)]
  
  def image_size(self, resolution):
    return self._info['dataset']['imagesize'][str(resolution)]
  
  def offset(self, resolution):
    return self._info['dataset']['offset'][str(resolution)]
  
  def get_channel(self, channel_name):
    return self._info['channels'][channel_name]
  
  def get_channel_datatype(self, channel_name):
    return self._info['channels'][channel_name]['datatype']

  def get_channel_channeltype(self, channel_name):
    return self._info['channels'][channel_name]['channel_type']

class ResourceInterface(object):

  def __init__(self, dataset_name, project_name, host_name, logger=None):
    self.dataset_name = dataset_name
    self.project_name = project_name
    self.host = host_name
    self.logger = logger
  
  def getChannel(self, channel_name):
    try:
      response = getJson('https://{}/resource/dataset/{}/project/{}/channel/{}/'.format(self.host, self.dataset_name, self.project_name, channel_name))
      if response.status_code == 404:
        raise ValueError('The specified channel {} does not exist on the server'.format(channel_name))
      if response.status_code != 200:
        raise ValueError('The server returned status code {}'.format(response.status_code))
      channel_json = response.json()
      del channel_json['id']
      del channel_json['project']
      return NDChannel.fromJson(self.project_name, json.dumps(channel_json))
    except Exception as e:
      self.logger.error(e)
      raise e
  
  def getProject(self):
    try:
      response = getJson('https://{}/resource/dataset/{}/project/{}/'.format(self.host, self.dataset_name, self.project_name))
      project_json = response.json()
      del project_json['user']
      del project_json['dataset']
      return NDProject.fromJson(self.dataset_name, json.dumps(project_json))
    except Exception as e:
      self.logger.error(e)
      raise e

  def createDataset(self):
    dataset_obj = NDDataset.fromName(self.dataset_name)
    dataset = model_to_dict(dataset_obj._ds)
    del dataset['user']
    try:
      response = getJson('https://{}/resource/dataset/{}/'.format(self.host, self.dataset_name))
      if response.status_code == 404:
        response = postJson('https://{}/resource/dataset/{}/'.format(self.host, self.dataset_name), dataset)
        if response.status_code != 201:
          raise ValueError('The server returned status code {}'.format(response.status_code))
      elif (response.status_code == 200) and (self.dataset_name == response.json()['dataset_name']):
        self.logger.warning("Dataset already exists. Skipping Dataset creation")
      else:
        raise ValueError('The server returned status code {} and content {}'.format(response.status_code, response.json()))
    except Exception as e:
      self.logger.error(e)
      sys.exit(0)

  def createProject(self):
    project_obj = NDProject.fromName(self.project_name)
    project = model_to_dict(project_obj.pr)
    project['kvengine'] = REDIS
    project['host'] = 'localhost'
    project['s3backend'] = S3_TRUE
    del project['user']
    del project['dataset']
    try:
      response = getJson('https://{}/resource/dataset/{}/project/{}/'.format(self.host, self.dataset_name, self.project_name))
      if response.status_code == 404:
        response = postJson('https://{}/resource/dataset/{}/project/{}/'.format(self.host, self.dataset_name, self.project_name), project)
        if response.status_code != 201:
          raise ValueError('The server returned status code {}'.format(response.status_code))
      elif (response.status_code == 200) and (self.project_name == response.json()['project_name']):
        self.logger.warning("Project already exists. Skipping Project creation")
      else:
        raise ValueError('The server returned status code {} and content {}'.format(response.status_code, response.json()))
    except Exception as e:
      self.logger.error(e)
      sys.exit(0)
  
  def createChannel(self, channel_name):
    project = NDProject.fromName(self.project_name)
    channel_obj = project.getChannelObj(channel_name)
    channel = model_to_dict(channel_obj.ch)
    del channel['id']
    del channel['project']
    # del channel['user']
    try:
      response = getJson('https://{}/resource/dataset/{}/project/{}/channel/{}/'.format(self.host, self.dataset_name, self.project_name, channel_name))
      if response.status_code == 404:
        response = postJson('https://{}/resource/dataset/{}/project/{}/channel/{}/'.format(self.host, self.dataset_name, self.project_name, channel_name), channel)
        if response.status_code != 201:
          raise ValueError('The server returned status code {}'.format(response.status_code))
      elif (response.status_code == 200) and (channel_name == response.json()['channel_name']):
        self.logger.warning("Channel already exists. Skipping Channel creation")
      else:
        raise ValueError('The server returned status code {} and content {}'.format(response.status_code, response.json()))
    except Exception as e:
      self.logger.error(e)
      sys.exit(0)
    
  def createToken(self):
    token_obj = NDToken.fromName(self.token_name)
    token = model_to_dict(token_obj._tk)
    del token['project']
    del token['user']
    try:
      response = getJson('https://{}/resource/dataset/{}/project/{}/token/{}/'.format(self.host, self.dataset_name, self.project_name, self.token_name))
      if response.status_code == 404:
        response = postJson('https://{}/resource/dataset/{}/project/{}/token/{}/'.format(self.host, self.dataset_name, self.project_name, self.token_name), token)
        if response.status_code != 201:
          raise ValueError('The server returned status code {}'.format(response.status_code))
      elif (response.status_code == 200) and (self.token_name == response.json()['token_name']):
        self.logger.warning("Token already exists. Skipping Token creation")
      else:
        raise ValueError('The server returned status code {} and content {}'.format(response.status_code, response.json()))
    except Exception as e:
      self.logger.error(e)
      sys.exit(0)
  
    def deleteDataset(self):
      try:
        response = deleteJson('https://{}/resource/dataset/{}/'.format(self.host, self.dataset_name))
        if response.status_code != 204:
          raise ValueError('The server returned status code {}'.format(response.status_code))
      except Exception as e:
        self.logger.error(e)
        sys.exit(0)
    
    def deleteProject(self):
      try:
        response = deleteJson('https://{}/resource/dataset/{}/project/{}'.format(self.host, self.dataset_name, self.project_name))
        if response.status_code != 204:
          raise ValueError('The server returned status code {}'.format(response.status_code))
      except Exception as e:
        self.logger.error(e)
        sys.exit(0)
    
    def deleteChannel(self, channel_name):
      try:
        response = deleteJson('https://{}/resource/dataset/{}/project/{}/channel/{}'.format(self.host, self.dataset_name, self.project_name, channel_name))
        if response.status_code != 204:
          raise ValueError('The server returned status code {}'.format(response.status_code))
      except Exception as e:
        self.logger.error(e)
        sys.exit(0)

    def deleteToken(self):
      try:
        response = deleteJson('https://{}/resource/dataset/{}/project/{}/token/{}'.format(self.host, self.dataset_name, self.project_name, self.token_name))
        if response.status_code != 204:
          raise ValueError('The server returned status code {}'.format(response.status_code))
      except Exception as e:
        self.logger.error(e)
        sys.exit(0)
