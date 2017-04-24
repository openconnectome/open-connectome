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

import os
import sys
import csv
import random
import argparse
import numpy as np
import multiprocessing
import math
import time
import json
import blosc
from operator import add, sub, mul
sys.path += [os.path.abspath('../django/')]
import ND.settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'ND.settings'
from ndlib.ndtype import *
from ndlib.restutil import *
from scripts.scripts_helper import *

class BenchmarkTest:

  def __init__(self, result):
    """Init"""

    self.host_name = result.host_name
    self.token_name = result.token_name
    self.channels = [result.channel_name]
    self.resolution = result.res_value
    self.fetch_list = []
    self.data_list = []
    self.write_tests = result.write_tests
    self.direct = result.direct
    self.scale = result.scale
    self.info_interface = InfoInterface(self.host_name, self.token_name)
    self.datatype = ND_dtypetonp[self.info_interface.get_channel_datatype(result.channel_name)]

  def singleThreadTest(self, start_value, size_iterations):
    """Generate the URL for read test"""
    
    min_values = [xmin,ymin,zmin] = map(add, self.info_interface.offset(self.resolution), start_value)
    max_values = map(add, min_values, self.info.cuboid_dimension(self.resolution))
    range_args = [None]*(len(min_values)+len(max_values))
    
    for i in range(0, size_iterations, 1):
      if all([a<b for a,b in zip(max_values, self.info_interface.image_size(self.resolution))]):
        range_args[::2] = min_values
        range_args[1::2] = max_values
        # print "Size", reduce(mul, map(sub, max_values, min_values), 1)*2.0/(1024*1024)
        if self.write_tests:
          data = blosc.pack_array(np.ones( [len(self.channels)]+map(sub, range_args[1::2], range_args[::2])[::-1], dtype=self.datatype) * random.randint(0,255))
          self.data_list.append(data)
          self.fetch_list.append(generateURLBlosc(self.host_name, self.token_name, self.channels, self.resolution, range_args, direct=self.direct))
        else:
          self.fetch_list.append(generateURLBlosc(self.host_name, self.token_name, self.channels, self.resolution, range_args, direct=self.direct))
        # min_values = max_values
        # max_values = map(add, map(sub, min_values, temp_values), min_values)
        min_values[2] = max_values[2]
        max_values[2] = min_values[2] + self.info.cuboid_dimension(self.resolution)[2] 
        max_values[(i+1)%2] = start_value[(i+1)%2] + (max_values[(i+1)%2]-min_values[(i+1)%2])*2
      else:
        break

  def multiThreadTest(self, start_value, size_iterations, number_of_processes):
    """Generate the URL for multi-thread test"""
    
    # min_values = [xmin,ymin,zmin] = map(add, self.info_interface.offset(self.resolution), start_value)
    min_values = [xmin, ymin, zmin] = self.info_interface.offset(self.resolution)
    # max_values = map(add, min_values, self.info_interface.cuboid_dimension(self.resolution))
    max_values = map(add, min_values, map(lambda x: x*self.scale, self.info_interface.supercuboid_dimension(self.resolution)))
    range_args = [None]*(len(min_values)+len(max_values))
    size_args = [None]*(len(min_values)+len(max_values))
    
    # determine the size of the cutout
    for i in range(0, size_iterations, 1):
      if all([a<b for a,b in zip(max_values, self.info_interface.image_size(self.resolution))]):
        size_args[::2] = min_values
        size_args[1::2] = max_values
        # increase in x,y
        max_values[(i+1)%2] = (max_values[(i+1)%2]-min_values[(i+1)%2])*2
      else:
        break
    
    # intialize the range args
    range_args[:] = size_args[:]
    range_args[::2] = map(add, start_value, size_args[::2])
    range_args[1::2] = map(add, start_value, size_args[1::2])
    
    # creating a fetch list for each process
    for i in range(0, number_of_processes, 1):
      # checking if the x,y,z dimensions are exceeded
      if all([a<b for a,b in zip(range_args[1::2], self.info_interface.image_size(self.resolution))]):
        if self.write_tests:
          data = blosc.pack_array(np.ones( [len(self.channels)]+map(sub, range_args[1::2], range_args[::2])[::-1], dtype=self.datatype) * random.randint(0,255))
          self.data_list.append(data)
          self.fetch_list.append(generateURLBlosc(self.host_name, self.token_name, self.channels, self.resolution, range_args, direct=self.direct))
        else:
          self.fetch_list.append(generateURLBlosc(self.host_name, self.token_name, self.channels, self.resolution, range_args, direct=self.direct))
        # checking if this exceeds the x,y image size
        if all([a<b for a,b in zip(map(add, range_args[1:-1:2], size_args[1:-1:2]), self.info_interface.image_size(self.resolution))]): 
          range_args[0:-2:2] = range_args[1:-1:2]
          range_args[1:-1:2]  = map(add, range_args[1:-1:2], size_args[1:-1:2])
        # if you cannot expand more in x,y then expand in z
        elif range_args[-1] < self.info_interface.image_size(self.resolution)[-1]:
          range_args[-2] = range_args[-1]
          range_args[-1] = range_args[-1] + size_args[-1]
        else:
          break
      else:
        break


def dropCache():
  """Drop the system cache"""
  pass
  # os.system('sudo bash -c "echo 3 > /proc/sys/vm/drop_caches"')
  # subprocess.call(['sudo', 'echo 3','>','/proc/sys/vm/drop_caches'])


def main():
  """Take in the arguments"""

  parser = argparse.ArgumentParser(description='Run the Benchmark script')
  parser.add_argument("token_name", action="store", type=str, help="Token Name")
  parser.add_argument("channel_name", action="store", type=str, help="Channel Name")
  parser.add_argument("res_value", action="store", type=int, help="Resolution")
  parser.add_argument("--host", dest="host_name", action="store", type=str, default="localhost/nd", help="Host Name")
  parser.add_argument("--direct", dest="direct", action="store", type=bool, default=False, help="Direct to S3")
  parser.add_argument('--offset', dest="offset_value", nargs=3, action="store", type=int, metavar=('X','Y','Z'), default=[0,0,0], help='Start Offset')
  parser.add_argument("--num", dest="number_of_processes", action="store", type=int, default=1, help="Number of Processes")
  parser.add_argument("--size", dest="data_size", action="store", type=int, default=1, help="Size of Data")
  parser.add_argument("--scale", dest="scale", action="store", type=int, default=1, help="Scale of Data")
  parser.add_argument("--iter", dest="number_of_iterations", action="store", type=int, default=1, help="Number of Iterations")
  parser.add_argument("--write", dest="write_tests", action="store", type=bool, default=False, help="Do write tests")
  
  result = parser.parse_args()
  
  # creating the benchmark class here
  # setting the number of processes here
  p = multiprocessing.Pool(result.number_of_processes)
  
  # opening the csv file here
  with open('{}_{}_threads.csv'.format('write' if result.write_tests else 'read' , result.number_of_processes), 'a+') as csv_file:
    
    csv_reader = csv.reader(csv_file, delimiter=',')
    csv_writer = csv.writer(csv_file, delimiter=',')
    
    # iterating over data size
    for data_size in range(1, result.data_size+1, 1):
      
      # setting the time value list to zero
      time_values = []

      # if result.number_of_processes == 1:
        # bt.singleThreadTest(result.offset_value, data_size)
      # else:
      bt = BenchmarkTest(result)
      bt.multiThreadTest(result.offset_value, data_size, result.number_of_processes)
    
      # from pprint import pprint
      # pprint(bt.fetch_list)
      
      for iter_number in range(result.number_of_iterations):
        
        dropCache()
        start_time = time.time()
        
        if result.write_tests:
          p.map(putURL, zip(bt.fetch_list,bt.data_list))
        else:
          p.map(getURL, bt.fetch_list)
        
        time_values.append(time.time()-start_time)
      
      actual_size = 0
      if bt.datatype == np.uint8:
        acutal_size = [math.pow(2,data_size-3)]
      elif bt.datatype == np.uint16:
        actual_size = [math.pow(2,data_size-2)]
      elif bt.datatype == np.uint32:
        actual_size = [math.pow(2,data_size-1)]
      
      csv_writer.writerow([actual_size]+time_values)


if __name__ == '__main__':
  main()
