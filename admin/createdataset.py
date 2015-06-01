# Copyright 2014 Open Connectome Project (http://openconnecto.me)
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#    http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import os
import sys

sys.path += [os.path.abspath('../django')]
import OCP.settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'OCP.settings'
from django.conf import settings

import ocpcaproj

def main():

  parser = argparse.ArgumentParser(description='Create a new dataset.')
  parser.add_argument('dsname', action="store", help='Name of the dataset')
  parser.add_argument('ximagesize', type=int, action="store")
  parser.add_argument('yimagesize', type=int, action="store")
  parser.add_argument('zimagesize', type=int, action="store")
  parser.add_argument('xoffset', type=int, action="store")
  parser.add_argument('yoffset', type=int, action="store")
  parser.add_argument('zoffset', type=int, action="store")
  parser.add_argument('xvoxelres', type=float, action="store")
  parser.add_argument('yvoxelres', type=float, action="store")
  parser.add_argument('zvoxelres', type=float, action="store")
  parser.add_argument('scalinglevels', type=int, action="store")
  parser.add_argument('scalingoption', type=str, action="store", help='should be isotropic or zslices', default='zslices')
  parser.add_argument('--startwindow', type=int, action="store", default=0)
  parser.add_argument('--endwindow', type=int, action="store", default=0)
  parser.add_argument('--starttime', type=int, action="store", default=0)
  parser.add_argument('--endtime', type=int, action="store", default=0)

  result = parser.parse_args()

  # Get database info
  pd = ocpcaproj.OCPCAProjectsDB()


  imagesize = (result.ximagesize,result.yimagesize,result.zimagesize)
  offset = (result.xoffset,result.yoffset,result.zoffset)
  voxelres = (result.xvoxelres,result.yvoxelres,result.zvoxelres)
  pd.newDataset ( result.dsname, imagesize, offset, voxelres, result.scalinglevels, result.scalingoption, result.startwindow, result.endwindow, result.starttime, result.endtime ) 


if __name__ == "__main__":
  main()


  
