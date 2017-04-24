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
import numpy as np
import makeunitdb
from ndlib.ndtype import TIMESERIES, UINT8, UINT16
from params import Params
from postmethods import postNPZ, getRAW
from test_settings import *

# Test_RAW
# 1 - test_get_raw

p = Params()

class Test_Raw:

  def setup_class(self):

    makeunitdb.createTestDB(p.token, channel_list=p.channels, channel_type=p.channel_type, channel_datatype=p.datatype)

  def teardown_class(self):
    makeunitdb.deleteTestDB(p.token)


  def test_get_raw (self):
    """Test the xyz cube cutout for raw data"""

    p.args = (3000, 3003, 4000, 4003, 200, 203, 50, 60)
    image_data = (np.random.rand(2, 10, 3, 3, 3) * 255).astype(np.uint8)
    response = postNPZ(p, image_data, time=True)
    requested_data = getRAW(p, time=True)
    requested_data.shape = (2, 10, 3, 3, 3)
    assert ( np.array_equal(image_data, requested_data) )


  @pytest.mark.skipif(KV_ENGINE == MYSQL, reason='Direct writes not supported in MySQL')
  def test_get_direct_raw(self):
    """Test the xyz cube cutout direct for raw data"""
    
    p.args = (1000, 1003, 2000, 2003, 100, 103, 10, 12)
    # p.args = (512, 1024, 0, 512, 1, 65)
    image_data = (np.random.rand(2, 2, 3, 3, 3) * 255).astype(np.uint8)
    # image_data = (np.random.rand(2, 64, 512, 512) * 255).astype(np.uint8)
    response = postNPZ(p, image_data, time=True, direct=True)
    requested_data = getRAW(p, time=True)
    requested_data.shape = (2, 2, 3, 3, 3)
    # requested_data.shape = (2,64,512,512)
    assert ( np.array_equal(image_data, requested_data) )
  
class Test_Raw_Neariso:

  def setup_class(self):

    makeunitdb.createTestDB(p.token, channel_list=p.channels, channel_type=p.channel_type, channel_datatype=p.datatype, base_resolution=3)

  def teardown_class(self):
    makeunitdb.deleteTestDB(p.token)
  
  def test_get_neariso_raw(self):
    """Test the xyz cube neariso cutout for raw data"""
    
    p.resolution = 3
    p.args = (500, 503, 400, 403, 10, 15, 7, 9)
    image_data = (np.random.rand(2, 2, 5, 3, 3) * 255).astype(np.uint8)
    response = postNPZ(p, image_data, time=True, neariso=True)
    requested_data = getRAW(p, time=True, neariso=True)
    requested_data.shape = (2, 2, 5, 3, 3)
    assert ( np.array_equal(image_data, requested_data) )
  
  @pytest.mark.skipif(KV_ENGINE == MYSQL, reason='Direct writes not supported in MySQL')
  def test_get_direct_neariso_raw(self):
    """Test the xyz cube cutout direct for raw data"""
    
    p.args = (400, 403, 200, 203, 10, 15, 7, 9)
    image_data = (np.random.rand(2, 2, 5, 3, 3) * 255).astype(np.uint8)
    response = postNPZ(p, image_data, time=True, neariso=True, direct=True)
    requested_data = getRAW(p, time=True, neariso=True)
    requested_data.shape = (2, 2, 5, 3, 3)
    assert ( np.array_equal(image_data, requested_data) )
