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
from collections import defaultdict

import csv
import MySQLdb

import ocppaths
import ocpcarest
import zindex

# Make it so that you can get settings from django
sys.path += [os.path.abspath('../../django')]
os.environ['DJANGO_SETTINGS_MODULE'] = 'OCP.settings'

from django.conf import settings

import logging
logger=logging.getLogger("neurodata")

#import logging
#logger=logging.getLogger("ocpcatmaid")

#
# Take Dean's CSV file and put it into a database
#

def main():

  parser = argparse.ArgumentParser(description='Create a mergemap file.')
  parser.add_argument('baseurl', action="store", help='Baseurl for OCP service')
  parser.add_argument('token', action="store", help='Database token to access')
  parser.add_argument('csvfile', action="store", help='File containing csv list of merges.')

  # customize for kasthuri11 
  resolution = 1

  result = parser.parse_args()

  # Convert the csv file into a dictionary
  f = open ( result.csvfile )

  # default dictionary of integers
  d = defaultdict(int)

  csvr = csv.reader(f, delimiter=',')
  for r in csvr:
    for s in r[1:]:
      d[int(s)]=int(r[0])

  # load the in database
  [ db, proj, projdb ] = ocpcarest.loadDBProj ( result.token )

  # get the dataset configuration
  (xcubedim,ycubedim,zcubedim) = proj.datasetcfg.cubedim[resolution]
  (ximagesz,yimagesz) = proj.datasetcfg.imagesz[resolution] 
  (startslice,endslice) = proj.datasetcfg.slicerange
  slices = endslice - startslice + 1

  # iterate over the defined set of cubes in the database
  sql = "SELECT zindex from res1;"
  cursor = db.conn.cursor()
  cursor.execute(sql)
  zindexes = np.array([item[0] for item in cursor.fetchall()])

  i=0

  # iterate over the cubes in morton order
  for mortonidx in zindexes:

    print "Working on cube {}".format(i)
    i = i+1

    cuboid = db.getCube ( mortonidx, resolution )
    annoids =  np.unique ( cuboid.data )
    for id in annoids:
      if d[id]!=0:
        print "Rewrite id {} to {} for cube {}".format(id,d[id],mortonidx)
        vec_func = np.vectorize ( lambda x: x if x != id else d[id] )
        cuboid.data = vec_func ( cuboid.data )
      else:
        if id != 0:
          print "Id {} is one of the target identifiers".format(id)

    db.putCube ( mortonidx, resolution, cuboid )
    db.commit()
    


  

      
 


if __name__ == "__main__":
  main()
