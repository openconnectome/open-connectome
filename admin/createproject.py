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

  parser = argparse.ArgumentParser(description='Create a new annotation project.')
  parser.add_argument('token', action="store")
  parser.add_argument('openid', action="store")
  parser.add_argument('host', action="store")
  parser.add_argument('project', action="store")
  parser.add_argument('datatype', action="store", type=int, help='1 8-bit data or 2 32-bit annotations' )
  parser.add_argument('dataset', action="store")
  parser.add_argument('dataurl', action="store")
  parser.add_argument('--kvserver', action="store", default='localhost')
  parser.add_argument('--kvengine', action="store", default='MySQL')
  parser.add_argument('--readonly', action='store_true', help='Project is readonly')
  parser.add_argument('--public', action='store_true', help='Project is readonly')
  parser.add_argument('--noexceptions', action='store_true', help='Project has no exceptions.  (FASTER).')
  parser.add_argument('--nocreate', action='store_true', help='Do not create a database.  Just make a project entry.')
  parser.add_argument('--resolution', action='store',type=int, help='Maximum resolution for an annotation projects', default=0)

  result = parser.parse_args()

  import pdb; pdb.set_trace()

  # Get database info
  pd = ocpcaproj.OCPCAProjectsDB()
  pd.newOCPCAProj ( result.token, result.openid, result.host, result.project, result.datatype, result.dataset, result.dataurl, result.readonly, not result.noexceptions, result.nocreate, result.resolution, result.public, result.kvserver, result.kvengine, False )


if __name__ == "__main__":
  main()


  
