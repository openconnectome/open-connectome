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

import numpy as np
import cStringIO
import MySQLdb
from collections import defaultdict

from ocpcaerror import OCPCAError 
import logging
logger=logging.getLogger("ocp")


"""Classes that hold annotation metadata"""

# Annotation types
ANNO_ANNOTATION = 1
ANNO_SYNAPSE = 2
ANNO_SEED = 3
ANNO_SEGMENT = 4
ANNO_NEURON = 5
ANNO_ORGANELLE = 6

#KLTODO -- where did synseg come from?
#  This table is not getting created or deleted
# list of database table names.  Move to annproj?
anno_dbtables = { 'annotation':'annotations',\
                  'kvpairs':'kvpairs',\
                  'synapse':'synapses',\
                  'segment':'segments',\
#                  'synseg':'synseg',\
                  'organelle':'organelles',\
                  'seed':'seeds' }


###############  Annotation  ##################

class Annotation:
  """Metdata common to all annotations."""

  def __init__ ( self, annodb ):
    """Initialize the fields to zero or null"""

    # database to which this annotation is registered
    self.annodb = annodb

    # metadata fields
    self.annid = 0 
    self.status = 0 
    self.confidence = 0.0 
    self.author = ""
    self.kvpairs = defaultdict(list)

  def setID ( self, ch, db ):
    """if annid == 0, create a new identifier"""
    if self.annid == 0: 
      self.annid = db.nextID(ch)
    else:
      db.setID(ch, self.annid)

  def getField ( self, ch, field ):
    """Accessor by field name"""

    if field == 'status':
      return self.status
    elif field == 'confidence':
      return self.confidence
    elif field == 'author':
      return self.author
    elif self.kvpairs.get(field):
      return self.kvpairs[field]
    else:
      logger.warning ( "getField: No such field %s" % (field))
      raise OCPCAError ( "getField: No such field %s" % (field))

  def setField ( self, ch, field, value ):
    """Mutator by field name.  Then need to store the field."""
    
    if field == 'status':
      self.status = value
    elif field == 'confidence':
      self.confidence = value
    elif field == 'author':
      self.author = value
    # if we don't recognize the field, store it as a kv pair.
    else: 
      self.kvpairs[field]=value
#    else:
#     logger.warning ( "setField: No such or can't update field %s" % (field))
#     raise OCPCAError ( "setField: No such or can't update field %s" % (field))

  def store ( self, ch, cursor, annotype=ANNO_ANNOTATION ):
    """Store the annotation to the annotations database"""

    sql = "INSERT INTO {} VALUES ( {}, {}, {}, {} )".format( ch.getAnnoTable('annotation'), self.annid, annotype, self.confidence, self.status )

    try:
      cursor.execute(sql)
    except MySQLdb.Error, e:
      logger.warning ( "Error inserting annotation %d: %s. sql=%s" % (e.args[0], e.args[1], sql))
      raise OCPCAError ( "Error inserting annotation: %d: %s. sql=%s" % (e.args[0], e.args[1], sql))

    # author: make a KV pair
    if self.author != "":
      self.kvpairs['ann_author'] = self.author
  
    if len(self.kvpairs) != 0:
      try:
        kvclause = ','.join(['(' + str(self.annid) +',\'' + k + '\',\'' + v +'\')' for (k,v) in self.kvpairs.iteritems()])  
      except:
        raise OCPCAError ( "Improperly formatted key/value csv string:" + kvclause ) 

      sql = "INSERT INTO {} VALUES {}".format( ch.getAnnoTable('kvpairs'), kvclause )

      try:
        cursor.execute(sql)
      except MySQLdb.Error, e:
        logger.warning ( "Error inserting kvpairs %d: %s. sql=%s" % (e.args[0], e.args[1], sql))
        raise OCPCAError ( "Error inserting kvpairs: %d: %s. sql=%s" % (e.args[0], e.args[1], sql))


  def update ( self, ch, cursor ):
    """Set type and update base class."""
    
    self.updateBase ( ch, ANNO_ANNOTATION, cursor )


  def updateBase ( self, ch, annotype, cursor ):
    """Update the annotation in the annotations database"""

    sql = "UPDATE {} SET type={}, confidence={}, status={} WHERE annoid = {}".format( ch.getAnnoTable('annotation'), annotype, self.confidence, self.status, self.annid)

    try:
      cursor.execute ( sql )
    except MySQLdb.Error, e:
      logger.warning ( "Error updating annotation %d: %s. sql=%s" % (e.args[0], e.args[1], sql))
      raise OCPCAError ( "Error updating annotation: %d: %s. sql=%s" % (e.args[0], e.args[1], sql))

    # Make the author field a kvpair
    if self.author != "":
      self.kvpairs['ann_author'] = self.author

    # Get the old kvpairs and identify new kvpairs
    sql = "SELECT * FROM {} WHERE annoid = {}".format( ch.getAnnoTable('kvpairs'), self.annid )
    try:
      cursor.execute ( sql )
    except MySQLdb.Error, e:
      logger.warning ( "Error retrieving kvpairs %d: %s. sql=%s" % (e.args[0], e.args[1], sql))
      raise OCPCAError ( "Error retrieving kvpairs: %d: %s. sql=%s" % (e.args[0], e.args[1], sql))

    kvresult = cursor.fetchall()

    kvupdate = {}

    for kv in kvresult:
      # for key values already stored
      if self.kvpairs.has_key( kv[1] ): 
        # update if they are new
        if self.kvpairs[kv[1]] != kv[2]:
          kvupdate[kv[1]] = self.kvpairs[kv[1]]
        # ignore if they are the same
        del(self.kvpairs[kv[1]])

    # Update changed keys
    if len(kvupdate) != 0:
      for (k,v) in kvupdate.iteritems():
        sql = "UPDATE {} SET kv_value='{}' WHERE annoid={} AND kv_key='{}'".format( ch.getAnnoTable('kvpairs'), v, self.annid, k )
        cursor.execute ( sql )
        
    # insert new kv pairs
    if len(self.kvpairs) != 0:
      kvclause = ','.join(['(' + str(self.annid) +',\'' + k + '\',\'' + v +'\')' for (k,v) in self.kvpairs.iteritems()])  
      sql = "INSERT INTO {} VALUES {}".format( ch.getAnnoTable('kvpairs'), kvclause )

      try:
        cursor.execute ( sql )
      except MySQLdb.Error, e:
        logger.warning ( "Error inserting annotation %d: %s. sql=%s" % (e.args[0], e.args[1], sql))
        raise OCPCAError ( "Error inserting annotation: %d: %s. sql=%s" % (e.args[0], e.args[1], sql))


  def delete ( self, ch, cursor ):
    """Delete the annotation from the database"""

    sql = "DELETE {0},{1} FROM {0},{1} WHERE {0}.annoid = {2} and {1}.annoid = {2}".format ( ch.getAnnoTable('annotation'), ch.getAnnoTable('kvpairs'), self.annid ) 

    try:
      cursor.execute ( sql )
    except MySQLdb.Error, e:
      logger.warning ( "Error deleting annotation {}: {}. sql={}".format(e.args[0], e.args[1], sql) )
      raise OCPCAError ( "Error deleting annotation: {}: {}. sql={}".format(e.args[0], e.args[1], sql))


  def retrieve ( self, ch, annid, cursor ):
    """Retrieve the annotation by annid"""

    sql = "SELECT * FROM {} WHERE annoid = {}".format(ch.getAnnoTable('annotation'), annid)

    try:
      cursor.execute(sql)
    except MySQLdb.Error, e:
      logger.warning ("Error retrieving annotation {}: {}. sql={}".format(e.args[0], e.args[1], sql))
      raise OCPCAError ("Error retrieving annotation: {}: {}. sql={}".format(e.args[0], e.args[1], sql))

    (self.annid, annotype, self.confidence, self.status) = cursor.fetchone()
    
    sql = "SELECT * FROM {} WHERE annoid = {}".format(ch.getAnnoTable('kvpairs'), annid) 
    
    try:
      cursor.execute(sql)
      kvpairs = cursor.fetchall()
    except MySQLdb.Error, e:
      logger.warning ( "Error retrieving annotation {}: {}. sql={}".format(e.args[0], e.args[1], sql) )
      raise OCPCAError ( "Error retrieving annotation: {}: {}. sql={}".format(e.args[0], e.args[1], sql))

    for kv in kvpairs:
      self.kvpairs[kv[1]] = kv[2]

    # Extract the author field if it exists
    if self.kvpairs.get('ann_author'):
      self.author = self.kvpairs['ann_author']
      del ( self.kvpairs['ann_author'] )
    else:
      self.author = "unknown"

    return annotype


###############  Synapse  ##################

class AnnSynapse (Annotation):
  """Metadata specific to synapses"""

  def __init__(self, annodb ):
    """Initialize the fields to zero or null"""

    self.weight = 0.0 
    self.synapse_type = 0 
    self.seeds = []
    self.segments = []

    # Call the base class constructor
    Annotation.__init__(self, annodb)

  def getField ( self, ch, field ):
    """Accessor by field name"""

    if field == 'weight':
      return self.weight
    elif field == 'synapse_type':
      return self.synapse_type
    elif field == 'seeds':
      return ','.join(str(x) for x in self.seeds)
    elif field == 'segments':
      return ','.join(str(x) for x in self.segments)
    else:
      return Annotation.getField(self, ch, field)

  def setField ( self, ch, field, value ):
    """Mutator by field name.  Then need to store the field."""
    
    if field == 'weight':
      self.weight = value
    elif field == 'synapse_type':
      self.synapse_type = value
    elif field == 'seeds':
      self.seeds = [int(x) for x in value.split(',')] 
    else:
      Annotation.setField ( self, ch, field, value )

  def store ( self, ch, cursor ):
    """Store the synapse to the annotations databae"""

    sql = "INSERT INTO {} VALUES ( {}, {}, {} )".format( ch.getAnnoTable('synapse'), self.annid, self.synapse_type, self.weight )

    try:
      cursor.execute ( sql )
    except MySQLdb.Error, e:
      logger.warning ( "Error inserting synapse %d: %s. sql=%s" % (e.args[0], e.args[1], sql))
      raise OCPCAError ( "Error inserting synapse: %d: %s. sql=%s" % (e.args[0], e.args[1], sql))

    # synapse_seeds: pack into a kv pair
    if len(self.seeds)!=0:
      try:
        self.kvpairs['synapse_seeds'] = ','.join([str(i) for i in self.seeds])
      except:
        raise OCPCAError ("Improperly formatted seeds: %s " % (self.seeds) )

    # synapse_segments: pack into a kv pair
    if len(self.segments)!=0:
      try:
        self.kvpairs['synapse_segments'] = ','.join([str(i) + ':' + str(j) for i,j in self.segments])
      except:
        raise OCPCAError ("Improperly formatted segments.  Should be nx2 matrix: %s" % (self.segments) )

    # and call store on the base classs
    Annotation.store ( self, ch, cursor, ANNO_SYNAPSE)


  def update ( self, ch, cursor ):
    """Update the synapse in the annotations database"""

    sql = "UPDATE {} SET synapse_type={}, weight={} WHERE annoid={}".format(ch.getAnnoTable('synapse'), self.synapse_type, self.weight, self.annid)

    try:
      cursor.execute ( sql )
    except MySQLdb.Error, e:
       
      logger.warning ( "Error updating synapse %d: %s. sql=%s" % (e.args[0], e.args[1], sql))
      raise OCPCAError ( "Error updating synapse: %d: %s. sql=%s" % (e.args[0], e.args[1], sql))

    # synapse_seeds: pack into a kv pair
    if len(self.seeds)!=0:
      try:
        self.kvpairs['synapse_seeds'] = ','.join([str(i) for i in self.seeds])
      except:
        raise OCPCAError ("Improperly formatted seeds: %s " % (self.seeds) )

    # synapse_segments: pack into a kv pair
    if len(self.segments)!=0:
      try:
        self.kvpairs['synapse_segments'] = ','.join([str(i) + ':' + str(j) for i,j in self.segments])
      except:
        raise OCPCAError ("Improperly formatted segments.  Should be nx2 matrix: %s" % (self.segments))

    # and call update on the base classs
    Annotation.updateBase ( self, ch, ANNO_SYNAPSE, cursor )


  def retrieve ( self, ch, annid, cursor ):
    """Retrieve the synapse by annid"""

    # Call the base class retrieve
    annotype = Annotation.retrieve ( self, ch, annid, cursor )

    # verify the annotation object type
    if annotype != ANNO_SYNAPSE:
      raise OCPCAError ( "Incompatible annotation type.  Expected SYNAPSE got %s" % annotype )

    sql = "SELECT synapse_type, weight FROM {} WHERE annoid = {}".format( ch.getAnnoTable('synapse'), annid )

    try:
      cursor.execute ( sql )
    except MySQLdb.Error, e:
      logger.warning ( "Error retrieving synapse %d: %s. sql=%s" % (e.args[0], e.args[1], sql))
      raise OCPCAError ( "Error retrieving synapse: %d: %s. sql=%s" % (e.args[0], e.args[1], sql))

    ( self.synapse_type, self.weight ) = cursor.fetchone()

    if self.kvpairs.get('synapse_seeds'):
      self.seeds = [int(i) for i in self.kvpairs['synapse_seeds'].split(',')]
      del ( self.kvpairs['synapse_seeds'] )

    if self.kvpairs.get('synapse_segments'):
      for p in self.kvpairs['synapse_segments'].split(','):
        f,s = p.split(':')
        self.segments.append([int(f),int(s)])
      del ( self.kvpairs['synapse_segments'] )


  def delete ( self, ch, cursor ):
    """Delete the synapse from the database"""

    sql = "DELETE FROM {} WHERE annoid ={};".format( ch.getAnnoTable('synapse'), self.annid );

    try:
      cursor.execute ( sql )
    except MySQLdb.Error, e:
      logger.warning ( "Error deleting annotation %d: %s. sql=%s" % (e.args[0], e.args[1], sql))
      raise OCPCAError ( "Error deleting annotation: %d: %s. sql=%s" % (e.args[0], e.args[1], sql))

    # and call delete on the base classs
    Annotation.delete ( self, ch, cursor )

    

###############  Seed  ##################

class AnnSeed (Annotation):
  """Metadata specific to seeds"""

  def __init__ (self,annodb):
    """Initialize the fields to zero or null"""

    self.parent=0        # parent seed
    self.position=[]
    self.cubelocation=0  # some enumeration
    self.source=0        # source annotation id

    # Call the base class constructor
    Annotation.__init__(self,annodb)

  def getField ( self, ch, field ):
    """Accessor by field name"""

    if field == 'parent':
      return self.parent
    elif field == 'position':
      return ','.join(str(x) for x in self.position)
    elif field == 'cubelocation':
      return self.cubelocation
    elif field == 'source':
      return self.source
    else:
      return Annotation.getField(self, ch, field)

  def setField ( self, ch, field, value ):
    """Mutator by field name.  Then need to store the field."""
    
    if field == 'parent':
      self.parent = value
    elif field == 'position':
      self.position = [int(x) for x in value.split(',')] 
      if len(self.position) != 3:
        raise OCPCAError ("Illegal arguments to set field position: %s" % value)
    elif field == 'cubelocation':
      self.cubelocation = value
    elif field == 'source':
      self.source = value
    else:
      Annotation.setField ( self, ch, field, value )

  def store ( self, ch, cursor ):
    """Store thwe seed to the annotations databae"""

    if self.position == []:
      storepos = [ 'NULL', 'NULL', 'NULL' ]
    else:
      storepos = self.position
      
    sql = "INSERT INTO {} VALUES ( {}, {}, {}, {}, {}, {}, {} )".format(ch.getAnnoTable('seed'), self.annid, self.parent, self.source, self.cubelocation, storepos[0], storepos[1], storepos[2])

    try:
      cursor.execute ( sql )
    except MySQLdb.Error, e:
      logger.warning ( "Error inserting seed %d: %s. sql=%s" % (e.args[0], e.args[1], sql))
      raise OCPCAError ( "Error inserting seed : %d: %s. sql=%s" % (e.args[0], e.args[1], sql))

    # and call store on the base classs
    Annotation.store ( self, ch, cursor, ANNO_SEED)


  def update ( self, ch, cursor ):
    """Update the seed to the annotations databae"""

    if self.position == [] or np.all(self.position==[None,None,None]):
      storepos = [ 'NULL', 'NULL', 'NULL' ]
    else:
      storepos = self.position
      
    sql = "UPDATE %s SET parentid=%s, sourceid=%s, cube_location=%s, positionx=%s, positiony=%s, positionz=%s where annoid = %s"\
            % ( ch.getAnnoTable('seed'), self.parent, self.source, self.cubelocation, storepos[0], storepos[1], storepos[2], self.annid)

    try:
      cursor.execute ( sql )
    except MySQLdb.Error, e:
      logger.warning ( "Error inserting seed %d: %s. sql=%s" % (e.args[0], e.args[1], sql))
      raise OCPCAError ( "Error inserting seed: %d: %s. sql=%s" % (e.args[0], e.args[1], sql))

    # and call update on the base classs
    Annotation.updateBase ( self, ch, ANNO_SEED, cursor )


  def retrieve ( self, ch, annid, cursor ):
    """Retrieve the seed by annid"""

    # Call the base class retrieve
    Annotation.retrieve ( self, ch, annid, cursor )

    sql = "SELECT parentid, sourceid, cube_location, positionx, positiony, positionz FROM {} WHERE annoid = {}".format( ch.getAnnoTable('seed'), annid )
      
    try:
      cursor.execute ( sql )
    except MySQLdb.Error, e:
      logger.warning ( "Error retrieving seed %d: %s. sql=%s" % (e.args[0], e.args[1], sql))
      raise OCPCAError ( "Error retrieving seed: %d: %s. sql=%s" % (e.args[0], e.args[1], sql))

    # need to initialize position to prevent index error
    self.position = [0,0,0]
    (self.parent, self.source, self.cubelocation, self.position[0], self.position[1], self.position[2]) = cursor.fetchone()


  def delete ( self, ch, cursor ):
    """Delete the seeed from the database"""

    sql = "DELETE FROM {} WHERE annoid ={};".format( ch.getAnnoTable('seed'), self.annid ) 

    try:
      cursor.execute ( sql )
    except MySQLdb.Error, e:
      logger.warning ( "Error deleting annotation %d: %s. sql=%s" % (e.args[0], e.args[1], sql))
      raise OCPCAError ( "Error deleting annotation: %d: %s. sql=%s" % (e.args[0], e.args[1], sql))

    # and call delete on the base classs
    Annotation.delete ( self, ch, cursor )


###############  Segment  ##################

class AnnSegment (Annotation):
  """Metadata specific to segment"""

  def __init__(self,annodb):
    """Initialize the fields to zero or null"""

    self.segmentclass = 0            # enumerated label
    self.parentseed = 0              # seed that started this segment
    self.neuron = 0                  # add a neuron field
    self.synapses = []               # synapses connected to this segment
    self.organelles = []             # organells associated with this segment

    # Call the base class constructor
    Annotation.__init__(self,annodb)

  def querySynapses ( self, ch, cursor ):
    """Query the synseg database to resolve"""

    sql = "SELECT synapse FROM {} WHERE segment={}".format( getAnnoTable('synseg'),self.annid)

    try:
      cursor.execute ( sql )
    except MySQLdb.Error, e:
      logger.warning ( "Error querying synapses %d: %s. sql=%s" % (e.args[0], e.args[1], sql))
      raise OCPCAError ( "Error querying synapses %d: %s. sql=%s" % (e.args[0], e.args[1], sql))

    return cursor.fetchall()


  def getField ( self, ch, field ):
    """Accessor by field name"""

    if field == 'segmentclass':
      return self.segmentclass
    elif field == 'parentseed':
      return self.parentseed
    elif field == 'neuron':
      return self.neuron
    elif field == 'synapses':
      return ','.join(str(x) for x in self.synapses)
    elif field == 'organelles':
      return ','.join(str(x) for x in self.organelles)
    else:
      return Annotation.getField(self, ch, field)

  def setField ( self, ch, field, value ):
    """Mutator by field name.  Then need to store the field."""
    
    if field == 'segmentclass':
      self.segmentclass = value
    elif field == 'parentseed':
      self.parentseed = value
    elif field == 'neuron':
      self.neuron = value
    elif field == 'synapses':
#      RBTODO synapses cannot be set in segment class.  replicated from synapse 
      #pass
      self.synapses = [int(x) for x in value.split(',')] 
    elif field == 'organelles':
#      RBTODO organelles cannot be updated in segment class.  replicated from organelle 
      #pass
      self.organelles = [int(x) for x in value.split(',')] 
    else:
      Annotation.setField ( self, ch, field, value )

  def store ( self, ch, cursor ):
    """Store the synapse to the annotations databae"""

    sql = "INSERT INTO {} VALUES ( {}, {}, {}, {} )".format( ch.getAnnoTable('segment'), self.annid, self.segmentclass, self.parentseed, self.neuron )

    try:
      cursor.execute ( sql )
    except MySQLdb.Error, e:
      logger.warning ( "Error inserting segment %d: %s. sql=%s" % (e.args[0], e.args[1], sql))
      raise OCPCAError ( "Error inserting segment: %d: %s. sql=%s" % (e.args[0], e.args[1], sql))

    # synapses: pack into a kv pair
    if len(self.synapses)!=0:
      self.kvpairs['synapses'] = ','.join([str(i) for i in self.synapses])

    # organelles: pack into a kv pair
    if len(self.organelles)!=0:
      self.kvpairs['organelles'] = ','.join([str(i) for i in self.organelles])

    # and call store on the base classs
    Annotation.store ( self, ch, cursor, ANNO_SEGMENT)


  def update ( self, ch, cursor ):
    """Update the synapse in the annotations database"""

    sql = "UPDATE %s SET segmentclass=%s, parentseed=%s, neuron=%s WHERE annoid=%s "\
            % (ch.getAnnoTable('segment'), self.segmentclass, self.parentseed, self.neuron, self.annid)

    try:
      cursor.execute ( sql )
    except MySQLdb.Error, e:
      logger.warning ( "Error updating segment %d: %s. sql=%s" % (e.args[0], e.args[1], sql))
      raise OCPCAError ( "Error updating segment: %d: %s. sql=%s" % (e.args[0], e.args[1], sql))

    # synapses: pack into a kv pair
    if len(self.synapses)!=0:
      self.kvpairs['synapses'] = ','.join([str(i) for i in self.synapses])

    # organelles: pack into a kv pair
    if len(self.organelles)!=0:
      self.kvpairs['organelles'] = ','.join([str(i) for i in self.organelles])

    # and call update on the base classs
    Annotation.updateBase ( self, ch, ANNO_SEGMENT, cursor )


  def retrieve ( self, ch, annid, cursor ):
    """Retrieve the synapse by annid"""

    # Call the base class retrieve
    annotype = Annotation.retrieve ( self, ch, annid, cursor )

    # verify the annotation object type
    if annotype != ANNO_SEGMENT:
      raise OCPCAError ( "Incompatible annotation type.  Expected SEGMENT got %s" % annotype )

    sql = "SELECT segmentclass, parentseed, neuron FROM {} WHERE annoid = {}".format( ch.getAnnoTable('segment'), annid )

    try:
      cursor.execute ( sql )
    except MySQLdb.Error, e:
      logger.warning ( "Error retrieving segment %d: %s. sql=%s" % (e.args[0], e.args[1], sql))
      raise OCPCAError ( "Error retrieving segment: %d: %s. sql=%s" % (e.args[0], e.args[1], sql))

    ( self.segmentclass, self.parentseed, self.neuron ) = cursor.fetchone()

    if self.kvpairs.get('synapses'):
      self.synapses = [int(i) for i in self.kvpairs['synapses'].split(',')]
      del ( self.kvpairs['synapses'] )

    if self.kvpairs.get('organelles'):
      self.organelles = [int(i) for i in self.kvpairs['organelles'].split(',')]
      del ( self.kvpairs['organelles'] )


  def delete ( self, ch, cursor ):
    """Delete the segment from the database"""

    sql = "DELETE FROM {} WHERE annoid ={};".format( ch.getAnnoTable('segment'), self.annid ) 

    try:
      cursor.execute ( sql )
    except MySQLdb.Error, e:
      logger.warning ( "Error deleting annotation %d: %s. sql=%s" % (e.args[0], e.args[1], sql))
      raise OCPCAError ( "Error deleting annotation: %d: %s. sql=%s" % (e.args[0], e.args[1], sql))

    # and call delete on the base classs
    Annotation.delete ( self, ch, cursor )



###############  Neuron  ##################

class AnnNeuron (Annotation):
  """Metadata specific to neurons"""

  def __init__(self,annodb):
    """Initialize the fields to zero or null"""

    self.segments = []

    # Call the base class constructor
    Annotation.__init__(self,annodb)

  def querySegments ( self, ch, cursor ):
    """Query the segments database to resolve"""

    sql = "SELECT annoid FROM {} WHERE neuron={}".format(ch.getAnnoTable('segment'), self.annid)

    try:
      cursor.execute ( sql )
    except MySQLdb.Error, e:
      logger.warning ( "Error querying neuron segments %d: %s. sql=%s" % (e.args[0], e.args[1], sql))
      raise OCPCAError ( "Error querying neuron segments %d: %s. sql=%s" % (e.args[0], e.args[1], sql))

    return cursor.fetchall()


  def getField ( self, ch, field ):
    """Accessor by field name"""

#  Make this a query not a field.

    #if field == 'segments':
      #return self.querySegments(cursor) 
    if field == 'segments':
      return ','.join(str(x) for x in self.segments)
    else:
      return Annotation.getField(self, ch, field)

  def setField ( self, ch, field, value ):
    """Mutator by field name.  Then need to store the field."""
    
    if field == 'segments':
      self.segments = [int(x) for x in value.split(',')]
    Annotation.setField ( self, ch, field, value )


  def store ( self, ch, cursor ):
    """Store the neuron to the annotations databae"""

    # and call store on the base classs
    # segments: pack into a kv pair
    if len(self.segments)!=0:
      self.kvpairs['segments'] = ','.join([str(i) for i in self.segments])
    Annotation.store ( self, ch, cursor, ANNO_NEURON )


  def update ( self, ch, cursor ):
    """Update the neuron in the annotations databae"""

    # segments: pack into a kv pair
    if len(self.segments)!=0:
      self.kvpairs['segments'] = ','.join([str(i) for i in self.segments])
    # and call update on the base classs
    Annotation.updateBase ( self, ch, ANNO_NEURON, cursor )


  def retrieve ( self, ch, annid, cursor ):
    """Retrieve the neuron by annid"""

    # Call the base class retrieve
    annotype = Annotation.retrieve ( self, ch, annid, cursor )

    # verify the annotation object type
    if annotype != ANNO_NEURON:
      raise OCPCAError ( "Incompatible annotation type.  Expected NEURON got %s" % annotype )

    if self.kvpairs.get('segments'):
      self.segments = [int(i) for i in self.kvpairs['segments'].split(',')]
      del ( self.kvpairs['segments'] )
    #self.segments = self.querySegments(cursor)


  def delete ( self, ch, cursor ):
    """Delete the annotation from the database"""

    sql = "DELETE FROM {} WHERE annoid ={};".format( ch.getAnnoTable('synapse'), self.annid ) 

    try:
      cursor.execute ( sql )
    except MySQLdb.Error, e:
      logger.warning ( "Error deleting synapse %d: %s. sql=%s" % (e.args[0], e.args[1], sql))
      raise OCPCAError ( "Error deleting annotation: %d: %s. sql=%s" % (e.args[0], e.args[1], sql))

    # and call delete on the base class
    Annotation.delete ( self, ch, cursor )

    


###############  Organelle  ##################

class AnnOrganelle (Annotation):
  """Metadata specific to organelle"""

  def __init__(self,annodb):
    """Initialize the fields to zero or None"""

    self.organelleclass = 0          # enumerated label
    self.centroid = [ None, None, None ]             # centroid -- xyz coordinate
    self.parentseed = 0              # seed that started this segment
    self.seeds = []                  # seeds generated from this organelle

    # Call the base class constructor
    Annotation.__init__(self,annodb)

  def getField ( self, ch, field ):
    """Accessor by field name"""

    if field == 'organelleclass':
      return self.organelleclass
    elif field == 'centroid':
      return ','.join(str(x) for x in self.centroid)
    elif field == 'parentseed':
      return self.parentseed
    elif field == 'seeds':
      return ','.join(str(x) for x in self.seeds)
    else:
      return Annotation.getField(self, ch, field)

  def setField ( self, ch, field, value ):
    """Mutator by field name.  Then need to store the field."""
    
    if field == 'organelleclass':
      self.organelleclass = value
    elif field == 'centroid':
      self.centroid = [int(x) for x in value.split(',')] 
      if len(self.centroid) != 3:
        raise OCPCAError ("Illegal arguments to set field centroid: %s" % value)
    elif field == 'parentseed':
      self.parentseed = value
    elif field == 'seeds':
      self.seeds = [int(x) for x in value.split(',')] 
    else:
      Annotation.setField ( self, ch, field, value )

  def store ( self, ch, cursor ):
    """Store the synapse to the annotations databae"""

    if self.centroid == None or np.all(self.centroid==[None,None,None]):
      storecentroid = [ 'NULL', 'NULL', 'NULL' ]
    else:
      storecentroid = self.centroid

    sql = "INSERT INTO %s VALUES ( %s, %s, %s, %s, %s, %s )"\
            % ( ch.getAnnoTable('organelle'), self.annid, self.organelleclass, self.parentseed,
              storecentroid[0], storecentroid[1], storecentroid[2] )

    try:
      cursor.execute ( sql )
    except MySQLdb.Error, e:
      logger.warning ( "Error inserting organelle %d: %s. sql=%s" % (e.args[0], e.args[1], sql))
      raise OCPCAError ( "Error inserting organelle: %d: %s. sql=%s" % (e.args[0], e.args[1], sql))

    # seeds: pack into a kv pair
#    if self.seeds != []:
    if len(self.seeds)!=0:
      self.kvpairs['seeds'] = ','.join([str(i) for i in self.seeds])

    # and call store on the base classs
    Annotation.store ( self, ch, cursor, ANNO_ORGANELLE)


  def update ( self, ch, cursor ):
    """Update the organelle in the annotations database"""

    if self.centroid == None or np.all(self.centroid==[None,None,None]):
      storecentroid = [ 'NULL', 'NULL', 'NULL' ]
    else:
      storecentroid = self.centroid

    sql = "UPDATE %s SET organelleclass=%s, parentseed=%s, centroidx=%s, centroidy=%s, centroidz=%s WHERE annoid=%s "\
            % (ch.getAnnoTable('organelle'), self.organelleclass, self.parentseed, storecentroid[0], storecentroid[1], storecentroid[2], self.annid)

    try:
      cursor.execute ( sql )
    except MySQLdb.Error, e:
      logger.warning ( "Error updating organelle %d: %s. sql=%s" % (e.args[0], e.args[1], sql))
      raise OCPCAError ( "Error updating organelle: %d: %s. sql=%s" % (e.args[0], e.args[1], sql))

    # seeds: pack into a kv pair
#    if self.seeds != []:
    if len(self.seeds)!=0:
      self.kvpairs['seeds'] = ','.join([str(i) for i in self.seeds])

    # and call update on the base classs
    Annotation.updateBase ( self, ch, ANNO_ORGANELLE, cursor )


  def retrieve ( self, ch, annid, cursor ):
    """Retrieve the organelle by annid"""

    # Call the base class retrieve
    annotype = Annotation.retrieve ( self, ch, annid, cursor )

    # verify the annotation object type
    if annotype != ANNO_ORGANELLE:
      raise OCPCAError ( "Incompatible annotation type.  Expected ORGANELLE got %s" % annotype )

    sql = "SELECT organelleclass, parentseed, centroidx, centroidy, centroidz FROM %s WHERE annoid = %s" % ( ch.getAnnoTable('organelle'), annid )

    try:
      cursor.execute ( sql )
    except MySQLdb.Error, e:
      logger.warning ( "Error retrieving organelle %d: %s. sql=%s" % (e.args[0], e.args[1], sql))
      raise OCPCAError ( "Error retrieving organelle: %d: %s. sql=%s" % (e.args[0], e.args[1], sql))

    ( self.organelleclass, self.parentseed, self.centroid[0], self.centroid[1], self.centroid[2] ) = cursor.fetchone()

    if self.kvpairs.get('seeds'):
      self.seeds = [int(i) for i in self.kvpairs['seeds'].split(',')]
      del ( self.kvpairs['seeds'] )


  def delete ( self, ch, cursor ):
    """Delete the organelle from the database"""

    sql = "DELETE FROM {} WHERE annoid ={};".format( ch.getAnnoTable('organelle'), self.annid ) 

    try:
      cursor.execute ( sql )
    except MySQLdb.Error, e:
      logger.warning ( "Error deleting organelle %d: %s. sql=%s" % (e.args[0], e.args[1], sql))
      raise OCPCAError ( "Error deleting organelle: %d: %s. sql=%s" % (e.args[0], e.args[1], sql))

    # and call delete on the base classs
    Annotation.delete ( self, ch, cursor )



#####################  Get and Put external interfaces  ##########################

def getAnnotation ( ch, annid, annodb, cursor ): 
  """Return an annotation object by identifier"""
  
  sql = "SELECT type FROM {} WHERE annoid= {}".format(ch.getAnnoTable('annotation'), annid)
  try:
    cursor.execute(sql)
    sql_result = cursor.fetchone()
  except MySQLdb.Error, e:
    logger.warning ( "Error reading id %d: %s. sql=%s" % (e.args[0], e.args[1], sql))
    raise OCPCAError ( "Error reading id: %d: %s. sql=%s" % (e.args[0], e.args[1], sql))

  type = None
  if sql_result is None:
    return None
  else:
    type = int(sql_result[0])
  # switch on the type of annotation
  if type is None:
    return None
  elif type == ANNO_SYNAPSE:
    anno = AnnSynapse(annodb)
  elif type == ANNO_SEED:
    anno = AnnSeed(annodb)
  elif type == ANNO_SEGMENT:
    anno = AnnSegment(annodb)
  elif type == ANNO_NEURON:
    anno = AnnNeuron(annodb)
  elif type == ANNO_ORGANELLE:
    anno = AnnOrganelle(annodb)
  elif type == ANNO_ANNOTATION:
    anno = Annotation(annodb)
  else:
    raise OCPCAError ( "Unrecognized annotation type {}".format(type) )

  anno.retrieve(ch, annid, cursor)

  return anno


def putAnnotation ( ch, anno, annodb, cursor, options ): 
  """Return an annotation object by identifier"""

  # for updates, make sure the annotation exists and is of the right type
  if  'update' in options:
    oldanno = getAnnotation ( ch, anno.annid, annodb, cursor )

    # can't update annotations that don't exist
    if  oldanno == None:
      raise OCPCAError ( "During update no annotation found at id {}".format(anno.annid)  )

    # can update if they are the same type
    elif oldanno.__class__ == anno.__class__:
      anno.update(ch, cursor)

    # need to delete and then insert if we're changing the annotation type only from the base type
    elif oldanno.__class__ == Annotation:
      oldanno.delete(ch, cursor)
      anno.store(ch, cursor)
    
  # Write the user chosen annotation id
  else:
    anno.store(ch, cursor)
 

def deleteAnnotation ( ch, annoid, annodb, cursor, options ): 
  """Polymorphically delete an annotaiton by identifier"""

  oldanno = getAnnotation ( ch, annoid, annodb, cursor )

  # can't delete annotations that don't exist
  if  oldanno == None:
    raise OCPCAError ( "During delete no annotation found at id %d" % annoid  )

  # methinks we can call polymorphically
  oldanno.delete(ch, cursor) 


def getChildren ( ch, annid, annodb, cursor ):
    """Return a list of all annotations in this neuron"""

    sql = "SELECT annoid FROM {} WHERE neuron = {}".format( ch.getAnnoTable('segment'), annid )

    try:
      cursor.execute ( sql )
    except MySQLdb.Error, e:
      cursor.close()
      logger.warning ( "Error deleting annotation %d: %s. sql=%s" % (e.args[0], e.args[1], sql))
      raise OCPCAError ( "Error deleting annotation: %d: %s. sql=%s" % (e.args[0], e.args[1], sql))
    
    seglist = cursor.fetchall()

    # return an empty iterable if there are none
    if seglist == None:
      seglist = []

    return np.array ( seglist, dtype=np.uint32 ).flatten()


