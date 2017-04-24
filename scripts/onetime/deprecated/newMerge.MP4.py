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
import argparse
import numpy as np
import urllib2
import cStringIO
import sys

import tempfile
import h5py

import zindex

def main():

  parser = argparse.ArgumentParser(description='Merge double labeled voxels')
  parser.add_argument('baseurl', action="store")
  parser.add_argument('token', action="store")
  parser.add_argument('--resolution', type=int, action="store", help='Resolution at which you want the voxels.  Defaults to 1.', default=1)
  parser.add_argument('--firstzindex', type=int, action="store", help='Zindex at which the script should start.  Defaults to 0.', default=0)
  parser.add_argument('--lastzindex', type=int, action="store", help='Zindex at which the script should start.  Defaults to 0.', default=0)

  result = parser.parse_args()

  url = 'http://{}/ocpca/{}/info/'.format(result.baseurl,result.token)
  try:
    f = urllib2.urlopen ( url )
  except urllib2.URLError, e:
    raise

  projinfo = json.loads ( f.read() )

  # Get the source database sizes
  ximagesz, yimagesz = projinfo['dataset']['imagesize']['{}'.format(result.resolution)]
  startslice, endslice = projinfo['dataset']['slicerange']
  slices = endslice - startslice + 1

  # cubedim for this resolution 
  xcubedim, ycubedim, zcubedim =  projinfo['dataset']['cube_dimension']['{}'.format(result.resolution)]

  # Set the limits for iteration on the number of cubes in each dimension
  xlimit = (ximagesz-1)/xcubedim+1
  ylimit = (yimagesz-1)/ycubedim+1
  #  Round up the zlimit to the next larger
  zlimit = (((slices-1)/zcubedim+1)*zcubedim)/zcubedim

  # Round up to the top of the range
  if result.lastzindex == 0:
    lastzindex = (zindex.XYZMorton([xlimit,ylimit,zlimit])/64+1)*64
  else:
    lastzindex = (result.lastzindex/64+1)*64

  if result.firstzindex == 0:
    firstzindex = 0
  else:
    firstzindex = (result.firstzindex/64-1)*64

  # Iterate over the cubes in morton order
  for mortonidx in range(firstzindex, lastzindex, 64):

    # 0-63 is a 4 by 4 cube 0,0,0 to 3,3,3
    x1, y1, z1 = zindex.MortonXYZ ( mortonidx )
    x2, y2, z2 = zindex.MortonXYZ ( mortonidx+64-1 )

    # need to round up 3,3,3 to 4,4,4 * cubedime
    startx = x1*xcubedim
    stopx = min((x2+1)*xcubedim,ximagesz)
    starty = y1*ycubedim
    stopy = min((y2+1)*ycubedim,yimagesz)
    startz = z1*zcubedim + startslice
    stopz = min((z2+1)*zcubedim + startslice,endslice+1)
    if startx >= ximagesz or starty >= yimagesz or startz > endslice:
      continue

    url = "http://%s/ocpca/%s/exceptions/%s/%s,%s/%s,%s/%s,%s/" % (result.baseurl,result.token,result.resolution,startx,stopx,starty,stopy,startz,stopz) 
    try:
      f = urllib2.urlopen ( url )
    except urllib2.URLError, e:
      print "Failed URL", url
      print "Error %s" % (e) 
      sys.exit(0)

    print "Processing zindex: {}, url: {}".format(mortonidx,url)

    # Read into a temporary file
    tmpfile = tempfile.NamedTemporaryFile ( )
    tmpfile.write ( f.read() )
    tmpfile.seek(0)
    h5f = h5py.File ( tmpfile.name, driver='core', backing_store=False )

    # The exceptions are of the form x,y,x, id1, id2....
    if  h5f.get('exceptions'):
      listOfSets = list(h5f['exceptions'][:])
    # At this point we have a list of numpy arrays

    # You've got the data, clean up open file handles
    f.close()
    h5f.close()
    tmpfile.close()
      
    # one time conversion for the first element
    if len(listOfSets) <= 3:
      continue;

    first_set = listOfSets[0]
    listOfSets[0] = set(first_set[3:])
    listOfSets[0].discard(0)

    first = True

<<<<<<< HEAD:onetime/newMerge.MP4.py
# Combine the exceptions to get one disjoint set of exceptions.Each element in the set represents ids that have tp be merged
=======
    # Combine the exceptions to get one disjoint set of exceptions.
    # Each element in the set represents ids that have tp be merged
>>>>>>> microns:onetime/deprecated/newMerge.MP4.py
    while True:
      merged_one = False
      supersets = [listOfSets[0]]
    
      for elm in listOfSets[1:]:
        if first:
          s = set(elm[3:])
          s.discard(0)
        else:
          s = set(elm)
          s.discard(0)
        in_super_set= False
        for ss in supersets:
          if s & ss:
            ss |= s
            merged_one = True
            in_super_set = True
            break
        
        if not in_super_set:
          supersets.append(s)
<<<<<<< HEAD:onetime/newMerge.MP4.py
      #     print supersets
=======
      # print supersets
>>>>>>> microns:onetime/deprecated/newMerge.MP4.py
      if not merged_one:
        break
      

      listOfSets = supersets
      first = False
   
    # Each element in the superset corresponds to onelist of ids that has to be merged
    print "==================Merging annotations========================"
    print "Number of merge calls %s" % len(supersets)
    for elm in supersets:
      if len(elm) == 1:
        continue
      mergeids = ','.join([str(n) for n in elm]) 
      url="http://%s/ocpca/%s/merge/%s/global/%s/"%(result.baseurl,result.token, mergeids, result.resolution)
      print url
      try:
        f = urllib2.urlopen ( url )
      except urllib2.URLError, e:
        print "Failed URL", url
        print "Error %s" % (e)
        sys.exit(0)

if __name__ == "__main__":
  main()
<<<<<<< HEAD:onetime/newMerge.MP4.py

=======
>>>>>>> microns:onetime/deprecated/newMerge.MP4.py
