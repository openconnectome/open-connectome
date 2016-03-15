# Copyright 2015 NeuroData (http://neurodata.io)
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

import os
import sys
import json
import tempfile
import pytest
import numpy as np
import random
import h5py

sys.path += [os.path.abspath('../django')]
import ND.settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'ND.settings'

from params import Params
from postmethods import getURL, postURL, putAnnotation
import makeunitdb
import site_to_test

SITE_HOST = site_to_test.site

p = Params()
p.token = 'unittest'
p.resolution = 0
p.channels = ['unit_anno']

class Test_Annotation_Json():

  def setup_class(self):
    """Setup Parameters"""
    makeunitdb.createTestDB(p.token, readonly=0)

  def teardown_class(self):
    """Teardown Parameters"""
    makeunitdb.deleteTestDB(p.token)
  
  def test_basic_json(self):
    """Test the annotation (RAMON) JSON interface"""
    
    # create hdf5 file and post it
    tmpfile = tempfile.NamedTemporaryFile()
    h5fh = h5py.File( tmpfile.name )

    ann_status = random.randint(0,4)
    ann_confidence = random.random()
    ann_author = 'unittest_author' 
    ann_annoid = 1
    
    # create annotation id namespace
    idgrp = h5fh.create_group ( str(ann_annoid) )

    # annotation type
    idgrp.create_dataset ( "ANNOTATION_TYPE", (1,), np.uint32, data=1 )
    mdgrp = idgrp.create_group( "METADATA" )

    # set annotation metadata
    mdgrp.create_dataset ( "STATUS", (1,), np.uint32, data=ann_status )
    mdgrp.create_dataset ( "CONFIDENCE", (1,), np.float, data=ann_confidence )
    mdgrp.create_dataset ( "AUTHOR", (1,), dtype=h5py.special_dtype(vlen=str), data=ann_author )

    h5fh.flush()
    tmpfile.seek(0)

    p.annoid = putAnnotation(p, tmpfile)
    
    # fetching the JSON info
    f = getURL("http://{}/sd/{}/{}/{}/json/".format(SITE_HOST, p.token, p.channels[0], ann_annoid))

    # read the JSON file
    ann_info = json.loads(f.read())
    assert( ann_info.keys()[0] == str(ann_annoid) )
    assert( str(ann_info[str(ann_annoid)]['ann_status']) == str(ann_status) )
    assert( str(ann_info[str(ann_annoid)]['ann_confidence'])[:5] == str(ann_confidence)[:5] )
    assert( ann_info[str(ann_annoid)]['ann_author'] == str(ann_author) )
  
  def test_bigint_json(self):
    """Test the annotation (RAMON) JSON interface with a large ID"""
    
    # create hdf5 file and post it
    tmpfile = tempfile.NamedTemporaryFile()
    h5fh = h5py.File( tmpfile.name )

    ann_status = random.randint(0,4)
    ann_confidence = random.random()
    ann_author = 'unittest_author' 
    ann_annoid = 10025
    
    # create annotation id namespace
    idgrp = h5fh.create_group ( str(ann_annoid) )

    # annotation type
    idgrp.create_dataset ( "ANNOTATION_TYPE", (1,), np.uint32, data=1 )
    mdgrp = idgrp.create_group( "METADATA" )

    # set annotation metadata
    mdgrp.create_dataset ( "STATUS", (1,), np.uint32, data=ann_status )
    mdgrp.create_dataset ( "CONFIDENCE", (1,), np.float, data=ann_confidence )
    mdgrp.create_dataset ( "AUTHOR", (1,), dtype=h5py.special_dtype(vlen=str), data=ann_author )

    h5fh.flush()
    tmpfile.seek(0)

    p.annoid = putAnnotation(p, tmpfile)
    
    # fetching the JSON info
    f = getURL("http://{}/ca/{}/{}/{}/json/".format(SITE_HOST, p.token, p.channels[0], ann_annoid))

    # read the JSON file
    ann_info = json.loads(f.read())
    assert( ann_info.keys()[0] == str(ann_annoid) )
    assert( str(ann_info[str(ann_annoid)]['ann_status']) == str(ann_status) )
    assert( str(ann_info[str(ann_annoid)]['ann_confidence'])[:5] == str(ann_confidence)[:5] )
    assert( ann_info[str(ann_annoid)]['ann_author'] == str(ann_author) )

  def test_multiple_json(self):
    """Test the annotation (RAMON) JSON interface with multiple objects"""
    number_of_annotations = 3 # Note: these are 1-indexed 
    anno_objs = {}

    for i in range(number_of_annotations):
      # create hdf5 file and post it
      tmpfile = tempfile.NamedTemporaryFile()
      h5fh = h5py.File( tmpfile.name )

      ann_status = random.randint(0,4)
      ann_confidence = random.random()
      ann_author = 'unittest_author' 
      ann_annoid = (i + 1)*10 # we multiply by 10 to avoid conflicts with above test
    
      anno_objs[ str(ann_annoid) ] = {
        'ann_status': ann_status,
        'ann_confidence': ann_confidence,
        'ann_author': ann_author
      }

      # create annotation id namespace
      idgrp = h5fh.create_group ( str(ann_annoid) )

      # annotation type
      idgrp.create_dataset ( "ANNOTATION_TYPE", (1,), np.uint32, data=1 )
      mdgrp = idgrp.create_group( "METADATA" )

      # set annotation metadata
      mdgrp.create_dataset ( "STATUS", (1,), np.uint32, data=ann_status )
      mdgrp.create_dataset ( "CONFIDENCE", (1,), np.float, data=ann_confidence )
      mdgrp.create_dataset ( "AUTHOR", (1,), dtype=h5py.special_dtype(vlen=str), data=ann_author )

      h5fh.flush()
      tmpfile.seek(0)

      p.annoid = putAnnotation(p, tmpfile)
    
    # fetching the JSON info
    ann_id_str = ''
    for i in range(number_of_annotations):
      ann_id_str += '{}'.format( (i + 1)*10 )
      if i < number_of_annotations - 1:
        ann_id_str += ','
    
    f = getURL("http://{}/ca/{}/{}/{}/json/".format(SITE_HOST, p.token, p.channels[0], ann_id_str))

    # read the JSON file
    ann_info = json.loads(f.read())
    
    for i in range(number_of_annotations):
      # make sure we have all the relevant annotation objects
      assert( str( (i + 1)*10 ) in ann_info.keys() )
      chosen_id = (i + 1)*10
      chosen_obj = anno_objs[str( chosen_id )]
      
      assert( str(ann_info[str(chosen_id)]['ann_status']) == str(chosen_obj['ann_status']) )
      assert( str(ann_info[str(chosen_id)]['ann_confidence'])[:5] == str(chosen_obj['ann_confidence'])[:5] )
      assert( ann_info[str(chosen_id)]['ann_author'] == str(chosen_obj['ann_author']) )
      
    # pick an annotation object at random and check its properties 
    chosen_id = random.randint(1,number_of_annotations)*10 
    chosen_obj = anno_objs[str(chosen_id)]
      
    assert( str(ann_info[str(chosen_id)]['ann_status']) == str(chosen_obj['ann_status']) )
    assert( str(ann_info[str(chosen_id)]['ann_confidence'])[:5] == str(chosen_obj['ann_confidence'])[:5] )
    assert( ann_info[str(chosen_id)]['ann_author'] == str(chosen_obj['ann_author']) )
      
    
    
  def test_error_json(self):
    """ Request an annotation Id that doesn't exist """

    ann_annoid = str(13);
    # fetching the JSON info
    f = getURL("http://{}/sd/{}/{}/{}/json/".format(SITE_HOST, p.token, p.channels, ann_annoid))
    
    assert(f == 404)


