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
import urllib, urllib2
import cStringIO
from contextlib import closing
import csv


"""Take a csv file and apply a new threshhold.  Write the file and return a count."""


def main():

  parser = argparse.ArgumentParser(description='Apply a new threshhold')
  parser.add_argument('infile', action="store")
  parser.add_argument('outfile', action="store")
  parser.add_argument('threshhold', action="store", type=int, help='Minimum value')
  
  result = parser.parse_args()

  count = 0

  with closing ( open ( result.infile )) as fin:
    with closing ( open ( result.outfile, "w+" )) as fout:

      reader = csv.reader ( fin )
      writer = csv.writer ( fout )

      for row in reader:
        if int(row[3]) >= result.threshhold:
          writer.writerow ( row )
          count += 1
          
  print count


if __name__ == "__main__":
  main()

