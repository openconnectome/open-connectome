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

import re
import tempfile
import h5py
import random 
import csv
import numpy as np
import pytest
import httplib
from contextlib import closing

from params import Params
from postmethods import putAnnotation, getAnnotation, getURL, postURL
import kvengine_to_test
import site_to_test
import makeunitdb
SITE_HOST = site_to_test.site


p = Params()
p.token = 'unittest'
p.resolution = 0
p.channels = ['unit_anno']


def H5AnnotationFile ( annotype, annoid, kv=None ):
  """Create an HDF5 file and populate the fields. Return a file object.
      This is a support routine for all the RAMON tests."""

  # Create an in-memory HDF5 file
  tmpfile = tempfile.NamedTemporaryFile()
  h5fh = h5py.File ( tmpfile.name )

  # Create the top level annotation id namespace
  idgrp = h5fh.create_group ( str(annoid) )

  # Annotation type
  idgrp.create_dataset ( "ANNOTATION_TYPE", (1,), np.uint32, data=annotype )

  # Create a metadata group
  mdgrp = idgrp.create_group ( "METADATA" )

  # now lets add a bunch of random values for the specific annotation type
  ann_status = random.randint(0,4)
  ann_confidence = random.random()
  ann_author = 'randal'

  # Set Annotation specific metadata
  mdgrp.create_dataset ( "STATUS", (1,), np.uint32, data=ann_status )
  mdgrp.create_dataset ( "CONFIDENCE", (1,), np.float, data=ann_confidence )
  mdgrp.create_dataset ( "AUTHOR", (1,), dtype=h5py.special_dtype(vlen=str), data=ann_author )

  kvpairs={}
  if kv!= None:
    [ k, sym, v ] = kv.partition(':')
    kvpairs[k]=v
     
    # Turn our dictionary into a csv file
    fstring = cStringIO.StringIO()
    csvw = csv.writer(fstring, delimiter=',')
    csvw.writerows([r for r in kvpairs.iteritems()])
     
    # User-defined metadata
    mdgrp.create_dataset ( "KVPAIRS", (1,), dtype=h5py.special_dtype(vlen=str), data=fstring.getvalue())

  # Synapse:
  if annotype == 2:

    syn_weight = random.random()*1000.0
    syn_synapse_type = random.randint(1,9)
    syn_seeds = [ random.randint(1,1000) for x in range(5) ]
    syn_segments = [ [random.randint(1,1000),random.randint(1,1000)] for x in range(4) ]

    mdgrp.create_dataset ( "WEIGHT", (1,), np.float, data=syn_weight )
    mdgrp.create_dataset ( "SYNAPSE_TYPE", (1,), np.uint32, data=syn_synapse_type )
    mdgrp.create_dataset ( "SEEDS", (len(syn_seeds),), np.uint32, data=syn_seeds )
    mdgrp.create_dataset ( "SEGMENTS", (len(syn_segments),2), np.uint32, data=syn_segments)

  # Seed
  elif annotype == 3:

    seed_parent = random.randint(1,1000)
    seed_position = [ random.randint(1,10000) for x in range(3) ]
    seed_cubelocation = random.randint(1,9)
    seed_source = random.randint(1,1000)

    mdgrp.create_dataset ( "PARENT", (1,), np.uint32, data=seed_parent )
    mdgrp.create_dataset ( "CUBE_LOCATION", (1,), np.uint32, data=seed_cubelocation )
    mdgrp.create_dataset ( "SOURCE", (1,), np.uint32, data=seed_source )    
    mdgrp.create_dataset ( "POSITION", (3,), np.uint32, data=seed_position )

  # Segment
  elif annotype == 4:
     
    seg_parentseed = random.randint(1,100000)
    seg_segmentclass = random.randint(1,9)
    seg_neuron = random.randint(1,100000)
    seg_synapses = [ random.randint(1,100000) for x in range(5) ]
    seg_organelles = [ random.randint(1,100000) for x in range(5) ]

    mdgrp.create_dataset ( "SEGMENTCLASS", (1,), np.uint32, data=seg_segmentclass )
    mdgrp.create_dataset ( "PARENTSEED", (1,), np.uint32, data=seg_parentseed )
    mdgrp.create_dataset ( "NEURON", (1,), np.uint32, data=seg_neuron )
    mdgrp.create_dataset ( "SYNAPSES", (len(seg_synapses),), np.uint32, seg_synapses )
    mdgrp.create_dataset ( "ORGANELLES", (len(seg_organelles),), np.uint32, seg_organelles )

  # Neuron
  elif annotype == 5:

    neuron_segments = [ random.randint(1,1000) for x in range(10) ]
    mdgrp.create_dataset ( "SEGMENTS", (len(neuron_segments),), np.uint32, neuron_segments )

  # Organelle
  elif annotype == 6:

    org_parentseed = random.randint(1,100000)
    org_organelleclass = random.randint(1,9)
    org_seeds = [ random.randint(1,100000) for x in range(5) ]
    org_centroid = [ random.randint(1,10000) for x in range(3) ]

    mdgrp.create_dataset ( "ORGANELLECLASS", (1,), np.uint32, data=org_organelleclass )
    mdgrp.create_dataset ( "PARENTSEED", (1,), np.uint32, data=org_parentseed )
    mdgrp.create_dataset ( "SEEDS", (len(org_seeds),), np.uint32, org_seeds )
    mdgrp.create_dataset ( "CENTROID", (3,), np.uint32, data=org_centroid )

  h5fh.flush()
  tmpfile.seek(0)
  return tmpfile


def getH5id ( f ):
  """Extract annotation id from the HDF5 file"""
  tmpfile = tempfile.NamedTemporaryFile ( )
  tmpfile.write ( f.read() )
#    tmpfile.tell()
  tmpfile.seek(0)
  h5f = h5py.File ( tmpfile.name, driver='core', backing_store=False )
  keys = h5f.keys()
  tmpfile.close()
  return int (keys[0])


def makeAnno ( p, anntype ):
  """Helper make an annotation"""

  # Create an annotation
  tmpfile = tempfile.NamedTemporaryFile()
  h5fh = h5py.File ( tmpfile.name )

  # Create the top level annotation id namespace
  idgrp = h5fh.create_group ( str(0) )
  mdgrp = idgrp.create_group ( "METADATA" )
  ann_author='Unit Test'
  mdgrp.create_dataset ( "AUTHOR", (1,), dtype=h5py.special_dtype(vlen=str), data=ann_author )

  idgrp.create_dataset ( "ANNOTATION_TYPE", (1,), np.uint32, data=anntype )

  h5fh.flush()
  tmpfile.seek(0)

  p.annoid =  putAnnotation (p, tmpfile)
  
  tmpfile.close()


def getId ( p ):
  """Get the annotation at this Id"""
  
  url = "http://{}/ca/{}/{}/{}/".format(SITE_HOST, p.token, p.channels[0], p.annoid)
  return getH5id ( getURL(url) )


def getField (p, field):
  """Get the specified field"""
  
  url =  "http://{}/ca/{}/{}/{}/getField/{}/".format(SITE_HOST, p.token, p.channels[0], p.annoid, field)
  return getURL( url )


def setField (p, field, value):
  """Set the specified field to the value"""
   
  url =  "http://{}/ca/{}/{}/{}/setField/{}/{}/".format(SITE_HOST, p.token, p.channels[0], p.annoid, field, value)
  assert ( getURL(url).read() == '')


def queryField (p, field, value):
  """Get the specified query to the value"""
   
  url =  "http://{}/ca/{}/{}/query/{}/{}/".format(SITE_HOST, p.token, p.channels[0], field, value)
  f = getURL(url)
  tmpfile = tempfile.NamedTemporaryFile ( )
  tmpfile.write ( f.read() )
  tmpfile.seek(0)
  h5f = h5py.File ( tmpfile.name, driver='core', backing_store=False )
  
  return h5f

def annoHelper ( p, voxels=False, cutout=False ):

  for i in range(p.num_objects):
    
    # either anonymous annotations ids
    if p.annoid == 0:
      p.annoid = 'noid.'+str(i)
    # or a sequence starting from p.annoid
    else:
      p.annoid = p.annoid + 1
      
      # if mutliple objects and no type, insert random object types
      if p.anntype == 1 and p.num_objects > 1 and not (p.field == 'voxels') and not (p.field == 'cutout'):
        p.anntype = random.randint(1,6)

    f = H5AnnotationFile (p.anntype, p.annoid)


    if cutout:
      if voxels:
        addVoxels (p, f)
      else:
        addCutout(p, f)

  return f


def addVoxels( p, f ):
  """Add a cube of data to the HDF5 file as a list of voxels"""

  h5f = h5py.File ( f.name )
  ( xlow, xhigh, ylow, yhigh, zlow, zhigh ) = p.args
  voxlist=[]
  
  for k in range (zlow,zhigh):
    for j in range (ylow,yhigh):
      for i in range (xlow,xhigh):
        voxlist.append ( [ i,j,k ] )
  
  idgrp = h5f[str(p.annoid)]
  # make annid 0 if it's not an integer
  if not isinstance(p.annoid,int):
    p.annoid = 0
  
  idgrp.create_dataset ( "ANNOTATION_ID", (1,), np.uint32, data = p.annoid )
  idgrp.create_dataset ( "RESOLUTION", (1,), np.uint32, data = p.resolution )
  idgrp.create_dataset ( "VOXELS", (len(voxlist),3), np.uint32, data=voxlist )

  h5f.flush()


def addCutout(p, f):
  """Add a cube of data to the HDF5 file"""

  h5f = h5py.File ( f.name )
  ( xlow, xhigh, ylow, yhigh, zlow, zhigh ) = p.args
  anndata = np.ones ( [ zhigh-zlow, yhigh-ylow, xhigh-xlow ], dtype=np.uint32 )
  
  idgrp = self.h5fh[str(annid)]
  idgrp.create_dataset ( "RESOLUTION", (1,), np.uint32, data=resolution )
  idgrp.create_dataset ( "XYZOFFSET", (3,), dtype = np.uint32, data=[xlow,ylow,zlow] )
  idgrp.create_dataset ( "CUTOUT", anndata.shape, dtype = anndata.dtype, data = anndata )

  h5f.flush()


def countVoxels (p, h5):
  """Count the number of voxels in an HDF5 file for an annid"""

  for k in h5.keys():
    if int(k) == p.annoid:
      idgrp = h5.get(k)
      if idgrp.get('VOXELS'): 
        return len(idgrp['VOXELS'][:]) 
      elif idgrp.get('CUTOUT') and idgrp.get('XYZOFFSET'):
        return len(np.nonzero(np.array(idgrp['CUTOUT'][:,:,:]))[0])
  
  return 0


def countCuboidVoxels (p, h5):
  """Count the number of voxels in an HDF5 file for an annotation id"""
  
  voxsum = 0
  
  for k in h5.keys():
    if int(k) == p.annoid:
      cbgrp = h5[k]['CUBOIDS']
      for cb in cbgrp.keys():
        voxsum += len(np.nonzero(np.array(cbgrp[cb]['CUBOID'][:,:,:]))[0])
  
  return voxsum
