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

"""  Unit tests that require the OCP stack to be available.
       All tests in other units should use Web services only.
"""

import sys
import os
import random 
import csv
import numpy as np
from PIL import Image
from StringIO import StringIO
import pytest

sys.path += [os.path.abspath('../django')]
import OCP.settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'OCP.settings'
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

from postmethods import getURL, postNPZ, getNPZ
import ocpcaproj
from params import Params
import kvengine_to_test
import site_to_test
import makeunitdb

SITE_HOST = site_to_test.site

# Test_Propagate
#
# 1 - test_update_propagate - Test the propagate service set values

p = Params()
p.token = 'unittest'
p.resolution = 0
p.channels = ['chan1']
p.channel_type = "image"
p.datatype = "uint8"

class Test_Image_Propagate:
  """Test image propagation"""

  def setup_class(self):
    """Create the unittest database"""
    makeunitdb.createTestDB(p.token, public=True, channel_list=p.channels, channel_type=p.channel_type, channel_datatype=p.datatype, ximagesize=1000, yimagesize=1000, zimagesize=10)

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
    f = getURL("http://{}/ca/{}/{}/getPropagate/".format(SITE_HOST, p.token, ','.join(p.channels)))
    value = int(f.read())
    assert(value == ocpcaproj.NOT_PROPAGATED)

    # Start propagating
    f = getURL("http://{}/ca/{}/{}/setPropagate/{}/".format(SITE_HOST, p.token, ','.join(p.channels), ocpcaproj.UNDER_PROPAGATION))

    # Checking if the PROPGATED value is set correctly
    f = getURL("http://{}/ca/{}/{}/getPropagate/".format(SITE_HOST, p.token, ','.join(p.channels)))
    value = int(f.read())
    assert(value == ocpcaproj.PROPAGATED)

    # Checking at res1
    p.args = (100,150,100,150,4,5)
    url = "http://{}/ca/{}/{}/xy/{}/{},{}/{},{}/{}/".format(SITE_HOST, p.token, p.channels[0], p.resolution+1, p.args[0], p.args[1], p.args[2], p.args[3], p.args[4])
    f = getURL(url)
    slice_data = np.asarray ( Image.open(StringIO(f.read())) )
    assert ( np.array_equal(slice_data, image_data[0][0][:50,:50]) )
   
    # Checking at res5
    p.args = (7,9,7,9,4,5)
    url = "http://{}/ca/{}/{}/xy/{}/{},{}/{},{}/{}/".format(SITE_HOST, p.token, p.channels[0], p.resolution+5, p.args[0], p.args[1], p.args[2], p.args[3], p.args[4])
    f = getURL(url)
    slice_data = np.asarray ( Image.open(StringIO(f.read())) )
    assert ( np.array_equal(slice_data, image_data[0][0][:2,:2]) )


class Test_Anno_Propagate():
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
    p.args = (0,1000,0,1000,0,10)
    image_data = np.ones( [1,10,1000,1000], dtype=np.uint32) * random.randint(255,65535)
    response = postNPZ(p, image_data)

    voxarray = getNPZ(p)
    # check that the return matches
    assert ( np.array_equal(voxarray,image_data) )

    # Check if the project is not proagated
    f = getURL("http://{}/ca/{}/{}/getPropagate/".format(SITE_HOST, p.token, ','.join(p.channels)))
    value = int(f.read())
    assert(value == ocpcaproj.NOT_PROPAGATED)

    # Start propagating
    f = getURL("http://{}/ca/{}/{}/setPropagate/{}/".format(SITE_HOST, p.token, ','.join(p.channels), ocpcaproj.UNDER_PROPAGATION))

    # Checking if the PROPGATED value is set correctly
    f = getURL("http://{}/ca/{}/{}/getPropagate/".format(SITE_HOST, p.token, ','.join(p.channels)))
    value = int(f.read())
    assert(value == ocpcaproj.PROPAGATED)

    import pdb; pdb.set_trace()
    # Checking at res1
    p.args = (100,150,100,150,4,5)
    p.resolution = 1
    voxarray = getNPZ(p)
    assert ( np.array_equal(voxarray[0][0], image_data[0][0][:50,:50]) )


  #def test_internal_propagate(self):
    #"""Test the internal update propogate function"""

    #pd = ocpcaproj.OCPCAProjectsDB()
    #proj = pd.loadToken ( p.token )
    #ch = ocpcaproj.OCPCAChannel(proj, p.channels[0])
    #assert ( ch.getReadOnly() == 0 )
    #assert ( ch.getPropagate() == 0 )
    #ch.setPropagate ( 1 )
    #ch.setReadOnly ( 1 )
    #assert ( ch.getReadOnly() == 1 )
    #assert ( ch.getPropagate() == 1 )
