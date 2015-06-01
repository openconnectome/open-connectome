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

import numpy as np
import h5py
import tempfile
import random
import urllib2

import makeunitdb
from params import Params
import site_to_test
SITE_HOST = site_to_test.site

#class TestImageBuild:
  
  #def setup_class(self):

    #makeunitdb.createTestDB('unittest_rw', channel_type='image', datatype='uint8', ximagesize=1000, yimagesize=1000, zimagesize=10, scalinglevels=3 )
    #self.p = Params()
    #self.p.token = "unittest_rw"
    #self.p.baseurl = SITE_HOST
    #self.p.resolution = 0
    #self.p.args = (500,600,300,400,1,6)
    #self.imagedata = None

  #def teardown_class(self):

    #makeunitdb.deleteTestDB('unittest_rw')
  
  #def post_image(self):

    ## upload some image data
    #self.imagedata = np.ones ( [5,100,100], dtype=np.uint8 ) * random.randint(0,255)
    
    #url = 'http://{}/ca/{}/hdf5/{}/{},{}/{},{}/{},{}/'.format ( self.p.baseurl, self.p.token, self.p.resolution, *self.p.args )
    
    #tmpfile = tempfile.NamedTemporaryFile ()
    #fh5out = h5py.File ( tmpfile.name )
    #fh5out.create_dataset ( "CUTOUT", tuple(self.imagedata.shape), self.imagedata.dtype,compression='gzip', data=self.imagedata )
    #fh5out.close()
    #tmpfile.seek(0)
     
    ## Build a post request
    #req = urllib2.Request(url,tmpfile.read())
    #response = urllib2.urlopen(req)

  #def test_image_build(self):
    
    #self.post_image()
    #url_set = 'http://{}/ca/{}/setPropagate/{}/'.format ( self.p.baseurl, self.p.token, makeunitdb.ocpcaproj.UNDER_PROPAGATION )
    #url_get = 'http://{}/ca/{}/getPropagate/'.format ( self.p.baseurl, self.p.token )

    #f = urllib2.urlopen(url_set)
    #while (True):
      #req = urllib2.urlopen(url_get)
      #status = int(req.read())
      #print status
      #if status == makeunitdb.ocpcaproj.PROPAGATED:
        #break

    #url = 'http://{}/ca/{}/hdf5/{}/{},{}/{},{}/{},{}/'.format ( self.p.baseurl, self.p.token, self.p.resolution+1, *(250,300,150,200,1,6) )
    #f = urllib2.urlopen(url)
    #tmpfile = tempfile.NamedTemporaryFile ( )
    #tmpfile.write ( f.read() )
    #tmpfile.seek(0)
    #h5f = h5py.File ( tmpfile.name, driver='core', backing_store=False )
    
    #assert ( np.array_equal(h5f.get('CUTOUT').value,self.imagedata[:5,:50,:50]) )

