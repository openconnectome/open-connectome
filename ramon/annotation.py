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
import MySQLdb
from collections import defaultdict
import json

from ndwserror import NDWSError 
import logging
logger=logging.getLogger("neurodata")


"""Classes that hold annotation metadata"""

# Annotation types
ANNO_ANNOTATION = 1
ANNO_SYNAPSE = 2
ANNO_SEED = 3
ANNO_SEGMENT = 4
ANNO_NEURON = 5
ANNO_ORGANELLE = 6
ANNO_NODE = 7
ANNO_SKELETON = 8
ANNO_ROI = 9


###############  Annotation  ##################

class Annotation:
  """Metdata common to all annotations."""

  def __init__ ( self, annodb, ch ):
    """Initialize the fields to zero or null"""

    self.annodb = annodb
    self.ch = ch

    # metadata fields
    self.annid = 0 
    self.status = 0 
    self.confidence = 0.0 
    self.author = ""
    self.kvpairs = defaultdict(list)

  def getField ( self, field ):
    """Accessor by field name"""

    if field == 'status':
      return self.status
    elif field == 'confidence':
      return self.confidence
    elif field == 'author':
      return self.author
    elif field =='annid':
      return self.annid
    elif self.kvpairs.get(field):
      return self.kvpairs[field]
    else:
      logger.warning ( "getField: No such field %s" % (field))
      raise NDWSError ( "getField: No such field %s" % (field))


  def setField ( self, field, value ):
    """Mutator by field name.  Then need to store the field."""
    
    if field == 'status':
      self.status = value
    elif field == 'confidence':
      self.confidence = value
    elif field == 'author':
      self.author = value
    # if we don't recognize the field, store it as a kv pair.
    elif field == 'annid':
      self.annid = value
    else: 
      self.kvpairs[field]=value

  def toDict ( self ):
    """return a dictionary of the kv pairs in for an annotation"""

    kvdict = defaultdict(list)

    kvdict['ann_type'] = ANNO_ANNOTATION
    kvdict['ann_status'] = self.status   
    kvdict['ann_confidence'] = self.confidence   
    kvdict['ann_author'] = self.author   
    kvdict['ann_id'] = self.annid   
    
    # should add kvpairs to kvdict
    kvdict.update(self.kvpairs)
    return kvdict

  def fromDict ( self, kvdict ):
    """convert a dictionary to the class elements"""

    for (k,v) in kvdict.iteritems():
      if k == 'ann_type':
        next
      elif k == 'ann_status':
        self.status = int(v)
      elif k == 'ann_confidence':
        self.confidence = float(v)
      elif k == 'ann_author':
        self.author = v
      elif k == 'ann_id':
        self.annid = int(v)
      else:
        self.kvpairs[k] = v


###############  Synapse  ##################

class AnnSynapse (Annotation):
  """Metadata specific to synapses"""

  def __init__(self, annodb, ch ):
    """Initialize the fields to zero or null"""

    self.weight = 0.0 
    self.synapse_type = 0 
    self.seeds = np.array([], dtype=np.uint32)
    self.segments = np.array([], dtype=np.uint32)      #undirected edge
    self.presegments = np.array([], dtype=np.uint32)    # directed edge
    self.postsegments = np.array([], dtype=np.uint32)   # directed edge   
    self.centroid = np.array([], dtype=np.uint32)    # centroid -- xyz coordinate

    # Call the base class constructor
    Annotation.__init__(self, annodb, ch)

  def getField ( self, field ):
    """Accessor by field name"""

    if field == 'weight':
      return self.weight
    elif field == 'synapse_type':
      return self.synapse_type
    elif field == 'seeds':
      return ','.join(str(x) for x in self.seeds)
    elif field == 'segments':
      return ','.join(str(x) for x in self.segments)
    elif field == 'presegments':
      return ','.join(str(x) for x in self.presegments)
    elif field == 'postsegments':
      return ','.join(str(x) for x in self.postsegments)
    elif field == 'centroid':
      return ','.join(str(x) for x in self.centroid)
      self.centroid = np.array([int(x) for x in value.split(',')], dtype=np.uint32)
    else:
      return Annotation.getField(self, field)

  def setField ( self, field, value ):
    """Mutator by field name.  Then need to store the field."""
    
    if field == 'weight':
      self.weight = value
    elif field == 'synapse_type':
      self.synapse_type = value
    elif field == 'seeds':
      self.seeds = np.array([int(x) for x in value.split(',')], dtype=np.uint32)
    elif field == 'segments':
      self.segments = np.array([int(x) for x in value.split(',')], dtype=np.uint32)
    elif field == 'presegments':
      self.presegments = np.array([int(x) for x in value.split(',')], dtype=np.uint32)
      print 'PRE in set', self.presegments
    elif field == 'postsegments':
      self.postsegments = np.array([int(x) for x in value.split(',')], dtype=np.uint32)
      print 'POST in set', self.postsegments
    elif field == 'centroid':
      self.centroid = np.array([int(x) for x in value.split(',')], dtype=np.uint32)
      if len(self.centroid) != 3:
        raise NDWSError ("Illegal arguments to set field centroid: %s" % value)
    else:
      Annotation.setField ( self, field, value )

  def toDict ( self ):
    """return a dictionary of the kv pairs in for an annotation"""

    kvdict = defaultdict(list)

    kvdict['syn_weight'] = self.weight   
    kvdict['syn_type'] = self.synapse_type   
    [ kvdict['syn_seeds'].append(s) for s in self.seeds ] 
    [ kvdict['syn_segments'].append(s) for s in self.segments ] 
    [ kvdict['syn_presegments'].append(s) for s in self.presegments ] 
    [ kvdict['syn_postsegments'].append(s) for s in self.postsegments ] 
    kvdict['syn_centroid'] = json.dumps(self.centroid.tolist())
    kvdict.update(Annotation.toDict(self))

    # update the type after merge
    kvdict['ann_type'] = ANNO_SYNAPSE

    return kvdict

  def fromDict ( self, kvdict ):
    """convert a dictionary to the class elements"""

    anndict = defaultdict(list)

    for (k,v) in kvdict.iteritems():
      if k == 'syn_weight':
        self.weight = float(v)
      elif k == 'syn_type':
        self.synapse_type = int(v)
      elif k == 'syn_centroid':
        self.centroid = np.array(json.loads(v), dtype=np.uint32)
      elif k == 'syn_seeds':
        if type(v) == list:
          self.seeds = [int(s) for s in v]
        else:
          self.seeds = [int(v)]
      elif k == 'syn_segments':
        if type(v) == list:
          self.segments = [int(s) for s in v]
        else:
          self.segments = [int(v)]
      elif k == 'syn_presegments':
        if type(v) == list:
          self.presegments = [int(s) for s in v]
        else:
          self.presegments = [int(v)]
      elif k == 'syn_postsegments':
        if type(v) == list:
          self.postsegments = [int(s) for s in v]
        else:
          self.postsegments = [int(v)]
      else:
        anndict[k] = v
    
    Annotation.fromDict ( self, anndict )


###############  Seed  ##################

class AnnSeed (Annotation):
  """Metadata specific to seeds"""

  def __init__ (self,annodb, ch):
    """Initialize the fields to zero or null"""

    self.parent=0        # parent seed
    self.position=np.array([], dtype=np.uint32)
    self.cubelocation=0  # some enumeration
    self.source=0        # source annotation id

    # Call the base class constructor
    Annotation.__init__(self,annodb, ch)

  def getField ( self, field ):
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
      return Annotation.getField(self, field)

  def setField ( self, field, value ):
    """Mutator by field name.  Then need to store the field."""
    
    if field == 'parent':
      self.parent = value
    elif field == 'position':
      self.position = np.array([int(x) for x in value.split(',')], dtype=np.uint32)
      if len(self.position) != 3:
        raise NDWSError ("Illegal arguments to set field position: %s" % value)
    elif field == 'cubelocation':
      self.cubelocation = value
    elif field == 'source':
      self.source = value
    else:
      Annotation.setField ( self, field, value )

  def toDict ( self ):
    """return a dictionary of the kv pairs in for an annotation"""

    kvdict = defaultdict(list)

    kvdict['seed_parent'] = self.parent   
    kvdict['seed_position'] = json.dumps(self.position.tolist())
    kvdict['seed_cubelocation'] = self.cubelocation
    kvdict['seed_source'] = self.source  

    kvdict.update(Annotation.toDict(self))

    # update the type after merge
    kvdict['ann_type'] = ANNO_SEED

    return kvdict

  def fromDict ( self, kvdict ):
    """convert a dictionary to the class elements"""

    anndict = defaultdict(list)

    for (k,v) in kvdict.iteritems():
      if k == 'seed_parent':
        self.parent = int(v)
      elif k == 'seed_position':
        self.position = np.array(json.loads(v), dtype=np.uint32)
      elif k == 'seed_cubelocation':
        self.cubelocation = int(v)
      elif k == 'seed_source':
        self.source = int(v)
      else:
        anndict[k] = v
    
    
    Annotation.fromDict ( self, anndict )


###############  Segment  ##################

class AnnSegment (Annotation):
  """Metadata specific to segment"""

  def __init__(self,annodb, ch):
    """Initialize the fields to zero or null"""

    self.segmentclass = 0            # enumerated label
    self.parentseed = 0              # seed that started this segment
    self.neuron = 0                  # add a neuron field
    self.synapses=np.array([], dtype=np.uint32)                # synapses connected to this segment
    self.organelles=np.array([], dtype=np.uint32)              # organelles associated with this segment

    # Call the base class constructor
    Annotation.__init__(self,annodb, ch)


  def getField ( self, field ):
    """Accessor by field name"""

    if field == 'segmentclass':
      return self.segmentclass
    elif field == 'parentseed':
      return self.parentseed
    elif field == 'neuron':
      return self.neuron
    elif field == 'synapses':
      return ','.join(str(x) for x in self.annodb.querySynapses( self.ch, self.annid ))
    elif field == 'presynapses':
      return ','.join(str(x) for x in self.annodb.queryPreSynapses( self.ch, self.annid ))
    elif field == 'postsynapses':
      return ','.join(str(x) for x in self.annodb.queryPostSynapses( self.ch, self.annid ))
    elif field == 'organelles':
      return ','.join(str(x) for x in self.annodb.queryOrganelles( self.ch, self.annid ))
    else:
      return Annotation.getField(self, field)

  def setField ( self, field, value ):
    """Mutator by field name.  Then need to store the field."""
    
    if field == 'segmentclass':
      self.segmentclass = value
    elif field == 'parentseed':
      self.parentseed = value
    elif field == 'neuron':
      self.neuron = value
    elif field == 'synapses':
      raise NDWSError ("Cannot set synapses in segments.  It is derived from the synapse annotations.")
    elif field == 'organelles':
      raise NDWSError ("Cannot set organelles in segments.  It is derived from the organelle annotations.")
    else:
      Annotation.setField ( self, field, value )

  def toDict ( self ):
    """return a dictionary of the kv pairs in for an annotation"""

    kvdict = defaultdict(list)

    kvdict['seg_class'] = self.segmentclass   
    kvdict['seg_parentseed'] = self.parentseed
    kvdict['seg_neuron'] = self.neuron  

    kvdict.update(Annotation.toDict(self))

    # update the type after merge
    kvdict['ann_type'] = ANNO_SEGMENT

    return kvdict

  def fromDict ( self, kvdict ):
    """convert a dictionary to the class elements"""

    anndict = defaultdict(list)

    for (k,v) in kvdict.iteritems():
      if k == 'seg_class':
        self.segmentclass = int(v)
      elif k == 'seg_parentseed':
        self.parentseed = int(v)
      elif k == 'seg_neuron':
        self.neuron = int(v)
      else:
        anndict[k] = v
    
    Annotation.fromDict ( self, anndict )



###############  Neuron  ##################

class AnnNeuron (Annotation):
  """Metadata specific to neurons"""

  def __init__(self,annodb, ch):
    """Initialize the fields to zero or null"""

    # Call the base class constructor
    Annotation.__init__(self,annodb, ch)

  def getField ( self, field ):
    """Accessor by field name"""

    if field == 'segments':
      return ','.join(str(x) for x in self.annodb.querySegments( self.ch, self.annid ))
    else:
      return Annotation.getField(self, field)

  def setField ( self, field, value ):
    """Mutator by field name.  Then need to store the field."""
    
    if field == 'segments':
      raise NDWSError ("Cannot set segments.  It is derived from the neuron field of ANNO_SEGMENTS.")
    else:
      Annotation.setField ( self, field, value )

  def toDict ( self ):
    """return a dictionary of the kv pairs in for an annotation"""

    kvdict = defaultdict(list)

    kvdict.update(Annotation.toDict(self))

    # update the type after merge
    kvdict['ann_type'] = ANNO_NEURON

    return kvdict

  def fromDict ( self, kvdict ):
    """convert a dictionary to the class elements"""

# No additional fields in neuron right now.
#
#    anndict = defaultdict(list)
#
#    for (k,v) in kvdict.iteritems():
#      anndict[k] = v
#    Annotation.fromDict ( self, anndict )
    
    Annotation.fromDict ( self, kvdict )


###############  Organelle  ##################

class AnnOrganelle (Annotation):
  """Metadata specific to organelle"""

  def __init__(self,annodb,ch):
    """Initialize the fields to zero or None"""

    self.organelleclass = 0          # enumerated label
    self.centroid = np.array([], dtype=np.uint32)    # centroid -- xyz coordinate
    self.segment = 0
    self.parentseed = 0              # seed that started this segment
    self.seeds=np.array([], dtype=np.uint32)  # seeds generated from this organelle 

    # Call the base class constructor
    Annotation.__init__(self,annodb,ch)

  def getField ( self, field ):
    """Accessor by field name"""

    if field == 'organelleclass':
      return self.organelleclass
    elif field == 'centroid':
      return ','.join(str(x) for x in self.centroid)
    elif field == 'parentseed':
      return self.parentseed
    elif field == 'segment':
      return self.segment
    elif field == 'seeds':
      return ','.join(str(x) for x in self.seeds)
    else:
      return Annotation.getField(self, field)

  def setField ( self, field, value ):
    """Mutator by field name.  Then need to store the field."""
    
    if field == 'organelleclass':
      self.organelleclass = value
    elif field == 'centroid':
      self.centroid = np.array([int(x) for x in value.split(',')], dtype=np.uint32)
      if len(self.centroid) != 3:
        raise NDWSError ("Illegal arguments to set field centroid: %s" % value)
    elif field == 'parentseed':
      self.parentseed = value
    elif field == 'segment':
      self.segment = value
    elif field == 'seeds':
      self.seeds = np.array([int(x) for x in value.split(',')], dtype=np.uint32)
    else:
      Annotation.setField ( self, field, value )

  def toDict ( self ):
    """return a dictionary of the kv pairs in for an annotation"""

    kvdict = defaultdict(list)
    kvdict['org_class'] = self.organelleclass   
    kvdict['org_segment'] = self.segment   
    kvdict['org_centroid'] = json.dumps(self.centroid.tolist())
    kvdict['org_parentseed'] = self.parentseed   
    [ kvdict['org_seeds'].append(s) for s in self.seeds ] 

    # somehow, Annotation.toDict is picking up a parent seed?
    kvdict.update(Annotation.toDict(self))

    # update the type after merge
    kvdict['ann_type'] = ANNO_ORGANELLE

    return kvdict

  def fromDict ( self, kvdict ):
    """convert a dictionary to the class elements"""

    anndict = defaultdict(list)

    for (k,v) in kvdict.iteritems():
      if k == 'org_class':
        self.organelleclass = int(v)
      elif k == 'org_centroid':
        self.centroid = np.array(json.loads(v), dtype=np.uint32)
      elif k == 'org_segment':
        self.segment = int(v)
      elif k == 'org_parentseed':
        self.parentseed = int(v)
      elif k == 'org_seeds':
        if type(v) == list:
          self.seeds = [int(s) for s in v]
        else:
          self.seeds = [int(v)]
      else:
        anndict[k] = v
    
    Annotation.fromDict ( self, anndict )


###############  Node  ##################

class AnnNode (Annotation):
  """Point annotation (sometimes in a skeleton)"""

  def __init__(self,annodb,ch):
    """Initialize the fields to zero or None"""

    self.nodetype = 0                           # enumerated label
    self.skeleton = 0
    self.point = 0
    self.location=np.array([], dtype=np.float)
    self.parent = 0                           # parent node
    self.radius = 0.0

    # Call the base class constructor
    Annotation.__init__(self,annodb,ch)

  def getField ( self, field ):
    """Accessor by field name"""

    if field == 'nodetype':
      return self.nodetype
    elif field == 'location':
      return ','.join(str(x) for x in self.location)
    elif field == 'parent':
      return self.parent
    elif field == 'radius':
      return self.radius
    elif field == 'children':
      return ','.join(str(x) for x in self.annodb.queryNodeChildren ( self.ch, self.annid ))
    else:
      return Annotation.getField(self, field)

  def setField ( self, field, value ):
    """Mutator by field name.  Then need to store the field."""
    
    if field == 'nodetype':
      self.nodetype = value
    elif field == 'children':
      raise NDWSError ("Cannot set children.  It is derived from the parent field of ANNO_NODE.")
    elif field == 'location':
      self.location = np.array([float(x) for x in value.split(',')], dtype=np.float)
      if len(self.location) != 3:
        raise NDWSError ("Illegal arguments to set field location: %s" % value)
    elif field == 'parent':
      self.parent = value
    elif field == 'radius':
      self.radius = value
    else:
      Annotation.setField ( self, field, value )

  def toDict ( self ):
    """return a dictionary of the kv pairs in for an annotation"""

    kvdict = defaultdict(list)
    kvdict['node_type'] = self.nodetype   
    kvdict['node_location'] = json.dumps(self.location.tolist())
    kvdict['node_parent'] = self.parent   
    kvdict['node_radius'] = self.radius   

    kvdict.update(Annotation.toDict(self))

    # update the type after merge
    kvdict['ann_type'] = ANNO_NODE

    return kvdict


  def fromDict ( self, kvdict ):
    """convert a dictionary to the class elements"""
    
    anndict = defaultdict(list)

    for (k,v) in kvdict.iteritems():
      if k == 'node_type':
        self.nodetype = int(v)
      elif k == 'node_location':
        self.location = np.array(json.loads(v), dtype=np.float)
      elif k == 'node_parent':
        self.parent = int(v)
      elif k == 'node_radius':
        self.radius = float(v)
      else:
        anndict[k] = v
    
    Annotation.fromDict ( self, anndict )


###############  Skeleton  ##################

class AnnSkeleton (Annotation):
  """Skeleton annotation"""

  def __init__(self,annodb,ch):
    """Initialize the fields to zero or None"""

    self.skeletontype = 0                          # enumerated label
    self.rootnode = 0                              # children

    # Call the base class constructor
    Annotation.__init__(self,annodb,ch)

  def getField ( self, field ):
    """Accessor by field name"""

    if field == 'skeletontype':
      return self.skeletontype
    elif field == 'nodes':
      return ','.join(str(x) for x in self.annodb.querySkeletonNodes ( self.ch, self.annid ))
    elif field == 'rootnode':
      return self.rootnode
    else:
      return Annotation.getField(self, field)

  def setField ( self, field, value ):
    """Mutator by field name.  Then need to store the field."""
    
    if field == 'skeletontype':
      self.skeletontype = value
    elif field == 'skeletonnodes':
      raise NDWSError ("Cannot set nodes.  It is derived from the parent field of ANNO_NODE.")
    elif field == 'rootnode':
      self.rootnode = value
    else:
      Annotation.setField ( self, field, value )

  def toDict ( self ):
    """return a dictionary of the kv pairs in for an annotation"""

    kvdict = defaultdict(list)
    kvdict['skel_type'] = self.skeletontype   
    kvdict['skel_rootnode'] = self.rootnode   

    kvdict.update(Annotation.toDict(self))

    # update the type after merge
    kvdict['ann_type'] = ANNO_SKELETON

    return kvdict

  def fromDict ( self, kvdict ):
    """convert a dictionary to the class elements"""

    anndict = defaultdict(list)

    for (k,v) in kvdict.iteritems():
      if k == 'skel_type':
        self.skeletontype = int(v)
      elif k == 'skel_rootnode':
        self.rootnode = int(v)
      else:
        anndict[k] = v
    
    Annotation.fromDict ( self, anndict )


###############  ROI  ##################

class AnnROI (Annotation):
  """Region of Interest annotation"""

  def __init__(self,annodb,ch):
    """Initialize the fields to zero or None"""

    self.parent = 0                          

    # Call the base class constructor
    Annotation.__init__(self,annodb,ch)

  def getField ( self, field ):
    """Accessor by field name"""

    if field == 'parent':
      return self.parent
    elif field == 'children':
      return ','.join(str(x) for x in self.annodb.queryROIChildren ( self.ch, self.annid ))
    else:
      return Annotation.getField(self, field)

  def setField ( self, field, value ):
    """Mutator by field name.  Then need to store the field."""
    
    if field == 'parent':
      self.parent = value
    elif field == 'children':
      raise NDWSError ("Cannot set children.  It is derived from the parent field of ANNO_NODE.")
    else:
      Annotation.setField ( self, field, value )

  def toDict ( self ):
    """return a dictionary of the kv pairs in for an annotation"""

    kvdict = defaultdict(list)
    kvdict['roi_parent'] = self.parent   

    kvdict.update(Annotation.toDict(self))

    # update the type after merge
    kvdict['ann_type'] = ANNO_ROI

    return kvdict

  def fromDict ( self, kvdict ):
    """convert a dictionary to the class elements"""

    anndict = defaultdict(list)

    for (k,v) in kvdict.iteritems():
      if k == 'roi_parent':
        self.parent = int(v)
      else:
        anndict[k] = v
    
    Annotation.fromDict ( self, anndict )

