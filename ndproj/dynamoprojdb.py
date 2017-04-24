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

import boto3

from ndchannel import NDChannel
from ndproject import NDProject

from ndwserror import NDWSError
import logging
logger=logging.getLogger("neurodata")

class DynamoProjDB:

  def __init__(self, project_name):
    """Create the database connection"""
    self.pr = NDProject(project_name)
    self.dynamodb = boto3.resource('dynamodb')
  

  def close(self):
    """Close the database connection"""
    pass
  
  def newNDProject(self, project_name):
    """Create the database for a project"""
    pass 
  

  def newNDChannel(self, project_name, channel_name):
    """Create the tables for a channel"""
    
    ch = NDChannel(self.pr, channel_name)
    
    try:
      ctable = self.dynamodb.create_table(
        # RB TODO add user name
        TableName = ch.getTable(),
        KeySchema = [
          {
            'AttributeName': 'cuboidkey',
            'KeyType': 'HASH'
          },
        ],
        AttributeDefinitions = [
          {
            'AttributeName': 'cuboidkey',
            'AttributeType': 'S'
          },
          {
            'AttributeName': 'cuboid',
            'AttributeType': 'B'
          },
        ],
        ProvisionedThroughput = {
          'ReadCapacityUnits': 10,
          'WriteCapacityUnits': 10
        },
      )

      # itable = dynamodb.create_table(
        # TableName = ch.getIdxTable(),
        # KeySchema=[
          # {
            # 'AttributeName': 'idxkey',
            # 'KeyType': 'HASH'
          # },
        # ],
        # AttributeDefinitions=[
          # {
            # 'AttributeName': 'idxkey',
            # 'AttributeType': 'S'
          # },
          # {
            # 'AttributeName': 'idx',
            # 'AttributeType': 'B'
          # },
        # ],
        # ProvisionedThroughput={
          # 'ReadCapacityUnits': 10,
          # 'WriteCapacityUnits': 10
        # },
      # )

      # etable = dynamodb.create_table(
        # TableName='{}_{}_exc'.format(pr.getProjectName(), ch.getChannelName()),
        # KeySchema=[
          # {
            # 'AttributeName': 'exckey',
            # 'KeyType': 'HASH'
          # },
        # ],
        # AttributeDefinitions=[
          # {
            # 'AttributeName': 'exckey',
            # 'AttributeType': 'S'
          # },
          # {
            # 'AttributeName': 'exc',
            # 'AttributeType': 'B'
          # },
        # ],
        # ProvisionedThroughput={
          # 'ReadCapacityUnits': 10,
          # 'WriteCapacityUnits': 10
        # },
      # )

      # wait for the tables to exist
      ctable.meta.client.get_waiter('table_exists').wait(TableName = ch.getTable())
      # itable.meta.client.get_waiter('table_exists').wait(TableName='{}_{}_idx'.format(pr.project_name, ch.channel_name))
      # etable.meta.client.get_waiter('table_exists').wait(TableName='{}_{}_exc'.format(pr.project_name, ch.channel_name))
    
    except Exception, e:
      ch.deleteChannel()
      logger.warning("Cannot create DynamoDB Table {}".format(channel_name))
      raise NDWSError("Cannot create DynamoDB Table {}".format(channel_name))


  def deleteNDProject(self, project_name):
    """Delete the database for a project"""
    
    pass

    # KL Why do we need these??
    # pr = NDProject(project_name)
    # # iterate over all the possible tables.  No name space delete.
    # channel_list = Channel.objects.filter(project_id=pr)
    # for ch in channel_list:
      # self.deleteNDChannel ( proj, ch.channel_name )


  def deleteNDChannel(self, channel_name):
    """Delete the tables for a channel"""
    
    ch = NDChannel(self.pr, channel_name)
    table_list = []


    table_list = [ ch.getTable() ]
    
    for table_name in table_list:
      try:
        table = self.dynamodb.Table(table_name)
        table.delete()
      except Exception, e:
        logger.warning("Channel table {} in DynamoDB does not exist".format(channel_name))
        pass
