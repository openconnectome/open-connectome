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
import urllib2
import tempfile
import h5py
import csv
import cStringIO
import collections
import re

import annotation

from ocpcaerror import OCPCAError
import logging
logger=logging.getLogger("ocp")

#
#  class to define the HDF5 format of annotations.
#

"""The HDF5 format currently looks like:

/**ID**  # the top namespace is the annotation identifier.

  ANNOTATION_TYPE (int)
  RESOLUTION (int optional) defaults to project resolution
  XYZOFFSET ( int[3] optional defined with volume )
  XYZDIMENSION ( int[3] optional used only by server when asking for a bounding box )
  CUTOUT ( int32 3-d array optional defined with XYZOFFSET )
  VOXELS ( int32[][3] optional if defined XYZOFFSET and CUTOUT must be empty ) 

  METADATA group;

   # metadata for all annotations
   CONFIDENCE (float)
   STATUS (int) 
   KVPAIRS   (string containing csv pairs)
   AUTHOR ( string ) 

   # for seeds

   PARENT (int)
   POSITION (int[3])
   CUBE_LOCATION (int)
   SOURCE (int)

   # for segments:

   SEGMENTCLASS (int)
   PARENTSEED (int)
   NEURON (int)
   SYNAPSES (int[]) 
   ORGANELLES ( int[])

   # for synapses:

   SYNAPSE_TYPE (int)
   WEIGHT (float)
   SEEDS (int[]) 
   SEGMENTS ( int[ ][2] )

   # for neurons
   SEGMENTS ( int[] )

   # for organelles
   ORGANELLECLASS (int)
   PARENTSEED (int)
   SEEDS (int[]) 

"""


class H5Annotation:
  """Class to move RAMON objects into and out of HDF5 files"""

  def __init__( self, annotype, annoid, h5fh ):
    """Create an annotation and put in the specified HDF5 file."""

    # Give the HDF5 file handle to the H5Annotation
    self.h5fh = h5fh

    # Create the top level annotation id namespace
    self.idgrp = self.h5fh.create_group ( str(annoid) ) 

    # Annotation type
    self.idgrp.create_dataset ( "ANNOTATION_TYPE", (1,), np.uint32, data=annotype )
    # Create a metadata group
    self.mdgrp = self.idgrp.create_group ( "METADATA" ) 


  def addVoxels ( self, resolution, voxlist ):
    """Add the list of voxels to the HDF5 file"""

    self.idgrp.create_dataset ( "RESOLUTION", (1,), np.uint32, data=resolution )     
    if len(voxlist) != 0:
      self.idgrp.create_dataset ( "VOXELS", (len(voxlist),3), np.uint32, data=voxlist )     

  def addCutout ( self, resolution, corner, volume ):
    """Add the cutout  to the HDF5 file"""

    self.idgrp.create_dataset ( "RESOLUTION", (1,), np.uint32, data=resolution )     
    self.idgrp.create_dataset ( "XYZOFFSET", (3,), np.uint32, data=corner )     
    if volume != None:
      self.idgrp.create_dataset ( "CUTOUT", volume.shape, volume.dtype, data=volume )     

  def mkCuboidGroup ( self, resolution ):
    """Create the group to store cuboids"""
    self.idgrp.create_dataset ( "RESOLUTION", (1,), np.uint32, data=resolution )     
    self.cbgrp = self.idgrp.create_group( "CUBOIDS" )


  def addCuboid ( self, offset, cbdata ):
    """Add the cutout  to the HDF5 file"""

    offgrp = self.cbgrp.create_group ( '{}'.format(offset) ) 

    offgrp.create_dataset ( "XYZOFFSET", (3,), np.uint32, data=offset )     
    offgrp.create_dataset ( "CUBOID", cbdata.shape, cbdata.dtype,  data=cbdata )     


  def addBoundingBox ( self, resolution, corner, dim ):
    """Add the cutout  to the HDF5 file"""

    self.idgrp.create_dataset ( "RESOLUTION", (1,), np.uint32, data=resolution )     
    self.idgrp.create_dataset ( "XYZOFFSET", (3,), np.uint32, data=corner )     
    self.idgrp.create_dataset ( "XYZDIMENSION", (3,), np.uint32, data=dim )     


############## Converting HDF5 to Annotations

def H5toAnnotation ( key, idgrp, annodb ):
  """Return an annotation constructed from the contents of this HDF5 file"""

  # get the annotation type
#  if idgrp.get('ANNOTATION_TYPE'):
  if 'ANNOTATION_TYPE' in idgrp:
    annotype = idgrp['ANNOTATION_TYPE'][0]
  else:
    annotype = annotation.ANNO_ANNOTATION

  # And get the metadata group
  mdgrp = idgrp.get('METADATA')

  if annotype == annotation.ANNO_SEED:

    # Create the appropriate annotation type
    anno = annotation.AnnSeed(annodb)

    # Load metadata if it exists
    if mdgrp:
      # load the seed specific metadata
#      if mdgrp.get('PARENT'):
      if 'PARENT' in mdgrp:
        anno.parent = mdgrp['PARENT'][0]
#      if mdgrp.get('POSITION'):
      if 'POSITION' in mdgrp:
        anno.position = mdgrp['POSITION'][:]
#      if mdgrp.get('CUBE_LOCATION'):
      if 'CUBE_LOCATION' in mdgrp:
        anno.cubelocation = mdgrp['CUBE_LOCATION'][0]
#      if mdgrp.get('SOURCE'):
      if 'SOURCE' in mdgrp:
        anno.source = mdgrp['SOURCE'][0] 

  elif annotype == annotation.ANNO_SYNAPSE:
    
    # Create the appropriate annotation type
    anno = annotation.AnnSynapse(annodb)

    # Load metadata if it exists
    if mdgrp:
      # load the synapse specific metadata
#      if mdgrp.get('SYNAPSE_TYPE'):
      if 'SYNAPSE_TYPE' in mdgrp:
        anno.synapse_type = mdgrp['SYNAPSE_TYPE'][0]
#      if mdgrp.get('WEIGHT'):
      if 'WEIGHT' in mdgrp:
        anno.weight = mdgrp['WEIGHT'][0]
#      if mdgrp.get('SEEDS') and len(mdgrp['SEEDS'])!=0:
      if 'SEEDS' in mdgrp:
        anno.seeds = mdgrp['SEEDS'][:]
#      if mdgrp.get('SEGMENTS') and len(mdgrp['SEGMENTS'])!=0:
      if 'SEGMENTS' in mdgrp:
        anno.segments = mdgrp['SEGMENTS'] [:]

  elif annotype == annotation.ANNO_SEGMENT:
    
    # Create the appropriate annotation type
    anno = annotation.AnnSegment(annodb)

    # Load metadata if it exists
    if mdgrp:
      # load the synapse specific metadata
      if mdgrp.get('PARENTSEED'):
        anno.parentseed = mdgrp['PARENTSEED'][0]
      if mdgrp.get('SEGMENTCLASS'):
        anno.segmentclass = mdgrp['SEGMENTCLASS'][0]
      if mdgrp.get('NEURON'):
        anno.neuron = mdgrp['NEURON'][0]
      if mdgrp.get('SYNAPSES') and len(mdgrp['SYNAPSES'])!=0:
        anno.synapses = mdgrp['SYNAPSES'][:]
      if mdgrp.get('ORGANELLES') and len(mdgrp['ORGANELLES'])!=0:
        anno.organelles = mdgrp['ORGANELLES'][:]

  elif annotype == annotation.ANNO_NEURON:

    # Create the appropriate annotation type
    anno = annotation.AnnNeuron(annodb)

    # Load metadata if it exists
    if mdgrp:
      # load the synapse specific metadata
      if mdgrp.get('SEGMENTS') and len(mdgrp['SEGMENTS'])!=0:
        anno.segments = mdgrp['SEGMENTS'][:]

  elif annotype == annotation.ANNO_ORGANELLE:
    
    # Create the appropriate annotation type
    anno = annotation.AnnOrganelle(annodb)

    # Load metadata if it exists
    if mdgrp:
      # load the synapse specific metadata
      if mdgrp.get('PARENTSEED'):
        anno.parentseed = mdgrp['PARENTSEED'][0]
      if mdgrp.get('ORGANELLECLASS'):
        anno.organelleclass = mdgrp['ORGANELLECLASS'][0]
      if mdgrp.get('SEEDS') and len(mdgrp['SEEDS'])!=0:
        anno.seeds = mdgrp['SEEDS'][:]
      if mdgrp.get('CENTROID'):
        anno.centroid = mdgrp['CENTROID'][:]

  # No special action if it's a no type
  elif annotype == annotation.ANNO_ANNOTATION:
    # Just create a generic annotation object
    anno = annotation.Annotation(annodb)

  else:
    logger.warning ("Dont support this annotation type yet. Type = %s" % annotype)
    raise OCPCAError ("Dont support this annotation type yet. Type = %s" % annotype)

  # now load the annotation common fields
  if re.match("^\d+$", key):
    anno.annid = int(key)
  else:
    anno.annid = 0

  if mdgrp:
    # now load the metadata common fields
    if mdgrp.get('STATUS'):
      anno.status = mdgrp['STATUS'][0]
    if mdgrp.get('CONFIDENCE'):
      anno.confidence = mdgrp['CONFIDENCE'][0]
    if mdgrp.get('AUTHOR'):
      anno.author = mdgrp['AUTHOR'][0]

    # and the key/value pairs
    if mdgrp.get('KVPAIRS'):
      fstring = cStringIO.StringIO( mdgrp['KVPAIRS'][0] )
      csvr = csv.reader(fstring, delimiter=',')
      for r in csvr:
        anno.kvpairs[r[0]] = r[1] 

  return anno

# Need to convert the rest of this to multiple key

def H5GetVoxels ( h5fh ):
  """Return the voxel data associated with the annotation"""

  # assume a single annotation for now
  keys = h5fh.keys()
  idgrp = h5fh.get(keys[0])

  if idgrp.get('VOXELS'):
    return idgrp['VOXELS']
  else:
    return None

def H5GetVolume ( h5fh ):
  """Return the volume associated with the annotation"""

  # assume a single annotation for now
  keys = h5fh.keys()
  idgrp = h5fh.get(keys[0])

  if idgrp.get('XYZOFFSET'):
    if idgrp.get('CUTOUT'):
      return (idgrp['XYZOFFSET'], idgrp['CUTOUT'])
    else:
      logger.warning("Improperly formatted HDF5 file.  XYZOFFSET define but no CUTOUT.")
      raise OCPCAError("Improperly formatted HDF5 file.  XYZOFFSET define but no CUTOUT.")
  else:
    return None


def H5getCuboids ( idgrp ):
  """Generator function that returns XYZOFFSETS and CUBOIDS"""
 
  cuboidsgrp = idgrp.get("CUBOIDS")
  for k in cuboidsgrp:
    corner = np.array(cuboidsgrp[k]["XYZOFFSET"])
    cuboiddata = np.array(cuboidsgrp[k]['CUBOID'])
    yield (corner, cuboiddata)
  

    

############## Converting Annotation to HDF5 ####################

def BasetoH5 ( anno, annotype, h5fh ):
  """Convert an annotation to HDF5 for interchange"""

  h5anno = H5Annotation ( annotype, anno.annid, h5fh )

  # Set Annotation specific metadata
  h5anno.mdgrp.create_dataset ( "STATUS", (1,), np.uint32, data=anno.status )
  h5anno.mdgrp.create_dataset ( "CONFIDENCE", (1,), np.float, data=anno.confidence )
  h5anno.mdgrp.create_dataset ( "AUTHOR", (1,), dtype=h5py.special_dtype(vlen=str), data=anno.author )

  # Turn our dictionary into a csv file
  fstring = cStringIO.StringIO()
  csvw = csv.writer(fstring, delimiter=',')
  csvw.writerows([r for r in anno.kvpairs.iteritems()]) 

  # User-defined metadata
  h5anno.mdgrp.create_dataset ( "KVPAIRS", (1,), dtype=h5py.special_dtype(vlen=str), data=fstring.getvalue())

  return h5anno


def SynapsetoH5 ( synapse, h5fh ):
  """Convert a synapse to HDF5"""

  # First create the base object
  h5synapse = BasetoH5 ( synapse, annotation.ANNO_SYNAPSE, h5fh )

  # Then customize
  h5synapse.mdgrp.create_dataset ( "WEIGHT", (1,), np.float, data=synapse.weight )
  h5synapse.mdgrp.create_dataset ( "SYNAPSE_TYPE", (1,), np.uint32, data=synapse.synapse_type )

  # Lists (as arrays)
  if ( synapse.seeds != [] ):
    h5synapse.mdgrp.create_dataset ( "SEEDS", (len(synapse.seeds),), np.uint32, synapse.seeds )

  #  segments and segment type
  if ( synapse.segments != [] ):
    h5synapse.mdgrp.create_dataset ( "SEGMENTS", (len(synapse.segments),2), np.uint32, data=synapse.segments)

  return h5synapse


def SeedtoH5 ( seed, h5fh ):
  """Convert a seed to HDF5"""

  # First create the base object
  h5seed = BasetoH5 ( seed, annotation.ANNO_SEED, h5fh )

  # convert these  to enumerations??
  h5seed.mdgrp.create_dataset ( "PARENT", (1,), np.uint32, data=seed.parent )
  h5seed.mdgrp.create_dataset ( "CUBE_LOCATION", (1,), np.uint32, data=seed.cubelocation )
  h5seed.mdgrp.create_dataset ( "SOURCE", (1,), np.uint32, data=seed.source )     
  if seed.position != [None, None, None]:
    h5seed.mdgrp.create_dataset ( "POSITION", (3,), np.uint32, data=seed.position )     

  return h5seed


def SegmenttoH5 ( segment, h5fh ):
  """Convert a segment to HDF5"""

  # First create the base object
  h5segment = BasetoH5 ( segment, annotation.ANNO_SEGMENT, h5fh )

  # Then customize
  h5segment.mdgrp.create_dataset ( "SEGMENTCLASS", (1,), np.uint32, data=segment.segmentclass )
  h5segment.mdgrp.create_dataset ( "PARENTSEED", (1,), np.uint32, data=segment.parentseed )
  h5segment.mdgrp.create_dataset ( "NEURON", (1,), np.uint32, data=segment.neuron )

  # Lists (as arrays)
  if ( segment.synapses != [] ):
    h5segment.mdgrp.create_dataset ( "SYNAPSES", (len(segment.synapses),), np.uint32, segment.synapses )

  if ( segment.organelles != [] ):
    h5segment.mdgrp.create_dataset ( "ORGANELLES", (len(segment.organelles),), np.uint32, segment.organelles )

  return h5segment


def NeurontoH5 ( neuron, h5fh ):
  """Convert a neuron to HDF5"""

  # First create the base object
  h5neuron = BasetoH5 ( neuron, annotation.ANNO_NEURON, h5fh )

  # Lists (as arrays)
  if ( neuron.segments != () ):
    h5neuron.mdgrp.create_dataset ( "SEGMENTS", (len(neuron.segments),), np.uint32, neuron.segments )

  return h5neuron


def OrganelletoH5 ( organelle, h5fh ):
  """Convert a organelle to HDF5"""

  # First create the base object
  h5organelle = BasetoH5 ( organelle, annotation.ANNO_ORGANELLE, h5fh )

  # Then customize
  h5organelle.mdgrp.create_dataset ( "ORGANELLECLASS", (1,), np.uint32, data=organelle.organelleclass )
  h5organelle.mdgrp.create_dataset ( "PARENTSEED", (1,), np.uint32, data=organelle.parentseed )

  # Lists (as arrays)
  if ( organelle.seeds != [] ):
    h5organelle.mdgrp.create_dataset ( "SEEDS", (len(organelle.seeds),), np.uint32, organelle.seeds )
    
  if organelle.centroid != [None, None, None]:
    h5organelle.mdgrp.create_dataset ( "CENTROID", (3,), np.uint32, data=organelle.centroid )     

  return h5organelle


def AnnotationtoH5 ( anno, h5fh ):
  """Operate polymorphically on annotations"""

  if anno.__class__ == annotation.AnnSynapse:
    return SynapsetoH5 ( anno, h5fh )
  elif anno.__class__ == annotation.AnnSeed:
    return SeedtoH5 ( anno, h5fh )
  if anno.__class__ == annotation.AnnSegment:
    return SegmenttoH5 ( anno, h5fh )
  if anno.__class__ == annotation.AnnNeuron:
    return NeurontoH5 ( anno, h5fh )
  if anno.__class__ == annotation.AnnOrganelle:
    return OrganelletoH5 ( anno, h5fh )
  elif anno.__class__ == annotation.Annotation:
    return BasetoH5 ( anno, annotation.ANNO_ANNOTATION, h5fh )
  else:
    logger.warning ("(AnnotationtoH5) Does not support this annotation type yet. Type = %s" % anno.__class__)
    raise OCPCAError ("(AnnotationtoH5) Does not support this annotation type yet. Type = %s" % anno.__class__)



#########  Other HDF5 utility functions.  Not RAMON   ############

def PackageIDs ( annoids ):
  """Create an HDF5 file that contains a list of IDs in a field entitled ANNOIDS
      and return a file reader for that HDF5 file"""

  # Create an in-memory HDF5 file
  tmpfile = tempfile.NamedTemporaryFile()
  h5fh = h5py.File ( tmpfile.name )

  if len(annoids) != 0: 
    h5fh.create_dataset ( "ANNOIDS", annoids.shape, np.uint32, data=annoids ) 

  h5fh.flush()
  tmpfile.seek(0)
  return tmpfile.read()

def h5toCSV ( h5f ):
  """Marshall all HDF5 fields into a csv file"""

  fstring = cStringIO.StringIO()
  csvw = csv.writer(fstring, delimiter=',')

  keys = h5f.keys()
  idgrp = h5f.get(keys[0])

  for k in idgrp.keys():
    if k == 'METADATA':
      mdgrp = idgrp.get('METADATA')
      for m in mdgrp.keys():
        if len(mdgrp[m]) == 1:
          csvw.writerow ( [m, mdgrp[m][0]] )
        else: 
          csvw.writerow ( [m, mdgrp[m][:]] )
    else:
      if len(idgrp[k]) == 1:
        csvw.writerow ( [k, idgrp[k][0]] )
      else: 
        csvw.writerow ( [k, idgrp[k][:]] )

  return fstring.getvalue()
