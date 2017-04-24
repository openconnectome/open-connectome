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

import random
import numpy as np
from PIL import Image
from StringIO import StringIO
import makeunitdb
from ndlib.ndtype import TIMESERIES, FLOAT32
from params import Params
from postmethods import postNPZ, getNPZ, getHDF5, postHDF5, getURL
from test_settings import *

# Test Image

# Test_Image_Slice
# 1 - test_xy
# 2 - test_yz
# 3 - test_xz
# 4 - test_xy_incorrect

# Test_Image_Post
# 1 - test_npz
# 2 - test_npz_incorrect_region
# 3 - test_npz_incorrect_datatype
# 4 - test_hdf5
# 5 - test_hdf5_incorrect_region
# 6 - test_hdf5_incorrect_datatype
# 7 - test_npz_incorrect_channel
# 8 - test_hdf5_incorrect_channel


p = Params()
p.datatype = FLOAT32


class Test_Probability_Slice:

  def setup_class(self):

    makeunitdb.createTestDB(p.token, channel_list=p.channels, channel_type=p.channel_type, channel_datatype=p.datatype)

  def teardown_class(self):
    makeunitdb.deleteTestDB(p.token)

  def test_xy (self):
    """Test the xy slice cutout"""

    p.args = (3000,3100,4000,4100,200,201,10,12)
    time_data = np.ones( [2,2,1,100,100], dtype=np.float32 ) * random.random()
    response = postNPZ(p, time_data, time=True)

    url = "https://{}/sd/{}/{}/xy/{}/{},{}/{},{}/{}/{}/".format(SITE_HOST, p.token, p.channels[0], p.resolution, p.args[0], p.args[1], p.args[2], p.args[3], p.args[4], p.args[6])
    f = getURL (url)
    
    from ndlib.windowcutout import windowCutout
    time_data = windowCutout(time_data, p.window).astype(np.uint8)
    # time_data = np.uint8(time_data*256)
    slice_data = np.asarray ( Image.open(StringIO(f.content)) )
    assert ( np.array_equal(slice_data, time_data[0][0][0]) )

  def test_yz (self):
    """Test the yz slice cutout"""

    p.args = (4000,4001,3000,3100,200,300,10,12)
    time_data = np.ones( [2,2,100,100,1], dtype=np.float32 ) * random.random()
    response = postNPZ(p, time_data, time=True)

    url = "https://{}/sd/{}/{}/yz/{}/{}/{},{}/{},{}/{}/".format(SITE_HOST, p.token, p.channels[0], p.resolution, p.args[0], p.args[2], p.args[3], p.args[4], p.args[5], p.args[6])
    f = getURL (url)

    from ndlib.windowcutout import windowCutout
    time_data = windowCutout(time_data, p.window).astype(np.uint8)
    # time_data = np.uint8(time_data*256)
    slice_data = np.asarray ( Image.open(StringIO(f.content)) )
    assert ( np.array_equal(slice_data, time_data[0][0][:75][:].reshape(75,100)) )

  def test_xz (self):
    """Test the xz slice cutout"""

    p.args = (5000,5100,2000,2001,200,300,10,12)
    time_data = np.ones( [2,2,100,1,100], dtype=np.float32 ) * random.random()
    response = postNPZ(p, time_data, time=True)

    url = "https://{}/sd/{}/{}/xz/{}/{},{}/{}/{},{}/{}/".format(SITE_HOST, p.token, p.channels[0], p.resolution, p.args[0], p.args[1], p.args[2], p.args[4], p.args[5], p.args[6])
    f = getURL (url)

    from ndlib.windowcutout import windowCutout
    time_data = windowCutout(time_data, p.window).astype(np.uint8)
    # time_data = np.uint8(time_data*256)
    slice_data = np.asarray ( Image.open(StringIO(f.content)) )
    assert ( np.array_equal(slice_data, time_data[0][0][:75][:].reshape(75,100)) )

  def test_xy_incorrect (self):
    """Test the xy slice cutout with incorrect cutout arguments"""

    p.args = (11000,11100,4000,4100,200,201)

    url = "https://{}/sd/{}/{}/xy/{}/{},{}/{},{}/{}/".format(SITE_HOST, p.token, p.channels[0], p.resolution, p.args[0], p.args[1], p.args[2], p.args[3], p.args[4])
    assert ( 404 == getURL(url).status_code )

class Test_Probability_Post:

  def setup_class(self):
    makeunitdb.createTestDB(p.token, channel_list=p.channels, channel_type=p.channel_type, channel_datatype=p.datatype)

  def teardown_class(self):
    makeunitdb.deleteTestDB(p.token)

  def test_npz (self):
    """Post npz data to correct region with correct datatype"""

    p.args = (3000,3100,4000,4100,500,510)
    # upload some image data
    time_data = np.ones ( [2,10,100,100], dtype=np.float32 ) * random.random()

    response = postNPZ(p, time_data)
    # Checking for successful post
    assert( response.status_code == 200 )
    voxarray = getNPZ(p)
    # check that the return matches
    assert ( np.array_equal(voxarray,time_data) )

  def test_npz_incorrect_region (self):
    """Post npz to incorrect region"""

    p.args = (11000,11100,4000,4100,500,510)
    time_data = np.ones ( [2,10,100,100], dtype=np.float32 ) * random.random()
    response = postNPZ(p, time_data)

  def test_npz_incorrect_datatype (self):
    """Post npz data with incorrect datatype"""

    p.args = (4000,4100,5000,5100,500,510)
    # upload some image data
    time_data = np.ones ( [2,10,100,100], dtype=np.float64 ) * random.random()

    response = postNPZ(p, time_data)
    assert (response.status_code == 404)

  def test_hdf5 (self):
    """Post hdf5 data to correct region with correct datatype"""

    p.args = (2000,2100,4000,4100,500,510)
    # upload some image data
    time_data = np.ones ( [2,10,100,100], dtype=np.float32 ) * random.random()

    response = postHDF5(p, time_data)
    assert ( response.status_code == 200 )
    h5f = getHDF5(p)

    for idx, channel_name in enumerate(p.channels):
      assert ( np.array_equal(h5f.get(channel_name).get('CUTOUT').value, time_data[idx,:]) )

  def test_hdf5_incorrect_region (self):
    """Post hdf5 file to an incorrect region"""

    p.args = (11000,11100,4000,4100,500,510)
    time_data = np.ones ( [2,10,100,100], dtype=np.float32 ) * random.random()
    response = postHDF5(p, time_data)
    assert (response.status_code == 404)

  def test_hdf5_incorrect_datatype (self):
    """Post hdf5 data with incorrect datatype"""

    p.args = (6000,6100,4000,4100,500,510)
    # upload some image data
    time_data = np.empty((2,10,100,100))
    time_data[0,:] = np.ones ( [10,100,100], dtype=np.float32 ) * random.random()
    time_data[1,:] = np.ones ( [10,100,100], dtype=np.float32 ) * random.random()

    response = postHDF5(p, time_data)
    assert ( response.status_code == 404 )

  def test_npz_incorrect_channel (self):
    """Post npz data with incorrect channel"""

    p.channels = p.channels + ['CHAN3']
    time_data = np.ones ( [3,10,100,100], dtype=np.float32 ) * random.random()
    response = postNPZ(p, time_data)
    assert (response.status_code == 404)

  def test_hdf5_incorrect_channel (self):
    """Post hdf5 data with incorrect channel"""

    time_data = np.ones ( [3,10,100,100], dtype=np.float32 ) * random.random()
    response = postHDF5(p, time_data)
    assert (response.status_code == 404)
