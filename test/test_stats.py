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
import time
import json
import numpy as np
import pytest
import makeunitdb
from ND import celery_app 
from params import Params
from ndlib.restutil import *
from postmethods import postNPZ, getNPZ
from ndlib.ndtype import * 
from test_settings import *

p = Params()
p.token = 'unittest'
p.channels = ['testchannel']
p.args = (0,1024,0,1024,1,11)

@pytest.mark.skipif(True, reason='Test not necessary for dev mode')
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

    assert( response.status_code == 200 )

    voxarray = getNPZ(p)
    # check that the return data matches
    assert( np.array_equal(voxarray, image_data) )

    # generate the histogram
    url = 'https://{}/stats/{}/{}/genhist/'.format( SITE_HOST, p.token, p.channels[0] )
    try:
      # Build a get request
      response = getURL(url)
    except Exception as e:
      print e

    assert( response.status_code == 200 )

    jsonresponse = json.loads(response.content)

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
    url = 'https://{}/stats/{}/{}/hist/'.format( SITE_HOST, p.token, p.channels[0] )
    try:
      # Build a get request
      response = getURL(url)
    except Exception as e:
      print e

    assert( response.status_code == 200 )

    jsonresponse = json.loads(response.content)

    # now see if the two histograms are equivalent
    testhist = np.histogram(image_data[image_data > 0], bins=256, range=(0,256))

    # check to see that the bins are equal
    assert( np.array_equal( jsonresponse['bins'], testhist[1] ) )

    # check to see that the counts are equal
    assert( np.array_equal( jsonresponse['hist'], testhist[0] ) )

@pytest.mark.skipif(True, reason='Test not necessary for dev mode')
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

    assert( response.status_code == 200 )

    voxarray = getNPZ(p)
    # check that the return data matches
    assert( np.array_equal(voxarray, image_data) )

    # generate the histogram
    url = 'https://{}/stats/{}/{}/genhist/'.format( SITE_HOST, p.token, p.channels[0] )
    try:
      # Build a get request
      response = getURL(url)
    except Exception as e:
      print e

    assert( response.status_code == 200 )

    jsonresponse = json.loads(response.content)

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
    url = 'https://{}/stats/{}/{}/hist/'.format( SITE_HOST, p.token, p.channels[0] )
    try:
      # Build a get request
      response = getURL(url)
    except Exception as e:
      print e

    assert( response.status_code == 200 )

    jsonresponse = json.loads(response.content)

    # now see if the two histograms are equivalent
    testhist = np.histogram(image_data[image_data > 0], bins=65536, range=(0,65536))

    # check to see that the bins are equal
    assert( np.array_equal( jsonresponse['bins'], testhist[1] ) )

    # check to see that the counts are equal
    assert( np.array_equal( jsonresponse['hist'], testhist[0] ) )

@pytest.mark.skipif(True, reason='Test not necessary for dev mode')
class TestHistogramROI:

  def setup_class(self):
    """Create the unittest database"""
    makeunitdb.createTestDB(p.token, p.channels, channel_type=IMAGE, channel_datatype=UINT8, public=True, ximagesize=1024, yimagesize=1024, zimagesize=20, xvoxelres=1.0, yvoxelres=1.0, zvoxelres=10.0, readonly=0)

    # modify params args to match new data size
    p.args = (0,1024,0,1024,1,21)

    # post some sample image data
    self.image_data = np.random.randint(0, high=255, size=[1, 20, 1024, 1024]).astype(np.uint8)
    response = postNPZ(p, self.image_data)

    assert( response.status_code == 200 )

    voxarray = getNPZ(p)
    # check that the return data matches
    assert( np.array_equal(voxarray, self.image_data) )

  def teardown_class (self):
    """Destroy the unittest database"""
    makeunitdb.deleteTestDB(p.token)

  def test_genhistogramROI (self):
    """Test generating an 8bit histogram given an ROI"""

    # set our ROI (this one spans cuboids)
    roi = [ [500, 500, 5], [650, 650, 15] ]
    #roistr = "{}-{}".format( ",".join(str(x) for x in roi[0]), ",".join(str(x) for x in roi[1]) )

    url = 'https://{}/stats/{}/{}/genhist/'.format( SITE_HOST, p.token, p.channels[0] )

    try:
      # Make a POST request
      req = urllib2.Request(url, json.dumps({ 'ROI': [roi] }))
      response = urllib2.urlopen(req)
    except urllib2.HTTPError,e:
      print e
      assert(e.reason == 0)

    assert( response.code == 200 )

    # jsonresponse for ROI returns job info, etc in a list in 'results'
    jsonresponse = json.loads(response.read())

    # make sure the ROI was received and transcribed correctly
    assert( jsonresponse['results'][0]['roi'] == roi )

    # make sure the celery job started
    celerystatus = celery_app.AsyncResult(jsonresponse['results'][0]['jobid'])

    # wait for histogram generation to finish (either 10 mins or failure)
    # note: actual generation time should be more like 1.3 seconds, but there may be other jobs in the queue
    count = 0
    while celerystatus.state != 'SUCCESS':
      time.sleep(1)
      celerystatus = celery_app.AsyncResult(jsonresponse['results'][0]['jobid'])
      assert( celerystatus.state != 'FAILURE' )
      assert( count != 60 )
      count += 1

    # make sure the ROI exists
    url = 'https://{}/stats/{}/{}/hist/roi/'.format( SITE_HOST, p.token, p.channels[0] )
    try:
      # Build a get request
      req = urllib2.Request(url)
      response = urllib2.urlopen(req)
    except urllib2.HTTPError,e:
      print e
      assert(e.reason == 0)

    jsonresponse = json.loads(response.read())

    roifound = False
    for roiresp in jsonresponse:
      if roiresp == roi:
        roifound = True

    assert( roifound == True )

    # now grab the generated histogram using a get request
    roistr = "{}-{}".format( ",".join(str(x) for x in roi[0]), ",".join(str(x) for x in roi[1]) )
    url = 'https://{}/stats/{}/{}/hist/roi/{}/'.format( SITE_HOST, p.token, p.channels[0], roistr )
    try:
      req = urllib2.Request(url)
      response = urllib2.urlopen(req)
    except urllib2.HTTPError, e:
      print e
      assert(e.reason == 0)

    jsonresponse = json.loads(response.read())

    # now see if the two histograms are equivalents
    image_data_roi = self.image_data[0, roi[0][2]:roi[1][2], roi[0][1]:roi[1][1], roi[0][0]:roi[1][0]]

    testhist = np.histogram(image_data_roi[image_data_roi > 0], bins=256, range=(0,256))

    # check to see that the bins are equal
    assert( np.array_equal( jsonresponse['bins'], testhist[1] ) )

    # check to see that the counts are equal
    assert( np.array_equal( jsonresponse['hist'], testhist[0] ) )

  def test_genhistogramROICuboid (self):
    """ Test generating an 8bit histogram using an ROI inside a single cuboid """

    roi = [ [0, 0, 1], [10, 10, 6] ]

    url = 'https://{}/stats/{}/{}/genhist/'.format( SITE_HOST, p.token, p.channels[0] )

    try:
      # Make a POST request
      req = urllib2.Request(url, json.dumps({ 'ROI': [roi] }))
      response = urllib2.urlopen(req)
    except urllib2.HTTPError,e:
      print e
      assert(e.reason == 0)

    assert( response.code == 200 )

    # jsonresponse for ROI returns job info, etc in a list in 'results'
    jsonresponse = json.loads(response.read())

    # make sure the ROI was received and transcribed correctly
    assert( jsonresponse['results'][0]['roi'] == roi )

    # make sure the celery job started
    celerystatus = celery_app.AsyncResult(jsonresponse['results'][0]['jobid'])

    # wait for histogram generation to finish (either 10 mins or failure)
    # note: actual generation time should be more like 1.3 seconds, but there may be other jobs in the queue
    count = 0
    while celerystatus.state != 'SUCCESS':
      time.sleep(1)
      celerystatus = celery_app.AsyncResult(jsonresponse['results'][0]['jobid'])
      assert( celerystatus.state != 'FAILURE' )
      assert( count != 60 )
      count += 1

    # now grab the generated histogram using a get request
    roistr = "{}-{}".format( ",".join(str(x) for x in roi[0]), ",".join(str(x) for x in roi[1]) )
    url = 'https://{}/stats/{}/{}/hist/roi/{}/'.format( SITE_HOST, p.token, p.channels[0], roistr )
    try:
      req = urllib2.Request(url)
      response = urllib2.urlopen(req)
    except urllib2.HTTPError, e:
      print e
      assert(e.reason == 0)

    jsonresponse = json.loads(response.read())

    # now see if the two histograms are equivalents
    image_data_roi = self.image_data[0, roi[0][2]:roi[1][2], roi[0][1]:roi[1][1], roi[0][0]:roi[1][0]]

    testhist = np.histogram(image_data_roi[image_data_roi > 0], bins=256, range=(0,256))

    # check to see that the bins are equal
    assert( np.array_equal( jsonresponse['bins'], testhist[1] ) )

    # check to see that the counts are equal
    assert( np.array_equal( jsonresponse['hist'], testhist[0] ) )

  def test_genhistogramROICuboidEnd (self):
    """ Test generating an 8bit histogram using an ROI inside a single cuboid at the end of the dataset """

    roi = [ [1000, 1000, 18], [1024, 1024, 21] ]

    url = 'https://{}/stats/{}/{}/genhist/'.format( SITE_HOST, p.token, p.channels[0] )

    try:
      # Make a POST request
      req = urllib2.Request(url, json.dumps({ 'ROI': [roi] }))
      response = urllib2.urlopen(req)
    except urllib2.HTTPError,e:
      print e
      assert(e.reason == 0)

    assert( response.code == 200 )

    # jsonresponse for ROI returns job info, etc in a list in 'results'
    jsonresponse = json.loads(response.read())

    # make sure the ROI was received and transcribed correctly
    assert( jsonresponse['results'][0]['roi'] == roi )

    # make sure the celery job started
    celerystatus = celery_app.AsyncResult(jsonresponse['results'][0]['jobid'])

    # wait for histogram generation to finish (either 10 mins or failure)
    # note: actual generation time should be more like 1.3 seconds, but there may be other jobs in the queue
    count = 0
    while celerystatus.state != 'SUCCESS':
      time.sleep(1)
      celerystatus = celery_app.AsyncResult(jsonresponse['results'][0]['jobid'])
      assert( celerystatus.state != 'FAILURE' )
      assert( count != 60 )
      count += 1

    # now grab the generated histogram using a get request
    roistr = "{}-{}".format( ",".join(str(x) for x in roi[0]), ",".join(str(x) for x in roi[1]) )
    url = 'https://{}/stats/{}/{}/hist/roi/{}/'.format( SITE_HOST, p.token, p.channels[0], roistr )
    try:
      req = urllib2.Request(url)
      response = urllib2.urlopen(req)
    except urllib2.HTTPError, e:
      print e
      assert(e.reason == 0)

    jsonresponse = json.loads(response.read())

    # now see if the two histograms are equivalents
    image_data_roi = self.image_data[0, roi[0][2]:roi[1][2], roi[0][1]:roi[1][1], roi[0][0]:roi[1][0]]

    testhist = np.histogram(image_data_roi[image_data_roi > 0], bins=256, range=(0,256))

    # check to see that the bins are equal
    assert( np.array_equal( jsonresponse['bins'], testhist[1] ) )

    # check to see that the counts are equal
    assert( np.array_equal( jsonresponse['hist'], testhist[0] ) )

  def test_genhistogramROIError(self):
    """ Test error checking in the ROI histogram service """

    # post ROI that isn't complete
    roi = [ 50, 100, 100]
    url = 'https://{}/stats/{}/{}/genhist/'.format( SITE_HOST, p.token, p.channels[0] )

    try:
      # Make a POST request
      req = urllib2.Request(url, json.dumps({ 'ROI': [roi] }))
      response = urllib2.urlopen(req)
      assert( response.code != 200 )
    except urllib2.HTTPError,e:
      print e
      assert(e.code == 400)

    # post ROI that isn't a cube
    roi = [ [50, 50, 18], [10, 10, 5] ]

    url = 'https://{}/stats/{}/{}/genhist/'.format( SITE_HOST, p.token, p.channels[0] )

    try:
      # Make a POST request
      req = urllib2.Request(url, json.dumps({ 'ROI': [roi] }))
      response = urllib2.urlopen(req)
      assert( response.code != 200 )
    except urllib2.HTTPError,e:
      print e
      assert(e.code == 400)

    # post ROI outside of dataset bounds
    roi = [ [0, 0, 1], [2000, 2000, 50] ]

    url = 'https://{}/stats/{}/{}/genhist/'.format( SITE_HOST, p.token, p.channels[0] )

    try:
      # Make a POST request
      req = urllib2.Request(url, json.dumps({ 'ROI': [roi] }))
      response = urllib2.urlopen(req)
      assert( response.code != 200 )
    except urllib2.HTTPError,e:
      print e
      assert(e.code == 400)

@pytest.mark.skipif(True, reason='Test not necessary for dev mode')
class TestHistogramROIMultiple:

  def setup_class(self):
    """Create the unittest database"""
    makeunitdb.createTestDB(p.token, p.channels, channel_type=IMAGE, channel_datatype=UINT8, public=True, ximagesize=1024, yimagesize=1024, zimagesize=20, xvoxelres=1.0, yvoxelres=1.0, zvoxelres=10.0, readonly=0)

    # modify params args to match new data size
    p.args = (0,1024,0,1024,1,21)

    # post some sample image data
    self.image_data = np.random.randint(0, high=255, size=[1, 20, 1024, 1024]).astype(np.uint8)
    response = postNPZ(p, self.image_data)

    assert( response.code == 200 )

    voxarray = getNPZ(p)
    # check that the return data matches
    assert( np.array_equal(voxarray, self.image_data) )

  def teardown_class (self):
    """Destroy the unittest database"""
    makeunitdb.deleteTestDB(p.token)

  def test_genhistogramROIMultiple (self):
    """Test generating an 8bit histogram given multiple ROIs"""

    # set our ROIs (this one spans cuboids)
    rois = [
      [ [100, 100, 5], [450, 450, 15] ],
      [ [500, 500, 5], [650, 650, 15] ],
      [ [100, 100, 15], [350, 350, 20] ],
    ]

    url = 'https://{}/stats/{}/{}/genhist/'.format( SITE_HOST, p.token, p.channels[0] )

    try:
      # Make a POST request
      req = urllib2.Request(url, json.dumps({ 'ROI': rois }))
      response = urllib2.urlopen(req)
    except urllib2.HTTPError,e:
      print e
      assert(e.reason == 0)

    assert( response.code == 200 )

    # jsonresponse for ROI returns job info, etc in a list in 'results'
    jsonresponse = json.loads(response.read())

    # loop over returned ROIs
    for result in jsonresponse['results']:
      roi = result['roi']

      # make sure the celery job started
      celerystatus = celery_app.AsyncResult(result['jobid'])

      # wait for histogram generation to finish (either 10 mins or failure)
      # note: actual generation time should be more like 1.3 seconds, but there may be other jobs in the queue
      count = 0
      while celerystatus.state != 'SUCCESS':
        time.sleep(1)
        celerystatus = celery_app.AsyncResult(result['jobid'])
        assert( celerystatus.state != 'FAILURE' )
        assert( count != 60 )
        count += 1

      # grab the generated histogram using a get request
      roistr = "{}-{}".format( ",".join(str(x) for x in roi[0]), ",".join(str(x) for x in roi[1]) )
      url = 'https://{}/stats/{}/{}/hist/roi/{}/'.format( SITE_HOST, p.token, p.channels[0], roistr )
      try:
        req = urllib2.Request(url)
        response = urllib2.urlopen(req)
      except urllib2.HTTPError, e:
        print e
        assert(e.reason == 0)

      jsonresponse = json.loads(response.read())

      # now see if the two histograms are equivalents
      image_data_roi = self.image_data[0, roi[0][2]:roi[1][2], roi[0][1]:roi[1][1], roi[0][0]:roi[1][0]]

      testhist = np.histogram(image_data_roi[image_data_roi > 0], bins=256, range=(0,256))

      # check to see that the bins are equal
      assert( np.array_equal( jsonresponse['bins'], testhist[1] ) )

      # check to see that the counts are equal
      assert( np.array_equal( jsonresponse['hist'], testhist[0] ) )
