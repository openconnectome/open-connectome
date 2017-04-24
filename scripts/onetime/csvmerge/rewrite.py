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
import sys
import os
import numpy as np
import cStringIO
import csv
import MySQLdb


import ocppaths
import ocpcarest
import zindex


#
# Rewrite an annotation database based on a remapping
#

def main():

  parser = argparse.ArgumentParser(description='Create a mergemap file.')
  parser.add_argument('dbname', action="store", help='Database in which to store the merge.')
  parser.add_argument('table', action="store", help='Table in which to store the merge.')
  parser.add_argument('dbuser', action="store", help='Database user')
  parser.add_argument('dbpass', action="store", help='Database passwd')
  parser.add_argument('intoken', action="store", help='Database passwd')
  parser.add_argument('outtoken', action="store", help='Database passwd')
  parser.add_argument('--resolution', action="store", help='Database passwd', default=0)

  result = parser.parse_args()

  # Connection info 
  try:
    mmconn = MySQLdb.connect (host = 'localhost',
                          user = result.dbuser,
                          passwd = result.dbpass,
                          db = result.dbname )
  except MySQLdb.Error, e:
    print("Failed to connect to database: %s" % (result.dbname))
    raise

  # get a cursor of the mergemap
  mmcursor = mmconn.cursor()

  # load the in database
  [ indb, inproj, inprojdb ] = ocpcarest.loadDBProj ( result.intoken )

  # load the out database
  [ outdb, outproj, outprojdb ] = ocpcarest.loadDBProj ( result.outtoken )

  # get the dataset configuration
  (xcubedim,ycubedim,zcubedim) = inproj.datasetcfg.cubedim[result.resolution]
  (ximagesz,yimagesz) = inproj.datasetcfg.imagesz[result.resolution] 
  (startslice,endslice) = inproj.datasetcfg.slicerange
  slices = endslice - startslice + 1

  # Set the limits for iteration on the number of cubes in each dimension
  xlimit = (ximagesz-1)/xcubedim+1
  ylimit = (yimagesz-1)/ycubedim+1
  #  Round up the zlimit to the next larger
  zlimit = (((slices-1)/zcubedim+1)*zcubedim)/zcubedim

  lastzindex = (zindex.XYZMorton([xlimit,ylimit,zlimit])/64+1)*64

  # iterate over the cubes in morton order
  for mortonidx in range(lastzindex):

    x,y,z = zindex.MortonXYZ ( mortonidx )
  
    # only process cubes in the space
    if x >= xlimit or y >= ylimit or z >= zlimit:
      continue

    incube = indb.getCube ( mortonidx, result.resolution )
    annoids =  np.unique ( incube.data )

    sql = "select * from {} where source in ({})".format(mergemap,','.join(annoids))

    # relabel the cube

#    outdb.putCube ( mortonidx, result.resolution  ) 

    if mortonidx % 256 == 0:
      outdb.commit()

    



      
 


if __name__ == "__main__":
  main()
