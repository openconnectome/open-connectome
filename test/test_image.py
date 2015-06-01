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
import h5py
import tempfile
import random
import numpy as np
from PIL import Image
from StringIO import StringIO

import makeunitdb
from params import Params
from postmethods import postNPZ, getNPZ, getHDF5, postHDF5, getURL
import kvengine_to_test
import site_to_test
SITE_HOST = site_to_test.site


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
p.token = "unittest_rw"
p.resolution = 0
p.channels = ['IMAGE1', 'IMAGE2']
p.window = [0,500]
p.channel_type = "image"
p.datatype = "uint8"
#p.args = (3000,3100,4000,4100,500,510)


class Test_Image_Slice:

  def setup_class(self):

    makeunitdb.createTestDB(p.token, channel_list=p.channels, channel_type=p.channel_type, channel_datatype=p.datatype)

  def teardown_class(self):
    makeunitdb.deleteTestDB(p.token)


  def test_xy (self):
    """Test the xy slice cutout"""

    p.args = (3000,3100,4000,4100,200,201)
    image_data = np.ones( [2,1,100,100], dtype=np.uint8 ) * random.randint(0,255)
    response = postNPZ(p, image_data)

    url = "http://{}/ca/{}/{}/xy/{}/{},{}/{},{}/{}/".format(SITE_HOST, p.token, p.channels[0], p.resolution, p.args[0], p.args[1], p.args[2], p.args[3], p.args[4])
    f = getURL (url)

    slice_data = np.asarray ( Image.open(StringIO(f.read())) )
    assert ( np.array_equal(slice_data,image_data[0][0]) )

  def test_yz (self):
    """Test the yz slice cutout"""

    p.args = (4000,4001,3000,3100,200,300)
    image_data = np.ones( [2,100,100,1], dtype=np.uint8 ) * random.randint(0,255)
    response = postNPZ(p, image_data)

    url = "http://{}/ca/{}/{}/yz/{}/{}/{},{}/{},{}/".format(SITE_HOST, p.token, p.channels[0], p.resolution, p.args[0], p.args[2], p.args[3], p.args[4], p.args[5])
    f = getURL (url)

    slice_data = np.asarray ( Image.open(StringIO(f.read())) )
    assert ( np.array_equal(slice_data, image_data[0][:75][:].reshape(75,100)) )

  def test_xz (self):
    """Test the xz slice cutout"""

    p.args = (5000,5100,2000,2001,200,300)
    image_data = np.ones( [2,100,1,100], dtype=np.uint8 ) * random.randint(0,255)
    response = postNPZ(p, image_data)

    url = "http://{}/ca/{}/{}/xz/{}/{},{}/{}/{},{}/".format(SITE_HOST, p.token, p.channels[0], p.resolution, p.args[0], p.args[1], p.args[2], p.args[4], p.args[5])
    f = getURL (url)

    slice_data = np.asarray ( Image.open(StringIO(f.read())) )
    assert ( np.array_equal(slice_data, image_data[0][:75][:].reshape(75,100)) )

  def test_xy_incorrect (self):
    """Test the xy slice cutout with incorrect cutout arguments"""

    p.args = (11000,11100,4000,4100,200,201)

    url = "http://{}/ca/{}/{}/xy/{}/{},{}/{},{}/{}/".format(SITE_HOST, p.token, p.channels[0], p.resolution, p.args[0], p.args[1], p.args[2], p.args[3], p.args[4])
    assert ( 404 == getURL (url) )


class Test_Image_Window:

  def setup_class(self):
    # Testing a different datatype now
    p.datatype = "uint16"
    makeunitdb.createTestDB(p.token, channel_list=p.channels, channel_type=p.channel_type, channel_datatype=p.datatype, window=p.window, default=True)

  def teardown_class(self):
    makeunitdb.deleteTestDB(p.token)

  def test_window_default(self):
    "Test the window functionality"

    p.args = (3000,3100,4000,4100,200,201)
    image_data = np.ones([2,1,100,100], dtype=np.uint16) * 2000
    response = postNPZ(p, image_data)

    url = "http://{}/ca/{}/{}/xy/{}/{},{}/{},{}/{}/".format(SITE_HOST, p.token, p.channels[0], p.resolution, p.args[0], p.args[1], p.args[2], p.args[3], p.args[4])
    f = getURL (url)

    from windowcutout import windowCutout
    windowCutout(image_data, p.window)
    slice_data = np.asarray ( Image.open(StringIO(f.read())) )
    assert ( np.array_equal(slice_data,image_data[0][0]) )
  
  def test_window_args(self):
    "Test the window functionality"

    p.args = (3000,3100,4000,4100,200,201)
    p.window = [0,1500]
    image_data = np.ones([2,1,100,100], dtype=np.uint16) * 2000
    response = postNPZ(p, image_data)

    url = "http://{}/ca/{}/{}/xy/{}/{},{}/{},{}/{}/window/{},{}/".format(SITE_HOST, p.token, p.channels[0], p.resolution, p.args[0], p.args[1], p.args[2], p.args[3], p.args[4], *p.window)
    f = getURL (url)

    from windowcutout import windowCutout
    windowCutout(image_data, p.window)
    slice_data = np.asarray ( Image.open(StringIO(f.read())) )
    assert ( np.array_equal(slice_data,image_data[0][0]) )


class Test_Image_Post:

  def setup_class(self):
    p.datatype = "uint8"
    makeunitdb.createTestDB(p.token, channel_list=p.channels, channel_type=p.channel_type, channel_datatype=p.datatype)

  def teardown_class(self):
    makeunitdb.deleteTestDB(p.token)

  def test_npz (self):
    """Post npz data to correct region with correct datatype"""

    p.args = (3000,3100,4000,4100,500,510)
    # upload some image data
    image_data = np.ones ( [2,10,100,100], dtype=np.uint8 ) * random.randint(0,255)
    
    response = postNPZ(p, image_data)
    # Checking for successful post
    assert( response.code == 200 )
    voxarray = getNPZ(p)
    # check that the return matches
    assert ( np.array_equal(voxarray,image_data) )

  def test_npz_incorrect_region (self):
    """Post npz to incorrect region"""

    p.args = (11000,11100,4000,4100,500,510)
    image_data = np.ones ( [2,10,100,100], dtype=np.uint8 ) * random.randint(0,255)
    response = postNPZ(p, image_data)

  def test_npz_incorrect_datatype (self):
    """Post npz data with incorrect datatype"""

    p.args = (4000,4100,5000,5100,500,510)
    # upload some image data
    image_data = np.ones ( [2,10,100,100], dtype=np.uint16 ) * random.randint(0,255)

    response = postNPZ(p, image_data)
    assert (response.code == 404)
  
  def test_hdf5 (self):
    """Post hdf5 data to correct region with correct datatype"""

    p.args = (2000,2100,4000,4100,500,510)
    # upload some image data
    image_data = np.ones ( [2,10,100,100], dtype=np.uint8 ) * random.randint(0,255)

    response = postHDF5(p, image_data)
    assert ( response.code == 200 )
    h5f = getHDF5(p)

    for idx, channel_name in enumerate(p.channels):
      assert ( np.array_equal(h5f.get(channel_name).get('CUTOUT').value, image_data[idx,:]) )

  def test_hdf5_incorrect_region (self):
    """Post hdf5 file to an incorrect region"""

    p.args = (11000,11100,4000,4100,500,510)
    image_data = np.ones ( [2,10,100,100], dtype=np.uint8 ) * random.randint(0,255)
    response = postHDF5(p, image_data)
    assert (response.code == 404)

  def test_hdf5_incorrect_datatype (self):
    """Post hdf5 data with incorrect datatype"""

    p.args = (6000,6100,4000,4100,500,510)
    # upload some image data
    image_data = np.empty((2,10,100,100))
    image_data[0,:] = np.ones ( [10,100,100], dtype=np.uint8 ) * random.randint(0,255)
    image_data[1,:] = np.ones ( [10,100,100], dtype=np.uint16 ) * random.randint(0,255)

    response = postHDF5(p, image_data)
    assert ( response.code == 404 )

  def test_npz_incorrect_channel (self):
    """Post npz data with incorrect channel"""

    p.channels = p.channels + ['IMAGE3']
    image_data = np.ones ( [3,10,100,100], dtype=np.uint8 ) * random.randint(0,255)
    response = postNPZ(p, image_data)
    assert (response.code == 404)
  
  def test_hdf5_incorrect_channel (self):
    """Post hdf5 data with incorrect channel"""

    image_data = np.ones ( [3,10,100,100], dtype=np.uint8 ) * random.randint(0,255)
    response = postHDF5(p, image_data)
    assert (response.code == 404)


class Test_Image_Default:

  def setup_class(self):
    p.channels = ['IMAGE']
    makeunitdb.createTestDB(p.token, channel_list=p.channels, channel_type=p.channel_type, channel_datatype=p.datatype, default=True)

  def teardown_class(self):
    makeunitdb.deleteTestDB(p.token)
  
  def test_npz_default_channel (self):
    """Post npz data with default channel"""

    image_data = np.ones ( [1,10,100,100], dtype=np.uint8 ) * random.randint(0,255)
    p.channels = None
    response = postNPZ(p, image_data)
    assert (response.code == 200)
    voxarray = getNPZ(p)
    # check that the return matches
    assert ( np.array_equal(voxarray,image_data) )

  def test_xy_default_channel (self):
    """Test the xy slice cutout"""

    p.args = (3000,3100,4000,4100,200,201)
    image_data = np.ones( [1,1,100,100], dtype=np.uint8 ) * random.randint(0,255)
    response = postNPZ(p, image_data)
    assert (response.code == 200)
    voxarray = getNPZ(p)
    # check that the return matches
    assert ( np.array_equal(voxarray,image_data) )

    url = "http://{}/ca/{}/xy/{}/{},{}/{},{}/{}/".format(SITE_HOST, p.token, p.resolution, p.args[0], p.args[1], p.args[2], p.args[3], p.args[4])
    f = getURL (url)

    slice_data = np.asarray ( Image.open(StringIO(f.read())) )
    assert ( np.array_equal(slice_data,image_data[0][0]) )

