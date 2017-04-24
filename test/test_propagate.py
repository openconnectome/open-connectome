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

"""  Unit tests that require the ND stack to be available.
     All tests in other units should use Web services only.
"""

import sys
import os
import random
import csv
import time
import pytest
import numpy as np
from PIL import Image
from StringIO import StringIO
sys.path += [os.path.abspath('../django')]
os.environ['DJANGO_SETTINGS_MODULE'] = 'ND.settings'
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
from postmethods import getURL, postNPZ, getNPZ
from ndlib.ndtype import *
from ndlib.ndctypelib import *
from params import Params
import makeunitdb
from test_settings import *

# Test_Propagate
#
# 1 - test_image_zslice_propagate - Test the propagate service for ZSlice image data
# 2 - test_image_isotropic_propagate - Test the propagate service for Isotropic image data
# 3 - test_anno_zsclice_propagate - Test the propagate service for Annotation Zslice data
# 4 - test_anno_isotropic_propagate - TEst the propagate service for Annotation Isotropic data

p = Params()
p.channels = ['chan1']

@pytest.mark.skipif(DEV_MODE, reason='Test not necessary for dev mode')
class Test_Image_Zslice_Propagate:
  """Test image propagation"""

  def setup_class(self):
    """Create the unittest database"""
    makeunitdb.createTestDB(p.token, public=True, channel_list=p.channels, channel_type=p.channel_type, channel_datatype=p.datatype, ximagesize=1000, yimagesize=1000, zimagesize=100)

  def teardown_class (self):
    """Destroy the unittest database"""
    makeunitdb.deleteTestDB(p.token)

  def test_web_propagate(self):
    """Test the web update propogate function"""

    # Posting some data at res0 to propagate
    p.args = (200, 300, 200, 300, 4, 5, 6, 7)
    image_data = np.ones( [1, 1, 1,100,100], dtype=np.uint8) * random.randint(0,255)
    if KV_ENGINE == REDIS:
      response = postNPZ(p, image_data, time=True, direct=True)
    else:
      response = postNPZ(p, image_data, time=True)

    # Check if the project is not proagated
    f = getURL("https://{}/sd/{}/{}/getPropagate/".format(SITE_HOST, p.token, ','.join(p.channels)))
    value = int(f.content)
    assert(value == NOT_PROPAGATED)

    # Start propagating
    f = getURL("https://{}/sd/{}/{}/setPropagate/{}/".format(SITE_HOST, p.token, ','.join(p.channels), UNDER_PROPAGATION))
    for iter_value in range(1, 500, 1):
      time.sleep(1)
      # Checking if the PROPGATED value is set correctly
      f = getURL("https://{}/sd/{}/{}/getPropagate/".format(SITE_HOST, p.token, ','.join(p.channels)))
      value = int(f.content)
      if value == PROPAGATED:
        break
    assert(value == PROPAGATED)

    # Checking at res1
    p.args = (100, 150, 100, 150, 4, 5, 6, 7)
    url = "https://{}/sd/{}/{}/xy/{}/{},{}/{},{}/{}/{}/".format(SITE_HOST, p.token, p.channels[0], p.resolution+1, p.args[0], p.args[1], p.args[2], p.args[3], p.args[4], p.args[6])
    f = getURL(url)
    slice_data = np.asarray ( Image.open(StringIO(f.content)) )
    assert ( np.array_equal(slice_data, image_data[0][0][0][:50,:50]) )

    # Checking at res5
    p.args = (7, 9, 7, 9, 4, 5, 6, 7)
    url = "https://{}/sd/{}/{}/xy/{}/{},{}/{},{}/{}/{}/".format(SITE_HOST, p.token, p.channels[0], p.resolution+5, p.args[0], p.args[1], p.args[2], p.args[3], p.args[4], p.args[6])
    f = getURL(url)
    slice_data = np.asarray ( Image.open(StringIO(f.content)) )
    assert ( np.array_equal(slice_data, image_data[0][0][0][:2,:2]) )
    
    # checking at res5 for neariso data
    # extract data from res4 slice 4
    p.args = (14, 18, 14, 18, 4, 5, 6, 7)
    url = "https://{}/sd/{}/{}/xy/{}/{},{}/{},{}/{}/{}/".format(SITE_HOST, p.token, p.channels[0], p.resolution+4, p.args[0], p.args[1], p.args[2], p.args[3], p.args[4], p.args[6])
    f = getURL(url)
    slice_data_1 = np.asarray ( Image.open(StringIO(f.content)) )
    # extract data from res4 slice 5
    url = "https://{}/sd/{}/{}/xy/{}/{},{}/{},{}/{}/{}/".format(SITE_HOST, p.token, p.channels[0], p.resolution+4, p.args[0], p.args[1], p.args[2], p.args[3], p.args[4]+1, p.args[6])
    f = getURL(url)
    slice_data_2 = np.asarray ( Image.open(StringIO(f.content)) )
    # generate isotropic slice from this
    new_slicedata = isotropicBuild_ctype(slice_data_1, slice_data_2)
    p.args = (7, 9, 7, 9, 2, 3, 6, 7)
    data = getNPZ(p, neariso=True)
    url = "https://{}/sd/{}/{}/xy/{}/{},{}/{},{}/{}/{}/neariso/".format(SITE_HOST, p.token, p.channels[0], p.resolution+5, p.args[0], p.args[1], p.args[2], p.args[3], p.args[4], p.args[6])
    f = getURL(url)
    slice_data = np.asarray ( Image.open(StringIO(f.content)) )
    assert ( np.array_equal(slice_data, new_slicedata[:2,:2]) )


@pytest.mark.skipif(DEV_MODE, reason='Test not necessary for dev mode')
class Test_Image_Zslice_Base_Resolution_Propagate:
  """Test image propagation"""

  def setup_class(self):
    """Create the unittest database"""
    # testing the propagation by setting the channel base resolution as 1
    makeunitdb.createTestDB(p.token, public=True, channel_list=p.channels, channel_type=p.channel_type, channel_datatype=p.datatype, ximagesize=1000, yimagesize=1000, zimagesize=100, base_resolution=1)

  def teardown_class (self):
    """Destroy the unittest database"""
    makeunitdb.deleteTestDB(p.token)

  def test_web_propagate(self):
    """Test the web update propogate function"""
    
    p.resolution = 1
    # Posting some data at res1 to propagate
    p.args = (100, 150, 100, 150, 4, 5, 6, 7)
    image_data = np.ones( [1, 1, 1, 50, 50], dtype=np.uint8) * random.randint(0,255)
    if KV_ENGINE == REDIS:
      response = postNPZ(p, image_data, time=True, direct=True)
    else:
      response = postNPZ(p, image_data, time=True)

    # Check if the project is not proagated
    f = getURL("https://{}/sd/{}/{}/getPropagate/".format(SITE_HOST, p.token, ','.join(p.channels)))
    value = int(f.content)
    assert(value == NOT_PROPAGATED)

    # Start propagating
    f = getURL("https://{}/sd/{}/{}/setPropagate/{}/".format(SITE_HOST, p.token, ','.join(p.channels), UNDER_PROPAGATION))
    for iter_value in range(1, 500, 1):
      time.sleep(1)
      # Checking if the PROPGATED value is set correctly
      f = getURL("https://{}/sd/{}/{}/getPropagate/".format(SITE_HOST, p.token, ','.join(p.channels)))
      value = int(f.content)
      if value == PROPAGATED:
        break
    assert(value == PROPAGATED)

    # Checking at res1
    # p.args = (100, 150, 100, 150, 4, 5, 6, 7)
    # url = "https://{}/sd/{}/{}/xy/{}/{},{}/{},{}/{}/{}/".format(SITE_HOST, p.token, p.channels[0], p.resolution+1, p.args[0], p.args[1], p.args[2], p.args[3], p.args[4], p.args[6])
    # f = getURL(url)
    # slice_data = np.asarray ( Image.open(StringIO(f.content)) )
    # assert ( np.array_equal(slice_data, image_data[0][0][0][:50,:50]) )
    
    # Checking at res5
    p.args = (7, 9, 7, 9, 4, 5, 6, 7)
    url = "https://{}/sd/{}/{}/xy/{}/{},{}/{},{}/{}/{}/".format(SITE_HOST, p.token, p.channels[0], p.resolution+4, p.args[0], p.args[1], p.args[2], p.args[3], p.args[4], p.args[6])
    f = getURL(url)
    slice_data = np.asarray ( Image.open(StringIO(f.content)) )
    assert ( np.array_equal(slice_data, image_data[0][0][0][:2,:2]) )
    
    # checking at res5 for neariso data
    # extract data from res4 slice 4
    p.args = (14, 18, 14, 18, 4, 5, 6, 7)
    url = "https://{}/sd/{}/{}/xy/{}/{},{}/{},{}/{}/{}/".format(SITE_HOST, p.token, p.channels[0], p.resolution+3, p.args[0], p.args[1], p.args[2], p.args[3], p.args[4], p.args[6])
    f = getURL(url)
    slice_data_1 = np.asarray ( Image.open(StringIO(f.content)) )
    # extract data from res4 slice 5
    url = "https://{}/sd/{}/{}/xy/{}/{},{}/{},{}/{}/{}/".format(SITE_HOST, p.token, p.channels[0], p.resolution+3, p.args[0], p.args[1], p.args[2], p.args[3], p.args[4]+1, p.args[6])
    f = getURL(url)
    slice_data_2 = np.asarray ( Image.open(StringIO(f.content)) )
    # generate isotropic slice from this
    new_slicedata = isotropicBuild_ctype(slice_data_1, slice_data_2)
    p.args = (7, 9, 7, 9, 2, 3, 6, 7)
    data = getNPZ(p, neariso=True)
    url = "https://{}/sd/{}/{}/xy/{}/{},{}/{},{}/{}/{}/neariso/".format(SITE_HOST, p.token, p.channels[0], p.resolution+4, p.args[0], p.args[1], p.args[2], p.args[3], p.args[4], p.args[6])
    f = getURL(url)
    slice_data = np.asarray ( Image.open(StringIO(f.content)) )
    assert ( np.array_equal(slice_data, new_slicedata[:2,:2]) )

@pytest.mark.skipif(DEV_MODE, reason='Test not necessary for dev mode')
class Test_Image_Readonly_Propagate:
  """Test image propagation"""

  def setup_class(self):
    """Create the unittest database"""
    makeunitdb.createTestDB(p.token, public=True, channel_list=p.channels, channel_type=p.channel_type, channel_datatype=p.datatype, ximagesize=1000, yimagesize=1000, zimagesize=10, readonly=READONLY_TRUE)

  def teardown_class (self):
    """Destroy the unittest database"""
    makeunitdb.deleteTestDB(p.token)

  def test_web_propagate(self):
    """Test the web update propogate function"""
    
    p.resolution = 0
    # Posting some data at res0 to propagate
    p.args = (200,300,200,300,4,5)
    image_data = np.ones( [1,1,100,100], dtype=np.uint8) * random.randint(0,255)
    response = postNPZ(p, image_data)
    # check that it cannot post to a readonly channle
    assert(response.status_code == 404)

    # Check if the project is not proagated
    f = getURL("https://{}/sd/{}/{}/getPropagate/".format(SITE_HOST, p.token, ','.join(p.channels)))
    value = int(f.content)
    assert(value == NOT_PROPAGATED)

    # check that it cannot start propagating a readonly channel
    assert (getURL("https://{}/sd/{}/{}/setPropagate/{}/".format(SITE_HOST, p.token, ','.join(p.channels), UNDER_PROPAGATION)).status_code == 404 )
    # check that it cannot mark a channel as propagated
    assert (getURL("https://{}/sd/{}/{}/setPropagate/{}/".format(SITE_HOST, p.token, ','.join(p.channels), PROPAGATED)).status_code == 404 )

@pytest.mark.skipif(DEV_MODE, reason='Test not necessary for dev mode')
class Test_Image_Propagated_Propagate:
  """Test image propagation"""

  def setup_class(self):
    """Create the unittest database"""
    makeunitdb.createTestDB(p.token, public=True, channel_list=p.channels, channel_type=p.channel_type, channel_datatype=p.datatype, ximagesize=1000, yimagesize=1000, zimagesize=10, readonly=READONLY_FALSE ,propagate=PROPAGATED)

  def teardown_class (self):
    """Destroy the unittest database"""
    makeunitdb.deleteTestDB(p.token)

  def test_web_propagate(self):
    """Test the web update propogate function"""

    # Posting some data at res0 to propagate
    p.args = (200,300,200,300,4,5)
    image_data = np.ones( [1,1,100,100], dtype=np.uint8) * random.randint(0,255)
    response = postNPZ(p, image_data)

    # Check if the project is not proagated
    f = getURL("https://{}/sd/{}/{}/getPropagate/".format(SITE_HOST, p.token, ','.join(p.channels)))
    value = int(f.content)
    assert(value == PROPAGATED)

    # check that it cannot start propagating a channel which is already propagated
    assert (getURL("https://{}/sd/{}/{}/setPropagate/{}/".format(SITE_HOST, p.token, ','.join(p.channels), UNDER_PROPAGATION)).status_code == 404 )
    f = getURL("https://{}/sd/{}/{}/setPropagate/{}/".format(SITE_HOST, p.token, ','.join(p.channels), NOT_PROPAGATED))
    # can set to not propagated
    f = getURL("https://{}/sd/{}/{}/getPropagate/".format(SITE_HOST, p.token, ','.join(p.channels)))
    value = int(f.content)
    assert(value == NOT_PROPAGATED)

@pytest.mark.skipif(DEV_MODE, reason='Test not necessary for dev mode')
class Test_Image_Isotropic_Propagate:
  """Test image propagation"""

  def setup_class(self):
    """Create the unittest database"""
    makeunitdb.createTestDB(p.token, public=True, channel_list=p.channels, channel_type=p.channel_type, channel_datatype=p.datatype, ximagesize=1000, yimagesize=1000, zimagesize=128, scalingoption=ISOTROPIC)

  def teardown_class (self):
    """Destroy the unittest database"""
    makeunitdb.deleteTestDB(p.token)

  def test_web_propagate(self):
    """Test the web update propogate function"""
    
    # Posting some data at res0 to propagate
    p.args = (200, 300, 200, 300, 32, 64, 9, 10)
    image_data = np.ones( [1, 1, 32, 100, 100], dtype=np.uint8) * random.randint(0,255)
    if KV_ENGINE == REDIS:
      response = postNPZ(p, image_data, time=True, direct=True)
    else:
      response = postNPZ(p, image_data, time=True)

    # Check if the project is not proagated
    f = getURL("https://{}/sd/{}/{}/getPropagate/".format(SITE_HOST, p.token, ','.join(p.channels)))
    value = int(f.content)
    assert(value == NOT_PROPAGATED)

    # Start propagating
    f = getURL("https://{}/sd/{}/{}/setPropagate/{}/".format(SITE_HOST, p.token, ','.join(p.channels), UNDER_PROPAGATION))

    # Checking if the PROPGATED value is set correctly
    for iter_value in range(1,500,1):
      time.sleep(1)
      f = getURL("https://{}/sd/{}/{}/getPropagate/".format(SITE_HOST, p.token, ','.join(p.channels)))
      value = int(f.content)
      if value == PROPAGATED:
        break
    assert(value == PROPAGATED)
    
    # Checking at res1
    p.args = (100, 150, 100, 150, 16, 32, 9, 10)
    p.resolution = 1
    voxarray = getNPZ(p, time=True)
    assert ( np.array_equal(voxarray[0][0][0], image_data[0][0][0][:50,:50]) )

    # Checking at res2
    p.args = (50, 75, 50, 75, 8, 16, 9, 10)
    p.resolution = 2
    voxarray = getNPZ(p, time=True)
    assert ( np.array_equal(voxarray[0][0][0], image_data[0][0][0][:25,:25]) )

    # Checking at res3
    p.args = (25, 37, 25, 37, 4, 8, 9, 10)
    p.resolution = 3
    voxarray = getNPZ(p, time=True)
    assert ( np.array_equal(voxarray[0][0][0], image_data[0][0][0][:12,:12]) )

    # Checking at res4
    # KL TODO Recheck this
    # p.args = (13,19,13,19,2,4)
    # p.resolution = 4
    # voxarray = getNPZ(p)
    # assert ( np.array_equal(voxarray[0][0], image_data[0][0][:6,:6]) )

@pytest.mark.skipif(DEV_MODE or KV_ENGINE == REDIS, reason='Test not necessary for dev mode')
class Test_Anno_Zslice_Propagate():
  """Test annotation propagation"""

  def setup_class(self):
    """Create the unittest database"""
    makeunitdb.createTestDB(p.token, public=True, channel_list=p.channels, ximagesize=1000, yimagesize=1000, zimagesize=16)

  def teardown_class (self):
    """Destroy the unittest database"""
    makeunitdb.deleteTestDB(p.token)

  def test_web_propagate(self):
    """Test the web update propogate function"""

    # Posting some data at res0 to propagate
    p.args = (200,300,200,300,4,5)
    p.resolution = 0
    image_data = np.ones( [1,1,100,100], dtype=np.uint32) * random.randint(255,65535)
    response = postNPZ(p, image_data)

    voxarray = getNPZ(p)
    # check that the return matches
    assert ( np.array_equal(voxarray,image_data) )

    # Check if the project is not propagated
    f = getURL("https://{}/sd/{}/{}/getPropagate/".format(SITE_HOST, p.token, ','.join(p.channels)))
    value = int(f.content)
    assert(value == NOT_PROPAGATED)

    # Start propagating
    f = getURL("https://{}/sd/{}/{}/setPropagate/{}/".format(SITE_HOST, p.token, ','.join(p.channels), UNDER_PROPAGATION))

    # Checking if the PROPGATED value is set correctly
    for iter_value in range(1, 500, 1):
      time.sleep(1)
      f = getURL("https://{}/sd/{}/{}/getPropagate/".format(SITE_HOST, p.token, ','.join(p.channels)))
      value = int(f.content)
      if value == PROPAGATED:
        break
    assert(value == PROPAGATED)

    # Checking at res1
    p.args = (100,150,100,150,4,5)
    p.resolution = 1
    voxarray = getNPZ(p)
    assert ( np.array_equal(voxarray[0][0], image_data[0][0][:50,:50]) )

    # Checking at res5
    p.args = (7,9,7,9,4,5)
    p.resolution = 5
    voxarray = getNPZ(p)
    assert ( np.array_equal(voxarray[0][0], image_data[0][0][:2,:2]) )

@pytest.mark.skipif(DEV_MODE or KV_ENGINE == REDIS, reason='Test not necessary for dev mode')
class Test_Anno_Isotropic_Propagate():
  """Test annotation propagation"""

  def setup_class(self):
    """Create the unittest database"""
    makeunitdb.createTestDB(p.token, public=True, channel_list=p.channels, ximagesize=500, yimagesize=500, zimagesize=64, scalingoption=ISOTROPIC)

  def teardown_class (self):
    """Destroy the unittest database"""
    makeunitdb.deleteTestDB(p.token)

  def test_web_propagate(self):
    """Test the web update propogate function"""

    # Posting some data at res0 to propagate
    p.args = (200,300,200,300,32,64)
    p.resolution=0
    image_data = np.ones( [1,32,100,100], dtype=np.uint32) * random.randint(255,65535)
    response = postNPZ(p, image_data)

    voxarray = getNPZ(p)
    # check that the return matches
    assert ( np.array_equal(voxarray,image_data) )

    # Check if the project is not proagated
    f = getURL("https://{}/sd/{}/{}/getPropagate/".format(SITE_HOST, p.token, ','.join(p.channels)))
    value = int(f.content)
    assert(value == NOT_PROPAGATED)

    # Start propagating
    f = getURL("https://{}/sd/{}/{}/setPropagate/{}/".format(SITE_HOST, p.token, ','.join(p.channels), UNDER_PROPAGATION))

    # Checking if the PROPGATED value is set correctly
    for iter_value in range(1, 100, 1):
      time.sleep(1)
      f = getURL("https://{}/sd/{}/{}/getPropagate/".format(SITE_HOST, p.token, ','.join(p.channels)))
      value = int(f.content)
      if value == PROPAGATED:
        break
    assert(value == PROPAGATED)

    # Checking at res1
    p.args = (100,150,100,150,16,32)
    p.resolution = 1
    voxarray = getNPZ(p)
    assert ( np.array_equal(voxarray[0][0], image_data[0][0][:50,:50]) )

    # Checking at res2
    p.args = (50,75,50,75,8,16)
    p.resolution = 2
    voxarray = getNPZ(p)
    assert ( np.array_equal(voxarray[0][0], image_data[0][0][:25,:25]) )

    # Checking at res3
    p.args = (25,37,25,37,4,8)
    p.resolution = 3
    voxarray = getNPZ(p)
    assert ( np.array_equal(voxarray[0][0], image_data[0][0][:12,:12]) )

    # Checking at res4
    p.args = (13,19,13,19,2,4)
    p.resolution = 4
    voxarray = getNPZ(p)
    assert ( np.array_equal(voxarray[0][0], image_data[0][0][:6,:6]) )
  
  #def test_internal_propagate(self):
    #"""Test the internal update propogate function"""

    #pd = ocpcaproj.NDCAProjectsDB()
    #proj = pd.loadToken ( p.token )
    #ch = ocpcaproj.NDCAChannel(proj, p.channels[0])
    #assert ( ch.getReadOnly() == 0 )
    #assert ( ch.getPropagate() == 0 )
    #ch.setPropagate ( 1 )
    #ch.setReadOnly ( 1 )
    #assert ( ch.getReadOnly() == 1 )
    #assert ( ch.getPropagate() == 1 )
