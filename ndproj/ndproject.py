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

from contextlib import closing
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from nduser.models import Dataset
from nduser.models import Project
from nduser.models import Channel
from nduser.models import Token
from ndlib.ndtype import *
from ndproj.ndobject import NDObject
from ndproj.nddataset import NDDataset
from ndproj.ndchannel import NDChannel
from ndproj.ndprojdb import NDProjectsDB
from webservices.ndwserror import NDWSError
import logging
logger = logging.getLogger("neurodata")

class NDProject(NDObject):

  def __init__(self, pr) :
    
    self.pr = pr
    self.datasetcfg = NDDataset.fromName(self.dataset_name)
    self.loadDB()

    # if isinstance(token_name, str) or isinstance(token_name, unicode):
      # try:
        # self.tk = Token.objects.get(token_name = token_name)
        # self.pr = Project.objects.get(project_name = self.tk.project_id)
        # self.datasetcfg = NDDataset.fromName(self.pr.dataset_id)
      # except ObjectDoesNotExist, e:
        # logger.error("Token {} does not exist. {}".format(token_name, e))
        # raise NDWSError("Token {} does not exist. {}".format(token_name, e))
    # elif isinstance(token_name, Project):
      # # Constructor for NDProject from Project Name
      # try:
        # self.tk = None
        # self.pr = token_name
        # self.datasetcfg = NDDataset.fromName(self.pr.dataset_id)
      # except ObjectDoesNotExist, e:
        # logger.error("Token {} does not exist. {}".format(token_name, e))
        # raise NDWSError("Token {} does not exist. {}".format(token_name, e))
  
  @staticmethod
  def public_list():
    projects = Project.objects.filter(public = PUBLIC_TRUE)
    # return projects
    return [pr.project_name for pr in projects]

  @classmethod
  def fromTokenName(cls, token_name):
    try:
      tk = Token.objects.get(token_name = token_name)
      pr = Project.objects.get(project_name = tk.project_id)
      return cls(pr)
    except ObjectDoesNotExist, e:
      logger.error("Token {} does not exist. {}".format(token_name, e))
      raise NDWSError("Token {} does not exist. {}".format(token_name, e))

  @classmethod
  def fromName(cls, project_name):
    try:
      pr = Project.objects.get(project_name=project_name)
      return cls(pr)
    except Project.DoesNotExist as e:
      logger.warning("Project {} does not exist".format(project_name))
      raise Project.DoesNotExist
  
  @classmethod
  def fromJson(cls, dataset_name, project):
    pr = Project(**cls.deserialize(project))
    pr.dataset_id = dataset_name
    return cls(pr)
  
  def loadDB(self):
    with closing (NDProjectsDB.getProjDB(self)) as db:
      self.db = db

  def create(self, create_table=True):

    try:
      self.pr.save()
      if create_table:
        self.db.newNDProject()
    except NDWSError as e:
      self.pr.delete()
      raise
    except Exception as e:
      raise

  def delete(self):
    try:
      self.db.deleteNDProject()
      self.pr.delete()
    except NDWSError as e:
      raise
    except Exception as e:
      raise
  
  def serialize(self):
    return NDObject.serialize(self.pr)

  @property
  def project_name(self):
    return self.pr.project_name

  @project_name.setter
  def project_name(self, value):
    # TODO KL check for unwanted chars
    self.pr.project_name = value
  
  @property
  def dataset_name(self):
    return self.pr.dataset_id
  
  @dataset_name.setter
  def dataset_name(self, value):
    self.pr.dataset_id = value
  
  @property
  def user_id(self):
    return self.pr.user_id

  @user_id.setter
  def user_id(self, value):
    self.pr.user_id = value

  @property
  def token(self):
    return self.tk.token_name

  @token.setter
  def token(self, value):
    self.tk.token_name = value

  @property
  def host(self):
    return self.pr.host

  @host.setter
  def host(self, value):
    self.pr.host = value

  @property
  def kvserver(self):
    return self.pr.kvserver

  @kvserver.setter
  def kvserver(self, value):
    self.pr.kvserver = value
  
  @property
  def kvengine(self):
    return self.pr.kvengine
  
  @kvengine.setter
  def kvengine(self, value):
    self.pr.kvengine = value
    self.loadDB()

  @property
  def mdengine(self):
    return self.pr.mdengine

  @mdengine.setter
  def mdengine(self, value):
    self.pr.mdengine = value
  
  @property
  def s3backend(self):
    return True if self.pr.s3backend is S3_TRUE else False 
  
  @s3backend.setter
  def s3backend(self, value):
    self.pr.s3backend = S3_TRUE if value == S3_TRUE else False
  
  @property
  def project_description(self):
    return self.pr.project_description

  @project_description.setter
  def project_description(self, value):
    self.pr.project_description = value

  @property
  def public(self):
    return self.pr.public

  @public.setter
  def public(self, value):
    self.pr.public = value

  @property
  def nd_version(self):
    return self.pr.nd_version

  @nd_version.setter
  def nd_version(self, value):
    self.pr.nd_version = value

  @property
  def schema_version(self):
    return self.pr.schema_version

  @schema_version.setter
  def schema_version(self, value):
    self.pr.schema_version = value
  
  @property
  def kvengine_user(self):
    return settings.DATABASES['default']['USER']

  @property
  def kvengine_password(self):
    return settings.DATABASES['default']['PASSWORD']
  
  @property
  def dbname(self):
    return self.pr.project_name
  
  @property
  def s3backend(self):
    return self.pr.s3backend

  # Accessors
  def getToken ( self ):
    return self.tk.token_name
  
  def projectChannels ( self, channel_list=None ):
    """Return a generator of Channel Objects"""
    if channel_list is None:
      chs = Channel.objects.filter(project_id=self.pr)
    else:
      chs = channel_list
    for name in chs:
      ch = Channel.objects.get(project_id=self.pr, channel_name=name)
      yield NDChannel(ch)

  def getChannelObj ( self, channel_name='default' ):
    """Returns a object for that channel"""
    if channel_name == 'default':
      channel_name = Channel.objects.get(project_id=self.pr, default=True)
    return NDChannel.fromName(self.pr, channel_name)

  def deleteProject(self):
    """Delete the Project"""
    self.pr.delete()
