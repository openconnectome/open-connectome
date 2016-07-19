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

import urllib2
import h5py
import tempfile
import random
import numpy as np
from PIL import Image
from StringIO import StringIO

import makeunitdb
from ndtype import IMAGE, UINT8, UINT16
from params import Params
from postmethods import postBlaze, getBlosc
import kvengine_to_test
import site_to_test
SITE_HOST = site_to_test.site


# Test_Blosc
# 1 - test_get_blosc
# 2 - test_post_blosc

p = Params()
p.token = 'unittest'
p.resolution = 0
p.channels = ['IMAGE1']
p.window = [0,500]
p.channel_type = IMAGE
p.datatype = UINT8
p.voxel = [4.0,4.0,3.0]
#p.args = (3000,3100,4000,4100,500,510)


class Test_Blaze:

  def setup_class(self):

    makeunitdb.createTestDB(p.token, channel_list=p.channels, channel_type=p.channel_type, channel_datatype=p.datatype)

  def teardown_class(self):
    makeunitdb.deleteTestDB(p.token)


  def test_post_blaze (self):
    """Test post for blaze service"""

    p.args = (128,255,128,255,17,33)
    image_data = np.ones( [1,100,100], dtype=np.uint8 ) * random.randint(0,255)
    response = postBlaze(p, image_data)
    assert (response.code == 200)
    posted_data = getBlosc(p)
    
    assert ( np.array_equal(image_data,posted_data) )
