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

import pytest
import cStringIO
import tempfile
import h5py
import random
import string
import makeunitdb
from params import Params
from ramonmethods import H5AnnotationFile, setField, getField, queryField, makeAnno
from test_settings import *

p = Params()
p.token = 'unittest'
p.channels = ['unit_anno']

@pytest.mark.skipif(KV_ENGINE == REDIS, reason='Annotation not supported in Redis')
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
      makeAnno( p, p.anntype)

      # set some fields in the even annotations
      if i % 2 == 0:
        setField(p, 'status', status)

        # set the confidence
        setField(p, 'confidence', confidence)

        # set the type
        setField(p, 'synapse_type', synapse_type)

      # set some fields in the odd annotations
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


  def test_query_kvpairs ( self ):
    """validate that one can query arbitray kvpairs for equality only"""

    # do a general kv test for each annotation type
    for i in range(1,10):

      key = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(random.randint(1,128)))
      value = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(random.randint(1,1024)))

      annids = []

      makeAnno (p, i)
      setField( p, key, value )
      annids.append(p.annoid)

      makeAnno (p, i)
      setField( p, key, value )
      annids.append(p.annoid)
      h5 = queryField ( p, key, value )

      assert ( h5['ANNOIDS'].shape[0] == 2 )
