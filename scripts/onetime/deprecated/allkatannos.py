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
import argparse
import numpy as np
import urllib2
import cStringIO
import sys

import tempfile
import h5py


# Annotation types
anno_names = { 1:'ANNO_ANNOTATION',\
               2:'ANNO_SYNAPSE',\
               3:'ANNO_SEED',\
               4:'ANNO_SEGMENT',\
               5:'ANNO_NEURON',\
               6:'ANNO_ORGANELLE' }

def main():

  parser = argparse.ArgumentParser(description='Download all annotations for a database')
  parser.add_argument('baseurl', action="store")
  parser.add_argument('token', action="store")
  parser.add_argument('outputdir', action="store", help='Directory into which to write HDF5 files')
  parser.add_argument('--resolution', action="store", help='Resolution at which you want the voxels.  Defaults to the annotation database resolution.', default=None)
  parser.add_argument('--cutout', action='store_true', help='Return a cutout instead of a list of voxels.')
  parser.add_argument('--status', type=int, action="store", default=None )
  parser.add_argument('--type', type=int, action="store", default=None )

  result = parser.parse_args()

  #  First let's get the list of annotations
  url = 'http://%s/emca/%s/list/' % ( result.baseurl, result.token )
  if result.type != None:
    url += 'type/%s/' % ( result.type )
  if result.status != None:
    url += 'status/%s/' % ( result.status )

  print "Getting the list of annotations from ", url

  # Get cube in question
  try:
    f = urllib2.urlopen ( url )
  except urllib2.URLError, e:
    print "Failed URL", url
    print "Error %s" % (e.read())
    sys.exit(0)

  # Now we are processing the return.  New tmpfile, new h5f
  tmpfile = tempfile.NamedTemporaryFile ( )
  tmpfile.write ( f.read() )
  f.close()
  tmpfile.tell()
  h5f = h5py.File ( tmpfile.name, driver='core', backing_store=False )

  if h5f.get('ANNOIDS'):
    if len(h5f['ANNOIDS']) == 0:
      print "Found no annotations matching type and status"
      sys.exit(0)
  else:
    print "Malformed HDF5 file!"
    sys.exit(0)

  for annoid in np.array(h5f['ANNOIDS'][:]):

    # Figure out how big the object is:
    if result.resolution == None:
      url = "http://%s/emca/%s/%s/boundingbox/" % (result.baseurl,result.token,annoid)
    else:
      url = "http://%s/emca/%s/%s/boundingbox/%s/" % (result.baseurl,result.token,result.annids, annoid)

    # Get annotation in question
    try:
      f = urllib2.urlopen ( url )
    except urllib2.URLError, e:
      print "Failed URL", url
      print "Error %s" % (e) 
      sys.exit(0)


    # create an in memory h5 file
    # Read into a temporary file
    tmpfile = tempfile.NamedTemporaryFile ( )
    tmpfile.write ( f.read() )
    f.close()
    tmpfile.tell()
    h5f = h5py.File ( tmpfile.name, driver='core', backing_store=False )

    # If the bounding box is bigger than 100M, don't cut out
    idgrp = h5f.get(h5f.keys()[0])
    print "Bounding box corner %s dim %s = " % (idgrp['XYZOFFSET'][:],idgrp['XYZDIMENSION'][:])
    cutoutdim = idgrp['XYZDIMENSION'][:]
    if cutoutdim[0]*cutoutdim[1]*cutoutdim[2] > 2**27:
     sys.stderr.write("Not fetching annotation %s now.  It's too big. %s bytes.\n" % ( annoid, cutoutdim[0]*cutoutdim[1]*cutoutdim[2]))
     sys.stderr.flush()
     continue

    h5f.close()
  
    #  Get voxel lists for all other annotations and write to the output directory
    if not result.cutout:
      if result.resolution == None:
        url = "http://%s/emca/%s/%s/voxels/" % (result.baseurl,result.token,annoid)
      else:
        url = "http://%s/emca/%s/%s/voxels/%s/" % (result.baseurl,result.token,annoid, result.resolution)
    # or get a cutout if requested instead
    else:
      if result.resolution == None:
        url = "http://%s/emca/%s/%s/cutout/" % (result.baseurl,result.token,annoid)
      else:
        url = "http://%s/emca/%s/%s/cutout/%s/" % (result.baseurl,result.token,annoid, result.resolution)

    # Get annotation in question
    try:
      f = urllib2.urlopen ( url )
    except urllib2.URLError, e:
      print "Failed URL", url
      print "Error %s" % (e.read()) 
      sys.exit(0)

    # Create an output file
    filename = "/tmp/anno" + str(annoid) + ".h5"
    fh = open ( filename, 'w' )
    fh.write ( f.read() )
    fh.tell()
    h5f = h5py.File ( filename )

    idgrp = h5f.get(h5f.keys()[0])

    print "Annotation id: ", h5f.keys()[0]
    print "Annotation type: ", anno_names[idgrp['ANNOTATION_TYPE'][0]]

    mdgrp = idgrp['METADATA']

    if idgrp.get('VOXELS'):
      print "Voxel list for object of length", len(idgrp['VOXELS'][:])
#      print idgrp['VOXELS'][:]
    elif not result.cutout:
      print "No voxels found at this resolution"

    if idgrp.get('CUTOUT') and idgrp.get('XYZOFFSET'):
      print "Cutout at corner %s dim %s = " % (idgrp['XYZOFFSET'][:],idgrp['CUTOUT'].shape)
      print "%s voxels match identifier in cutout" % ( len(np.nonzero(np.array(idgrp['CUTOUT'][:,:,:]))[0]))

    h5f.flush()
    h5f.close()

if __name__ == "__main__":
  main()

