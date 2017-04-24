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

import json
import urllib2
import h5py
import cStringIO
import zlib
import tempfile
import blosc
import numpy as np
import requests

from params import Params
from ndlib.restutil import *
from ndlib.ndtype import UINT8, ND_dtypetonp
from test_settings import *

def postNPZ (p, post_data, time=False, neariso=False, direct=False):
  """Post data using npz"""

  # Build the url and then create a npz object
  if time:
    url = 'https://{}/sd/{}/{}/npz/{}/{},{}/{},{}/{},{}/{},{}/'.format ( SITE_HOST, p.token, ','.join(p.channels), p.resolution, *p.args )
  elif p.channels is not None:
    url = 'https://{}/sd/{}/{}/npz/{}/{},{}/{},{}/{},{}/'.format ( SITE_HOST, p.token, ','.join(p.channels), p.resolution, *p.args )
  elif p.channels is None:
    url = 'https://{}/sd/{}/npz/{}/{},{}/{},{}/{},{}/'.format ( SITE_HOST, p.token, p.resolution, *p.args )
  
  if neariso:
    url = url + NEARISO

  if direct:
    url = url + DIRECT

  fileobj = cStringIO.StringIO ()
  np.save (fileobj, post_data)
  cdz = zlib.compress (fileobj.getvalue())

  try:
    # Build a post request
    # req = urllib2.Request(url,cdz)
    # response = urllib2.urlopen(req)
    resp = postURL(url, cdz)
    return resp
  except Exception as e:
    return e

def getNPZ (p, time=False, neariso=False, direct=False):
  """Get data using npz. Returns a numpy array"""

  # Build the url to get the npz object
  if time:
    url = 'https://{}/sd/{}/{}/npz/{}/{},{}/{},{}/{},{}/{},{}/'.format ( SITE_HOST, p.token, ','.join(p.channels), p.resolution, *p.args )
  elif p.channels is not None:
    url = 'https://{}/sd/{}/{}/npz/{}/{},{}/{},{}/{},{}/'.format ( SITE_HOST, p.token, ','.join(p.channels), p.resolution, *p.args )
  elif p.channels is None:
    url = 'https://{}/sd/{}/npz/{}/{},{}/{},{}/{},{}/'.format ( SITE_HOST, p.token, p.resolution, *p.args )

  if neariso:
    url = url + NEARISO

  if direct:
    url = url + DIRECT
  
  resp = getURL(url)
  rawdata = zlib.decompress (resp.content)
  fileobj = cStringIO.StringIO (rawdata)
  return np.load (fileobj)

def postBlaze (p, post_data, time=False):
  """Post data using npz"""

  # Build the url and then create a npz object
  if time:
    url = 'https://{}/sd/{}/{}/blaze/{}/{},{}/{},{}/{},{}/{},{}/'.format ( SITE_HOST, p.token, ','.join(p.channels), p.resolution, *p.args )
  elif p.channels is not None:
    url = 'https://{}/sd/{}/{}/blaze/{}/{},{}/{},{}/{},{}/'.format ( SITE_HOST, p.token, ','.join(p.channels), p.resolution, *p.args )
  elif p.channels is None:
    url = 'https://{}/sd/{}/blaze/{}/{},{}/{},{}/{},{}/'.format ( SITE_HOST, p.token, p.resolution, *p.args )

  try:
    # Build a post request
    resp = postURL(url, blosc.pack_array(post_data))
    return resp
  except Exception as e:
    return e

def postBlosc (p, post_data, time=False, neariso=False, direct=False):
  """Post data using blosc packed numpy array"""

  # Build the url and then create a npz object
  if time:
    url = 'https://{}/sd/{}/{}/blosc/{}/{},{}/{},{}/{},{}/{},{}/'.format ( SITE_HOST, p.token, ','.join(p.channels), p.resolution, *p.args )
  elif p.channels is not None:
    url = 'https://{}/sd/{}/{}/blosc/{}/{},{}/{},{}/{},{}/'.format ( SITE_HOST, p.token, ','.join(p.channels), p.resolution, *p.args )
  elif p.channels is None:
    url = 'https://{}/sd/{}/blosc/{}/{},{}/{},{}/{},{}/'.format ( SITE_HOST, p.token, p.resolution, *p.args )

  if neariso:
    url = url + NEARISO

  if direct:
    url = url + DIRECT
  
  try:
    # Build a post request
    resp = postURL(url,blosc.pack_array(post_data))
    return resp
  except Exception as e:
    return e

def getBlosc (p, time=False, neariso=False, direct=False):
  """Get data using blosc. Returns a blosc packed numpy array"""

  # Build the url to get the npz object
  if time:
    url = 'https://{}/sd/{}/{}/blosc/{}/{},{}/{},{}/{},{}/{},{}/'.format ( SITE_HOST, p.token, ','.join(p.channels), p.resolution, *p.args )
  elif p.channels is not None:
    url = 'https://{}/sd/{}/{}/blosc/{}/{},{}/{},{}/{},{}/'.format ( SITE_HOST, p.token, ','.join(p.channels), p.resolution, *p.args )
  elif p.channels is None:
    url = 'https://{}/sd/{}/blosc/{}/{},{}/{},{}/{},{}/'.format ( SITE_HOST, p.token, p.resolution, *p.args )
  
  if neariso:
    url = url + NEARISO

  if direct:
    url = url + DIRECT
  
  # Get the image back
  resp = getURL(url)
  return blosc.unpack_array(resp.content)


def postHDF5 (p, post_data, time=False, neariso=False, direct=False):
  """Post data using the hdf5"""

  # Build the url and then create a hdf5 object
  if time:
    url = 'https://{}/sd/{}/{}/hdf5/{}/{},{}/{},{}/{},{}/{},{}/'.format ( SITE_HOST, p.token, ','.join(p.channels), p.resolution, *p.args )
  elif p.channels is not None:
    url = 'https://{}/sd/{}/{}/hdf5/{}/{},{}/{},{}/{},{}/'.format ( SITE_HOST, p.token, ','.join(p.channels), p.resolution, *p.args )
  elif p.channels is None:
    url = 'https://{}/sd/{}/hdf5/{}/{},{}/{},{}/{},{}/'.format ( SITE_HOST, p.token, p.resolution, *p.args )

  if neariso:
    url = url + NEARISO

  if direct:
    url = url + DIRECT
  
  tmpfile = tempfile.NamedTemporaryFile ()
  fh5out = h5py.File ( tmpfile.name )
  for idx, channel_name in enumerate(p.channels):
    chan_grp = fh5out.create_group(channel_name)
    chan_grp.create_dataset("CUTOUT", tuple(post_data[idx,:].shape), post_data[idx,:].dtype, compression='gzip', data=post_data[idx,:])
    chan_grp.create_dataset("CHANNELTYPE", (1,), dtype=h5py.special_dtype(vlen=str), data=p.channel_type)
    chan_grp.create_dataset("DATATYPE", (1,), dtype=h5py.special_dtype(vlen=str), data=p.datatype)

    print chan_grp['CUTOUT'], chan_grp['CHANNELTYPE'], chan_grp['DATATYPE']

  fh5out.close()
  tmpfile.seek(0)

  try:
    # Build a post request
    resp = postURL(url,tmpfile.read())
    return resp
  except Exception as e:
    return e

def getHDF5 (p, time=False, neariso=False, direct=False):
  """Get data using npz. Returns a hdf5 file"""

  # Build the url and then create a hdf5 object
  if time:
    url = 'https://{}/sd/{}/{}/hdf5/{}/{},{}/{},{}/{},{}/{},{}/'.format(SITE_HOST, p.token, ','.join(p.channels), p.resolution, *p.args )
  else:
    url = 'https://{}/sd/{}/{}/hdf5/{}/{},{}/{},{}/{},{}/'.format(SITE_HOST, p.token, ','.join(p.channels), p.resolution, *p.args)

  if neariso:
    url = url + NEARISO

  if direct:
    url = url + DIRECT
  
  # Get the image back
  resp = getURL(url)
  tmpfile = tempfile.NamedTemporaryFile()
  tmpfile.write(resp.content)
  tmpfile.seek(0)
  h5f = h5py.File(tmpfile.name, driver='core', backing_store=False)

  return h5f

def getRAW (p, time=False, neariso=False, direct=False):
  """Get data using raw format. Returns a numpy array"""

  # Build the url and then create a raw object
  if time:
    url = 'https://{}/sd/{}/{}/raw/{}/{},{}/{},{}/{},{}/{},{}/'.format(SITE_HOST, p.token, ','.join(p.channels), p.resolution, *p.args )
  else:
    url = 'https://{}/sd/{}/{}/raw/{}/{},{}/{},{}/{},{}/'.format(SITE_HOST, p.token, ','.join(p.channels), p.resolution, *p.args)

  if neariso:
    url = url + NEARISO
  
  if direct:
    url = url + DIRECT

  # Get the data back
  resp = getURL(url)
  rawdata = resp.content
  return np.frombuffer(rawdata, dtype = ND_dtypetonp[p.datatype])

def putAnnotation ( p, f ):
  """Put the annotation file"""

  # Build a url based on update
  if p.field is None:
    resp = postURL( "https://{}/sd/{}/{}/".format(SITE_HOST, p.token, p.channels[0]), f )
  else:
    resp = postURL( "https://{}/sd/{}/{}/{}/".format(SITE_HOST, p.token, p.channels[0], p.field), f )

  try:
    anno_value = int(resp.content)
    return anno_value
  except Exception as e:
    return 0

def getAnnotation ( p ):
  """Get the specified annotation"""

  if p.field is None:
    url = "https://{}/sd/{}/{}/{}/".format(SITE_HOST, p.token, p.channels[0], p.annoid)
  elif p.field == 'tight_cutout':
    url = "https://{}/sd/{}/{}/{}/cutout/{}/".format(SITE_HOST, p.token, p.channels[0], p.annoid, p.resolution)
  elif p.field == 'normal_cutout':
    url = "https://{}/sd/{}/{}/{}/cutout/{}/{},{}/{},{}/{},{}/".format(SITE_HOST, p.token, p.channels[0], p.annoid, p.resolution, *p.args)
  else:
    url = "https://{}/sd/{}/{}/{}/{}/{}/".format(SITE_HOST, p.token, p.channels[0], p.annoid, p.field, p.resolution)

  f = getURL(url)
  tmpfile = tempfile.NamedTemporaryFile ( )
  tmpfile.write ( f.content )
  tmpfile.seek(0)
  return h5py.File ( tmpfile.name, driver='core', backing_store=False )
