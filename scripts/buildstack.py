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

import argparse
import sys
import os
import numpy as np
import urllib, urllib2
import cStringIO

sys.path += [os.path.abspath('../django')]
import OCP.settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'OCP.settings'
from django.conf import settings

import ocpcastack

"""Construct an annotation hierarchy off of a completed annotation database."""


def main():

  parser = argparse.ArgumentParser(description='Build a stack of annotations')
  parser.add_argument('token', action="store", help='Token for the annotation project.')
  parser.add_argument('resolution', action="store", type=int, help='Start (highest) resolution')
  
  result = parser.parse_args()

  # Iterate over the database creating the hierarchy
  ocpcastack.buildStack ( result.token, result.resolution )

if __name__ == "__main__":
  main()

