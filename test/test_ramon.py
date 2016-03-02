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

import urllib2
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
from postmethods import putAnnotation, getAnnotation
from ramon import H5AnnotationFile, getH5id, makeAnno, getId, getField, setField
import kvengine_to_test
import site_to_test
import makeunitdb
SITE_HOST = site_to_test.site

p = Params()
p.token = 'unittest'
p.resolution = 0
p.channels = ['unit_anno']

class Test_Ramon:

  def setup_class(self):
    """Create the unittest database"""
    makeunitdb.createTestDB(p.token, readonly=0)

  def teardown_class (self):
    """Destroy the unittest database"""
    makeunitdb.deleteTestDB(p.token)


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

    conn = httplib.HTTPConnection ( base )

    if suffix:
      conn.request ('DELETE', '/{}/sd/{}/{}/{}/'.format(suffix, 'unittest', 'unit_anno', p.annoid)) 
    else:
      conn.request ('DELETE', '/sd/{}/{}/{}/'.format('unittest', 'unit_anno', p.annoid))

    resp = conn.getresponse()
    content=resp.read()

    assert content == 'Success'

    # retrieve the annotation
    # verify that it's not there.
    url = "http://{}/sd/{}/{}/{}/".format(SITE_HOST, 'unittest', 'unit_anno', p.annoid)
    with pytest.raises(urllib2.HTTPError): 
      urllib2.urlopen ( url )


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
    assert status == int(f.read()) 

    # Test confidence
    confidence = random.random ()
    f = setField(p, 'confidence', confidence)
    f = getField(p, 'confidence')
    assert abs(confidence - float(f.read())) < 0.001
    
    # Test author
    #f = self.getField(p, 'author')
    #assert 'Unit Test' == f.read()


  def test_synapse (self):
    """Upload a synapse and test it's fields"""

    # Make a synapse
    makeAnno (p, 2)

    # Test synapse type
    synapse_type = random.randint (0,100)
    f = setField(p, 'synapse_type', synapse_type)
    f = getField(p, 'synapse_type')
    assert synapse_type == int(f.read()) 

    # Test the weight
    weight = random.random ()
    f = setField(p, 'weight', weight)
    f = getField(p, 'weight')
    assert abs(weight - float(f.read())) < 0.001

    # Test the inheritance
    status = random.randint (0,100)
    f = setField(p, 'status', status)
    f = getField(p, 'status')
    assert status == int(f.read()) 

    # Test the seeds
    seeds = [random.randint(0,100), random.randint(0,100), random.randint(0,100)]
    f = setField(p, 'seeds', ','.join([str(i) for i in seeds]))
    f = getField(p, 'seeds')
    assert ','.join([str(i) for i in seeds]) == f.read()

    # test the centroid
    centroid = [random.randint(0,65535), random.randint(0,65535), random.randint(0,65535)]
    f = setField(p, 'centroid', ','.join([str(i) for i in centroid]))
    f = getField(p, 'centroid')
    assert ','.join([str(i) for i in centroid]) == f.read()

  def test_seed (self):
    """Upload a seed and test it's fields"""

    # Make a seed
    makeAnno (p, 3)

    # Test the parent
    parent = random.randint (0,100)
    f = setField(p, 'parent', parent)
    f = getField(p, 'parent')
    assert parent == int(f.read()) 

    # Test the source
    source = random.randint (0,100)
    f = setField(p, 'source', source)
    f = getField(p, 'source')
    assert source == int(f.read()) 

    # Test the cubelocation
    cubelocation = random.randint (0,100)
    f = setField(p, 'cubelocation', cubelocation)
    f = getField(p, 'cubelocation')
    assert cubelocation == int(f.read()) 
    
    # Test the position
    position = [random.randint (0,100), random.randint(0,100), random.randint(0,100)]
    f = setField(p, 'position', ','.join([str(i) for i in position]))
    f = getField(p, 'position')
    assert ','.join([str(i) for i in position]) == f.read()


  def test_segment (self):
    """Upload a segment and test it's fields"""

    # Make a segment
    makeAnno (p, 4)

    # Test the parentseed
    parentseed = random.randint (0,100)
    f = setField(p, 'parentseed', parentseed)
    f = getField(p, 'parentseed')
    assert parentseed == int(f.read()) 

    # Test the segmentclass
    segmentclass = random.randint (0,100)
    f = setField(p, 'segmentclass', segmentclass)
    f = getField(p, 'segmentclass')
    assert segmentclass == int(f.read()) 

    # Test the neuron
    neuron = random.randint (0,100)
    f = setField(p, 'neuron', neuron)
    f = getField(p, 'neuron')
    assert neuron == int(f.read()) 

    # Test inheritance
    status = random.randint (0,100)
    f = setField(p, 'status', status)
    f = getField(p, 'status')
    assert status == int(f.read()) 
    
# These may need to be two way.  Must figure out.  RBTODO
#    # Test the synapses
#    synapses = [random.randint(0,100), random.randint(0,100), random.randint(0,100)]
#    f = setField(p, 'synapses', ','.join([str(i) for i in synapses]))
#    f = getField(p, 'synapses')
#    assert ','.join([str(i) for i in synapses]) == f.read()


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
    rsegids = f.read().split(',')
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
    assert parentseed == int(f.read()) 

    # Test the organelleclass
    organelleclass = random.randint (0,100)
    f = setField(p, 'organelleclass', organelleclass)
    f = getField(p, 'organelleclass')
    assert organelleclass == int(f.read()) 

    # Test inheritance
    status = random.randint (0,100)
    f = setField(p, 'status', status)
    f = getField(p, 'status')
    assert status == int(f.read()) 

    # Test the seeds
    seeds = [random.randint(0,100), random.randint(0,100), random.randint(0,100)]
    f = setField(p, 'seeds', ','.join([str(i) for i in seeds]))
    f = getField(p, 'seeds')
    assert ','.join([str(i) for i in seeds]) == f.read()

  def test_wrong ( self ):
   
    # Make an annotation 
    makeAnno (p, 2)

    # Test the synapse type
    synapse_type = random.randint (0,100)
    f = setField(p, 'synapse_type', synapse_type)
    f = getField(p, 'synapse_type')
    assert synapse_type == int(f.read()) 

    # Test the weight
    weight = random.random ()
    f = setField(p, 'weight', weight)
    f = getField(p, 'weight')
    assert abs(weight - float(f.read())) < 0.001

    # Test inheritance
    status = random.randint (0,100)
    f = setField(p, 'status', status)
    f = getField(p, 'status')
    assert status == int(f.read())
    
    #  bad format to a number
    url =  "http://{}/sd/{}/{}/{}/setField/status/aa/".format(SITE_HOST, 'unittest', 'unit_anno', p.annoid)
    with pytest.raises(urllib2.HTTPError): 
      req = urllib2.Request ( url )
      f = urllib2.urlopen ( url )
    
    #  request a missing field
    url =  "http://{}/sd/{}/{}/{}/getField/othernonesuch/".format(SITE_HOST, 'unittest', 'unit_anno', p.annoid)
    with pytest.raises(urllib2.HTTPError): 
      req = urllib2.Request ( url )
      f = urllib2.urlopen ( url )



  def test_organelle (self):
    """Upload an organelle and test it's fields"""

    # Make an organelle 
    makeAnno ( p, 6 )

    # Test the parentseed
    parentseed = random.randint (0,100)
    f = setField(p, 'parentseed', parentseed)
    f = getField(p, 'parentseed')
    assert parentseed == int(f.read()) 

    # Test the organelleclass
    organelleclass = random.randint (0,100)
    f = setField(p, 'organelleclass', organelleclass)
    f = getField(p, 'organelleclass')
    assert organelleclass == int(f.read()) 

    # Test inheritance
    status = random.randint (0,100)
    f = setField(p, 'status', status)
    f = getField(p, 'status')
    assert status == int(f.read()) 

    # Test the seeds
    seeds = [random.randint(0,100), random.randint(0,100), random.randint(0,100)]
    f = setField(p, 'seeds', ','.join([str(i) for i in seeds]))
    f = getField(p, 'seeds')
    assert ','.join([str(i) for i in seeds]) == f.read()


  def test_node (self):
    """Upload a skeleton node and test it's fields"""

    # Make a neuron
    makeAnno (p, 7)

    # test the nodetype
    nodetype = random.randint (0,100)
    f = setField(p, 'nodetype', nodetype)
    f = getField(p, 'nodetype')
    assert nodetype == int(f.read())

    # test the skeletonid
    skeletonid = random.randint (0,65535)
    f = setField(p, 'skeletonid', skeletonid)
    f = getField(p, 'skeletonid')
    assert skeletonid == int(f.read())

    # test the pointid
    pointid = random.randint (0,65535)
    f = setField(p, 'pointid', pointid)
    f = getField(p, 'pointid')
    assert pointid == int(f.read())

    # test the parentid
    parentid = random.randint (0,65535)
    f = setField(p, 'parentid', parentid)
    f = getField(p, 'parentid')
    assert parentid == int(f.read())

    # test the radius
    radius = random.random()
    f = setField(p, 'radius', radius)
    f = getField(p, 'radius')
    assert abs(radius - float(f.read())) < 0.001

    # test the location
    location = [random.random(), random.random(), random.random()]
    f = setField(p, 'location', ','.join([str(i) for i in location]))
    f = getField(p, 'location')
    assert ','.join([str(i) for i in location]) == f.read()


  def test_node (self):
    """Upload a skeleton node and test it's fields"""

    # Make a node
    makeAnno (p, 7)

    # test the nodetype
    nodetype = random.randint (0,100)
    f = setField(p, 'nodetype', nodetype)
    f = getField(p, 'nodetype')
    assert nodetype == int(f.read())

    # test the skeletonid
    skeletonid = random.randint (0,65535)
    f = setField(p, 'skeletonid', skeletonid)
    f = getField(p, 'skeletonid')
    assert skeletonid == int(f.read())

    # test the pointid
    pointid = random.randint (0,65535)
    f = setField(p, 'pointid', pointid)
    f = getField(p, 'pointid')
    assert pointid == int(f.read())

    # test the parentid
    parentid = random.randint (0,65535)
    f = setField(p, 'parentid', parentid)
    f = getField(p, 'parentid')
    assert parentid == int(f.read())

    # test the radius
    radius = random.random()
    f = setField(p, 'radius', radius)
    f = getField(p, 'radius')
    assert abs(radius - float(f.read())) < 0.001

    # test the location
    location = [random.random(), random.random(), random.random()]
    f = setField(p, 'location', ','.join([str(i) for i in location]))
    f = getField(p, 'location')
    assert ','.join([str(i) for i in location]) == f.read()

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
    rchildids = f.read().split(',')
    for cid in rchildids:
      assert int(cid) in childids
    assert len(rchildids) == 4


  def test_nodes_and_skeletons (self):
    """Upload a skeleton node and test it's fields"""

    # test the nodetype
    skeletontype = random.randint (0,100)
    f = setField(p, 'skeletontype', skeletontype)
    f = getField(p, 'skeletontype')
    assert skeletontype == int(f.read())

    # test the rootnode
    rootnode = random.randint (0,65535)
    f = setField(p, 'rootnode', rootnode)
    f = getField(p, 'rootnode')
    assert rootnode == int(f.read())

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

    # Make 2 grandparents and four parents
    skelids = []
#    for i in range(0,2):
#      makeAnno ( q, 9) 
#      f = setField(q, 'parent', p.annoid)
#      skelids.append(q.annoid)
#      for i in range(0,2):
#        makeAnno ( r, 9) 
#        f = setField(r, 'parent', q.annoid)
#        skelids.append(r.annoid)
#
#    # Test skeleton
#    f = getField(p, 'skeletonnodes')
#    rskelids = f.read().split(',')
#    for sid in rskelids:
#      assert int(sid) in skelids
#    assert len(rskelids) == 6


  def test_roi (self):
    """Upload an roi and test it's fields"""

    # Make a skeleton
    makeAnno (p, 9)

    # test the parent
    parent = random.randint (0,65535)
    f = setField(p, 'parent', parent)
    f = getField(p, 'parent')
    assert parent == int(f.read())

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
    rchildids = f.read().split(',')
    for cid in rchildids:
      assert int(cid) in childids
    assert len(rchildids) == 4


# RBTODO add tests key/value and compound fields.
    #  assign a field for a wrong annotation type
#    url =  "http://%s/sd/%s/%s/setField/segmentclass/2/" % ( SITE_HOST, 'unittest',str(annid))
#    with pytest.raises(urllib2.HTTPError): 
#      req = urllib2.Request ( url )
#      f = urllib2.urlopen ( url )

#  def test_kvpairs(self):
#
#    """Test 1: Create a minimal HDF5 file"""
#    # Create an in-memory HDF5 file
#    tmpfile = tempfile.NamedTemporaryFile()
#    h5fh = h5py.File ( tmpfile.name )
#
#    # Create the top level annotation id namespace
#    idgrp = h5fh.create_group ( str(0) )
#
#    # Create a metadata group
#    mdgrp = idgrp.create_group ( "METADATA" )
#
#    kvpairs={}
#
#    # Turn our dictionary into a csv file
#    fstring = cStringIO.StringIO()
#    csvw = csv.writer(fstring, delimiter=',')
#    csvw.writerows([r for r in kvpairs.iteritems()])
#
#    # User-defined metadata
#    mdgrp.create_dataset ( "KVPAIRS", (1,), dtype=h5py.special_dtype(vlen=str), data=fstring.getvalue())
#
#    # Now put an empty file
#    # Build the put URL
#    url = "http://%s/sd/%s/" % ( SITE_HOST, 'unittest')
#
#    # write an object (server creates identifier)
#    req = urllib2.Request ( url, tmpfile.read())
#    response = urllib2.urlopen(req)
#    putid = int(response.read())
#
#    # now read and verify
#    # retrieve the annotation
#    url = "http://%s/sd/%s/%s/" % ( SITE_HOST, 'unittest', str(putid))
#    f = urllib2.urlopen ( url )
#    retfile = tempfile.NamedTemporaryFile ( )
#    retfile.write ( f.read() )
#    retfile.seek(0)
#    h5ret = h5py.File ( tmpfile.name, driver='core', backing_store=False )
#
#    mdgrpret = idgrpret['METADATA']
#    idgrpret = h5ret.get(str(putid1))
#
#    assert ( mdgrpret['KVPAIRS'][:] == '' )
#
#    for i in range(10):
