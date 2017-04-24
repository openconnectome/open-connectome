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

import argparse
import numpy as np
import cStringIO
import sys
import csv
import os

import tempfile
import h5py

sys.path += [os.path.abspath('../django')]
import ND.settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'ND.settings'

from ndlib.restutil import *


# Annotation types
anno_names = { 1:'ANNO_ANNOTATION',\
               2:'ANNO_SYNAPSE',\
               3:'ANNO_SEED',\
               4:'ANNO_SEGMENT',\
               5:'ANNO_NEURON',\
               6:'ANNO_ORGANELLE',\
               7:'ANNO_NODE',\
               8:'ANNO_SKELETON' }

def main():

  parser = argparse.ArgumentParser(description='Fetch an annotation as an HDF5 file')
  parser.add_argument('baseurl', action="store")
  parser.add_argument('token', action="store")
  parser.add_argument('channel', action="store")
  parser.add_argument('annids', action="store", help='Annotation IDs (comman sepearted list  to extract')
  parser.add_argument('--voxels', action='store_true', help='Return data as a list of voxels.')
  parser.add_argument('--resolution', type=int, action="store", help='Resolution at which you want the voxels.  Defaults to 0.', default=0)
  parser.add_argument('--cutout', action="store", help='Cutout arguments of the form resolution/x1,x2/y1,y2/z1,z2.', default=None)
  parser.add_argument('--output', action="store", help='File name to output the HDF5 file.', default=None)
  parser.add_argument('--tightcutout', action='store_true', help='Return a cutout as a bounding box. Requires a resolution')
  parser.add_argument('--boundingbox', action='store_true', help='Return a the bounding box with no data. Requires a resolution')
  parser.add_argument('--cuboids', action='store_true', help='Perform a mininal cutout.')
  parser.add_argument('--remap', action='store_true', help='Remap all connected items to the parent annotation id')

  result = parser.parse_args()

  if result.voxels:
    url = "https://%s/sd/%s/%s/%s/voxels/%s/" % (result.baseurl,result.token,result.channel,result.annids,result.resolution)
  elif result.cutout != None:
    url = "https://%s/sd/%s/%s/%s/cutout/%s/" % (result.baseurl,result.token,result.channel,result.annids,result.cutout)
  elif result.tightcutout: 
    url = "https://%s/sd/%s/%s/%s/cutout/%s/" % (result.baseurl,result.token,result.channel,result.annids,result.resolution)
  elif result.boundingbox: 
    url = "https://%s/sd/%s/%s/%s/boundingbox/%s/" % (result.baseurl,result.token,result.channel,result.annids,result.resolution)
  elif result.cuboids: 
    url = "https://%s/sd/%s/%s/%s/cuboids/%s/" % (result.baseurl,result.token,result.channel,result.annids,result.resolution)
  else:
    url = "https://%s/sd/%s/%s/%s/" % (result.baseurl,result.token,result.channel,result.annids)

  if result.remap:
    url += 'remap/'

  print url

  # Get annotation in question
  try:
    f = getURL( url )
  except urllib2.URLError, e:
    print "Failed URL", url
    print "Error %s" % (e) 
    sys.exit(0)

  # create an in memory h5 file
  if result.output == None:
    # Read into a temporary file
    tmpfile = tempfile.NamedTemporaryFile ( )
    tmpfile.write ( f.content )
    tmpfile.seek(0)
    h5f = h5py.File ( tmpfile.name, driver='core', backing_store=False )

  # unless an output file was requested
  else:
    fh = open ( result.output, 'w' )
    fh.write ( f.content )
    fh.seek(0)
    h5f = h5py.File ( result.output )

  # assume a single annotation for now
  keys = h5f.keys()
  for k in keys:
    idgrp = h5f.get(k)

    print "Annotation id: ", k
    print "Annotation type: ", anno_names[idgrp['ANNOTATION_TYPE'][0]]

    mdgrp = idgrp['METADATA']

    for field in mdgrp.keys():
      if field == 'KVPAIRS':
        fstring = cStringIO.StringIO( mdgrp[field][0] )
        csvr = csv.reader(fstring, delimiter=',')
        for r in csvr:
          print 'key: {}, value: {}'.format(r[0],r[1])
      else:
        print field, mdgrp[field][:]

    if idgrp.get('VOXELS'):
      print "Voxel list for object of length", len(idgrp['VOXELS'][:])
      print idgrp['VOXELS'][:]
    elif result.voxels:
      print "No voxels found at this resolution"

    if idgrp.get('CUTOUT') and idgrp.get('XYZOFFSET'):
      print "Cutout at corner %s dim %s = " % (idgrp['XYZOFFSET'][:],idgrp['CUTOUT'].shape)
      print "%s voxels match identifier in cutout" % ( len(np.nonzero(np.array(idgrp['CUTOUT'][:,:,:]))[0]))

    if idgrp.get('XYZDIMENSION') and idgrp.get('XYZOFFSET'):
      print "Bounding box corner %s dim %s = " % (idgrp['XYZOFFSET'][:],idgrp['XYZDIMENSION'][:])

    if idgrp.get('CUBOIDS'):
      numvoxels = 0
      for k in idgrp.get('CUBOIDS').keys():
        cb = idgrp.get('CUBOIDS').get(k).get('CUBOID')
        numvoxels += len(np.nonzero(np.array(cb[:,:,:]))[0])
      print "%s voxels match identifier in cutout" % ( numvoxels )

  h5f.flush()
  h5f.close()

if __name__ == "__main__":
  main()

