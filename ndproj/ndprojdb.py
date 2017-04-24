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

from abc import abstractmethod
from ndlib.ndtype import MYSQL, CASSANDRA, RIAK, REDIS, DYNAMODB, PUBLIC_TRUE
from nduser.models import Token
from webservices.ndwserror import NDWSError
import logging
logger=logging.getLogger("neurodata")

class NDProjectsDB(object):
  """Database for the projects"""

  def __init__(self):
    """Create the database connection"""
    pass
  
  def close(self):
    """Close the database connection"""
    pass

  
  def newNDProject(self):
    """Create the database for a project"""
    return NotImplemented

  
  def newNDChannel(self, channel_name):
    """Create the tables for a channel"""
    return NotImplemented

  
  def deleteNDProject(self):
    """Delete the database for a project"""
    return NotImplemented


  def deleteNDChannel(self, channel_name):
    """Delete the tables for a channel"""
    return NotImplemented


  @staticmethod
  def loadDatasetConfig(dataset_name):
    """Query the database for the dataset information and build a db configuration"""
    from nddataset import NDDataset
    return NDDataset(dataset_name)


  @staticmethod
  def loadToken(token_name):
    """Query django configuration for a token to bind to a project"""
    from ndproject import NDProject
    return NDProject.fromTokenName(token_name)


  # @staticmethod
  # def getPublic():
    # """Return a list of public tokens"""
    # tkns = Token.objects.filter(public = PUBLIC_TRUE)
    # return [t.token_name for t in tkns]
 

  # @staticmethod
  # def getPublicDatasets():
    # """Return a list of public datasets"""
    # datasets = Dataset.objects.filter(public = PUBLIC_TRUE)
    # return [d.dataset_name for d in datasets]
  
    
  # @staticmethod
  # def getPublicTokens():
    # """Return a list of public tokens"""
    # tkns = Token.objects.filter(public = PUBLIC_TRUE)
    # return [t.token_name for t in tkns]

  
  # factory method to get a projectdb object
  @staticmethod
  def getProjDB(pr):
    """Return a the kvengine object"""
    
    # from ndproject import NDProject
    # pr = NDProject.fromName(project_name)
    if pr.kvengine == MYSQL:
      from mysqlprojdb import MySQLProjectDB
      return MySQLProjectDB(pr)
    elif pr.kvengine == REDIS:
      from redisprojdb import RedisProjectDB
      return RedisProjectDB(pr)
    else:
      logging.error ("Unknown KV Engine requested: {}".format(pr.kvengine))
      raise NDWSError ("Unknown KV Engine requested: {}".format(pr.kvengine))
