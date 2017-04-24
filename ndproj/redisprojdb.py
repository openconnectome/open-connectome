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

import redis
from ndproj.ndproject import NDProject
from ndproj.ndchannel import NDChannel
from ndproj.s3projdb import S3ProjectDB
from django.conf import settings
from webservices.ndwserror import NDWSError
import logging
logger=logging.getLogger("neurodata")

class RedisProjectDB:
  """Database for the projects"""

  def __init__(self, pr):
    """Create the database connection"""
    self.pr = pr
    # Connect to the redis cluster
    try:
      self.client = redis.StrictRedis(host=self.pr.host, port=6379, db=0)
      self.pipe = self.client.pipeline(transaction=False)
      # delete from S3 when deleting from Redis
      self.s3_proj = S3ProjectDB(pr)
    except redis.ConnectionError as e:
      logger.error("Cannot connect to Redis server. {}".format(e))
      raise NDWSError("Cannot connect to Redis server. {}".format(e))
    except Exception as e:
      logger.error("Unknown error while connecting to Redis. {}".format(e))
      raise NDWSError("Unknown error while connecting to Redis. {}".format(e))

  def __del__(self):
    """Close the database connection"""
    self.close()

  def close (self):
    """Close the database connection"""
    pass


  def newNDProject(self):
    """Create the database for a project."""
    pass
  

  def newNDChannel(self, channel_name):
    """Create the tables for a channel."""
    pass


  def deleteNDProject(self):
    """Delete the database for a project"""
    
    # KL TODO Is this redundant since all channels must be deleted before project is dropped?
    try:
      # removing keys for kvio data
      # project pattern to fetch all the keys with project_name&
      project_pattern = "{}&*".format(self.pr.project_name)
      project_keys = self.client.keys(project_pattern)
      # delete all the keys with the pattern
      if project_keys:
        self.client.delete(*project_keys)
      # removing keys for kvindex data
      index_min_pattern = "[{}".format(self.pr.project_name)
      index_max_pattern = "+"
      self.client.zremrangebylex(settings.REDIS_INDEX_KEY, index_min_pattern, index_max_pattern)
      # deleteting from s3 and dynamo
      self.s3_proj.deleteNDProject()
    except Exception as e:
      logger.error("Error in deleting Redis project {}. {}".format(self.pr.project_name, e))
      raise NDWSError("Error in deleting Redis project {}. {}".format(self.pr.project_name, e))


  def deleteNDChannel(self, channel_name):
    """Delete the keys for a channel"""
    
    # KL TODO Maybe do this as a transaction or lock the cache when we drop the channel?
    try:
      # removing keys related to kvio data
      # channel pattern to fetch all the keys with project_name&channel_name&
      channel_pattern = "{}&{}&*".format(self.pr.project_name, channel_name)
      channel_keys = self.client.keys(channel_pattern)
      # delete all the keys with the pattern
      if channel_keys:
        self.client.delete(*channel_keys)
      # removing keys related to kvindex data
      index_min_pattern = "[{}&{}".format(self.pr.project_name, channel_name)
      index_max_pattern = "+"
      self.client.zremrangebylex(settings.REDIS_INDEX_KEY, index_min_pattern, index_max_pattern)
      # deleteting from s3 and dynamo
      self.s3_proj.deleteNDChannel(channel_name)
    except Exception as e:
      logger.error("Error in deleting channel {}. {}".format(channel_name, e))
      raise NDWSError("Error in deleting channel {}. {}".format(channel_name, e))

  def deleteNDResolution(self, channel_name, resolution):
    """Delete the resolution for a channel"""
    
    # KL TODO Maybe do this as a transaction or lock the cache when we drop the channel?
    try:
      # removing keys for kvio
      # resolution pattern to fetch all keys with project_name&channel_name&resolution&
      resolution_pattern = "{}&{}&{}&*".format(self.pr.project_name, channel_name, resolution)
      resolution_keys = self.client.keys(channel_pattern)
      # delete all the keys with pattern
      if resolution_keys:
        self.client.delete(*resolution_keys)
      # removing keys for kvindex data
      index_min_pattern = "[{}&{}&{}".format(self.pr.project_name, channel_name, resolution)
      index_max_pattern = "+"
      self.client.zremrangebylex(settings.REDIS_INDEX_KEY, index_min_pattern, index_max_pattern)
      # deleteting from s3 and dynamo
      self.s3_proj.deleteNDResolution(channel_name, resolution)
    except Exception as e:
      logger.error("Error in deleting resolution {} channel {}. {}".format(resolution, channel_name, e))
      raise NDWSError("Error in deleting resolution {} channel {}. {}".format(resolution, channel_name, e))
