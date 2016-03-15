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

import numpy as np
import cStringIO
import zlib
import re
from collections import defaultdict
import itertools
import blosc
from contextlib import closing
from operator import add, sub, div, mod
import MySQLdb

import ndlib
from ndtype import ANNOTATION_CHANNELS, TIMESERIES_CHANNELS, EXCEPTION_TRUE, PROPAGATED

import annotation

from ndwserror import NDWSError
import logging
logger=logging.getLogger("neurodata")

"""
.. module:: ramonddb
    :synopsis: Manipulate/create/read annotations in the ramon format

.. moduleauthor:: Kunal Lillaney <lillaney@jhu.edu>
"""

class MySQLRamonDB:

  def __init__ (self, proj):
    """Connect with the brain databases"""

    self.proj = proj

    # Connection info for the metadata
    try:
      self.conn = MySQLdb.connect (host = self.proj.getDBHost(), user = self.proj.getDBUser(), passwd = self.proj.getDBPasswd(), db = self.proj.getDBName())
      self.cursor = self.conn.cursor()
    except MySQLdb.Error, e:
      self.conn = None
      logger.error("Failed to connect to database: {}, {}".format(self.proj.getDBHost(), self.proj.getDBName()))


  def close ( self ):
    """Close the connection"""

    if self.cursor:
      self.cursor.close()
    if self.conn:
      self.conn.close()

  def commit ( self ):
    """Commit the transaction. Moved out of __del__ to make explicit.""" 

    if self.cursor is not None:
      self.cursor.close()
      self.conn.commit()

  def startTxn ( self ):
    """Start a transaction.  Ensure database is in multi-statement mode."""

    self.cursor = self.conn.cursor()
    sql = "START TRANSACTION"
    self.cursor.execute ( sql )

  def rollback ( self ):
    """Rollback the transaction.  To be called on exceptions."""

    self.cursor.close()
    self.conn.rollback()

  def nextID ( self, ch ):
    """Get an new identifier. This is it's own txn and should not be called inside another transaction."""

    with closing(self.conn.cursor()) as cursor:
    
      # LOCK the table to prevent race conditions on the ID
      sql = "LOCK TABLES {} WRITE".format(ch.getIdsTable())
      try:

        cursor.execute ( sql )

        # Query the current max identifier
        sql = "SELECT max(id) FROM {}".format(ch.getIdsTable()) 
        try:
          cursor.execute ( sql )
        except MySQLdb.Error, e:
          logger.error ( "Failed to create annotation identifier {}: {}. sql={}".format(e.args[0], e.args[1], sql))
          raise

        # Here we've queried the highest id successfully    
        row = cursor.fetchone ()
        # if the table is empty start at 1, 0 is no 
        if ( row[0] == None ):
          identifier = 1
        else:
          identifier = int ( row[0] ) + 1

        # increment and update query
        sql = "INSERT INTO {} VALUES ({})".format(ch.getIdsTable(), identifier)
        try:
          cursor.execute ( sql )
        except MySQLdb.Error, e:
          logger.error ( "Failed to insert into identifier table: {}: {}. sql={}".format(e.args[0], e.args[1], sql))
          raise

      finally:
        sql = "UNLOCK TABLES" 
        cursor.execute ( sql )
        self.conn.commit()

      return identifier


  def setID ( self, ch, annoid ):
    """Set a user specified identifier in the ids table"""

    with closing(self.conn.cursor()) as cursor:

      # LOCK the table to prevent race conditions on the ID
      sql = "LOCK TABLES {} WRITE".format( ch.getIdsTable() )
      try:
        # try the insert, get ane exception if it doesn't work
        sql = "INSERT INTO {} VALUES({})".format(ch.getIdsTable(), annoid)
        try:
          cursor.execute ( sql )
        except MySQLdb.Error, e:
          logger.warning ( "Failed to set identifier table: {}: {}. sql={}".format(e.args[0], e.args[1], sql))
          raise

      finally:
        sql = "UNLOCK TABLES" 
        cursor.execute ( sql )
        self.conn.commit()

    return annoid

  #
  #  setBatchID
  # 
  #  Place the user selected id into the ids table
  #
  def setBatchID ( self, annoidList ):
    """ Set a user specified identifier """

    with closing(self.conn.cursor()) as cursor:

      # LOCK the table to prevent race conditions on the ID
      sql = "LOCK TABLES {} WRITE".format(self.proj.getIdsTable())
      try:
        # try the insert, get and if it doesn't work
        sql = "INSERT INTO {} VALUES ( %s ) ".format( str(self.proj.getIdsTable()) )
        try:
          cursor.executemany ( sql, [str(i) for i in annoidList] )  
        except MySQLdb.Error, e:
          logger.warning ( "Failed to set identifier table: {}: {}. sql={}".format(e.args[0], e.args[1], sql))
          raise

      finally:
        sql = "UNLOCK TABLES" 
        cursor.execute ( sql )
        self.conn.commit()

    return annoidList


  def reserve ( self, ch, count ):
    """Reserve contiguous identifiers. This is it's own txn and should not be called inside another transaction."""

    with closing(self.conn.cursor()) as cursor:

      # LOCK the table to prevent race conditions on the ID
      sql = "LOCK TABLES {} WRITE".format( ch.getIdsTable() )
      try:
        cursor.execute ( sql )

        # Query the current max identifier
        sql = "SELECT max(id) FROM {}".format( ch.getIdsTable() ) 
        try:
          cursor.execute ( sql )
        except MySQLdb.Error, e:
          logger.error ( "Failed to create annotation identifier {}: {}. sql={}".format(e.args[0], e.args[1], sql))
          raise

        # Here we've queried the highest id successfully    
        row = cursor.fetchone ()
        # if the table is empty start at 1, 0 is no 
        if ( row[0] == None ):
          identifier = 0
        else:
          identifier = int ( row[0] ) 

        # increment and update query
        sql = "INSERT INTO {} VALUES ({}) ".format(ch.getIdsTable(), identifier+count)
        try:
          cursor.execute ( sql )
        except MySQLdb.Error, e:
          logger.error ( "Failed to insert into identifier table: {}: {}. sql={}".format(e.args[0], e.args[1], sql))
          raise

      except Exception, e:
        logger.error ( "Failed to insert into identifier table: {}: {}. sql={}".format(e.args[0], e.args[1], sql))

      finally:
        sql = "UNLOCK TABLES" 
        cursor.execute ( sql )
        self.conn.commit()

      return identifier+1


  def getAnnotationKV ( self, ch, annid ):

    sql = "SELECT kv_key, kv_value FROM {}_ramon WHERE annoid='{}'".format(ch.getChannelName(),annid)
    try:
      self.cursor.execute ( sql )
      pairs = self.cursor.fetchall()
    except MySQLdb.Error, e:
      logger.error ( "Failed to fetch annotation: {}: {}. sql={}".format(e.args[0], e.args[1], sql))
      raise
    
    if len(pairs) == 0:
      logger.error( "Failed to fetch annotation: {}: No annotation object found. sql={}".format( annid, sql ) )
      raise NDWSError( "Failed to fetch annotation: {}: No annotation object found. sql={}".format( annid, sql ) )
    
    # convert answer into a dictionary
    kvdict = defaultdict(list)
    for (k,v) in pairs:
      # detect multiple key values
      if kvdict[k]:
        if type(kvdict[k]) == list:
          kvdict[k].append(v)
        else:
          kvdict[k] = [kvdict[k],v]
      else:
        kvdict[k]=v

    return kvdict


  def putAnnotationKV ( self, ch, annid, kvdict, update=False ):
    """store an HDF5 annotation to the database"""

    if update:
      self.deleteAnnotation ( ch, annid )

    sql = "INSERT INTO {}_ramon (annoid, kv_key, kv_value) VALUES (%s,%s,%s)".format(ch.getChannelName())
 
    data = []
    for (k,v) in kvdict.iteritems():
      # blowout lists to multiple values
      if type(v) in [list,tuple]:
        [ data.append((annid,k,vv)) for vv in v ]
      else:
        data.append((annid,k,v))

    try:
      self.cursor.executemany ( sql, data )
    except MySQLdb.Error, e:
      import pdb; pdb.set_trace()
      logger.error ( "Failed to put annotation: {}: {}. sql={}".format(e.args[0], e.args[1], sql))
      raise


  def deleteAnnotation ( self, ch, annoid ):
    """delete an HDF5 annotation from the database"""

    sql = "DELETE FROM {}_ramon WHERE annoid={}".format(ch.getChannelName(),annoid)
    try:
      self.cursor.execute ( sql )
    except MySQLdb.Error, e:
      logger.error ( "Failed to delete annotation: {}: {}. sql={}".format(e.args[0], e.args[1], sql))
      raise


  # getAnnoObjects:
  #    Return a list of annotation object IDs
  #  for now by type and status
  def getAnnoObjects ( self, ch, args ):
    """Return a list of annotation object ids that match equality predicates.
      Legal predicates are currently:
        type
        status
      Predicates are given in a dictionary.
    """

    # legal equality fields
    eqfields = ( 'type', 'status' )
    # legal comparative fields
    compfields = ( 'confidence' )

    # dictionary to look up key name.  this should be rewritten to
    # be replaced in a higher level module.  the fields are defined 
    # in annotation.py
    key_name = { 'type' : 'ann_type',\
                  'status' : 'ann_status',\
                  'confidence' : 'ann_confidence' }

    # start of the SQL clause
    sql = "SELECT annoid FROM {}_ramon".format(ch.getChannelName())
    clause = ''
    limitclause = ""

    # iterate over the predicates
    it = iter(args)
    try:

      field = it.next()

      # build a query for all the predicates
      while ( field ):

        # provide a limit clause for iterating through the database
        if field == "limit":
          val = it.next()
          if not re.match('^\d+$',val):
            logger.warning ( "Limit needs an integer. Illegal value:%s" % (field,val) )
            raise OCPCAError ( "Limit needs an integer. Illegal value:%s" % (field,val) )

          limitclause = " LIMIT %s " % (val)


        # all other clauses
        else:
          if clause == '':
            clause += " WHERE "
          else:
            clause += ' AND '

          if field in compfields:

            opstr = it.next()
            if opstr == 'lt':
              op = ' < '
            elif opstr == 'gt':
              op = ' > '
            else:
              logger.warning ( "Not a comparison operator: %s" % (opstr) )
              raise OCPCAError ( "Not a comparison operator: %s" % (opstr) )

            val = it.next()
            if not re.match('^[\d\.]+$',val):
              logger.warning ( "For field %s. Illegal value:%s" % (field,val) )
              raise OCPCAError ( "For field %s. Illegal value:%s" % (field,val) )
            clause += "kv_key = '%s' AND kv_value %s %s" % ( key_name[field], op, val )

          # all other fields have equality predicates
          # rewrite those in interface 
          elif field in eqfields:
            val = it.next()
            clause += "kv_key = '%s' AND kv_value = '%s'" % ( key_name[field], val )

          # all others are kv equality
          else: 
            val = it.next()
            clause += "kv_key = '%s' AND kv_value = '%s'" % ( field, val )

        field = it.next()

    except StopIteration:
      pass

    sql += clause + limitclause + ';'

    try:
      self.cursor.execute ( sql )
      annoids = np.array ( self.cursor.fetchall(), dtype=np.uint32 ).flatten()
    except MySQLdb.Error, e:
      logger.error ( "Error retrieving ids: %d: %s. sql=%s" % (e.args[0], e.args[1], sql))
      raise

    return np.array(annoids)


  def querySegments ( self, ch, annid ):
    """Return segments that belong to this neuron"""

    sql = "SELECT annoid FROM {}_ramon WHERE kv_key='{}' AND kv_value={}".format(ch.getChannelName(), 'seg_neuron', annid)

    try:
      self.cursor.execute ( sql )
    except MySQLdb.Error, e:
      logger.warning ( "Error querying neuron segments %d: %s. sql=%s" % (e.args[0], e.args[1], sql))
      raise NDWSError ( "Error querying neuron segments %d: %s. sql=%s" % (e.args[0], e.args[1], sql))

    return np.array(self.cursor.fetchall(), dtype=np.uint32).flatten()


  def queryROIChildren ( self, ch, annid ):
    """Return children that belong to this ROI"""

    sql = "SELECT annoid FROM {}_ramon WHERE kv_key='{}' AND kv_value={}".format(ch.getChannelName(), 'roi_parent', annid)

    try:
      self.cursor.execute ( sql )
    except MySQLdb.Error, e:
      logger.warning ( "Error querying children %d: %s. sql=%s" % (e.args[0], e.args[1], sql))
      raise NDWSError ( "Error querying children %d: %s. sql=%s" % (e.args[0], e.args[1], sql))

    return np.array(self.cursor.fetchall(), dtype=np.uint32).flatten()

  def queryNodeChildren ( self, ch, annid ):
    """Return children that belong to this ROI"""

    sql = "SELECT annoid FROM {}_ramon WHERE kv_key='{}' AND kv_value={}".format(ch.getChannelName(), 'roi_parent', annid)

    try:
      self.cursor.execute ( sql )
    except MySQLdb.Error, e:
      logger.warning ( "Error querying children %d: %s. sql=%s" % (e.args[0], e.args[1], sql))
      raise NDWSError ( "Error querying children %d: %s. sql=%s" % (e.args[0], e.args[1], sql))

    return np.array(self.cursor.fetchall(), dtype=np.uint32).flatten()

  def querySkeletonNodes ( self, ch, annid ):
    """Return the nodes that belong to this skeleton"""

    # two lists for marked and processed nodes in a tree search
    skelnodes = []
    activenodes = []

    # get the root node of the skeleton
    sql = "SELECT kv_value FROM {}_ramon WHERE kv_key='{}' and annoid={}".format(ch.getChannelName(), 'skel_rootnode', annid)

    try:
      self.cursor.execute ( sql )
    except MySQLdb.Error, e:
      logger.warning ( "Error querying skeleton rootnode %d: %s. sql=%s" % (e.args[0], e.args[1], sql))
      raise NDWSError ( "Error querying skeleton rootnode %d: %s. sql=%s" % (e.args[0], e.args[1], sql))

    activenodes.append ( int(self.cursor.fetchone()[0]))

    while len(activenodes) != 0:
   
      cur = activenodes.pop()
      skelnodes.append(cur)
      print "adding {} to skelnodes {}".format(cur, skelnodes)

      # get all children of active node
      sql = "SELECT annoid FROM {}_ramon WHERE kv_key='{}' AND kv_value={}".format(ch.getChannelName(), 'node_parent', cur)

      try:
        self.cursor.execute ( sql )
      except MySQLdb.Error, e:
        logger.warning ( "Error querying children %d: %s. sql=%s" % (e.args[0], e.args[1], sql))
        raise NDWSError ( "Error querying children %d: %s. sql=%s" % (e.args[0], e.args[1], sql))

      [ activenodes.append(x) for x in np.array(self.cursor.fetchall(), dtype=np.uint32).flatten() ]

    return np.array(skelnodes, dtype=np.uint32)


  def querySynapses ( self, ch, annid ):
    """Return synapses that belong to this segment"""

    sql = "SELECT annoid FROM {}_ramon WHERE kv_key='{}' AND kv_value={}".format(ch.getChannelName(), 'syn_segments', annid)

    try:
      self.cursor.execute ( sql )
    except MySQLdb.Error, e:
      logger.warning ( "Error querying synapses %d: %s. sql=%s" % (e.args[0], e.args[1], sql))
      raise NDWSError ( "Error querying synapses %d: %s. sql=%s" % (e.args[0], e.args[1], sql))

    return np.array(self.cursor.fetchall(), dtype=np.uint32).flatten()

  def queryPreSynapses ( self, ch, annid ):
    """Return presynaptic synapses that belong to this segment"""
  
    sql = "SELECT annoid FROM {}_ramon WHERE kv_key='{}' AND kv_value={}".format(ch.getChannelName(), 'syn_presegments', annid)

    try:
      self.cursor.execute ( sql )
    except MySQLdb.Error, e:
      logger.warning ( "Error querying synapses %d: %s. sql=%s" % (e.args[0], e.args[1], sql))
      raise NDWSError ( "Error querying synapses %d: %s. sql=%s" % (e.args[0], e.args[1], sql))

    return np.array(self.cursor.fetchall(), dtype=np.uint32).flatten()

  def queryPostSynapses ( self, ch, annid ):
    """Return postsynaptic synapses that belong to this segment"""

    sql = "SELECT annoid FROM {}_ramon WHERE kv_key='{}' AND kv_value={}".format(ch.getChannelName(), 'syn_postsegments', annid)

    try:
      self.cursor.execute ( sql )
    except MySQLdb.Error, e:
      logger.warning ( "Error querying synapses %d: %s. sql=%s" % (e.args[0], e.args[1], sql))
      raise NDWSError ( "Error querying synapses %d: %s. sql=%s" % (e.args[0], e.args[1], sql))

    return np.array(self.cursor.fetchall(), dtype=np.uint32).flatten()

  def queryOrganelles ( self, ch, annid ):
    """Return organelles that belong to this segment"""

    sql = "SELECT annoid FROM {}_ramon WHERE kv_key='{}' AND kv_value={}".format(ch.getChannelName(), 'org_segment', annid)

    try:
      self.cursor.execute ( sql )
    except MySQLdb.Error, e:
      logger.warning ( "Error querying synapses %d: %s. sql=%s" % (e.args[0], e.args[1], sql))
      raise NDWSError ( "Error querying synapses %d: %s. sql=%s" % (e.args[0], e.args[1], sql))

    return np.array(self.cursor.fetchall(), dtype=np.uint32).flatten()


