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
import random
import numpy as np
import makeunitdb
from ndlib.ndtype import *
from params import Params
from postmethods import *
from test_settings import *

# Test_Blosc
# 1 - test_get_blosc
# 2 - test_post_blosc

p = Params()
p.token = 'unittest'
p.resolution = 0
p.channels = ['IMAGE1', 'IMAGE2']
p.window = [0,500]
p.channel_type = TIMESERIES
p.datatype = UINT8
p.voxel = [4.0,4.0,3.0]

class Test_Blosc:

  def setup_class(self):

    makeunitdb.createTestDB(p.token, channel_list=p.channels, channel_type=p.channel_type, channel_datatype=p.datatype)

  def teardown_class(self):
    makeunitdb.deleteTestDB(p.token)


  def test_get_blosc (self):
    """Test the xy slice cutout"""

    p.args = (3000,3100,4000,4100,200,201,10, 12)
    time_data = np.ones( [2,2,1,100,100], dtype=np.uint8 ) * random.randint(0,255)
    response = postNPZ(p, time_data, time=True)
    posted_data = getBlosc(p, time=True)
    
    assert (np.array_equal(time_data, posted_data))
  
  @pytest.mark.skipif(KV_ENGINE == MYSQL, reason='Direct writes not supported in MySQL') 
  def test_post_direct_blosc (self):
    """Test the xy slice cutout"""

    p.args = (3000,3100,4000,4100,200,201,51,53)
    time_data = np.ones( [2,2,1,100,100], dtype=np.uint8 ) * random.randint(0,255)
    response = postBlosc(p, time_data, time=True, direct=True)
    posted_data = getNPZ(p, time=True)

    assert (np.array_equal(time_data, posted_data))
  
  def test_post_blosc (self):
    """Test the xy slice cutout"""

    p.args = (3000,3100,4000,4100,200,201,10,12)
    time_data = np.ones( [2,2,1,100,100], dtype=np.uint8 ) * random.randint(0,255)
    response = postBlosc(p, time_data, time=True)
    posted_data = getNPZ(p, time=True)

    assert (np.array_equal(time_data, posted_data))
  
  def test_incorrect_dim_blosc (self):
    """Test the xy slice cutout"""

    p.args = (3000,3100,4000,4100,200,201,10,12)
    time_data = np.ones( [2,2,1,200,200], dtype=np.uint8 ) * random.randint(0,255)
    response = postBlosc(p, time_data, time=True)
    assert(response.status_code == 404)
  
  def test_incorrect_channel_blosc (self):
    """Test the xy slice cutout"""

    p.args = (3000,3100,4000,4100,200,201,10,12)
    time_data = np.ones( [2,1,1,100,100], dtype=np.uint8 ) * random.randint(0,255)
    response = postBlosc(p, time_data, time=True)
    assert(response.status_code == 404)
