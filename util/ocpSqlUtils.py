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

#
# SQL dump and ingest script for OCP databases. All projects and datasets supported.
#

import argparse
import sys
import os
import subprocess
from contextlib import closing
import MySQLdb

sys.path += [os.path.abspath('../django')]
import OCP.settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'OCP.settings'
from django.conf import settings
import django
django.setup()

import ocpcaproj
import ocpcaprivate
import ocpcadb
import annotation

# Helper Methods
def runCommand (cmd):
  """Run the command"""
  
  try:
    print cmd
    os.system(cmd)
  except Exception, e:
    print "Error, {}".format(e)
    raise Exception("Error, {}".format(e))


class SQLDatabase:

  def __init__(self, host, token, location):
    """ Load the database and project """

    with closing ( ocpcaproj.OCPCAProjectsDB() ) as projdb:
      self.proj = projdb.loadToken ( token )

    self.user = ocpcaprivate.dbuser
    self.password = ocpcaprivate.dbpasswd
    self.host = host
    self.token = token
    self.location = location
    self.starterString = '-u {} -p{} -h {}'.format( self.user, self.password, self.host )

    try:
      self.conn = MySQLdb.connect ( host = self.host, user = self.user, passwd = self.password, db = self.proj.getProjectName() ) 
      self.cursor = self.conn.cursor()    
    except MySQLdb.Error, e:
      print e

  def dumpBigTable( self, tableName ):
    """ Dump a very big Table """

    sql = "SELECT COUNT(*) FROM {}".format(tableName)
    self.cur.execute( sql )
    rowSize = self.cur.fetchone()
    cmd = 'mysqldump {}  -d {} {} > {}{}.{}_schema.sql'.format( self.starterString, self.token, tableName, self.location, self.token, tableName )
    runCommand(cmd)
    for i in range(0, rowSize[0], rowSize[0]/10):
        cmd = 'mysqldump {} {} {} --where "1 LIMIT {},{}" --no-create-info --skip-add-locks > {}{}.{}_{}.sql'.format ( self.starterString, self.token, tableName, i, (i-rowSize[0]) if (i-1+rowSize[0]/10) > rowSize[0] else (rowSize[0]/10), self.location, self.token, tableName, rowSize[0] if (i+rowSize[0]/10) > rowSize[0] else (i+  rowSize[0]/10) )
        runCommand(cmd)
    
    # Now ingesting this Big Table in the database

    cmd = 'mysql {} {} < {}{}.{}_schema.sql'.format( self.token, self.starterString, self.location, self.token, tableName )
    runCommand(cmd)
    for i in range(0, rowSize[0], rowSize[0]/10):
        cmd = 'mysql -h {} -u {} -p{} {} < {}{}.{}_{}.sql'.format ( "localhost", self.user, self.password, self.token, self.location, self.token, tableName, rowSize[0] if (i+rowSize[0]/10) > rowSize[0] else i+ rowSize[0]/10 )
        runCommand(cmd)

  
  def renameDatabase ( self, newDBName ):
    """Copy Tables from Database to another"""

    try:
      sql = "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE table_schema='{}'".format( self.token )
      print sql
      self.cursor.execute(sql)
      
      conn = MySQLdb.connect(host = self.host, user = self.user, passwd = self.password, db = newDBName) 
      cursor2 = conn2.cursor()
      
      sql = "CREATE DATABASE {}".format(newDBName)
      print sql
      cursor2.execute(sql)

      for row in self.cur.fetchall():
        sql = "RENAME TABLE {}.{} TO {}.{}".format(self.proj.getProjectName(), row[0], newDBName, row[0])
        print sql
        cursor2.execute(sql)
        sql = "DROP TABLE {}.{}".format(self.proj.getProjectName(), row[0])
        print sql
        self.cursor.execute(sql)

      sql = "DROP DATABASE {}".format(self.proj.getProjectName())
      self.cursor.execute(sql)

      self.conn.commit()
      conn2.commit()
    
    except MySQLdb.Error, e:
      self.conn.rollback()
      conn2.rollback()
      print "Error"
      raise Exception (e) 
    finally:
      self.cursor.close()
      conn2.cursor.close()


  def interface (self, ingest, channel_name=None):
    """Ingest/Dump the stack"""

    if channel_name is None:
      channel_list = [ch for ch in self.proj.projectChannels()]
    else:
      channel_list = [ocpcaproj.OCPCAChannel(self.proj, channel_name)]
    
    for ch in channel_list:
      if ch.getChannelType() in ocpcaproj.IMAGE_CHANNELS + ocpcaproj.TIMESERIES_CHANNELS:
        self.ingestImageChannel(ch) if ingest else self.dumpImageChannel(ch)
      elif ch.getChannelType() in ocpcaproj.ANNOTATION_CHANNELS:
        self.ingestAnnotataionChannel(ch) if ingest else self.dumpAnnotationChannel(ch)
      else:
        raise Exception("Error")


  def dumpImageChannel (self, ch):
    """Dump an Annotation Channel Stack"""

    for i in range(0, len(self.proj.datasetcfg.resolutions)):
      cmd = 'mysqldump {} {} --tables {} > {}{}.{}.sql'.format(self.starterString, self.proj.getProjectName(), ch.getTable(i), self.location, self.proj.getProjectName(), ch.getTable(i) )
      runCommand(cmd)


  def dumpAnnotationChannel (self, ch):
    """Dump an Image Channel Stack"""

    anno_tables = [ch.getIdsTable()]
    # Adding all the ids, idx and exceptions tables
    for i in range(0, len(self.proj.datasetcfg.resolutions)):
      anno_tables = anno_tables + [ch.getIdxTable(i),ch.getTable(i)]
      if ch.getExceptions == ocpcaproj.EXCEPTION_TRUE:
        anno_tables.append(ch.getExceptionsTable(i))
    
    # Adding all the anntype tables
    for key in annotation.anno_dbtables.keys():
      anno_tables.append(ch.getAnnoTable(key))
    
    cmd = 'mysqldump {} {} --tables {} > {}{}_{}.sql'.format(self.starterString, self.proj.getProjectName(), ' '.join(anno_tables), self.location, self.proj.getProjectName(), ch.getChannelName())
    runCommand(cmd)


  def ingestImageChannel (self, ch):
    """Ingest an Image Channel Stack"""

    for i in range(0, len(self.proj.datasetcfg.resolutions)):
      cmd = 'mysql {} {} < {}{}.{}.sql'.format(self.starterString, self.proj.getProjectName(), self.location, self.proj.getProjectName(), ch.getTable(i))
      runCommand(cmd)

  
  def ingestAnnotataionChannel (self, ch):
    """Ingest an Annotation Channel Stack"""

    cmd = 'mysql {} {} < {}{}.sql'.format(self.starterString, self.proj.getProjectName(), self.location, ch.getChannelName())
    runCommand(cmd)


def main():
  """Parse Arguments from User"""

  parser = argparse.ArgumentParser (description='Dump an Image Stack')
  parser.add_argument('--host', dest='host', action='store', default='localhost', help='HostName where to dump from(Deafault is localhost)')
  parser.add_argument('token', action='store', help='Token for the project.')
  parser.add_argument('location', action='store', help='Location where to store/load the dump')
  parser.add_argument('--channel', dest='channel', action='store', default=None, help='Specify a channel (will dump all channels for the project if ignored)')
  parser.add_argument('--dump', dest='dump', action='store_true', default=False, help='Dump the database')
  parser.add_argument('--ingest', dest='ingest', action='store_true', default=False, help='Ingest the database')
  parser.add_argument('--bigdump', dest='bigdump', help='Dump a big mysql table')
  parser.add_argument('--dbcopy', dest='dbcopy', action="store", default=None, help='Copy the database')
  parser.add_argument('--dbrename', dest='dbrename', action="store", default=None, help='Rename the database')

  result = parser.parse_args()
  sqldb = SQLDatabase(result.host, result.token, result.location)
  
  # Big dump of bock11
  if result.bigdump!=None:
    sqldb.dumpBigTable ( result.bigdump ) 

  # Renaming the database
  elif result.dbrename!=None:
    sqldb.renameTable(result.dbrename)

  # Copying the database
  elif result.dbcopy!=None:
    sqldb.interface(False, channel_name = result.channel)
    sqldb_remote = SQLDatabase ( result.host, result.dbcopy, result.location )
    sqldb_remote.interface(True, channel_name = result.channel)
  
  # Dumping/Ingesting the database
  elif (result.dump or result.ingest) and not(result.dump and result.ingest):
    if result.ingest:
      sqldb.interface(result.ingest, channel_name = result.channel)
    else:
      sqldb.interface(not result.dump, channel_name = result.channel)
    
  else:
      print "Error: Use atleast one option"

if __name__ == "__main__":
  main()
