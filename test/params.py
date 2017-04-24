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

from ndlib.ndtype import *

class Params:
  """Arguments Class"""
  
  def __init__ (self):
    self.token = 'unittest'
    self.project = 'unittest'
    self.time = [0, 100]
    self.window = [0, 500]
    self.voxel = [4.0, 4.0, 3.0]
    self.channel_type = TIMESERIES
    self.datatype = UINT8
    self.resolution = 0
    self.channels = ['TIME1', 'TIME2']
    self.num_objects = 1
    self.args = None
    self.annoid = 0
    self.field = None
    self.value = None
    self.anntype = 1
