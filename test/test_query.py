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
import cStringIO
import tempfile
import h5py
import random 
import csv
import os, sys
import numpy as np
import pytest
from contextlib import closing

import makeunitdb
from params import Params
from ramon import H5AnnotationFile, setField, getField, queryField, makeAnno
#from postmethods import setURL
import kvengine_to_test
import site_to_test
SITE_HOST = site_to_test.site


p = Params()
p.token = 'unittest'
p.channels = ['unit_anno']

class Test_Ramon:

  def setup_class(self):
    """Create the unittest database"""
    makeunitdb.createTestDB('unittest', public=True, readonly=0)

  def teardown_class (self):
    """Destroy the unittest database"""
    makeunitdb.deleteTestDB('unittest')


  def test_query_objects (self):
    """Test the function that lists objects of different types."""

    # synapse annotations
    p.anntype = 2
    status = random.randint(0,100)
    confidence = random.random()*0.3+0.1   # number between 0.1 and 0.4
    synapse_type = random.randint(0,100)
    synapse_weight = random.random()*0.9+0.1   # number between 0.1 and 0.9

    for i in range (10):

      # Make an annotation 
      #annid = makeAnno ( anntype, SITE_HOST )
      makeAnno( p, p.anntype)
      #H5AnnotationFile(p)

      # set some fields in the even annotations
      if i % 2 == 0:
        setField(p, 'status', status)

        # set the confidence
        setField(p, 'confidence', confidence)

        # set the type
        setField(p, 'synapse_type', synapse_type)

      # set some fields in the even annotations
      if i % 2 == 1:
        # set the confidence
        setField(p, 'confidence', 1.0 - confidence)


    # check the status
    h5 = queryField(p, 'status', status)
    assert ( h5['ANNOIDS'].shape[0] == 5 )

    # check all the confidence variants
    field_value = '/'.join( ['lt',str(1.0-confidence-0.0001), ''] )
    h5 = queryField(p, 'confidence', field_value)
    assert ( h5['ANNOIDS'].shape[0] == 5 )

    field_value = '/'.join( ['gt',str(confidence+0.0001), ''] )
    h5 = queryField(p, 'confidence', field_value)
    assert ( h5['ANNOIDS'].shape[0] == 5 )


# Not implemented yet.

    # check the synapse_type 
#    url =  "http://%s/ca/%s/query/synapse_type/%s/" % ( SITE_HOST, 'unittest', synapse_type )
#    req = urllib2.Request ( url )
#    f = urllib2.urlopen ( url )
#    retfile = tempfile.NamedTemporaryFile ( )
#    retfile.write ( f.read() )
#    retfile.seek(0)
#    h5ret = h5py.File ( retfile.name, driver='core', backing_store=False )
#    assert h5ret['ANNOIDS'].shape[0] ==5
#
#    # check the synapse_weight 
#    url =  "http://%s/ca/%s/query/synapse_weight/%s/%s/" % ( SITE_HOST, 'unittest', 'gt', confidence-0.00001 )
#    req = urllib2.Request ( url )
#    f = urllib2.urlopen ( url )
#    retfile = tempfile.NamedTemporaryFile ( )
#    retfile.write ( f.read() )
#    retfile.seek(0)
#    h5ret = h5py.File ( retfile.name, driver='core', backing_store=False )
#    assert h5ret['ANNOIDS'].shape[0] ==5
