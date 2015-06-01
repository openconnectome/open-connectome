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

import numpy as np

def filterCutout ( cutout, filterlist ):
  """Remove all annotations in a cutout that do not match the filterlist"""

  # dumbest implementation
  for z in range(cutout.shape[0]):
    for y in range(cutout.shape[1]):
      for x in range(cutout.shape[2]):
        if cutout[z,y,x] not in filterlist:
          cutout[z,y,x] = 0
          

