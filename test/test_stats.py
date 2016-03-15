# Copyright 2016 NeuroData (http://neurodata.io)
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
import time 
import random 
import json 
import os, sys
import numpy as np
import pytest
from contextlib import closing

import makeunitdb
from params import Params
from postmethods import postNPZ, getNPZ 
import kvengine_to_test
import site_to_test
SITE_HOST = site_to_test.site

from ndtype import UINT8, UINT16, UINT32, ANNOTATION, IMAGE 

from ND import celery_app 

p = Params()
p.token = 'unittest'
p.channels = ['testchannel']
p.args = (0,1024,0,1024,1,11)

class Test_Histogram8:

  def setup_class(self):
    """Create the unittest database"""
    makeunitdb.createTestDB(p.token, p.channels, channel_type=IMAGE, channel_datatype=UINT8, public=True, ximagesize=1024, yimagesize=1024, zimagesize=10, xvoxelres=1.0, yvoxelres=1.0, zvoxelres=10.0, readonly=0)

  def teardown_class (self):
    """Destroy the unittest database"""
    makeunitdb.deleteTestDB(p.token)

  def test_genhistogram (self):
    """Test generating an 8bit histogram"""

    image_data = np.random.randint(0, high=255, size=[1, 10, 1024, 1024]).astype(np.uint8)
    response = postNPZ(p, image_data)

    assert( response.code == 200 )

    voxarray = getNPZ(p)
    # check that the return data matches
    assert( np.array_equal(voxarray, image_data) )

    # generate the histogram 
    url = 'http://{}/stats/{}/{}/genhist/'.format( SITE_HOST, p.token, p.channels[0] )
    try:
      # Build a get request
      req = urllib2.Request(url)
      response = urllib2.urlopen(req)
    except urllib2.HTTPError,e:
      print e 
      assert(e.reason == 0)
    
    assert( response.code == 200 )
  
    jsonresponse = json.loads(response.read())

    # make sure the celery job started
    celerystatus = celery_app.AsyncResult(jsonresponse['jobid'])

    # wait for histogram generation to finish (either 10 mins or failure)
    # note: actual generation time should be more like 0.2 seconds, but there may be other jobs in the queue 
    count = 0
    while celerystatus.state != 'SUCCESS':
      time.sleep(1)
      celerystatus = celery_app.AsyncResult(jsonresponse['jobid'])
      assert( celerystatus.state != 'FAILURE' )
      assert( count != 60 )
      count += 1

    # now get the histogram
    url = 'http://{}/stats/{}/{}/hist/'.format( SITE_HOST, p.token, p.channels[0] )
    try: 
      # Build a get request
      req = urllib2.Request(url)
      response = urllib2.urlopen(req)
    except urllib2.HTTPError,e:
      print e 
      assert(e.reason == 0)
  
    assert( response.code == 200 )
  
    jsonresponse = json.loads(response.read())

    # now see if the two histograms are equivalent 
    testhist = np.histogram(image_data[image_data > 0], bins=256, range=(0,256))
    
    # check to see that the bins are equal
    assert( np.array_equal( jsonresponse['bins'], testhist[1] ) )

    # check to see that the counts are equal
    assert( np.array_equal( jsonresponse['hist'], testhist[0] ) )

class Test_Histogram16:

  def setup_class(self):
    """Create the unittest database"""
    makeunitdb.createTestDB(p.token, p.channels, channel_type=IMAGE, channel_datatype=UINT16, public=True, ximagesize=1024, yimagesize=1024, zimagesize=10, xvoxelres=1.0, yvoxelres=1.0, zvoxelres=10.0, readonly=0)

  def teardown_class (self):
    """Destroy the unittest database"""
    makeunitdb.deleteTestDB(p.token)

  def test_genhistogram (self):
    """Test generating an 8bit histogram"""

    image_data = np.random.randint(0, high=65535, size=[1, 10, 1024, 1024]).astype(np.uint16)
    response = postNPZ(p, image_data)

    assert( response.code == 200 )

    voxarray = getNPZ(p)
    # check that the return data matches
    assert( np.array_equal(voxarray, image_data) )

    # generate the histogram 
    url = 'http://{}/stats/{}/{}/genhist/'.format( SITE_HOST, p.token, p.channels[0] )
    try:
      # Build a get request
      req = urllib2.Request(url)
      response = urllib2.urlopen(req)
    except urllib2.HTTPError,e:
      print e 
      assert(e.reason == 0)
    
    assert( response.code == 200 )
  
    jsonresponse = json.loads(response.read())

    # make sure the celery job started
    celerystatus = celery_app.AsyncResult(jsonresponse['jobid'])

    # wait for histogram generation to finish (either 10 mins or failure)
    # note: actual generation time should be more like 1.3 seconds, but there may be other jobs in the queue 
    count = 0
    while celerystatus.state != 'SUCCESS':
      time.sleep(1)
      celerystatus = celery_app.AsyncResult(jsonresponse['jobid'])
      assert( celerystatus.state != 'FAILURE' )
      assert( count != 60 )
      count += 1

    # now get the histogram
    url = 'http://{}/stats/{}/{}/hist/'.format( SITE_HOST, p.token, p.channels[0] )
    try: 
      # Build a get request
      req = urllib2.Request(url)
      response = urllib2.urlopen(req)
    except urllib2.HTTPError,e:
      print e 
      assert(e.reason == 0)
    
    assert( response.code == 200 )
  
    jsonresponse = json.loads(response.read())

    # now see if the two histograms are equivalent 
    testhist = np.histogram(image_data[image_data > 0], bins=65536, range=(0,65536))
    
    # check to see that the bins are equal
    assert( np.array_equal( jsonresponse['bins'], testhist[1] ) )

    # check to see that the counts are equal
    assert( np.array_equal( jsonresponse['hist'], testhist[0] ) )

