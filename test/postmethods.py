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
import cStringIO
import zlib
import tempfile
import numpy as np

from params import Params
import kvengine_to_test
import site_to_test
import makeunitdb
    
SITE_HOST = site_to_test.site


def postNPZ (p, post_data, time=False):
  """Post data using npz"""
  
  # Build the url and then create a npz object
  if time:
    url = 'http://{}/ca/{}/{}/npz/{}/{},{}/{},{}/{},{}/{},{}/'.format ( SITE_HOST, p.token, ','.join(p.channels), p.resolution, *p.args )
  elif p.channels is not None:
    url = 'http://{}/ca/{}/{}/npz/{}/{},{}/{},{}/{},{}/'.format ( SITE_HOST, p.token, ','.join(p.channels), p.resolution, *p.args )
  elif p.channels is None:
    url = 'http://{}/ca/{}/npz/{}/{},{}/{},{}/{},{}/'.format ( SITE_HOST, p.token, p.resolution, *p.args )

  fileobj = cStringIO.StringIO ()
  np.save (fileobj, post_data)
  cdz = zlib.compress (fileobj.getvalue())
  
  try:
    # Build a post request
    req = urllib2.Request(url,cdz)
    response = urllib2.urlopen(req)
    return response
  except urllib2.HTTPError,e:
    return e


def getNPZ (p, time=False):
  """Get data using npz. Returns a numpy array"""
  
  # Build the url to get the npz object 
  if time:
    url = 'http://{}/ca/{}/{}/npz/{}/{},{}/{},{}/{},{}/{},{}/'.format ( SITE_HOST, p.token, ','.join(p.channels), p.resolution, *p.args )
  elif p.channels is not None:
    url = 'http://{}/ca/{}/{}/npz/{}/{},{}/{},{}/{},{}/'.format ( SITE_HOST, p.token, ','.join(p.channels), p.resolution, *p.args )
  elif p.channels is None:
    url = 'http://{}/ca/{}/npz/{}/{},{}/{},{}/{},{}/'.format ( SITE_HOST, p.token, p.resolution, *p.args )
  # Get the image back
  f = urllib2.urlopen (url)
  rawdata = zlib.decompress (f.read())
  fileobj = cStringIO.StringIO (rawdata)
  return np.load (fileobj)


def postHDF5 (p, post_data, time=False):
  """Post data using the hdf5"""

  # Build the url and then create a hdf5 object
  if time:
    url = 'http://{}/ca/{}/{}/hdf5/{}/{},{}/{},{}/{},{}/{},{}/'.format ( SITE_HOST, p.token, ','.join(p.channels), p.resolution, *p.args )
  elif p.channels is not None:
    url = 'http://{}/ca/{}/{}/hdf5/{}/{},{}/{},{}/{},{}/'.format ( SITE_HOST, p.token, ','.join(p.channels), p.resolution, *p.args )
  elif p.channels is None:
    url = 'http://{}/ca/{}/hdf5/{}/{},{}/{},{}/{},{}/'.format ( SITE_HOST, p.token, p.resolution, *p.args )

  tmpfile = tempfile.NamedTemporaryFile ()
  fh5out = h5py.File ( tmpfile.name )
  for idx, channel_name in enumerate(p.channels):
    chan_grp = fh5out.create_group(channel_name)
    chan_grp.create_dataset("CUTOUT", tuple(post_data[idx,:].shape), post_data[idx,:].dtype, compression='gzip', data=post_data[idx,:])
    chan_grp.create_dataset("CHANNELTYPE", (1,), dtype=h5py.special_dtype(vlen=str), data=p.channel_type)
    chan_grp.create_dataset("DATATYPE", (1,), dtype=h5py.special_dtype(vlen=str), data=p.datatype)
  fh5out.close()
  tmpfile.seek(0)
  
  try:
    # Build a post request
    req = urllib2.Request(url,tmpfile.read())
    response = urllib2.urlopen(req)
    return response
  except urllib2.HTTPError,e:
    return e


def getHDF5 (p, time=False):
  """Get data using npz. Returns a hdf5 file"""

  # Build the url and then create a hdf5 object
  if time:
    url = 'http://{}/ca/{}/{}/hdf5/{}/{},{}/{},{}/{},{}/{},{}/'.format(SITE_HOST, p.token, ','.join(p.channels), p.resolution, *p.args )
  else:
    url = 'http://{}/ca/{}/{}/hdf5/{}/{},{}/{},{}/{},{}/'.format(SITE_HOST, p.token, ','.join(p.channels), p.resolution, *p.args)

  # Get the image back
  f = urllib2.urlopen (url)
  tmpfile = tempfile.NamedTemporaryFile()
  tmpfile.write(f.read())
  tmpfile.seek(0)
  h5f = h5py.File(tmpfile.name, driver='core', backing_store=False)

  return h5f

def putAnnotation ( p, f ):
  """Put the annotation file"""

  # Build a url based on update
  if p.field is None:
    f = postURL( "http://{}/ca/{}/{}/".format(SITE_HOST, p.token, p.channels[0]), f )
  else:
    f = postURL( "http://{}/ca/{}/{}/{}/".format(SITE_HOST, p.token, p.channels[0], p.field), f )

  try:
    anno_value = int(f.read())
    return anno_value
  except Exception,e:
    return 0


def getAnnotation ( p ):
  """Get the specified annotation"""

  if p.field is None:
    url = "http://{}/ca/{}/{}/{}/".format(SITE_HOST, p.token, p.channels[0], p.annoid)
  elif p.field == 'normal_cutout':
    url = "http://{}/ca/{}/{}/{}/cutout/{}/{},{}/{},{}/{},{}/".format(SITE_HOST, p.token, p.channels[0], p.annoid, p.resolution, *p.args) 
  else:
    url = "http://{}/ca/{}/{}/{}/{}/{}/".format(SITE_HOST, p.token, p.channels[0], p.annoid, p.field, p.resolution)

  f = getURL(url)
  tmpfile = tempfile.NamedTemporaryFile ( )
  tmpfile.write ( f.read() )
  tmpfile.seek(0)
  return h5py.File ( tmpfile.name, driver='core', backing_store=False )

def postURL ( url, f ):

  req = urllib2.Request(url, f.read())
  response = urllib2.urlopen(req)

  return response

def getURL ( url ):
  """Post the url"""

  try:
    req = urllib2.Request ( url )
    f = urllib2.urlopen ( url )
  except urllib2.HTTPError, e:
    return e.code

  return f
