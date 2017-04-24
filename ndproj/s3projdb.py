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

import botocore
import boto3
import redis
from ndproj.ndproject import NDProject
from ndproj.ndchannel import NDChannel
from webservices.ndwserror import NDWSError
from ndingest.nddynamo.cuboidindexdb import CuboidIndexDB
from ndingest.ndbucket.cuboidbucket import CuboidBucket
from ndingest.settings.settings import Settings
ndingest_settings = Settings.load()
import logging
logger=logging.getLogger("neurodata")

class S3ProjectDB:
  """Database for the projects"""

  def __init__(self, pr):
    """Create the database connection"""
    self.pr = pr
    # create connections for cuboid bucket and cuboid dyanmo table
    self.cuboid_bucket = CuboidBucket(self.pr.project_name, endpoint_url=ndingest_settings.S3_ENDPOINT)
    self.cuboidindex_db = CuboidIndexDB(self.pr.project_name, endpoint_url=ndingest_settings.DYNAMO_ENDPOINT)

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
    """Delete a project in s3 and dyanmo"""
    
    try:
      for item in self.cuboidindex_db.queryProjectItems():
        self.cuboid_bucket.deleteObject(item['supercuboid_key'])
        self.cuboidindex_db.deleteItem(item['supercuboid_key'])
    except botocore.exceptions.ClientError as e:
      if e.response['Error']['Code'] == 'ResourceNotFoundException':
        logger.warning("Resource was not accessible {}".format(e))
        pass
      else:
        raise e
    except Exception as e:
      logger.error("Error in deleting S3 project {}. {}".format(self.pr.project_name, e))
      raise NDWSError("Error in deleting S3 project {}. {}".format(self.pr.project_name, e))


  def deleteNDChannel(self, channel_name):
    """Delete a channel in s3 and dynamo"""
    
    try:
      for item in self.cuboidindex_db.queryChannelItems(channel_name):
        self.cuboid_bucket.deleteObject(item['supercuboid_key'])
        self.cuboidindex_db.deleteItem(item['supercuboid_key'])
    except botocore.exceptions.ClientError as e:
      if e.response['Error']['Code'] == 'ResourceNotFoundException':
        logger.warning("Resource was not accessible {}".format(e))
        pass
      else:
        raise e
    except Exception as e:
      logger.error("Error in deleting S3 channel {}. {}".format(channel_name, e))
      raise NDWSError("Error in deleting S3 channel {}. {}".format(channel_name, e))

  def deleteNDResolution(self, channel_name, resolution):
    """Delete the resolution in s3 and dynamo"""

    try:
      for item in self.cuboidindex_db.queryResolutionItems(channel_name, resolution):
        self.cuboid_bucket.deleteObject(item['supercuboid_key'])
        self.cuboidindex_db.deleteItem(item['supercuboid_key'])
    except botocore.exceptions.ClientError as e:
      if e.response['Error']['Code'] == 'ResourceNotFoundException':
        logger.warning("Resource was not accessible {}".format(e))
        pass
      else:
        raise e
    except Exception as e:
      logger.error("Error in deleting S3 channel resolution {},{}. {}".format(channel_name, resolution, e))
      raise NDWSError("Error in deleting S3 channel resolution {},{}. {}".format(channel_name, resolution, e))

