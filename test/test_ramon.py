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

import requests
import re
import tempfile
import h5py
import string
import random
import csv
import numpy as np
import pytest
import httplib
from contextlib import closing
import makeunitdb
import ndlib.ndtype
from params import Params
from ndlib.restutil import *
from postmethods import *
from ramonmethods import H5AnnotationFile, getH5id, makeAnno, getId, getField, setField
from test_settings import *

p = Params()
p.token = 'unittest'
p.resolution = 0
p.channels = ['unit_anno']

@pytest.mark.skipif(KV_ENGINE == REDIS, reason='Annotation not supported in Redis')
class Test_Ramon:

  def setup_class(self):
    """Create the unittest database"""
    makeunitdb.createTestDB(p.token, readonly=0)

  def teardown_class (self):
    """Destroy the unittest database"""
    makeunitdb.deleteTestDB(p.token)

  def test_test_segment (self):
    """Upload a segment and test it's fields"""

    for i in range(1,10):
      makeAnno (p, 1)

    # Make a segment
    makeAnno (p, 4)

    # make a bunch of synapses
    q = Params()
    q.token = 'unittest'
    q.resolution = 0
    q.channels = ['unit_anno']

    synids = []
    presynids = []
    postsynids = []
    for i in range(0,8):
      makeAnno ( q, 2)
      f = setField(q, 'segments', ','.join([str(p.annoid),str(random.randint(500,1000))]))
#      f = setField(q, 'presegments', ','.join([str(p.annoid),str(random.randint(500,1000))]))
      f = setField(q, 'presegments', ','.join([str(p.annoid)]))
      f = setField(q, 'postsegments', ','.join([str(p.annoid)]))
      synids.append(q.annoid)
      presynids.append(q.annoid)
      postsynids.append(q.annoid)

    # make one more segment
    makeAnno ( q, 2)
    f = setField(q, 'segments', p.annoid)
    synids.append(q.annoid)

    # Test synapses
    f = getField(p, 'synapses')
    rsynids = f.content.split(',')
    for sid in rsynids:
      assert int(sid) in synids
    assert len(rsynids) == 9

    # Test presynapses
    f = getField(p, 'presynapses')
    rsynids = f.content.split(',')
    for sid in rsynids:
      assert int(sid) in presynids
    assert len(rsynids) == 8

    # Test postsynapses
    f = getField(p, 'postsynapses')
    rsynids = f.content.split(',')
    for sid in rsynids:
      assert int(sid) in postsynids
    assert len(rsynids) == 8

    # make a bunch of organelles
    q = Params()
    q.token = 'unittest'
    q.resolution = 0
    q.channels = ['unit_anno']

    orgids = []
    for i in range(0,8):
      makeAnno ( q, 6 )
      f = setField(q, 'segment', p.annoid)
      orgids.append(q.annoid)

    # Test synapses
    f = getField(p, 'organelles')
    rorgids = f.content.split(',')
    for cid in rorgids:
      assert int(cid) in orgids
    assert len(rorgids) == 8



  def test_anno_minmal(self):
    """Upload a minimal and maximal annotation. Verify fields."""

    # Create an in-memory HDF5 file
    tmpfile = tempfile.NamedTemporaryFile()
    h5fh = h5py.File ( tmpfile.name )
    # Create the top level annotation id namespace
    idgrp = h5fh.create_group ( str(0) )
    h5fh.flush()
    tmpfile.seek(0)

    p.annoid = putAnnotation(p, tmpfile)
    h5ret = getAnnotation(p)

    idgrpret = h5ret.get(str(p.annoid))
    assert idgrpret
    assert ( idgrpret['ANNOTATION_TYPE'][0] == 1 )
    assert not idgrpret.get('RESOLUTION')
    assert not idgrpret.get('XYZOFFSET')
    assert not idgrpret.get('VOXELS')
    assert not idgrpret.get('CUTOUT')
    mdgrpret = idgrpret['METADATA']
    assert mdgrpret
    assert ( mdgrpret['CONFIDENCE'][0] == 0.0 )
    assert ( mdgrpret['STATUS'][0] == 0 )
    assert ( mdgrpret['KVPAIRS'][:] == '' )
    assert ( mdgrpret['AUTHOR'][:] == '' )


  def test_anno_full (self):
    """Upload a fully populated HDF5 file"""

    # Create an in-memory HDF5 file
    tmpfile = tempfile.NamedTemporaryFile()
    h5fh = h5py.File ( tmpfile.name )
    # Create the top level annotation id namespace
    idgrp = h5fh.create_group ( str(0) )

    # Create a metadata group
    mdgrp = idgrp.create_group ( "METADATA" )

    # now lets add a bunch of random values for the specific annotation type
    ann_status = random.randint(0,4)
    ann_confidence = random.random()
    ann_author = 'unittest_author'

    # Annotation type
    idgrp.create_dataset ( "ANNOTATION_TYPE", (1,), np.uint32, data=1 )

    # Set Annotation specific metadata
    mdgrp.create_dataset ( "STATUS", (1,), np.uint32, data=ann_status )
    mdgrp.create_dataset ( "CONFIDENCE", (1,), np.float, data=ann_confidence )
    mdgrp.create_dataset ( "AUTHOR", (1,), dtype=h5py.special_dtype(vlen=str), data=ann_author )

    h5fh.flush()
    tmpfile.seek(0)

    p.annoid = putAnnotation(p, tmpfile)
    h5ret = getAnnotation(p)

    idgrpret = h5ret.get(str(p.annoid))
    assert idgrpret
    assert ( idgrpret['ANNOTATION_TYPE'][0] == 1 )
    assert not idgrpret.get('RESOLUTION')
    assert not idgrpret.get('XYZOFFSET')
    assert not idgrpret.get('VOXELS')
    assert not idgrpret.get('CUTOUT')
    mdgrpret = idgrpret['METADATA']
    assert mdgrpret
    assert ( abs(mdgrpret['CONFIDENCE'][0] - ann_confidence) < 0.0001 )
    assert ( mdgrpret['STATUS'][0] == ann_status )
    assert ( mdgrpret['AUTHOR'][:] == ann_author )

    tmpfile.close()


  def test_anno_update (self):
    """Upload an Updated file with new data"""

    tmpfile = tempfile.NamedTemporaryFile()
    h5fh = h5py.File ( tmpfile.name )

    # Create the top level annotation id namespace
    idgrp = h5fh.create_group ( str(p.annoid) )

    # Create a metadata group
    mdgrp = idgrp.create_group ( "METADATA" )

    # now lets add a bunch of random values for the specific annotation type
    ann_status = random.randint(0,4)
    ann_confidence = random.random()
    ann_author = 'unittest_author2'

    # Annotation type
    idgrp.create_dataset ( "ANNOTATION_TYPE", (1,), np.uint32, data=1 )

    # Set Annotation specific metadata
    mdgrp.create_dataset ( "STATUS", (1,), np.uint32, data=ann_status )
    mdgrp.create_dataset ( "CONFIDENCE", (1,), np.float, data=ann_confidence )
    mdgrp.create_dataset ( "AUTHOR", (1,), dtype=h5py.special_dtype(vlen=str), data=ann_author )

    h5fh.flush()
    tmpfile.seek(0)

    p.field = 'update'
    p.annoid = putAnnotation(p, tmpfile)
    p.field = None
    h5ret = getAnnotation(p)

    idgrpret = h5ret.get(str(p.annoid))
    assert idgrpret
    assert ( idgrpret['ANNOTATION_TYPE'][0] == 1 )
    assert not idgrpret.get('RESOLUTION')
    assert not idgrpret.get('XYZOFFSET')
    assert not idgrpret.get('VOXELS')
    assert not idgrpret.get('CUTOUT')
    mdgrpret = idgrpret['METADATA']
    assert mdgrpret
    assert ( abs(mdgrpret['CONFIDENCE'][0] - ann_confidence) < 0.0001 )
    assert ( mdgrpret['STATUS'][0] == ann_status )
    assert ( mdgrpret['AUTHOR'][:] == ann_author )


  def test_anno_delete (self):
    """Delete the object"""

    # Build the delete URL
    try:
      (base,suffix) = SITE_HOST.split("/",1)
    except:
      base = SITE_HOST
      suffix = None

    if suffix:
      url = 'https://{}/{}/sd/{}/{}/{}/'.format(base, suffix, 'unittest', 'unit_anno', p.annoid )
    else:
      url = 'https://{}/sd/{}/{}/{}/'.format(base, 'unittest', 'unit_anno', p.annoid )

    resp = deleteURL(url)
    assert resp.content == "Success"

    # retrieve the annotation
    # verify that it's not there.
    url = "https://{}/sd/{}/{}/{}/".format(SITE_HOST, 'unittest', 'unit_anno', p.annoid)
    resp = getURL( url )
    assert(resp.status_code >= 400)


  def test_anno_upload( self ):
    """Upload all different kinds of annotations and retrieve"""

    for anntype in [ 1, 2, 3, 4, 5, 6]:

      annoid = 0
      f = H5AnnotationFile ( anntype, annoid )

      putid1 = putAnnotation(p, f)

      #  this assumes that +1 is available (which it is)
      newid = putid1 + 1
      f = H5AnnotationFile ( anntype, newid )

      putid2 = putAnnotation(p, f)

      # retrieve both annotations
      p.annoid = putid1
      assert ( putid1 == getId(p) )
      p.annoid = putid2
      assert ( putid2 == getId(p) )


  def test_annotation (self):
    """Upload an annotation and test it's fields"""

    # Make an annotation
    makeAnno (p, 1)

    # Test Status
    status = random.randint (0,100)
    f = setField(p, 'status', status)
    f = getField(p, 'status')
    assert status == int(f.content)

    # Test confidence
    confidence = random.random ()
    f = setField(p, 'confidence', confidence)
    f = getField(p, 'confidence')
    assert abs(confidence - float(f.content)) < 0.001

    # Test author
    #f = self.getField(p, 'author')
    #assert 'Unit Test' == f.content


  def test_synapse (self):
    """Upload a synapse and test it's fields"""

    # Make a synapse
    makeAnno (p, 2)

    # Test synapse type
    synapse_type = random.randint (0,100)
    f = setField(p, 'synapse_type', synapse_type)
    f = getField(p, 'synapse_type')
    assert synapse_type == int(f.content)

    # Test the weight
    weight = random.random ()
    f = setField(p, 'weight', weight)
    f = getField(p, 'weight')
    assert abs(weight - float(f.content)) < 0.001

    # Test the inheritance
    status = random.randint (0,100)
    f = setField(p, 'status', status)
    f = getField(p, 'status')
    assert status == int(f.content)

    # Test the seeds
    seeds = [random.randint(0,100), random.randint(0,100), random.randint(0,100)]
    f = setField(p, 'seeds', ','.join([str(i) for i in seeds]))
    f = getField(p, 'seeds')
    assert ','.join([str(i) for i in seeds]) == f.content

    # test the centroid
    centroid = [random.randint(0,65535), random.randint(0,65535), random.randint(0,65535)]
    f = setField(p, 'centroid', ','.join([str(i) for i in centroid]))
    f = getField(p, 'centroid')
    assert ','.join([str(i) for i in centroid]) == f.content

    # Test the segments
    segments = [random.randint(0,100), random.randint(0,100), random.randint(0,100)]
    f = setField(p, 'segments', ','.join([str(i) for i in segments]))
    f = getField(p, 'segments')
    assert ','.join([str(i) for i in segments]) == f.content

    # Test the presegments
    presegments = [random.randint(0,100), random.randint(0,100), random.randint(0,100)]
    f = setField(p, 'presegments', ','.join([str(i) for i in presegments]))
    f = getField(p, 'presegments')
    assert ','.join([str(i) for i in presegments]) == f.content

    # Test the postsegments
    postsegments = [random.randint(0,100), random.randint(0,100), random.randint(0,100)]
    f = setField(p, 'postsegments', ','.join([str(i) for i in postsegments]))
    f = getField(p, 'postsegments')
    assert ','.join([str(i) for i in postsegments]) == f.content

  def test_seed (self):
    """Upload a seed and test it's fields"""

    # Make a seed
    makeAnno (p, 3)

    # Test the parent
    parent = random.randint (0,100)
    f = setField(p, 'parent', parent)
    f = getField(p, 'parent')
    assert parent == int(f.content)

    # Test the source
    source = random.randint (0,100)
    f = setField(p, 'source', source)
    f = getField(p, 'source')
    assert source == int(f.content)

    # Test the cubelocation
    cubelocation = random.randint (0,100)
    f = setField(p, 'cubelocation', cubelocation)
    f = getField(p, 'cubelocation')
    assert cubelocation == int(f.content)

    # Test the position
    position = [random.randint (0,100), random.randint(0,100), random.randint(0,100)]
    f = setField(p, 'position', ','.join([str(i) for i in position]))
    f = getField(p, 'position')
    assert ','.join([str(i) for i in position]) == f.content




  def test_neuron (self):
    """Upload a neuron and test it's fields"""

    # Make a neuron
    makeAnno (p, 5)

    # make a bunch of segments and add to the neuron
    q = Params()
    q.token = 'unittest'
    q.resolution = 0
    q.channels = ['unit_anno']

    segids = []
    for i in range(0,5):
      makeAnno ( q, 4)
      f = setField(q, 'neuron', p.annoid)
      segids.append(q.annoid)

    # Test segments
    f = getField(p, 'segments')
    rsegids = f.content.split(',')
    for sid in rsegids:
      assert int(sid) in segids
    assert len(rsegids) == 5

  def test_organelle (self):
    """Upload an organelle and test it's fields"""

    # Make an organelle
    makeAnno ( p, 6 )

    # Test the parentseed
    parentseed = random.randint (0,100)
    f = setField(p, 'parentseed', parentseed)
    f = getField(p, 'parentseed')
    assert parentseed == int(f.content)

    # Test the organelleclass
    organelleclass = random.randint (0,100)
    f = setField(p, 'organelleclass', organelleclass)
    f = getField(p, 'organelleclass')
    assert organelleclass == int(f.content)

    # Test the segment
    segment = random.randint (0,65535)
    f = setField(p, 'segment', segment)
    f = getField(p, 'segment')
    assert segment == int(f.content)

    # Test status
    status = random.randint (0,100)
    f = setField(p, 'status', status)
    f = getField(p, 'status')
    assert status == int(f.content)

    # Test the seeds
    seeds = [random.randint(0,100), random.randint(0,100), random.randint(0,100)]
    f = setField(p, 'seeds', ','.join([str(i) for i in seeds]))
    f = getField(p, 'seeds')
    assert ','.join([str(i) for i in seeds]) == f.content

  def test_wrong ( self ):

    # Make an annotation
    makeAnno (p, 2)

    # Test the synapse type
    synapse_type = random.randint (0,100)
    f = setField(p, 'synapse_type', synapse_type)
    f = getField(p, 'synapse_type')
    assert synapse_type == int(f.content)

    # Test the weight
    weight = random.random ()
    f = setField(p, 'weight', weight)
    f = getField(p, 'weight')
    assert abs(weight - float(f.content)) < 0.001

    # Test inheritance
    status = random.randint (0,100)
    f = setField(p, 'status', status)
    f = getField(p, 'status')
    assert status == int(f.content)

    #  bad format to a number
    url =  "https://{}/sd/{}/{}/{}/setField/status/aa/".format(SITE_HOST, 'unittest', 'unit_anno', p.annoid)
    req = getURL( url )
    assert(req.status_code >= 400)

    #  request a missing field
    url =  "https://{}/sd/{}/{}/{}/getField/othernonesuch/".format(SITE_HOST, 'unittest', 'unit_anno', p.annoid)
    req = getURL( url )
    assert(req.status_code >= 400)

  def test_node (self):
    """Upload a skeleton node and test it's fields"""

    # Make a node
    makeAnno (p, 7)

    # test the nodetype
    nodetype = random.randint (0,100)
    f = setField(p, 'nodetype', nodetype)
    f = getField(p, 'nodetype')
    assert nodetype == int(f.content)

    # test the skeletonid
    skeletonid = random.randint (0,65535)
    f = setField(p, 'skeletonid', skeletonid)
    f = getField(p, 'skeletonid')
    assert skeletonid == int(f.content)

    # test the pointid
    pointid = random.randint (0,65535)
    f = setField(p, 'pointid', pointid)
    f = getField(p, 'pointid')
    assert pointid == int(f.content)

    # test the parentid
    parentid = random.randint (0,65535)
    f = setField(p, 'parentid', parentid)
    f = getField(p, 'parentid')
    assert parentid == int(f.content)

    # test the radius
    radius = random.random()
    f = setField(p, 'radius', radius)
    f = getField(p, 'radius')
    assert abs(radius - float(f.content)) < 0.001

    # test the location
    location = [random.random(), random.random(), random.random()]
    f = setField(p, 'location', ','.join([str(i) for i in location]))
    f = getField(p, 'location')
    assert ','.join([str(i) for i in location]) == f.content

    # make a bunch of children
    q = Params()
    q.token = 'unittest'
    q.resolution = 0
    q.channels = ['unit_anno']

    childids = []
    for i in range(0,4):
      makeAnno ( q, 9)
      f = setField(q, 'parent', p.annoid)
      childids.append(q.annoid)

    # Test children
    f = getField(p, 'children')
    rchildids = f.content.split(',')
    for cid in rchildids:
      assert int(cid) in childids
    assert len(rchildids) == 4


  def test_skeleton (self):
    """Upload a skeleton and test it's fields"""

    # Make a node
    makeAnno (p, 8)

    # test the nodetype
    skeletontype = random.randint (0,100)
    f = setField(p, 'skeletontype', skeletontype)
    f = getField(p, 'skeletontype')
    assert skeletontype == int(f.content)

    # test the rootnode
    rootnode = random.randint (0,65535)
    f = setField(p, 'rootnode', rootnode)
    f = getField(p, 'rootnode')
    assert rootnode == int(f.content)

    # add some nodes to the skeleton and query them
    # make a bunch of children cnodes
    q = Params()
    q.token = 'unittest'
    q.resolution = 0
    q.channels = ['unit_anno']

    r = Params()
    r.token = 'unittest'
    r.resolution = 0
    r.channels = ['unit_anno']
    # make a root node

    s = Params()
    s.token = 'unittest'
    s.resolution = 0
    s.channels = ['unit_anno']
    # make a root node

    skelids = []

    # make a root node
    makeAnno ( q, 7)
    setField(p, 'rootnode', q.annoid)
    setField(q, 'skeleton', p.annoid)
    skelids.append(q.annoid)

    # Make 2 children and four grandchildren
    for i in range(0,2):
      makeAnno ( r, 7)
      f = setField(r, 'parent', q.annoid)
      f = setField(r, 'skeleton', p.annoid)
      skelids.append(r.annoid)
      for i in range(0,2):
        makeAnno ( s, 7)
        f = setField(s, 'parent', r.annoid)
        f = setField(s, 'skeleton', p.annoid)
        skelids.append(s.annoid)

    # Test skeleton
    f = getField(p, 'nodes')
    rskelids = f.content.split(',')
    for sid in rskelids:
      assert int(sid) in skelids
    assert len(rskelids) == 7


  def test_roi (self):
    """Upload an roi and test it's fields"""

    # Make a skeleton
    makeAnno (p, 9)

    # test the parent
    parent = random.randint (0,65535)
    f = setField(p, 'parent', parent)
    f = getField(p, 'parent')
    assert parent == int(f.content)

    # make a bunch of children ROIs
    q = Params()
    q.token = 'unittest'
    q.resolution = 0
    q.channels = ['unit_anno']

    childids = []
    for i in range(0,4):
      makeAnno ( q, 9)
      f = setField(q, 'parent', p.annoid)
      childids.append(q.annoid)

    # Test children
    f = getField(p, 'children')
    rchildids = f.content.split(',')
    for cid in rchildids:
      assert int(cid) in childids
    assert len(rchildids) == 4


  def test_kvpairs(self):

    # do a general kv test for each annotation type
    for i in range(1,10):

      makeAnno (p, i)

      key = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(random.randint(1,128)))
      value = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(random.randint(1,1024)))

      setField( p, key, value )
      f = getField ( p, key )
      assert ( f.content == value )
