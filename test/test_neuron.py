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
import urllib2
import h5py
import tempfile
import random
import numpy as np
from PIL import Image
from StringIO import StringIO
import makeunitdb
from ndlib.ndtype import IMAGE, UINT8, UINT16
from params import Params
from postmethods import postNPZ, getNPZ, getHDF5, postHDF5, getURL, postBlosc, getBlosc
from postmethods import putAnnotation, getAnnotation, getURL, postURL
from ramonmethods import H5AnnotationFile, getH5id, makeAnno, getId, getField, setField
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
p.token = 'unittest'
p.resolution = 0
p.channels = ['unit_anno']

@pytest.mark.skipif(KV_ENGINE == REDIS, reason='Annotation not supported in Redis')
class Test_Neuron:

  def setup_class(self):
    """Create the unittest database"""
    makeunitdb.createTestDB(p.token, readonly=0)

  def teardown_class (self):
    """Destroy the unittest database"""
    makeunitdb.deleteTestDB(p.token)

  def test_neuron (self):
    """Make a multiple segments that overlap and then query them as a neuron"""

    # create neuron
    makeAnno(p,5)
    neuronid = p.annoid

    # create annotations
    for i in range(0,3):

      # create annotations
      makeAnno(p,4)
      f = setField(p,'neuron',neuronid)

      # add data
      p.args = (3000,3100,4000,4100,100+2*i,100+2*i+3)
      image_data = np.ones( [1,3,100,100], dtype=np.uint32 ) * p.annoid
      response = postNPZ(p, image_data)

    # get the neuron annotation
    p.annoid = neuronid
    p.field = 'tight_cutout'
    h5ret = getAnnotation(p)
    idgrp = h5ret.get(str(p.annoid))

    # count the voxels to make sure they remapped correctly
    assert ( np.unique(np.array(idgrp['CUTOUT'][:,:,:])) == [0,neuronid] ).all()
    assert ( len(np.nonzero(np.array(idgrp['CUTOUT'][:,:,:]))[0]) == 70000 )
