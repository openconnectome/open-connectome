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

import django.http

import numpy as np
from PIL import Image
import urllib2
import zlib
import json

import cStringIO

from django.conf import settings

from ocpcaerror import OCPCAError

import logging
logger=logging.getLogger("ocp")

"""Merge two cutouts of any type"""
def overlayImage (request, webargs):
 
  """Get both data and annotation cubes as npz"""
  alpha, server1, token1, channel1, server2, token2, channel2, plane, cutout = webargs.split('/',8)

  alpha = float(alpha)

  # Get the info for project 1
  url = 'http://{}/ocp/ca/{}/info/'.format(server1,token1)
  try:
    f = urllib2.urlopen ( url )
  except urllib2.URLError, e:
    raise OCPCAError ( "Web service error. URL {}.  Error {}.".format(url,e))
  layer1info = json.loads ( f.read() )

  # Get the info for project 2
  url = 'http://{}/ocp/ca/{}/info/'.format(server2,token2)
  try:
    f = urllib2.urlopen ( url )
  except urllib2.URLError, e:
    raise OCPCAError ( "Web service error. URL {}.  Error {}.".format(url,e.fp.read()))
  layer2info = json.loads ( f.read() )

  # Do some checking to make sure that are compatible based on the same datasets
  # and that the channels exist
 
  # get the first image
  url = 'http://{}/ocp/ca/{}/{}/{}/{}'.format(server1,token1,plane,channel1,cutout) 
  try:
    f = urllib2.urlopen ( url )
  except urllib2.URLError, e:
    raise OCPCAError ( "Web service error. URL {}.  Error {}.".format(url,e.fp.read()))

  fobj = cStringIO.StringIO ( f.read() )
  img1 = Image.open(fobj) 
   
  # get the second image
  url = 'http://{}/ocp/ca/{}/{}/{}/{}'.format(server2,token2,plane,channel2,cutout) 
  try:
    f = urllib2.urlopen ( url )
  except urllib2.URLError, e:
    raise OCPCAError ( "Web service error. URL {}.  Error {}.".format(url,e.fp.read()))

  fobj = cStringIO.StringIO ( f.read() )
  img2 = Image.open(fobj) 

  try:
    # convert data image to RGBA
    img1 = img1.convert("RGBA")
    img2 = img2.convert("RGBA")
    # build the overlay
    compimg1 = Image.composite ( img1, img2, img1 )
    compimg = Image.blend ( img2, compimg1, alpha )

  except Exception, e:
    logger.error ("Unknown error processing overlay images. Error={}".format(e))
    raise
  # Create blended image of the two
  return compimg


def overlay (request, webargs):
  """Return overlayCutout as a png"""

  try:
    overlayimg = overlayImage ( request, webargs )
  except Exception, e:
     raise

  # write the merged image to a buffer
  fobj2 = cStringIO.StringIO ( )
  overlayimg.save ( fobj2, "PNG" )

  fobj2.seek(0)

  return django.http.HttpResponse(fobj2.read(), content_type="image/png" )


