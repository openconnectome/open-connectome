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
# from ndproject import NDProject
from ndproj.ndchannel import NDChannel
from ndlib.ndtype import *
from webservices.ndwserror import NDWSError
import logging
logger=logging.getLogger("neurodata")

class MySQLProjectDB:
  """Database for the projects"""

  def __init__(self, pr):
    """Create the database connection"""
    # connect to the database
    # self.pr = NDProject(project_name)
    self.pr = pr

  def __del__(self):
    """Close the database connection"""
    self.close()
  
  def close (self):
    """Close the database connection"""
    pass

  def newNDProject(self):
    """Create the database for a project"""

    with closing(MySQLdb.connect (host = self.pr.host, user = settings.DATABASES['default']['USER'], passwd = settings.DATABASES['default']['PASSWORD'], db = settings.DATABASES['default']['NAME'], connect_timeout=1)) as conn:
      with closing(conn.cursor()) as cursor:

        try:
          # create the database
          sql = "CREATE DATABASE {}".format(self.pr.dbname)
       
          cursor.execute(sql)
          conn.commit()
        
        except MySQLdb.Error, e:
          logger.error("Failed to create database for new project {}: {}.".format(e.args[0], e.args[1]))
          raise NDWSError("Failed to create database for new project {}: {}.".format(e.args[0], e.args[1]))
  
  def updateNDChannel(self, channel_name):
    """Create the tables for a channel"""

    ch = NDChannel.fromName(self.pr, channel_name)

    # connect to the database
    with closing(MySQLdb.connect(host = self.pr.host, user = settings.DATABASES['default']['USER'], passwd = settings.DATABASES['default']['PASSWORD'], db = self.pr.dbname, connect_timeout=1)) as conn:
      with closing(conn.cursor()) as cursor:
        
        try:
          # tables specific to all other non time data
          for res in self.pr.datasetcfg.resolutions:
            cursor.execute("CREATE TABLE {} ( zindex BIGINT, timestamp INT, cube LONGBLOB, PRIMARY KEY(zindex,timestamp))".format(ch.getNearIsoTable(res)))
            cursor.execute("ALTER TABLE {} ADD timestamp INT AFTER zindex".format(ch.getTable(res)))
            cursor.execute("UPDATE {} set timestamp={}".format(ch.getTable(res), 0))
            cursor.execute("ALTER TABLE {} DROP PRIMARY KEY, ADD PRIMARY KEY(zindex, timestamp)".format(ch.getTable(res)))
        
          # Commiting at the end
          conn.commit()
        except MySQLdb.Error, e:
          logging.error ("Failed to create neariso tables for existing project {}: {}.".format(e.args[0], e.args[1]))
          raise NDWSError ("Failed to create neariso tables for existing project {}: {}.".format(e.args[0], e.args[1]))

  def newNDChannel(self, channel_name):
    """Create the tables for a channel"""

    ch = NDChannel.fromName(self.pr, channel_name)

    # connect to the database
    with closing(MySQLdb.connect(host = self.pr.host, user = settings.DATABASES['default']['USER'], passwd = settings.DATABASES['default']['PASSWORD'], db = self.pr.dbname, connect_timeout=1)) as conn:
      with closing(conn.cursor()) as cursor:
        
        try:
          # tables specific to all other non time data
          for res in self.pr.datasetcfg.resolutions:
            cursor.execute("CREATE TABLE {} ( zindex BIGINT, timestamp INT, cube LONGBLOB, PRIMARY KEY(zindex,timestamp))".format(ch.getTable(res)))
            if self.pr.datasetcfg.scalingoption == ZSLICES:
              cursor.execute("CREATE TABLE {} ( zindex BIGINT, timestamp INT, cube LONGBLOB, PRIMARY KEY(zindex,timestamp))".format(ch.getNearIsoTable(res)))
        
          # tables specific to annotation projects
          if ch.channel_type == ANNOTATION: 
            cursor.execute("CREATE TABLE {} ( id BIGINT PRIMARY KEY)".format(ch.getIdsTable()))
            # And the RAMON objects
            cursor.execute("CREATE TABLE {} ( annoid BIGINT, kv_key VARCHAR(255), kv_value VARCHAR(20000), INDEX ( annoid, kv_key ) USING BTREE)".format(ch.getRamonTable()))
            for res in self.pr.datasetcfg.resolutions:
              cursor.execute("CREATE TABLE {} ( zindex BIGINT, timestamp INT NOT NULL, id BIGINT, exlist LONGBLOB, PRIMARY KEY ( zindex, timestamp, id))".format(ch.getExceptionsTable(res)))
              cursor.execute("CREATE TABLE {} ( annid BIGINT, timestamp INT NOT NULL, cube LONGBLOB, PRIMARY KEY ( annid, timestamp ))".format(ch.getIdxTable(res)))
         
          # Commiting at the end
          conn.commit()
        except MySQLdb.Error, e:
          ch.deleteChannel()
          logging.error ("Failed to create tables for new project {}: {}.".format(e.args[0], e.args[1]))
          raise NDWSError ("Failed to create tables for new project {}: {}.".format(e.args[0], e.args[1]))


  def deleteNDProject(self):
    """Delete the database for a project"""

    try:
      with closing(MySQLdb.connect (host = self.pr.host, user = settings.DATABASES['default']['USER'], passwd = settings.DATABASES['default']['PASSWORD'], connect_timeout=1)) as conn:
        with closing(conn.cursor()) as cursor:
          # delete the database
          sql = "DROP DATABASE {}".format(self.pr.dbname)

          try:
            cursor.execute(sql)
            conn.commit()
          except MySQLdb.Error, e:
            # Skipping the error if the database does not exist
            if e.args[0] == 1008:
              logger.warning("Database {} does not exist".format(self.pr.dbname))
              pass
            else:
              conn.rollback()
              logger.error("Failed to drop project database {}: {}. sql={}".format(e.args[0], e.args[1], sql))
              raise NDWSError("Failed to drop project database {}: {}. sql={}".format(e.args[0], e.args[1], sql))
    except MySQLdb.OperationalError as e:
      logger.warning("Cannot connect to the server at host {}. {}".format(self.pr.host, e))

  def deleteNDChannel(self, channel_name):
    """Delete the tables for this channel"""
    
    ch = NDChannel.fromName(self.pr, channel_name)
    table_list = []

    if ch.channel_type in ANNOTATION_CHANNELS:
      # delete the ids table
      table_list.append(ch.getIdsTable())
      # delete the ramon table
      table_list.append(ch.getRamonTable())

    for res in self.pr.datasetcfg.resolutions:
      # delete the res tables
      table_list.append(ch.getTable(res))
      if self.pr.datasetcfg.scalingoption == ZSLICES:
        table_list.append(ch.getNearIsoTable(res))
      # delete the index tables
      table_list.append(ch.getS3IndexTable(res))
      if ch.channel_type in ANNOTATION_CHANNELS:
        # delete the exceptions tables
        table_list = table_list + [ch.getIdxTable(res), ch.getExceptionsTable(res)]

    try:
      with closing(MySQLdb.connect(host = self.pr.host, user = settings.DATABASES['default']['USER'], passwd = settings.DATABASES['default']['PASSWORD'], db = self.pr.dbname, connect_timeout=1)) as conn:
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
    except Exception as e:
      logger.warning("Database {} on host {} not found".format(self.pr.dbname, self.pr.host))
