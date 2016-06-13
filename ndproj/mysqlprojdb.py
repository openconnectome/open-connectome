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

import MySQLdb
from contextlib import closing

from django.conf import settings
from ndproject import NDProject
from ndchannel import NDChannel

import annotation
from ndtype import *

from ndwserror import NDWSError
import logging
logger=logging.getLogger("neurodata")

class MySQLProjectDB:
  """Database for the projects"""

  def __init__(self, project_name):
    """Create the database connection"""
    # connect to the database
    self.pr = NDProject(project_name)

  def __del__(self):
    """Close the database connection"""
    self.close()
  
  def close (self):
    """Close the database connection"""
    pass

  def newNDProject(self):
    """Create the database for a project"""
    
    with closing(MySQLdb.connect (host = self.pr.getDBHost(), user = settings.DATABASES['default']['USER'], passwd = settings.DATABASES['default']['PASSWORD'], db = settings.DATABASES['default']['NAME'], connect_timeout=1)) as conn:
      with closing(conn.cursor()) as cursor:

        try:
          # create the database
          sql = "CREATE DATABASE {}".format(self.pr.getDBName())
       
          cursor.execute(sql)
          conn.commit()
        
        except MySQLdb.Error, e:
          logger.error("Failed to create database for new project {}: {}. sql={}".format(e.args[0], e.args[1], sql))
          raise NDWSError("Failed to create database for new project {}: {}. sql={}".format(e.args[0], e.args[1], sql))
  

  def newNDChannel(self, channel_name):
    """Create the tables for a channel"""

    ch = NDChannel(self.pr, channel_name)

    # Connect to the database

    with closing(MySQLdb.connect(host = self.pr.getDBHost(), user = settings.DATABASES['default']['USER'], passwd = settings.DATABASES['default']['PASSWORD'], db = self.pr.getDBName(), connect_timeout=1)) as conn:
      with closing(conn.cursor()) as cursor:
        
        try:
          # tables specific to all other non time data
          if ch.getChannelType() not in [TIMESERIES]:
            for res in self.pr.datasetcfg.getResolutions():
              cursor.execute("CREATE TABLE {} ( zindex BIGINT PRIMARY KEY, cube LONGBLOB )".format(ch.getTable(res)))
              cursor.execute ( "CREATE TABLE {} (zindex BIGINT NOT NULL PRIMARY KEY)".format(ch.getS3IndexTable(res)) )
          # tables specific to timeseries data
          elif ch.getChannelType() == TIMESERIES:
            for res in self.pr.datasetcfg.getResolutions():
              cursor.execute("CREATE TABLE {} ( zindex BIGINT, timestamp INT, cube LONGBLOB, PRIMARY KEY(zindex,timestamp))".format(ch.getTable(res)))
              cursor.execute ( "CREATE TABLE {} (zindex BIGINT NOT NULL, timestamp INT NOT NULL, PRIMARY KEY(zindex,timestamp))".format(ch.getS3IndexTable(res)))
          else:
            raise NDWSError("Channel type {} does not exist".format(ch.getChannelType()))
          
          # tables specific to annotation projects
          if ch.getChannelType() == ANNOTATION: 
            cursor.execute("CREATE TABLE {} ( id BIGINT PRIMARY KEY)".format(ch.getIdsTable()))
            # And the RAMON objects
            cursor.execute("CREATE TABLE {} ( annoid BIGINT, kv_key VARCHAR(255), kv_value VARCHAR(20000), INDEX ( annoid, kv_key ) USING BTREE)".format(ch.getRamonTable()))
            for res in self.pr.datasetcfg.getResolutions():
              cursor.execute("CREATE TABLE {} ( zindex BIGINT, id BIGINT, exlist LONGBLOB, PRIMARY KEY ( zindex, id))".format(ch.getExceptionsTable(res)))
              cursor.execute("CREATE TABLE {} ( annid BIGINT PRIMARY KEY, cube LONGBLOB )".format(ch.getIdxTable(res)))
         
          # Commiting at the end
          conn.commit()
        except MySQLdb.Error, e:
          ch.deleteChannel()
          logging.error ("Failed to create tables for new project {}: {}.".format(e.args[0], e.args[1]))
          raise NDWSError ("Failed to create tables for new project {}: {}.".format(e.args[0], e.args[1]))


  def deleteNDProject(self):
    """Delete the database for a project"""

    try:
      with closing(MySQLdb.connect (host = self.pr.getDBHost(), user = settings.DATABASES['default']['USER'], passwd = settings.DATABASES['default']['PASSWORD'], connect_timeout=1)) as conn:
        with closing(conn.cursor()) as cursor:
          # delete the database
          sql = "DROP DATABASE {}".format(self.pr.getDBName())

          try:
            cursor.execute(sql)
            conn.commit()
          except MySQLdb.Error, e:
            # Skipping the error if the database does not exist
            if e.args[0] == 1008:
              logger.warning("Database {} does not exist".format(self.pr.getDBName()))
              pass
            else:
              conn.rollback()
              logger.error("Failed to drop project database {}: {}. sql={}".format(e.args[0], e.args[1], sql))
              raise NDWSError("Failed to drop project database {}: {}. sql={}".format(e.args[0], e.args[1], sql))
    except MySQLdb.OperationalError as e:
      logger.warning("Cannot connect to the server at host {}. {}".format(self.pr.getDBHost(), e))

  def deleteNDChannel(self, channel_name):
    """Delete the tables for this channel"""
    
    ch = NDChannel(self.pr, channel_name)
    table_list = []

    if ch.getChannelType() in ANNOTATION_CHANNELS:
      table_list.append(ch.getIdsTable())
      # for key in annotation.anno_dbtables.keys():
        # table_list.append(ch.getAnnoTable(key))

    for res in self.pr.datasetcfg.getResolutions():
      table_list.append(ch.getTable(res))
      table_list.append(ch.getS3IndexTable(res))
      if ch.getChannelType() in ANNOTATION_CHANNELS:
        table_list = table_list + [ch.getIdxTable(res), ch.getExceptionsTable(res)]

    with closing(MySQLdb.connect(host = self.pr.getDBHost(), user = settings.DATABASES['default']['USER'], passwd = settings.DATABASES['default']['PASSWORD'], db = self.pr.getDBName(), connect_timeout=1)) as conn:
      with closing(conn.cursor()) as cursor:
        
        # delete the tables for this channel
        sql = "DROP TABLES IF EXISTS {}".format(','.join(table_list))
        try: 
          cursor.execute (sql)
          conn.commit()
        except MySQLdb.Error, e:
          # Skipping the error if the table does not exist
          if e.args[0] == 1051:
            pass
          if e.args[0] == 1049:
            pass
          else:
            conn.rollback()
            logger.error("Failed to drop channel tables {}: {}. sql={}".format(e.args[0], e.args[1], sql))
            raise NDWSError("Failed to drop channel tables {}: {}. sql={}".format(e.args[0], e.args[1], sql))
