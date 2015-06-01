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
    assert ( mdgrpret['AUTHOR'][:] == 'unknown' )


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
    """Upload a Updated file with new data"""

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
    #assert ( mdgrpret['CONFIDENCE'][0] == ann_confidence )
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
      conn.request ('DELETE', '/{}/ca/{}/{}/{}/'.format(suffix, 'unittest', 'unit_anno', p.annoid)) 
    else:
      conn.request ('DELETE', '/ca/{}/{}/{}/'.format('unittest', 'unit_anno', p.annoid))

    resp = conn.getresponse()
    content=resp.read()

    assert content == 'Success'

    # retrieve the annotation
    # verify that it's not there.
    url = "http://{}/ca/{}/{}/{}/".format(SITE_HOST, 'unittest', 'unit_anno', p.annoid)
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
  

  def test_annotation_field (self):
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
    assert confidence - float(f.read()) < 0.001
    
    # Test author
    #f = self.getField(p, 'author')
    #assert 'Unit Test' == f.read()


  def test_synapse_field (self):
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
    assert weight - float(f.read()) < 0.001

    # Test the inheritance
    status = random.randint (0,100)
    f = setField(p, 'status', status)
    f = getField(p, 'status')
    assert status == int(f.read()) 


  def test_seed_field (self):
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


  def test_segment_field (self):
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


  def test_neuron_field (self):
    """Upload a neuron and test it's fields"""

    # Make a neuron
    makeAnno (p, 5)

    # Test inheritance
    status = random.randint (0,100)
    f = setField(p, 'status', status)
    f = getField(p, 'status')
    assert status == int(f.read()) 


  def test_organelle_field (self):
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


  def test_wrong_field ( self ):
   
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
    assert weight - float(f.read()) < 0.001

    # Test inheritance
    status = random.randint (0,100)
    f = setField(p, 'status', status)
    f = getField(p, 'status')
    assert status == int(f.read())
    
    #  bad format to a number
    url =  "http://{}/ca/{}/{}/{}/setField/status/aa/".format(SITE_HOST, 'unittest', 'unit_anno', p.annoid)
    with pytest.raises(urllib2.HTTPError): 
      req = urllib2.Request ( url )
      f = urllib2.urlopen ( url )
    
    #  request a missing field
    url =  "http://{}/ca/{}/{}/{}/getField/othernonesuch/".format(SITE_HOST, 'unittest', 'unit_anno', p.annoid)
    with pytest.raises(urllib2.HTTPError): 
      req = urllib2.Request ( url )
      f = urllib2.urlopen ( url )

# RBTODO add tests key/value and compound fields.
    #  assign a field for a wrong annotation type
#    url =  "http://%s/ca/%s/%s/setField/segmentclass/2/" % ( SITE_HOST, 'unittest',str(annid))
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
#    url = "http://%s/ca/%s/" % ( SITE_HOST, 'unittest')
#
#    # write an object (server creates identifier)
#    req = urllib2.Request ( url, tmpfile.read())
#    response = urllib2.urlopen(req)
#    putid = int(response.read())
#
#    # now read and verify
#    # retrieve the annotation
#    url = "http://%s/ca/%s/%s/" % ( SITE_HOST, 'unittest', str(putid))
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
